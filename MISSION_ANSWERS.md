# Day 12 Lab - Mission Answers

> **Student Name:** Nguyễn Minh Hiếu
> **Date:** 17/04/2026

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcoded API Secrets/Keys:** API key bị gắn cứng (`hardcoded`) trực tiếp vào mã nguồn, làm tốn rủi ro bong bóng lộ mã nếu đưa code lên public repo.
2. **Hardcode Network Port:** Cứng chuẩn cổng 8000 trực tiếp thay vì chọc từ biến môi trường `PORT`, khiến Cloud Platforms (như Railway/Render) không thể tự động gán động Port.
3. **Debug Enabled:** Bật chế độ chạy `debug=True` dưới môi trường Production sẽ ném ra lỗi cùng đường dẫn tuyệt đối (Stack trace) trên server cho đối phương nhìn thấy → Lỗ hổng bảo mật rò rỉ cấu trúc ứng dụng.
4. **Missing Health Checks:** Cloud không thể biết lúc nào container đã chết/đã quá tải hay chưa nạp xong Model, dẫn đến Load Balancer định tuyến sai và fail request của user.
5. **Đóng ngang ứng dụng (No Graceful Shutdown):** Khi Server khởi động lại (restart) hoặc bị tắt, luồng request đang xử lý dở dang sẽ bị ngắt đột ngột gây lỗi cho bên phía khách.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Khác biệt và Tại sao quan trọng? |
|---------|---------|------------|----------------|
| **Config** | Hardcode | Env vars (12-factor) | Bảo mật thông minh, dễ dàng linh hoạt chuyển qua lại giữa các máy dev/staging/prod mà không cần chỉnh sửa đụng chạm (commit lại) source code. |
| **Health check** | Không có | Liveness / Readiness | Nền tảng Cloud (kể cả Nginx/LoadBalancer) định kỳ chọc vào `/health` để biết Agent có sống không nhằm restart lại Pod/Container kịp thời. |
| **Logging** | Dùng `print()` | JSON Structured | Log ở Production đẩy về dưới định dạng `{...}` giúp các tool như Datadog/ELK parsing, dễ tìm lỗi (bằng query theo field) thay vì chuỗi text đơn điệu. |
| **Shutdown** | Đột ngột | Graceful | Chờ các request API LLM hiện tại hoàn tất xong xuôi rồi mới thu dọn tắt ứng dụng, không làm gãy trải nghiệm người dùng cuối. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** Cụ thể ở đây sử dụng `python:3.11-slim`, bản hệ điều hành loại bỏ tất cả các package và thư viện biên dịch của Linux không cần thiết.
2. **Working directory:** Thường là `/app`. Đây là quy chuẩn để cô lập toàn bộ tệp lệnh của mình tách biệt với file thực thi của hệ điều hành.
3. **Tại sao `COPY requirements.txt` trước?** Lợi dụng tối đa Cache Layer của Docker. Tầng cài thư viện (pip install) mất thời gian nhất, nếu ta Copy file này cài trước thì mỗi rảo sửa code (bước COPY code) về sau thì layer đó không lặp lại load lại từ đầu, rút ngắn thời gian build xuống còn vài giây.
4. **CMD vs ENTRYPOINT:** `CMD` đưa ra command mặt định nhưng người dùng có thể "ghi đè" bổ sung bằng CLI lúc chạy, còn `ENTRYPOINT` định ra luồng lệnh cốt lõi mà container LUÔN được ép thực thi.

### Exercise 2.3: Image size comparison
*(Số liệu ví dụ - tuỳ thuộc vào máy tính)*
- Develop size: `~1.1 GB`
- Production size: `~180 MB` (nhờ cơ chế multi-stage build kết hợp file image cực kỳ .slim gạt bỏ thư viện C++)
- Difference: `~83%` tối ưu bộ nhớ.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
*(Giả định nộp bài - Hãy thay đổi URL Railway thực tế của bạn nếu có chạy public)*
- **URL:** `https://my-student-agent.up.railway.app` 
- **Screenshot:** [XEM TRONG THƯ MỤC REPO: screenshots/dashboard.png]

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results
Khi kiểm thử dưới dạng Test Postman / cURL:
1. Gửi `/ask` **không kèm** Header `X-API-Key` 
   -> Server chặn: `HTTP 401 Unauthorized` "Invalid or missing API key".
2. Spam >10 hit giới hạn ở endpoint `/ask` 
   -> Server chặn: `HTTP 429 Too Many Requests` "Rate limit exceeded".
3. Nhập token hợp lệ -> Phản hồi kết quả bình thường `HTTP 200 OK`.

### Exercise 4.4: Cost guard implementation
**Cách tiếp cận (Implementation Notes):**
Tôi đã thiết kế 1 file `cost_guard.py` áp dụng Database Memory tốc độ cao là **Redis**:
- Cứ mỗi User gọi Request sẽ sinh ra Key trong Redis định dạng: `budget:{user_id}:2026-04`.
- Before Action LLM, script ước lượng Request/Response token x Quy ra USD và check xem chi phí hiện tại + Chi phí hứa hẹn có bị vượt Budget (Ví dụ: 10$) hay không.
- Nếu vượt (Over), từ chối ngay lập tức bằng lỗi HTTP `503`. Ngược lại tiến hành ghi vào Redis qua toán tử `.incrbyfloat(cost)`.
- Thiết lập thời gian sống `r.expire()` bằng vòng đời tháng (khoảng 32 ngày), sang tháng sau mọi dữ liệu Redis tự tàn khuyết, vòng lặp budget hoạt động trở lại.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Thử nghiệm mở rộng (Stateless):** Để phòng hờ có hàng triệu Request ập đến phải nhân bản ra nhiều máy chủ App, Chatbot đã được chuyển logic khỏi biến `dictionary memory` sang lưu trữ Lịch sử chat (Context) qua Redis. Tôi đã config Node Nginx với `docker-compose up --scale agent=3`, khi 1 Request vào Node B, nó vẫn tải lịch sử trò chuyện khớp ngữ cảnh với Node A do dùng chung móng Database Redis.
- **Self-Healing:** Với /health và /ready, Docker Compose / Load Balancer sẽ từ chối đưa traffic vào một container bị tắt mạng / chưa load xong LLM model, loại bỏ Zero-downtime Deploy (Treo hệ thống không thông báo).
