class McpBroker:
    def __init__(self, servers=None):
        self.servers = servers or {
            "commerce": LocalMcpServer("commerce"),
            "support": LocalMcpServer("support"),
            "payments": LocalMcpServer("payments"),
            "banking": LocalMcpServer("banking"),
        }

    def call(self, server, tool, arguments, trace_id):
        envelope = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": arguments,
                "meta": {"traceId": trace_id},
            },
            "id": trace_id,
        }
        response = self.servers[server].handle(envelope)
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response["result"]["content"][0]["json"]


class LocalMcpServer:
    def __init__(self, name):
        self.name = name

    def handle(self, envelope):
        tool_name = envelope["params"]["name"]
        arguments = envelope["params"]["arguments"]

        handlers = {
            "orders.read_history": self._read_order_history,
            "tickets.create": self._create_ticket,
            "payments.refund": self._refund,
            "banking.update_details": self._update_bank_details,
        }

        if tool_name not in handlers:
            return {
                "jsonrpc": "2.0",
                "id": envelope["id"],
                "error": {"code": -32601, "message": f"unknown MCP tool: {tool_name}"},
            }

        result = handlers[tool_name](arguments)
        return {
            "jsonrpc": "2.0",
            "id": envelope["id"],
            "result": {"content": [{"type": "json", "json": result}]},
        }

    def _read_order_history(self, arguments):
        return {
            "customerId": arguments["customerId"],
            "orders": [
                {"orderId": "ord_7781", "status": "settled", "total": 250.0},
                {"orderId": "ord_7712", "status": "delivered", "total": 39.5},
            ],
        }

    def _create_ticket(self, arguments):
        return {
            "ticketId": "tic_1042",
            "status": "open",
            "message": f"Ticket created for {arguments['customerId']}.",
        }

    def _refund(self, arguments):
        return {
            "refundId": "rf_10291",
            "status": "pending_settlement",
            "amount": arguments["amount"],
            "message": f"Refund created for order {arguments['orderId']}.",
        }

    def _update_bank_details(self, arguments):
        return {
            "changeId": "bankchg_7001",
            "status": "pending_bank_verification",
            "message": f"Bank details update queued for {arguments['customerId']}.",
        }

