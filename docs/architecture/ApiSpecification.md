# API Specification: LTMC

**Base URL:** `/api/v1`

All request and response bodies are in JSON format. All endpoints use standard HTTP status codes to indicate success or failure.

---

## Resource Management

### `POST /resources`

Adds a new document or code file to the memory. The content is processed, chunked, and embedded asynchronously.

* **Description:** Adds a new resource to be indexed.
* **Request Body Schema:** `ResourceCreationRequest`
    ```json
    {
      "file_name": "string",
      "type": "string",
      "content": "string"
    }
    ```
* **Success Response:** `201 Created`
    * **Body Schema:** `ResourceCreationResponse`
        ```json
        {
          "message": "Resource accepted for processing.",
          "resource_id": "integer"
        }
        ```
* **Error Response:** `422 Unprocessable Entity` if the request body is invalid.

---

## Context Retrieval

### `POST /context`

Retrieves relevant context for a given query, logs the interaction, and returns the context.

* **Description:** Gets relevant context for a new query and logs the interaction.
* **Request Body Schema:** `ContextQueryRequest`
    ```json
    {
      "conversation_id": "string",
      "query": "string",
      "top_k": "integer"
    }
    ```
* **Success Response:** `200 OK`
    * **Body Schema:** `ContextQueryResponse`
        ```json
        {
          "context": "string",
          "retrieved_chunks": [
            {
              "chunk_id": "integer",
              "resource_id": "integer",
              "file_name": "string",
              "score": "float"
            }
          ]
        }
        ```
* **Error Response:** `422 Unprocessable Entity` if the request body is invalid.
