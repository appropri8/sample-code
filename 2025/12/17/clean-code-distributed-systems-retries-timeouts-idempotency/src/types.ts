/**
 * Shared type definitions
 */

export interface HttpError extends Error {
  statusCode: number;
  message: string;
}

export interface ChargeRequest {
  amount: number;
  customerId: string;
}

export interface ChargeResult {
  transactionId: string;
  amount: number;
  status: 'success' | 'failed';
}

export interface OrderMessage {
  messageId: string;
  orderId: string;
  userId: string;
  items: OrderItem[];
}


export interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: string;
  userId: string;
  items: OrderItem[];
  total: number;
  status: 'pending' | 'confirmed' | 'cancelled';
}

export function isRetryableError(error: Error): boolean {
  if ('statusCode' in error) {
    const httpError = error as HttpError;
    return httpError.statusCode === 503 || 
           httpError.statusCode === 429 ||
           (httpError.statusCode >= 500 && httpError.statusCode < 600);
  }
  return false;
}
