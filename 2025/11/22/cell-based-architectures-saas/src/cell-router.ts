import { CellDirectory } from './cell-directory';

export interface Request {
  headers: Record<string, string>;
  method: string;
  url: string;
  body?: any;
}

export interface Response {
  status: number;
  headers: Record<string, string>;
  body: any;
}

export class CellRouter {
  private directory: CellDirectory;
  private cellBaseUrls: Map<string, string>;

  constructor(directory: CellDirectory, cellBaseUrls: Map<string, string>) {
    this.directory = directory;
    this.cellBaseUrls = cellBaseUrls;
  }

  async route(request: Request): Promise<Response> {
    // Extract tenant ID
    const tenantId = this.extractTenantId(request);
    if (!tenantId) {
      return {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
        body: { error: 'Tenant ID required' }
      };
    }

    // Get cell for tenant
    let cellId: string;
    try {
      cellId = await this.directory.getCellForTenant(tenantId);
    } catch (error) {
      console.error('Failed to get cell for tenant', { tenantId, error });
      return {
        status: 503,
        headers: { 'Content-Type': 'application/json', 'Retry-After': '60' },
        body: { error: 'Service unavailable' }
      };
    }

    // Get cell base URL
    const cellBaseUrl = this.cellBaseUrls.get(cellId);
    if (!cellBaseUrl) {
      console.error('Cell base URL not found', { cellId });
      return {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
        body: { error: 'Service unavailable' }
      };
    }

    // Forward request to cell
    try {
      return await this.forwardToCell(request, cellBaseUrl);
    } catch (error) {
      return this.handleCellError(tenantId, cellId, error as Error, request.method);
    }
  }

  private extractTenantId(request: Request): string | null {
    // Try JWT token
    const authHeader = request.headers['authorization'];
    if (authHeader) {
      const token = authHeader.replace('Bearer ', '');
      const payload = this.decodeJWT(token);
      if (payload?.tenantId) {
        return payload.tenantId;
      }
    }

    // Try header
    if (request.headers['x-tenant-id']) {
      return request.headers['x-tenant-id'];
    }

    // Try subdomain
    const host = request.headers['host'];
    if (host) {
      const parts = host.split('.');
      if (parts.length > 2) {
        return parts[0]; // tenant.example.com
      }
    }

    return null;
  }

  private decodeJWT(token: string): any {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return null;
      }
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
      return payload;
    } catch (error) {
      return null;
    }
  }

  private async forwardToCell(request: Request, cellBaseUrl: string): Promise<Response> {
    // In a real implementation, this would make an HTTP request
    // For this example, we'll simulate it
    const url = new URL(request.url);
    const targetUrl = `${cellBaseUrl}${url.pathname}${url.search}`;

    // Simulate forwarding (in production, use fetch or http client)
    console.log(`Forwarding ${request.method} request to ${targetUrl}`);

    // Return mock response
    return {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: { message: 'Request forwarded to cell', url: targetUrl }
    };
  }

  private handleCellError(
    tenantId: string,
    cellId: string,
    error: Error,
    method: string
  ): Response {
    console.error('Cell request failed', { tenantId, cellId, error: error.message, method });

    // For read operations, could try cache here
    if (method === 'GET') {
      // Could try cached data here
    }

    return {
      status: 503,
      headers: { 'Content-Type': 'application/json', 'Retry-After': '60' },
      body: { error: 'Service temporarily unavailable' }
    };
  }
}


