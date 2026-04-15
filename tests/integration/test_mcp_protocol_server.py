from total_recall.mcp_server.server import MCPRuntime


class _FakeTools:
    def __init__(self) -> None:
        self.query_calls: list[tuple[str, int]] = []

    def query_vault_context(self, query: str, k: int) -> dict:
        self.query_calls.append((query, k))
        return {
            "k": 1,
            "results": [
                {
                    "chunk_id": "c1",
                    "content": "hello",
                    "doc_path": "vault/note.md",
                    "score": 0.92,
                    "source": {"doc_path": "vault/note.md", "chunk_id": "c1"},
                    "similarity_score": 0.92,
                }
            ],
        }


def test_mcp_tool_discovery_and_query_invocation() -> None:
    runtime = MCPRuntime(_FakeTools())

    init_resp = runtime.handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init_resp is not None
    assert init_resp["result"]["capabilities"]["tools"]["listChanged"] is False

    list_resp = runtime.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert list_resp is not None
    tools = list_resp["result"]["tools"]
    names = [t["name"] for t in tools]
    assert names == ["query_vault_context"]
    query_schema = next(t["inputSchema"] for t in tools if t["name"] == "query_vault_context")
    assert "query" in query_schema["properties"]

    call_resp = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "query_vault_context", "arguments": {"query": "hello", "k": 3}},
        }
    )
    assert call_resp is not None
    payload = call_resp["result"]["structuredContent"]
    assert payload["k"] == 1
    assert payload["results"][0]["similarity_score"] == 0.92


def test_mcp_validation_and_runtime_error_contracts() -> None:
    runtime = MCPRuntime(_FakeTools())

    validation = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "query_vault_context", "arguments": {"k": 5}},
        }
    )
    assert validation is not None
    assert validation["error"]["code"] == -32602
    assert validation["error"]["message"] == "Invalid tool arguments"

    class _ExplodingTools(_FakeTools):
        def query_vault_context(self, query: str, k: int) -> dict:
            raise RuntimeError("boom")

    runtime = MCPRuntime(_ExplodingTools())
    runtime_error = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "query_vault_context", "arguments": {"query": "x", "k": 1}},
        }
    )
    assert runtime_error is not None
    assert runtime_error["error"]["code"] == -32000
    assert runtime_error["error"]["message"] == "Tool execution failed"
    assert runtime_error["error"]["data"]["tool"] == "query_vault_context"


def test_removed_update_markdown_note_returns_tool_not_found() -> None:
    runtime = MCPRuntime(_FakeTools())

    response = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {
                "name": "update_markdown_note",
                "arguments": {"note_reference": "my note", "update_context": "organize it", "confidence_threshold": 0.65},
            },
        }
    )
    assert response is not None
    assert response["error"]["code"] == -32601
    assert response["error"]["message"] == "Tool not found"
    assert response["error"]["data"]["tool"] == "update_markdown_note"
