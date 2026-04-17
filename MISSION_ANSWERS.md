# Day 12 Lab - Mission Answers

> **Student Name:** Nguyễn Minh Hiếu
> **Date:** 17/04/2026

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcoded API Secrets/Keys:** API key bị gắn cứng (`hardcoded`) trực tiếp vào mã nguồn, tạo rủi ro lộ key nếu đưa code lên public repo. → Fix: Dùng biến môi trường qua `pydantic-settings`.
2. **Hardcode Network Port:** Cứng cổng `8000` thay vì đọc từ biến môi trường `$PORT`, khiến Cloud Platforms (Railway/Render) không thể tự động gán port động. → Fix: `CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`
3. **Debug Enabled:** Bật `debug=True` trong môi trường Production sẽ lộ stack trace đầy đủ cho người dùng → Lỗ hổng bảo mật. → Fix: `debug: bool = False` mặc định.
4. **Missing Health Checks:** Cloud không thể biết container đã sẵn sàng hay chưa, dẫn đến Load Balancer định tuyến sai. → Fix: Thêm `/health` và `/ready` endpoint.
5. **No Graceful Shutdown:** Khi container restart, request đang xử lý bị ngắt đột ngột. → Fix: Dùng `signal.signal(signal.SIGTERM, ...)` và `asynccontextmanager lifespan`.

### Exercise 1.3: Comparison table
| Feature | Development | Production | Tại sao quan trọng? |
|---------|------------|------------|-------------------|
| **Config** | Hardcode trong code | Env vars (12-factor app) | Bảo mật, dễ thay đổi giữa môi trường mà không sửa code |
| **Health check** | Không có | `/health` + `/ready` | Cloud tự động restart container chết, load balancer định tuyến đúng |
| **Logging** | `print()` ngẫu hứng | JSON Structured logging | Tool như Datadog/ELK parse được, truy vấn theo field |
| **Shutdown** | Đột ngột (kill -9) | Graceful (SIGTERM handler) | Không làm gãy request đang xử lý khi deploy mới |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** `python:3.11-slim` — phiên bản loại bỏ các thư viện Linux không cần thiết, giảm attack surface và kích thước image.
2. **Working directory:** `/app` — tiêu chuẩn để cô lập file ứng dụng khỏi file hệ điều hành.
3. **Tại sao `COPY requirements.txt` trước?** Lợi dụng Docker Layer Cache. Layer `pip install` tốn thời gian nhất; nếu copy `requirements.txt` trước, mỗi lần sửa code thì layer này không bị invalidate, build chỉ mất vài giây thay vì hàng phút.
4. **CMD vs ENTRYPOINT:** `CMD` cho phép override khi chạy `docker run <image> <custom-cmd>`, còn `ENTRYPOINT` luôn được thực thi và không override được (chỉ có thể append thêm args).

### Exercise 2.3: Image size comparison
- **python:3.11 (full):** ~1.1 GB
- **python:3.11-slim (production):** ~180 MB
- **Tiết kiệm:** ~83% dung lượng — nhờ loại bỏ các compiler tools (gcc, make,...) và thư viện C không cần thiết khi runtime.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment ✅ (Đã deploy thành công)
- **URL:** `https://hieuday12-production.up.railway.app`
- **Platform:** Railway — auto-deploy từ GitHub nhánh `main`
- **Build time:** ~20 giây (Dockerfile detected)
- **Healthcheck:** `/health` → `{"status": "ok", "version": "1.0.0"}` ✅
- **Runtime log thực tế:**
  ```
  Static dir resolved to: /app/static (exists=True)
  INFO: Started server process [2]
  Application startup — binding on port 8080
  INFO: Application startup complete.
  INFO: Uvicorn running on http://0.0.0.0:8080
  INFO: "GET /health HTTP/1.1" 200 OK
  ```

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results (Kết quả thực tế)
1. Gửi `/ask` **không kèm** Header `X-API-Key`
   → Server trả về: `HTTP 401 Unauthorized` — "Invalid API Key" ✅
2. Spam > 10 requests/phút tới endpoint `/ask`
   → Server trả về: `HTTP 429 Too Many Requests` — "Rate limit exceeded: 10 req/min" ✅
3. Nhập API key hợp lệ → `HTTP 200 OK` với câu trả lời từ GPT-4o-mini ✅

### Exercise 4.4: Cost guard implementation
**Implementation thực tế trong `cost_guard.py`:**
- Mỗi request tới `/ask` sẽ tạo key Redis: `budget:{user_id}:2026-04`
- Trước khi gọi LLM, hệ thống kiểm tra `current_cost + estimated_cost > monthly_budget_usd`
- Nếu vượt → từ chối ngay bằng `HTTP 503 Service Unavailable`
- Sau khi gọi thành công → `r.incrbyfloat(key, cost)` cộng dồn chi phí
- Key tự hết hạn sau 32 ngày (`r.expire(key, 32*24*3600)`) → budget reset theo tháng tự động

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Stateless Design:** Lịch sử hội thoại lưu trong Redis (`history:{user_id}`) thay vì biến Python local. Khi scale lên nhiều instance, mọi node đều đọc cùng 1 Redis → context nhất quán.
- **Fakeredis Fallback:** Nếu không có Redis server, ứng dụng tự động dùng `fakeredis.FakeStrictRedis()` trong bộ nhớ → không crash, vẫn hoạt động.
- **Self-Healing:** Railway tự restart container khi `/health` không phản hồi (cấu hình trong `railway.toml`: `restartPolicyType = "ON_FAILURE"`).
- **LLM Fallback:** Nếu không có `OPENAI_API_KEY`, hệ thống dùng `mock_llm.py` thay vì crash — đảm bảo uptime 100% kể cả khi thiếu key.
