import { Verifier } from '@pact-foundation/pact';
import server from '../../src/provider/billing-service';
import http from 'http';

describe('BillingService Provider Verification', () => {
  let app: http.Server;
  const PORT = 3000;

  beforeAll((done) => {
    app = server.listen(PORT, () => {
      console.log(`Provider service running on port ${PORT}`);
      done();
    });
  });

  afterAll((done) => {
    app.close(done);
  });

  it('verifies all contracts from OrderService', async () => {
    const verifier = new Verifier({
      providerBaseUrl: `http://localhost:${PORT}`,
      pactBrokerUrl: process.env.PACT_BROKER_URL || 'http://localhost:9292',
      provider: 'BillingService',
      consumerVersionTags: ['main'],
      publishVerificationResult: true,
      providerVersion: process.env.GIT_COMMIT || '1.0.0',
      logLevel: 'INFO',
      // For local testing without broker, use local pact files
      pactUrls: [
        './pacts/orderservice-billingservice.json',
      ],
    });

    const output = await verifier.verifyProvider();
    expect(output).toBeDefined();
  }, 30000);
});

