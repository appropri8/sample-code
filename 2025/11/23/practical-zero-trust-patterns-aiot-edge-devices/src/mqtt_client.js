/**
 * Mutual TLS MQTT client for edge devices (Node.js)
 */

const mqtt = require('mqtt');
const fs = require('fs');

/**
 * Create MQTT client with mTLS
 * @param {string} deviceId - Device identifier
 * @param {string} deviceCertPath - Path to device certificate
 * @param {string} deviceKeyPath - Path to device private key
 * @param {string} caCertPath - Path to CA certificate
 * @param {string} brokerUrl - MQTT broker URL
 * @returns {mqtt.MqttClient} MQTT client instance
 */
function createMQTTClient(
  deviceId,
  deviceCertPath = process.env.DEVICE_CERT || '/etc/device/certs/device.crt',
  deviceKeyPath = process.env.DEVICE_KEY || '/etc/device/certs/device.key',
  caCertPath = process.env.CA_CERT || '/etc/device/certs/ca.crt',
  brokerUrl = process.env.MQTT_BROKER_URL || 'mqtts://iot.example.com:8883'
) {
  // Read certificates
  const deviceCert = fs.readFileSync(deviceCertPath);
  const deviceKey = fs.readFileSync(deviceKeyPath);
  const caCert = fs.readFileSync(caCertPath);

  // Create client with mTLS
  const client = mqtt.connect(brokerUrl, {
    clientId: deviceId,
    cert: deviceCert,
    key: deviceKey,
    ca: caCert,
    rejectUnauthorized: true, // Verify server certificate
    protocolVersion: 4,
    protocol: 'mqtts',
    reconnectPeriod: 5000,
    connectTimeout: 30000,
  });

  // Event handlers
  client.on('connect', () => {
    console.log('Connected to MQTT broker');
    // Subscribe to device-specific topic
    client.subscribe(`devices/${deviceId}/commands`);
  });

  client.on('message', (topic, message) => {
    console.log(`Received message on ${topic}: ${message.toString()}`);
  });

  client.on('error', (error) => {
    console.error('MQTT error:', error);
  });

  client.on('close', () => {
    console.log('Disconnected from MQTT broker');
  });

  return client;
}

/**
 * Publish telemetry data
 * @param {mqtt.MqttClient} client - MQTT client instance
 * @param {string} deviceId - Device identifier
 * @param {object} telemetryData - Telemetry data to publish
 */
function publishTelemetry(client, deviceId, telemetryData) {
  const topic = `devices/${deviceId}/telemetry`;
  const payload = JSON.stringify(telemetryData);
  
  client.publish(topic, payload, (err) => {
    if (err) {
      console.error('Publish error:', err);
    } else {
      console.log(`Published telemetry to ${topic}`);
    }
  });
}

module.exports = {
  createMQTTClient,
  publishTelemetry,
};

