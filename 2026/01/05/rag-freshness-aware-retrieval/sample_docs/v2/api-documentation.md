# API Documentation

## Authentication

All API requests require authentication using API keys or OAuth 2.0 tokens.

## Endpoints

### GET /api/v1/products
Retrieve list of products.

### POST /api/v1/orders
Create a new order.

### GET /api/v1/orders/{id}
Retrieve order details.

### GET /api/v2/users/{id}
Retrieve user profile (new in v2).

### PUT /api/v2/users/{id}
Update user profile (new in v2).

## Rate Limits

API requests are limited to 200 requests per minute per API key. OAuth tokens have a limit of 500 requests per minute.

## Webhooks

Subscribe to webhooks for order updates and product changes.
