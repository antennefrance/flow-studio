# FLOW Studio Local API Reference 🔌

FLOW Studio provides a local, high-speed OpenAI-compatible HTTP REST API on `http://127.0.0.1:8080/v1`.

---

## Endpoints

### 1. List Models

* **Method:** `GET`
* **Path:** `/v1/models`
* **Description:** Returns the catalog of active streaming models and their hardware resource requirements.

#### Example Request
```bash
curl http://127.0.0.1:8080/v1/models
```

#### Example Response
```json
{
  "object": "list",
  "data": [
    {
      "id": "DeepSeek-Coder-V2-Lite (Standard GGUF)",
      "object": "model",
      "owned_by": "masahiroid",
      "metadata": {
        "architecture": "Mixture-of-Experts",
        "streaming_mode": "FLOW-Direct (Zero-Copy Non-Compressed)",
        "format": ".gguf",
        "active_ram_gb": 2.48
      }
    }
  ]
}
```

---

### 2. Chat Completions

* **Method:** `POST`
* **Path:** `/v1/chat/completions`
* **Description:** Generates streaming or non-streaming responses for interactive chats and code completion.

#### Example Request
```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-direct",
    "messages": [
      {"role": "user", "content": "Write a Python function to parse JSON."}
    ],
    "max_tokens": 256,
    "temperature": 0.7
  }'
```
