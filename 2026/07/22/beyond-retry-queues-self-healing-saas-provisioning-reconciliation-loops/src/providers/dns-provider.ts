import http from 'http';
import { ProvisioningAction, ProvisioningResult } from './interfaces';

export class DnsProviderAdapter implements {
  name: string = 'dns';
  async execute(action: ProvisioningAction): Promise<ProvisioningResult> {
    if (action.type === 'create_dns') {
      const { tenantId, hostname } = action.input as { tenantId: string; hostname: string };
      const resource = await this.httpPost('/dns/records', {
        name: hostname,
        type: 'CNAME',
        ttl: 300,
      });

      if (resource.alreadyExists) {
        return { success: true, externalResourceId: resource.id, alreadyExists: true };
      }
      return { success: true, externalResourceId: resource.id };
    }

    if (action.type === 'delete_dns') {
      const { recordId } = action.input as { recordId: string };
      await this.httpDelete(`/dns/records/${recordId}`);
      return { success: true };
    }

    return { success: false, error: 'unknown action type' };
  }

  private async httpPost(path: string, body: unknown): Promise<{ id: string; alreadyExists?: boolean }> {
    const request = this.createRequest(path, 'POST', body);
    return this.sendRequest(request);
  }

  private async httpDelete(path: string): Promise<void> {
    this.createRequest(path, 'DELETE', null);
  }

  private createRequest(path: string, method: string, body: unknown): http.ClientRequest {
    return {} as http.ClientRequest;
  }

  private async sendRequest(_req: http.ClientRequest): Promise<{ id: string; alreadyExists?: boolean }> {
    return { id: 'dns-mock-123' };
  }
}