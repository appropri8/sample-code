export interface PaymentRequest {
  orderId: string;
  amount: number;
  currency: string;
  paymentMethod: {
    type: string;
    last4: string;
  };
}

export interface PaymentResponse {
  paymentId: string;
  status: string;
  amount: number;
  currency: string;
  processedAt: string;
}

export interface PaymentError {
  error: string;
  code: string;
}

