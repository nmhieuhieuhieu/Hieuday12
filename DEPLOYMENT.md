# Deployment Information

## Public URL

https://hieuday12-production.up.railway.app

## Platform
Railway — Dockerfile detected, single-stage build, auto-deploy từ nhánh `main`.

## Test Commands

### Health Check
```bash
curl https://hieuday12-production.up.railway.app/health
# Phản hồi: {"status": "ok", "version": "1.0.0"}
```

### API Test (Yêu cầu Agent API Key)
```bash
curl -X POST https://hieuday12-production.up.railway.app/ask \
  -H "X-API-Key: <AGENT_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"question":"Bạn là chuyên gia về AI Agent phải không?"}'
# Phản hồi: {"question": "...", "answer": "...", "model": "gpt-4o-mini", "timestamp": "..."}
```

### Rate Limit Test
```bash
# Gửi > 10 requests/phút → HTTP 429 Too Many Requests
```

## Environment Variables (Railway)
| Variable | Mô tả |
|----------|-------|
| `OPENAI_API_KEY` | Key OpenAI để gọi GPT-4o-mini ✅ |
| `AGENT_API_KEY` | Mật khẩu xác thực API ✅ |
| `RATE_LIMIT_PER_MINUTE` | Giới hạn request/phút ✅ |
| `DAILY_BUDGET_USD` | Giới hạn ngân sách ✅ |
| `REDIS_URL` | URL Redis storage ✅ |
| `ENVIRONMENT` | production ✅ |
| `APP_NAME`, `APP_VERSION` | Thông tin ứng dụng ✅ |

## Deployment Status
- ✅ Build thành công (single-stage Dockerfile)
- ✅ Healthcheck `/health` → 200 OK
- ✅ GPT-4o-mini hoạt động
- ✅ Rate limiting hoạt động
- ✅ API Key authentication hoạt động
- ✅ Mock fallback khi không có OpenAI key

## Screenshots
Chụp màn hình và đặt vào thư mục `screenshots/`:
- `![Railway Dashboard](screenshots/dashboard.png)`
- `![Chat UI](screenshots/chatbot_ui.png)`
- `![Health Check](screenshots/health.png)`
