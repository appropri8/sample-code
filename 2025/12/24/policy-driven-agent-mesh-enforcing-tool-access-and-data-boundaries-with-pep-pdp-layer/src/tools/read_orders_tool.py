"""ReadOrders tool with tenant isolation and field masking."""
from typing import Dict, Any, List
from src.tools.tenant_guard import TenantGuard


class ReadOrdersTool:
    """ReadOrders tool with tenant isolation."""
    
    def __init__(self, database=None, tenant_guard: TenantGuard = None):
        """Initialize ReadOrders tool.
        
        Args:
            database: Database connection (mock for demo)
            tenant_guard: Tenant guard instance
        """
        self.database = database
        self.tenant_guard = tenant_guard or TenantGuard()
    
    def call(self, params: Dict[str, Any], request_tenant_id: str) -> Dict[str, Any]:
        """Read orders with tenant isolation.
        
        Args:
            params: Query parameters
            request_tenant_id: Tenant ID from request
            
        Returns:
            Dictionary with orders and count
        """
        # Enforce tenant isolation
        safe_params = self.tenant_guard.enforce_tenant_isolation(
            request_tenant_id,
            params,
            "ReadOrders"
        )
        
        # Apply row limit
        limit = safe_params.get("limit", 100)
        
        # Query database (mock for demo)
        if self.database:
            query = f"SELECT * FROM orders WHERE tenant_id = :tenant_id LIMIT :limit"
            results = self.database.query(
                query,
                tenant_id=safe_params["tenant_id"],
                limit=limit
            )
        else:
            # Mock data for demo
            results = [
                {
                    "order_id": f"order-{i}",
                    "tenant_id": safe_params["tenant_id"],
                    "customer_email": f"customer{i}@example.com",
                    "amount": 100.0 * i,
                    "status": "completed"
                }
                for i in range(min(limit, 10))
            ]
        
        # Filter results (defense in depth)
        filtered_results = self.tenant_guard.filter_results_by_tenant(
            results,
            request_tenant_id
        )
        
        # Apply field masking if requested
        mask_fields = safe_params.get("_mask_fields", [])
        if mask_fields:
            filtered_results = self._mask_fields(filtered_results, mask_fields)
        
        return {
            "orders": filtered_results,
            "count": len(filtered_results)
        }
    
    def _mask_fields(
        self,
        records: List[Dict[str, Any]],
        fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Mask specified fields in records.
        
        Args:
            records: List of records
            fields: List of field names to mask
            
        Returns:
            Records with specified fields masked
        """
        masked = []
        for record in records:
            masked_record = record.copy()
            for field in fields:
                if field in masked_record:
                    masked_record[field] = "[MASKED]"
            masked.append(masked_record)
        return masked

