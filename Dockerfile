FROM python:3.10-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn
COPY . .

# Thiết lập biến môi trường
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Biến môi trường có thể được ghi đè khi chạy container
ENV FLASK_SECRET_KEY=""
ENV GOOGLE_CLIENT_ID=""
ENV GOOGLE_CLIENT_SECRET=""
ENV DEV_FIREBASE_API_KEY=""
ENV DEV_FIREBASE_AUTH_DOMAIN=""
ENV DEV_FIREBASE_PROJECT_ID=""
ENV DEV_FIREBASE_STORAGE_BUCKET=""
ENV DEV_FIREBASE_MESSAGING_SENDER_ID=""
ENV DEV_FIREBASE_APP_ID=""
ENV GEMINI_API_KEY=""

# Mở cổng
EXPOSE 5000

# Chạy ứng dụng
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]