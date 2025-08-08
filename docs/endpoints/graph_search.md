## Graph Search API (Read-only)

Simple wrapper around Neo4j read-only relationship queries.

### Base
- Path: `/api/v1/graph/search`
- Auth: None (read-only). Returns empty `records` if Neo4j is unavailable.

### POST /api/v1/graph/search
Request body:
```
{
  "entity_id": "string",          // required document/node id
  "relation_type": "string|null", // optional relationship type filter
  "direction": "incoming|outgoing|both" // default: both
}
```

Response body:
```
{
  "success": true,
  "records": [
    {
      "source_id": "string",
      "target_id": "string",
      "relationship_type": "string",
      "properties": {"...": "..."}
    }
  ]
}
```

Example:
```bash
curl -s -X POST http://localhost:5050/api/v1/graph/search \
  -H 'Content-Type: application/json' \
  -d '{"entity_id":"doc-1","direction":"both"}' | jq .
```

### Notes
- No writes are performed in this endpoint; attempts always return read-only results.
- Code: `ltms/mcp_server_http.py` and `ltms/database/neo4j_store.py`

