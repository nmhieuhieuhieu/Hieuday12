# My Production Agent

This is a production-ready AI agent built for Day 12 of the AICB-P1 course.
It features stateless design (Redis), rate limiting, cost guarding, API key auth, and multi-stage Docker setup.

## Running Locally w/ Docker

```bash
docker-compose up --build
```
The agent runs on `http://localhost:8000`.

## Testing

```bash
# Health
curl http://localhost:8000/health

# Ask Agent
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```
