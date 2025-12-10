import { Request, Response, NextFunction } from 'express';
import { IdempotencyStore } from './database';
import { hashString } from './utils';

export interface IdempotentRequest extends Request {
  idempotencyKey?: string;
  idempotencyStore?: IdempotencyStore;
}

export function idempotencyMiddleware(
  idempotencyStore: IdempotencyStore
) {
  return async (
    req: IdempotentRequest,
    res: Response,
    next: NextFunction
  ) => {
    // Extract idempotency key from header
    const idempotencyKey = req.headers['idempotency-key'] as string;

    if (!idempotencyKey) {
      // No key provided - proceed without idempotency
      return next();
    }

    req.idempotencyKey = idempotencyKey;
    req.idempotencyStore = idempotencyStore;

    // Hash the request body to detect if key is reused with different request
    const requestBody = JSON.stringify(req.body);
    const requestHash = hashString(requestBody);

    try {
      // Check if key already exists
      const existing = await idempotencyStore.findByIdempotencyKey(
        idempotencyKey
      );

      if (existing) {
        // Key exists - check if it's the same request
        if (existing.request_hash && existing.request_hash !== requestHash) {
          return res.status(409).json({
            error: 'Idempotency key reused with different request',
            code: 'IDEMPOTENCY_KEY_REUSED'
          });
        }

        // If completed, return cached response
        if (existing.status === 'completed') {
          return res.status(200).json(JSON.parse(existing.response_body || '{}'));
        }

        // If processing, return 409 Conflict (or wait, depending on design)
        if (existing.status === 'processing') {
          return res.status(409).json({
            error: 'Request is already being processed',
            code: 'REQUEST_IN_PROGRESS'
          });
        }

        // If failed, allow retry (or return cached error, depending on design)
        if (existing.status === 'failed') {
          // Option 1: Allow retry
          // Option 2: Return cached error
          const errorResponse = existing.response_body 
            ? JSON.parse(existing.response_body)
            : { error: 'Previous request failed' };
          return res.status(500).json(errorResponse);
        }
      }

      // Key doesn't exist - create processing record
      try {
        await idempotencyStore.createProcessingRecord(
          idempotencyKey,
          (req as any).user?.id, // Assuming user is attached by auth middleware
          req.path,
          requestHash
        );
      } catch (error: any) {
        if (error.message === 'Idempotency key already exists') {
          // Race condition - another request created it first
          return res.status(409).json({
            error: 'Request is already being processed',
            code: 'REQUEST_IN_PROGRESS'
          });
        }
        throw error;
      }

      // Store original json method to capture response
      const originalJson = res.json.bind(res);
      res.json = function (body: any) {
        // Update idempotency record with response
        if (req.idempotencyKey && res.statusCode < 400) {
          const responseBody = JSON.stringify(body);
          const responseHash = hashString(responseBody);
          
          idempotencyStore
            .updateCompleted(req.idempotencyKey, responseBody, responseHash)
            .catch((err) => {
              console.error('Failed to update idempotency record:', err);
            });
        }
        
        return originalJson(body);
      };

      // Handle errors
      const originalStatus = res.status.bind(res);
      res.status = function (code: number) {
        if (code >= 400 && req.idempotencyKey) {
          // Mark as failed
          const errorMessage = JSON.stringify({ 
            error: 'Request failed',
            statusCode: code 
          });
          
          idempotencyStore
            .updateFailed(req.idempotencyKey, errorMessage)
            .catch((err) => {
              console.error('Failed to update idempotency record:', err);
            });
        }
        
        return originalStatus(code);
      };

      next();
    } catch (error) {
      console.error('Idempotency middleware error:', error);
      // On error, continue without idempotency (fail open)
      next();
    }
  };
}
