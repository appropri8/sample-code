import axios, { AxiosInstance } from 'axios';
import { PaymentRequest, PaymentResponse, PaymentError } from '../types';

export class OrderService {
  private client: AxiosInstance;

  constructor(billingServiceUrl: string) {
    this.client = axios.create({
      baseURL: billingServiceUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 5000,
    });
  }

  async createPayment(request: PaymentRequest): Promise<PaymentResponse> {
    try {
      const response = await this.client.post<PaymentResponse>('/payments', request);
      return response.data;
    } catch (error: any) {
      if (error.response) {
        const paymentError: PaymentError = error.response.data;
        throw new Error(`Payment failed: ${paymentError.error} (${paymentError.code})`);
      }
      throw error;
    }
  }
}

