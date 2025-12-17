// Shared TypeScript types for clean code examples

export interface User {
  id: string;
  email: string;
  name: string;
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
  status: 'pending' | 'processing' | 'completed' | 'cancelled';
  total?: number;
  shippingAddress?: Address;
  paymentMethod?: PaymentMethod;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
}

export interface PaymentMethod {
  type: 'credit_card' | 'paypal' | 'bank_transfer';
  last4?: string;
}

export interface ProcessOrderRequest {
  user: { id: string };
}

export interface ProcessedOrder {
  id: string;
  userId: string;
  total: number;
  status: 'pending' | 'processing';
  items: OrderItem[];
}

export interface ProcessOrderResult {
  orders: ProcessedOrder[];
  userId: string;
  count: number;
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export interface CreateOrderRequest {
  userId: string;
  items: OrderItem[];
  shippingAddress?: Address;
  paymentMethod?: PaymentMethod;
  discountCode?: string;
}

export interface CreateOrderOptions {
  shippingAddress?: Address;
  paymentMethod?: PaymentMethod;
  discountCode?: string;
  applyTax?: boolean;
  includeShipping?: boolean;
}
