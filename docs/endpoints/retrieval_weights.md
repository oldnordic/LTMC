## Retrieval Weights API

Lightweight configuration endpoints for hybrid ranking in LTMC retrieval. Weights are persisted in SQLite table `RetrievalWeights` (single row, id = 1).

### Base
- Path: `/api/v1/retrieval/weights`
- Auth: None (intentionally open; can be gated later if needed)

### GET /api/v1/retrieval/weights
- Returns current weights used by hybrid ranking.

Response body:
```
{
  "alpha": number,   // similarity weight
  "beta": number,    // recency weight
  "gamma": number,
  "delta": number,
  "epsilon": number
}
```

Example:
```bash
curl -s http://localhost:5050/api/v1/retrieval/weights | jq .
```

### POST /api/v1/retrieval/weights
- Updates persisted weights.

Request body:
```
{
  "alpha": number,
  "beta": number,
  "gamma": number,
  "delta": number,
  "epsilon": number
}
```

Response body:
```
{ "success": true }
```

Example:
```bash
curl -s -X POST http://localhost:5050/api/v1/retrieval/weights \
  -H 'Content-Type: application/json' \
  -d '{"alpha":1.0,"beta":0.5,"gamma":0.1,"delta":0.05,"epsilon":0.1}' | jq .
```

### Notes
- Defaults (if no row): α=1.0, β=0.2, γ=0.1, δ=0.05, ε=0.1
- Retrieval logic uses: score = α·similarity + β·recency; DB fallback uses β·recency.
- Code: `ltms/mcp_server_http.py` and `tools/retrieve.py`

