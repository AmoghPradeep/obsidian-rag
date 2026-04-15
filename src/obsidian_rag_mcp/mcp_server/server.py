from __future__ import annotations

import json
import logging
import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.mcp_server.tools import MCPTools

LOG = logging.getLogger(__name__)


PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {"name": "obsidian-rag-mcp", "version": "0.1.0"}


class QueryVaultContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, description="Natural language query to retrieve relevant context chunks.")
    k: int = Field(default=5, ge=1, le=20, description="Maximum number of chunks to return.")


class MCPRequestError(Exception):
    def __init__(self, code: int, message: str, data: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}


class MCPRuntime:
    def __init__(self, tools: MCPTools) -> None:
        self.tools = tools
        self.tool_schemas = {"query_vault_context": QueryVaultContextInput.model_json_schema()}

    def tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "query_vault_context",
                "description": "Fetch top-k vault chunks relevant to a query using vector similarity.",
                "inputSchema": self.tool_schemas["query_vault_context"],
            },
        ]

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        request_id = message.get("id")
        try:
            method = str(message.get("method", "")).strip()
            LOG.debug("Handling MCP message method=%s request_id=%s", method, request_id)
            params = message.get("params", {})
            if not isinstance(params, dict):
                raise MCPRequestError(-32602, "Invalid params", {"reason": "params must be an object"})

            if method == "initialize":
                result = self._initialize_result()
            elif method == "notifications/initialized":
                return None
            elif method == "tools/list":
                result = {"tools": self.tool_definitions()}
            elif method == "tools/call":
                result = self._handle_tool_call(params)
            else:
                raise MCPRequestError(-32601, "Method not found", {"method": method})
            if request_id is None:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except MCPRequestError as exc:
            LOG.warning(
                "MCP request failed method=%s request_id=%s code=%s message=%s",
                message.get("method"),
                request_id,
                exc.code,
                exc.message,
            )
            if request_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": exc.code, "message": exc.message, "data": exc.data},
            }
        except Exception as exc:  # pragma: no cover - terminal safety net
            LOG.exception("Unhandled MCP runtime error method=%s request_id=%s", message.get("method"), request_id)
            if request_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": "Internal error",
                    "data": {"type": exc.__class__.__name__},
                },
            }

    def _initialize_result(self) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {"tools": {"listChanged": False}},
        }

    def _handle_tool_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = str(params.get("name", "")).strip()
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            raise MCPRequestError(-32602, "Invalid params", {"reason": "arguments must be an object"})
        LOG.info("Handling MCP tool call tool=%s", name)

        if name == "query_vault_context":
            parsed = self._validate_tool_arguments(name, QueryVaultContextInput, arguments)
            try:
                payload = self.tools.query_vault_context(parsed.query, parsed.k)
            except Exception as exc:
                raise MCPRequestError(
                    -32000,
                    "Tool execution failed",
                    {"tool": name, "type": exc.__class__.__name__},
                ) from exc
            LOG.info("Completed MCP tool call tool=%s", name)
            return _tool_success(payload)
        raise MCPRequestError(-32601, "Tool not found", {"tool": name})

    def _validate_tool_arguments(
        self,
        tool_name: str,
        schema: type[BaseModel],
        arguments: dict[str, Any],
    ) -> BaseModel:
        try:
            return schema.model_validate(arguments)
        except ValidationError as exc:
            raise MCPRequestError(
                -32602,
                "Invalid tool arguments",
                {
                    "tool": tool_name,
                    "validationErrors": exc.errors(include_url=False),
                },
            ) from exc
        except Exception as exc:
            raise MCPRequestError(
                -32602,
                "Invalid tool arguments",
                {"tool": tool_name, "reason": str(exc)},
            ) from exc


def _tool_success(payload: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False)
    return {
        "structuredContent": payload,
        "content": [{"type": "text", "text": text}],
        "isError": False,
    }


def run_stdio_server(config: AppConfig) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict", newline="\n")

    runtime = MCPRuntime(MCPTools(config))
    LOG.info("Starting MCP stdio server")
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            LOG.warning("Received invalid JSON request on MCP stdio")
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error", "data": {"reason": "invalid JSON input"}},
            }
            print(json.dumps(response, ensure_ascii=False), flush=True)
            continue
        if not isinstance(request, dict):
            LOG.warning("Received non-object MCP request payload type=%s", type(request).__name__)
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request", "data": {"reason": "request must be an object"}},
            }
            print(json.dumps(response, ensure_ascii=False), flush=True)
            continue

        response = runtime.handle_message(request)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
