export interface CreateOrderRequest {
  cart_id: string;
  items: OrderItem[];
  user_id: string;
}

export interface OrderItem {
  product_id: string;
  quantity: number;
  price: number;
}

export interface Order {
  order_id: string;
  user_id: string;
  cart_id: string;
  status: string;
  total_amount: number;
  items: OrderItem[];
  created_at: Date;
}

export interface IdempotencyResponse {
  cached: boolean;
  response: any;
}

export interface ProcessedMessage {
  idempotency_key: string;
  topic: string;
  partition?: number;
  offset?: number;
  processed_at: Date;
}
