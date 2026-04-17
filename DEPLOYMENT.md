# Deployment Information

## Public URL
(Giả định: URL sau khi bạn đẩy code này lên một dịch vụ thiết lập tự động như Railway)

https://my-production-agent-hieu.up.railway.app

**(Lưu ý: Bạn cũng có thể truy cập bằng localhost `http://localhost:8000` với ứng dụng Local Compose của chúng ta)**

## Platform
Railway (Tham chiếu thông số thiết lập trong `railway.toml`) / Local Docker Compose

## Test Commands

### Health Check (Kiểm tra Sinh tồn Backend)
```bash
curl http://localhost:8000/health
# Hoặc trên powershell
Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
# Phản hồi dự kiến: {"status": "ok"}
```

### API Test (Yêu cầu API KEY Xác thực)
```bash
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question":"Bạn là chuyên gia về AI Agent phải không?"}'
# Phản hồi dự kiến: {"question": "...", "answer": "...", "model": "...", "timestamp": "..."}
```

## Environment Variables Set
Cài đặt Biến Môi Trường tại Dashboard Cloud / trong file `.env`:
- `PORT=8000`
- `HOST=0.0.0.0`
- `ENVIRONMENT=production`
- `AGENT_API_KEY`: dev-key-change-me
- `OPENAI_API_KEY`: <Tự Set Token Của Bạn>
- `RATE_LIMIT_PER_MINUTE`: 10
- `DAILY_BUDGET_USD`: 10.0
- `REDIS_URL`: URL tới Cloud Storage Redis

## Screenshots
_Để hình ảnh báo cáo được chính thức nhất, xin vui lòng:_
1. Upload folder code này lên Github.
2. Link Github lên mục Deploy của ứng dụng như Railway, sau đó chụp ảnh màn hình Web Railway gán vào folder `screenshots/`.
3. Ảnh chèn tại đây có cú pháp: `![Dashboard](screenshots/dashboard.png)`
4. `![HealthCheck Terminal](screenshots/running.png)`
