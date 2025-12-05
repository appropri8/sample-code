// Example of making requests to the API server with tenant ID

async function makeRequest(tenantId: string, endpoint: string) {
  const apiUrl = process.env.API_URL || 'http://localhost:3000';
  
  try {
    const response = await fetch(`${apiUrl}${endpoint}`, {
      headers: {
        'X-Tenant-ID': tenantId,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      console.error(`Error for ${tenantId}:`, error);
      return;
    }

    const data = await response.json();
    console.log(`Response for ${tenantId}:`, JSON.stringify(data, null, 2));
  } catch (error) {
    console.error(`Request failed for ${tenantId}:`, error);
  }
}

async function main() {
  console.log('Testing API with different tenants:\n');

  // Test GET request
  await makeRequest('tenant-acme', '/api/users');
  await makeRequest('tenant-eu-corp', '/api/users');

  // Test POST request
  await makeRequest('tenant-acme', '/api/orders');
  
  // Test with unknown tenant
  await makeRequest('tenant-unknown', '/api/users');
}

main().catch(console.error);
