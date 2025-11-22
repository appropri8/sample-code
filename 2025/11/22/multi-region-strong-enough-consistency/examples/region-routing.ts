import {
  RegionRouter,
  RegionHealthChecker,
  Region,
  RoutingConfig
} from '../src/region-routing';

/**
 * Example: Region-aware routing
 * 
 * Demonstrates how to route requests to appropriate regions
 * based on consistency requirements
 */

async function main() {
  const regions: Region[] = [
    {
      id: 'us-east',
      endpoint: 'https://us-east.api.example.com',
      health: 'healthy'
    },
    {
      id: 'eu-west',
      endpoint: 'https://eu-west.api.example.com',
      health: 'healthy'
    },
    {
      id: 'ap-southeast',
      endpoint: 'https://ap-southeast.api.example.com',
      health: 'healthy'
    }
  ];

  const config: RoutingConfig = {
    defaultRegion: 'us-east',
    regions,
    strongConsistencyEndpoints: [
      '/api/accounts',
      '/api/payments',
      '/api/orders'
    ],
    userRegionMap: new Map([
      ['user-123', 'us-east'],
      ['user-456', 'ap-southeast']
    ])
  };

  const healthChecker = new RegionHealthChecker();
  const router = new RegionRouter(config, healthChecker);

  console.log('=== Strong Consistency Request ===');
  const strongRequest = {
    headers: {},
    method: 'POST',
    path: '/api/payments',
    userId: 'user-123'
  };

  const strongRoute = await router.route(strongRequest);
  console.log('Route:', strongRoute);
  console.log('Expected: us-east (user primary region)');

  console.log('\n=== Eventual Consistency Request ===');
  const eventualRequest = {
    headers: {},
    method: 'GET',
    path: '/api/analytics',
    userId: 'user-123'
  };

  const eventualRoute = await router.route(eventualRequest);
  console.log('Route:', eventualRoute);
  console.log('Expected: closest healthy region (could be any)');

  console.log('\n=== Request for Different User ===');
  const differentUserRequest = {
    headers: {},
    method: 'POST',
    path: '/api/payments',
    userId: 'user-456' // User in ap-southeast
  };

  const differentRoute = await router.route(differentUserRequest);
  console.log('Route:', differentRoute);
  console.log('Expected: ap-southeast (user primary region)');
}

main().catch(console.error);

