import express, { Request, Response } from 'express';
import { cellAwareMiddleware } from './middleware';
import { InMemoryCellRouter } from './router';

const app = express();
app.use(express.json());

// Initialize cell router
const controlPlaneUrl = process.env.CONTROL_PLANE_URL || 'http://localhost:3001';
const router = new InMemoryCellRouter(controlPlaneUrl);

// Apply cell-aware middleware
app.use(cellAwareMiddleware(router));

// Example API endpoint that uses cell context
app.get('/api/users', (req: Request, res: Response) => {
  const { cellContext } = req;
  
  if (!cellContext) {
    return res.status(500).json({ error: 'Cell context missing' });
  }

  // In a real implementation, you'd query the cell's database here
  res.json({
    message: 'Users retrieved',
    cellId: cellContext.cellId,
    tenantId: cellContext.tenantId,
    region: cellContext.region,
    // Mock data
    users: [
      { id: '1', name: 'User 1' },
      { id: '2', name: 'User 2' },
    ],
  });
});

app.post('/api/orders', (req: Request, res: Response) => {
  const { cellContext } = req;
  
  if (!cellContext) {
    return res.status(500).json({ error: 'Cell context missing' });
  }

  // In a real implementation, you'd write to the cell's database and queue
  res.json({
    message: 'Order created',
    cellId: cellContext.cellId,
    tenantId: cellContext.tenantId,
    orderId: `order-${Date.now()}`,
  });
});

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({ 
    status: 'healthy',
    routerCacheSize: router.getCacheSize(),
  });
});

// Metrics endpoint
app.get('/metrics', (req: Request, res: Response) => {
  res.json({
    routerCacheSize: router.getCacheSize(),
    controlPlaneUrl,
  });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`API server running on port ${port}`);
  console.log(`Cell router connected to: ${controlPlaneUrl}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  router.stop();
  process.exit(0);
});
