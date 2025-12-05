// Main entry point - starts both control plane and API server
// In production, these would run as separate services

import { ControlPlane } from './control-plane';

// Start control plane
const controlPlane = new ControlPlane();
controlPlane.start(3001);

// Note: In production, the API server would be a separate process
// For this example, we're just starting the control plane
console.log('\nTo start the API server, run:');
console.log('  npm run dev src/api-server.ts');
console.log('\nOr in separate terminals:');
console.log('  Terminal 1: npm run dev src/control-plane.ts');
console.log('  Terminal 2: npm run dev src/api-server.ts');
