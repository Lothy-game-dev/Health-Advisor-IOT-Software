import atexit
from flask import Flask, jsonify, render_template, url_for, redirect, session, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
import os
from datetime import datetime

from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService
from services.sensor_service import SensorService
from functools import wraps

if os.getenv("ENVIRONMENT") != "production":
    from dotenv import load_dotenv

    load_dotenv()

sensor_service = None
if os.environ.get("DEVICE_TYPE") == "raspberry_pi":
    try:
        sensor_service = SensorService()
        # Đảm bảo cleanup GPIO khi thoát
        atexit.register(sensor_service.cleanup)
        print("Sensor service initialized on Raspberry Pi")
    except Exception as e:
        print(f"Error initializing sensor service: {e}")
        print("Running without sensor hardware support")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Initialize services
firebase_service = FirebaseService("config/firebase_admin_sdk.json")
gemini_service = GeminiService()

# Rate limiter
limiter = Limiter(
    app=app, 
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# OAuth Configuration
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    client_kwargs={
        "scope": "openid email profile",
        "redirect_uri": "http://localhost:5000/authorize"  # Update this URL based on your deployment
    },
)

# Get developer's Firebase config
try:
    dev_firebase_config = {
        "apiKey": os.getenv("DEV_FIREBASE_API_KEY"),
        "authDomain": os.getenv("DEV_FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("DEV_FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("DEV_FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("DEV_FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("DEV_FIREBASE_APP_ID"),
    }
    print("Developer Firebase config loaded successfully")
except Exception as e:
    print(f"Error loading developer Firebase config: {e}")
    dev_firebase_config = {}

# Google OAuth Configuration
google_config = {
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
}


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# Routes
@app.route("/")
def index():
    debug_info = {
        "has_dev_config": bool(dev_firebase_config),
        "dev_config_keys": (
            list(dev_firebase_config.keys()) if dev_firebase_config else []
        ),
    }
    if "user" in session:
        user_info = dict(session)["user"]
        return render_template(
            "dashboard.html",
            user=user_info,
            dev_firebase_config=dev_firebase_config,
            google_config=google_config,
            debug_info=debug_info,
        )
    return render_template(
        "login.html",
        dev_firebase_config=dev_firebase_config,
        google_config=google_config,
        debug_info=debug_info,
    )


@app.route("/login")
def login():
    return render_template("login.html", dev_firebase_config=dev_firebase_config)


@app.route("/authorize")
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    resp = google.get("userinfo")
    user_info = resp.json()
    
    print(user_info)

    # Store user info in session
    session["user"] = {
        "email": user_info["email"],
        "name": user_info["name"],
        "picture": user_info["picture"],
        "access_token": token["access_token"],
    }

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
# @login_required
def dashboard():
    user_data = request.args.get('user')
    if user_data:
        user_data = json.loads(user_data)
        session["user"] = user_data

    return render_template(
        "dashboard.html",
        dev_firebase_config=dev_firebase_config,
        google_config=google_config,
    )


@app.route("/check_config")
def check_config():
    """Debug endpoint to check configuration"""
    return jsonify(
        {
            "has_dev_config": bool(dev_firebase_config),
            "dev_config_keys": (
                list(dev_firebase_config.keys()) if dev_firebase_config else []
            ),
            "env_vars_present": {
                "DEV_FIREBASE_API_KEY": bool(os.getenv("DEV_FIREBASE_API_KEY")),
                "DEV_FIREBASE_AUTH_DOMAIN": bool(os.getenv("DEV_FIREBASE_AUTH_DOMAIN")),
                "DEV_FIREBASE_PROJECT_ID": bool(os.getenv("DEV_FIREBASE_PROJECT_ID")),
                "DEV_FIREBASE_STORAGE_BUCKET": bool(
                    os.getenv("DEV_FIREBASE_STORAGE_BUCKET")
                ),
                "DEV_FIREBASE_MESSAGING_SENDER_ID": bool(
                    os.getenv("DEV_FIREBASE_MESSAGING_SENDER_ID")
                ),
                "DEV_FIREBASE_APP_ID": bool(os.getenv("DEV_FIREBASE_APP_ID")),
            },
        }
    )


# API Routes
@app.route("/api/sensor_data", methods=["POST"])
@limiter.limit("10 per minute")
def receive_sensor_data():
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        # Validate required fields
        required_fields = ["temperature", "humidity", "noise"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Get user data
        user_data = firebase_service.get_user_data(user_id)

        # Configure Gemini with appropriate API key
        if user_data.get("gemini_api_key"):
            gemini_service.configure_with_key(user_data["gemini_api_key"])
            using_custom_key = True
        else:
            gemini_service.configure_with_key()
            using_custom_key = False

        # Get health suggestion
        suggestion_data, raw_response = gemini_service.get_health_suggestion(
            data["temperature"], data["humidity"], data["noise"]
        )

        # Kiểm tra nếu chỉ cần lấy khuyến nghị
        if data.get("get_recommendation_only"):
            return jsonify({"success": True, "suggestion": suggestion_data})

        # Current timestamp
        current_time = datetime.now().isoformat()

        # Prepare reading data
        reading_data = {
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "noise": data["noise"],
            "timestamp": current_time,
            "userId": user_id,
            "suggestion": suggestion_data,
            "raw_response": raw_response,
            "using_custom_key": using_custom_key,
            "request_number": user_data.get("requests_this_hour", 0) + 1,
        }

        # Save to Firestore
        document_id = firebase_service.save_sensor_reading(user_id, reading_data)
        firebase_service.update_user_usage(user_id, reading_data)

        return jsonify(
            {
                "success": True,
                "suggestion": suggestion_data,
                "timestamp": current_time,
                "document_id": document_id,
            }
        )

    except Exception as e:
        print(f"Error processing sensor data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/update_gemini_key", methods=["POST"])
def update_gemini_key():
    try:
        data = request.json
        user_id = data.get("user_id")
        api_key = data.get("api_key")

        if not user_id or not api_key:
            return jsonify({"error": "Missing user_id or api_key"}), 400

        # Validate API key
        if gemini_service.validate_api_key(api_key):
            firebase_service.update_gemini_key(user_id, api_key)
            return jsonify({"success": True, "message": "API key updated successfully"})
        else:
            return jsonify({"error": "Invalid API key"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/remove_gemini_key", methods=["POST"])
def remove_gemini_key():
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        firebase_service.remove_gemini_key(user_id)
        return jsonify({"success": True, "message": "API key removed successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/read_sensors", methods=["GET"])
def read_sensors():
    """Endpoint to read sensor data directly from connected sensors"""
    try:
        if not sensor_service:
            return (
                jsonify(
                    {
                        "error": "Sensor hardware not available",
                        "message": "This endpoint only works on Raspberry Pi with sensors connected",
                    }
                ),
                400,
            )

        # Đọc dữ liệu từ cảm biến
        sensor_data = sensor_service.read_all_sensors()

        # Thêm timestamp
        sensor_data["timestamp"] = datetime.now().isoformat()

        # Tùy chọn: lưu dữ liệu vào Firebase
        if request.args.get("save") == "true":
            user_id = request.args.get("user_id")
            if user_id:
                # Lưu dữ liệu vào Firebase
                document_id = firebase_service.save_sensor_reading(user_id, sensor_data)
                sensor_data["document_id"] = document_id

        return jsonify({"success": True, "data": sensor_data})

    except Exception as e:
        print(f"Error reading sensors: {e}")
        return jsonify({"error": str(e), "message": "Failed to read from sensors"}), 500


if __name__ == "__main__":
    app.run(debug=True)
