# Health-Advisor-IOT-Software

Health Advisor IOT là một hệ thống phần mềm thu thập dữ liệu từ cảm biến (nhiệt độ, độ ẩm, tiếng ồn) và cung cấp các khuyến nghị về sức khỏe sử dụng Firebase và Gemini AI.

## Mục lục
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Biến môi trường](#biến-môi-trường)
- [Cài đặt và chạy trên môi trường local](#cài-đặt-và-chạy-trên-môi-trường-local)
- [Build source code](#build-source-code)
- [Deploy lên Raspberry Pi](#deploy-lên-raspberry-pi)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

## Yêu cầu hệ thống
- Python 3.7+
- pip
- Firebase account
- Google Cloud account (cho Gemini AI)
- Raspberry Pi (để deploy)

## Biến môi trường

Dự án này yêu cầu các biến môi trường sau. Bạn có thể thiết lập chúng trực tiếp hoặc sử dụng file `.env` trong quá trình phát triển.

### Firebase Configuration

1. Truy cập [Firebase Console](https://console.firebase.google.com/)
2. Tạo project mới hoặc sử dụng project có sẵn
3. Trong phần "Project settings" > "General", cuộn xuống phần "Your apps" và chọn icon web (</>) để thêm ứng dụng web
4. Đặt tên cho ứng dụng và nhấn "Register app"
5. Sao chép thông tin cấu hình Firebase SDK vào các biến môi trường:
   - `DEV_FIREBASE_API_KEY`
   - `DEV_FIREBASE_AUTH_DOMAIN` 
   - `DEV_FIREBASE_PROJECT_ID`
   - `DEV_FIREBASE_STORAGE_BUCKET`
   - `DEV_FIREBASE_MESSAGING_SENDER_ID`
   - `DEV_FIREBASE_APP_ID`

6. Tạo Admin SDK private key:
   - Trong Firebase Console, chọn "Project settings" > "Service accounts"
   - Nhấn "Generate new private key" và tải file JSON về
   - Lưu file này vào thư mục `config/firebase_admin_sdk.json`

### Google OAuth Configuration

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project có sẵn
3. Vào "APIs & Services" > "Credentials"
4. Nhấn "Create Credentials" > "OAuth client ID"
5. Chọn "Web application", đặt tên và thêm URLs:
   - Authorized JavaScript origins: `http://localhost:5000` (và URL production nếu có)
   - Authorized redirect URIs: `http://localhost:5000/authorize` (và URL production nếu có)
6. Sao chép Client ID và Client Secret vào biến môi trường:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

### Gemini AI API

1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Đăng nhập và tạo API key mới
3. Sao chép API key vào biến môi trường `GEMINI_API_KEY`

### Flask Secret Key

Tạo một secret key ngẫu nhiên cho Flask:

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```
## Cài đặt và chạy trên môi trường local
### Cài đặt
1. Tải mã nguồn về:
   ```bash
   git clone https://github.com/yourusername/Health-Advisor-IOT-Software.git
   cd Health-Advisor-IOT-Software
   ```
2. Tạo và kích hoạt môi trường ảo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Trên Windows: venv\Scripts\activate
   ```
3. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
4. Thiết lập biến môi trường:
   ```bash
   export DEV_FIREBASE_API_KEY='your_firebase_api_key'
   export DEV_FIREBASE_AUTH_DOMAIN='your_firebase_auth_domain'
   export DEV_FIREBASE_PROJECT_ID='your_firebase_project_id'
   export DEV_FIREBASE_STORAGE_BUCKET='your_firebase_storage_bucket'
   export DEV_FIREBASE_MESSAGING_SENDER_ID='your_firebase_messaging_sender_id'
   export DEV_FIREBASE_APP_ID='your_firebase_app_id'
   export GOOGLE_CLIENT_ID='your_google_client_id'
   export GOOGLE_CLIENT_SECRET='your_google_client_secret'
   export GEMINI_API_KEY='your_gemini_api_key'
   export FLASK_SECRET_KEY='your_flask_secret_key'
   ```
5. Chạy ứng dụng Flask:
   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development  # Chế độ phát triển
   flask run
   ```
6. Mở trình duyệt và truy cập `http://localhost:5000` để xem ứng dụng.
## Build source code
### Tạo file `.env`
Tạo file `.env` trong thư mục gốc của dự án và thêm các biến môi trường sau:

```plaintext
DEV_FIREBASE_API_KEY=your_firebase_api_key
DEV_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
DEV_FIREBASE_PROJECT_ID=your_firebase_project_id
DEV_FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
DEV_FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
DEV_FIREBASE_APP_ID=your_firebase_app_id
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GEMINI_API_KEY=your_gemini_api_key
FLASK_SECRET_KEY=your_flask_secret_key
```
### Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```
### Chạy ứng dụng Flask
```bash
export FLASK_APP=app.py
export FLASK_ENV=development  # Chế độ phát triển
flask run
```
## Deploy lên Raspberry Pi
### Chuẩn bị Raspberry Pi
1. Cài đặt hệ điều hành Raspberry Pi OS (Lite hoặc Desktop).
2. Cài đặt Python 3.7+ và pip nếu chưa có:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```
3. Cài đặt các thư viện cần thiết:
   ```bash
   sudo apt install python3-venv
   ```
4. Tạo và kích hoạt môi trường ảo:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
5. Cài đặt các thư viện từ file `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
6. Thiết lập biến môi trường trong file `.env` hoặc trực tiếp trong terminal:
   ```bash
   export DEV_FIREBASE_API_KEY='your_firebase_api_key'
   export DEV_FIREBASE_AUTH_DOMAIN='your_firebase_auth_domain'
   export DEV_FIREBASE_PROJECT_ID='your_firebase_project_id'
   export DEV_FIREBASE_STORAGE_BUCKET='your_firebase_storage_bucket'
   export DEV_FIREBASE_MESSAGING_SENDER_ID='your_firebase_messaging_sender_id'
   export DEV_FIREBASE_APP_ID='your_firebase_app_id'
   export GOOGLE_CLIENT_ID='your_google_client_id'
   export GOOGLE_CLIENT_SECRET='your_google_client_secret'
   export GEMINI_API_KEY='your_gemini_api_key'
   export FLASK_SECRET_KEY='your_flask_secret_key'
   ```
7. Chạy ứng dụng Flask:
   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=production  # Chế độ sản xuất
   flask run --host=0.0.0.0
   ```
8. Mở trình duyệt và truy cập `http://<raspberry_pi_ip>:5000` để xem ứng dụng.
## API Endpoints
### GET /api/sensors
Lấy dữ liệu cảm biến từ Firebase.
### POST /api/sensors
Gửi dữ liệu cảm biến mới lên Firebase.
### GET /api/recommendations
Lấy các khuyến nghị sức khỏe từ Gemini AI dựa trên dữ liệu cảm biến.
### POST /api/recommendations
Gửi dữ liệu cảm biến để nhận khuyến nghị sức khỏe từ Gemini AI.
## Troubleshooting
### Lỗi không thể kết nối đến Firebase
- Kiểm tra biến môi trường Firebase đã được thiết lập đúng chưa.
- Đảm bảo rằng bạn đã tạo Admin SDK private key và lưu đúng đường dẫn trong `config/firebase_admin_sdk.json`.
### Lỗi không thể kết nối đến Gemini AI
- Kiểm tra biến môi trường `GEMINI_API_KEY` đã được thiết lập đúng chưa.
- Đảm bảo rằng bạn đã kích hoạt API Gemini AI trong Google Cloud Console.
### Lỗi không thể xác thực người dùng
- Kiểm tra biến môi trường `GOOGLE_CLIENT_ID` và `GOOGLE_CLIENT_SECRET` đã được thiết lập đúng chưa.
- Đảm bảo rằng bạn đã cấu hình đúng OAuth consent screen trong Google Cloud Console.
### Lỗi không thể chạy ứng dụng Flask
- Kiểm tra xem bạn đã kích hoạt môi trường ảo chưa.
- Đảm bảo rằng bạn đã cài đặt tất cả các thư viện cần thiết từ `requirements.txt`.
### Lỗi không thể truy cập ứng dụng trên Raspberry Pi
- Kiểm tra xem ứng dụng Flask có đang chạy không.
- Đảm bảo rằng bạn đã mở cổng 5000 trên Raspberry Pi (nếu cần).
### Lỗi không thể truy cập API
- Kiểm tra xem ứng dụng Flask có đang chạy không.
- Đảm bảo rằng bạn đã cấu hình đúng các endpoint trong ứng dụng Flask.
### Lỗi không nhận được dữ liệu cảm biến
- Kiểm tra xem cảm biến có đang hoạt động không.
- Đảm bảo rằng dữ liệu cảm biến được gửi đúng định dạng và đã được lưu vào Firebase.
### Lỗi không nhận được khuyến nghị sức khỏe
- Kiểm tra xem dữ liệu cảm biến đã được gửi đến Gemini AI chưa.
- Đảm bảo rằng API key của Gemini AI đã được thiết lập đúng và API đang hoạt động.
### Lỗi không thể kết nối đến Raspberry Pi
- Kiểm tra kết nối mạng của Raspberry Pi.
- Đảm bảo rằng địa chỉ IP của Raspberry Pi là chính xác.
### Lỗi không thể truy cập trang web
- Kiểm tra xem ứng dụng Flask có đang chạy không.
- Đảm bảo rằng bạn đã mở cổng 5000 trên Raspberry Pi (nếu cần).
### Lỗi không thể xác thực người dùng với Google
- Kiểm tra xem bạn đã cấu hình đúng OAuth consent screen trong Google Cloud Console chưa.
- Đảm bảo rằng bạn đã thêm đúng các Authorized redirect URIs trong Google Cloud Console.
### Lỗi không thể gửi dữ liệu cảm biến
- Kiểm tra xem dữ liệu cảm biến có đang được gửi đúng định dạng không.
- Đảm bảo rằng bạn đã cấu hình đúng Firebase để nhận dữ liệu từ ứng dụng.
### Lỗi không thể nhận khuyến nghị từ Gemini AI
- Kiểm tra xem API key của Gemini AI đã được thiết lập đúng chưa.
- Đảm bảo rằng bạn đã gửi dữ liệu cảm biến đúng định dạng và đã nhận phản hồi từ API.
### Lỗi không thể lưu dữ liệu vào Firebase
- Kiểm tra xem bạn đã cấu hình đúng Firebase Admin SDK chưa.
- Đảm bảo rằng bạn đã cấp quyền ghi dữ liệu cho ứng dụng trong Firebase Console.
### Lỗi không thể đọc dữ liệu từ Firebase
- Kiểm tra xem bạn đã cấu hình đúng Firebase Admin SDK chưa.
- Đảm bảo rằng bạn đã cấp quyền đọc dữ liệu cho ứng dụng trong Firebase Console.
### Lỗi không thể gửi email thông báo
- Kiểm tra xem bạn đã cấu hình đúng SMTP server chưa.
- Đảm bảo rằng bạn đã cung cấp đúng thông tin đăng nhập email trong biến môi trường.
### Lỗi không thể gửi thông báo đến người dùng
- Kiểm tra xem bạn đã cấu hình đúng Firebase Cloud Messaging chưa.
- Đảm bảo rằng bạn đã cấp quyền gửi thông báo cho ứng dụng trong Firebase Console.
### Lỗi không thể lưu trữ tệp lên Firebase Storage
- Kiểm tra xem bạn đã cấu hình đúng Firebase Storage chưa.
- Đảm bảo rằng bạn đã cấp quyền ghi tệp cho ứng dụng trong Firebase Console.
### Lỗi không thể đọc tệp từ Firebase Storage
- Kiểm tra xem bạn đã cấu hình đúng Firebase Storage chưa.
- Đảm bảo rằng bạn đã cấp quyền đọc tệp cho ứng dụng trong Firebase Console.
### Lỗi không thể kết nối đến cơ sở dữ liệu
- Kiểm tra xem bạn đã cấu hình đúng Firebase Realtime Database hoặc Firestore chưa.
- Đảm bảo rằng bạn đã cấp quyền truy cập cho ứng dụng trong Firebase Console.
### Lỗi không thể gửi dữ liệu cảm biến từ Raspberry Pi
- Kiểm tra xem cảm biến có đang hoạt động không.
- Đảm bảo rằng bạn đã cài đặt đúng các thư viện cần thiết trên Raspberry Pi.
### Lỗi không thể nhận dữ liệu cảm biến từ Raspberry Pi
- Kiểm tra xem ứng dụng Flask có đang chạy trên Raspberry Pi không.
- Đảm bảo rằng bạn đã cấu hình đúng các endpoint trong ứng dụng Flask để nhận dữ liệu cảm biến.
### Lỗi không thể gửi dữ liệu cảm biến từ ứng dụng web
- Kiểm tra xem ứng dụng web có đang chạy không.
- Đảm bảo rằng bạn đã cấu hình đúng các endpoint trong ứng dụng Flask để gửi dữ liệu cảm biến.
### Lỗi không thể nhận khuyến nghị sức khỏe từ ứng dụng web
- Kiểm tra xem ứng dụng web có đang chạy không.
- Đảm bảo rằng bạn đã cấu hình đúng các endpoint trong ứng dụng Flask để nhận khuyến nghị sức khỏe từ Gemini AI.
### Lỗi không thể gửi thông báo đến người dùng từ ứng dụng web
- Kiểm tra xem ứng dụng web có đang chạy không.
- Đảm bảo rằng bạn đã cấu hình đúng Firebase Cloud Messaging trong ứng dụng Flask.
### Lỗi không thể lưu trữ tệp từ ứng dụng web
- Kiểm tra xem ứng dụng web có đang chạy không.
- Đảm bảo rằng bạn đã cấu hình đúng Firebase Storage trong ứng dụng Flask.
### Lỗi không thể đọc tệp từ ứng dụng web
- Kiểm tra xem ứng dụng web có đang chạy không.
- Đảm bảo rằng bạn đã cấu hình đúng Firebase Storage trong ứng dụng Flask.
