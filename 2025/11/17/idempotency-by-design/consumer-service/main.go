package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/lib/pq"
	"github.com/IBM/sarama"
)

type Consumer struct {
	db          *sql.DB
	consumer    sarama.Consumer
	producer    sarama.SyncProducer
	outboxTopic string
}

type OrderCreatedEvent struct {
	OrderID string  `json:"orderId"`
	UserID  string  `json:"userId"`
	Amount  float64 `json:"amount"`
}

func NewConsumer(dbURL, brokerList, outboxTopic string) (*Consumer, error) {
	// Database connection
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// Kafka consumer config
	config := sarama.NewConfig()
	config.Consumer.Return.Errors = true
	config.Consumer.Offsets.Initial = sarama.OffsetOldest

	consumer, err := sarama.NewConsumer([]string{brokerList}, config)
	if err != nil {
		return nil, fmt.Errorf("failed to create consumer: %w", err)
	}

	// Kafka producer config for outbox
	producerConfig := sarama.NewConfig()
	producerConfig.Producer.Return.Successes = true
	producerConfig.Producer.Transactional.ID = "outbox-producer"

	producer, err := sarama.NewSyncProducer([]string{brokerList}, producerConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create producer: %w", err)
	}

	return &Consumer{
		db:          db,
		consumer:    consumer,
		producer:    producer,
		outboxTopic: outboxTopic,
	}, nil
}

func (c *Consumer) ProcessMessage(msg *sarama.ConsumerMessage) error {
	messageID := string(msg.Key)
	if messageID == "" {
		messageID = fmt.Sprintf("%s-%d", msg.Topic, msg.Offset)
	}

	log.Printf("Processing message: topic=%s, partition=%d, offset=%d, key=%s",
		msg.Topic, msg.Partition, msg.Offset, messageID)

	// Check inbox for duplicate
	var existingID string
	err := c.db.QueryRow(
		"SELECT message_id FROM inbox WHERE message_id = $1",
		messageID,
	).Scan(&existingID)

	if err == nil {
		log.Printf("Message %s already processed, skipping", messageID)
		return nil
	}

	if err != sql.ErrNoRows {
		return fmt.Errorf("failed to check inbox: %w", err)
	}

	// Process message
	start := time.Now()
	if err := c.handleMessage(msg); err != nil {
		return fmt.Errorf("failed to handle message: %w", err)
	}
	duration := time.Since(start)

	// Insert into inbox
	_, err = c.db.Exec(
		`INSERT INTO inbox (message_id, topic, payload, processed_at, processing_duration_ms) 
		 VALUES ($1, $2, $3, $4, $5)`,
		messageID,
		msg.Topic,
		msg.Value,
		time.Now(),
		duration.Milliseconds(),
	)

	if err != nil {
		// Race condition check - another consumer might have processed it
		var checkID string
		checkErr := c.db.QueryRow(
			"SELECT message_id FROM inbox WHERE message_id = $1",
			messageID,
		).Scan(&checkID)

		if checkErr == nil {
			log.Printf("Message %s processed by another consumer, skipping", messageID)
			return nil
		}

		return fmt.Errorf("failed to insert into inbox: %w", err)
	}

	log.Printf("Message %s processed successfully in %v", messageID, duration)
	return nil
}

func (c *Consumer) handleMessage(msg *sarama.ConsumerMessage) error {
	var event OrderCreatedEvent
	if err := json.Unmarshal(msg.Value, &event); err != nil {
		return fmt.Errorf("failed to unmarshal event: %w", err)
	}

	log.Printf("Processing order created event: orderId=%s, userId=%s, amount=%.2f",
		event.OrderID, event.UserID, event.Amount)

	// Business logic here
	// For example: update inventory, send notification, etc.
	
	// Simulate processing
	time.Sleep(10 * time.Millisecond)

	return nil
}

func (c *Consumer) ProcessOutbox() error {
	rows, err := c.db.Query(
		`SELECT id, message_id, topic, payload 
		 FROM outbox 
		 WHERE published_at IS NULL 
		 ORDER BY created_at ASC 
		 LIMIT 100`,
	)
	if err != nil {
		return fmt.Errorf("failed to query outbox: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var id int64
		var messageID, topic string
		var payload []byte

		if err := rows.Scan(&id, &messageID, &topic, &payload); err != nil {
			log.Printf("Failed to scan outbox row: %v", err)
			continue
		}

		// Publish to Kafka
		producerMsg := &sarama.ProducerMessage{
			Topic: topic,
			Key:   sarama.StringEncoder(messageID),
			Value: sarama.ByteEncoder(payload),
		}

		partition, offset, err := c.producer.SendMessage(producerMsg)
		if err != nil {
			log.Printf("Failed to publish message %s: %v", messageID, err)
			continue
		}

		log.Printf("Published message %s to topic %s, partition %d, offset %d",
			messageID, topic, partition, offset)

		// Mark as published
		_, err = c.db.Exec(
			"UPDATE outbox SET published_at = $1 WHERE id = $2",
			time.Now(), id,
		)
		if err != nil {
			log.Printf("Failed to mark message %s as published: %v", messageID, err)
		}
	}

	return nil
}

func (c *Consumer) StartOutboxProcessor() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		if err := c.ProcessOutbox(); err != nil {
			log.Printf("Error processing outbox: %v", err)
		}
	}
}

func (c *Consumer) Consume(topic string) error {
	partitionList, err := c.consumer.Partitions(topic)
	if err != nil {
		return fmt.Errorf("failed to get partitions: %w", err)
	}

	for _, partition := range partitionList {
		pc, err := c.consumer.ConsumePartition(topic, partition, sarama.OffsetOldest)
		if err != nil {
			return fmt.Errorf("failed to consume partition %d: %w", partition, err)
		}

		go func(pc sarama.PartitionConsumer) {
			for msg := range pc.Messages() {
				if err := c.ProcessMessage(msg); err != nil {
					log.Printf("Error processing message: %v", err)
				}
			}
		}(pc)
	}

	return nil
}

func (c *Consumer) Close() error {
	if err := c.consumer.Close(); err != nil {
		return err
	}
	if err := c.producer.Close(); err != nil {
		return err
	}
	return c.db.Close()
}

func main() {
	dbURL := getEnv("DATABASE_URL", "postgres://localhost/idempotency_example?sslmode=disable")
	brokerList := getEnv("KAFKA_BROKERS", "localhost:9092")
	topic := getEnv("KAFKA_TOPIC", "order.created")
	outboxTopic := getEnv("OUTBOX_TOPIC", "order.created")

	consumer, err := NewConsumer(dbURL, brokerList, outboxTopic)
	if err != nil {
		log.Fatalf("Failed to create consumer: %v", err)
	}
	defer consumer.Close()

	// Start outbox processor
	go consumer.StartOutboxProcessor()

	// Start consuming
	if err := consumer.Consume(topic); err != nil {
		log.Fatalf("Failed to consume: %v", err)
	}

	// Keep running
	select {}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

