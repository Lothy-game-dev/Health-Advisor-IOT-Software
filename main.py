from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, render_template, url_for, redirect, session, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import json
from functools import wraps
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
# limiter = Limiter(app, key_func=get_remote_address)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

# OAuth Configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)

# Initialize developer's Firebase Admin SDK
try:
    cred = credentials.Certificate("config/firebase_admin_sdk.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")

# Get developer's Firebase config
try:
    dev_firebase_config = {
        "apiKey": os.getenv("DEV_FIREBASE_API_KEY"),
        "authDomain": os.getenv("DEV_FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("DEV_FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("DEV_FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("DEV_FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("DEV_FIREBASE_APP_ID")
    }
    print("Developer Firebase config loaded successfully")
except Exception as e:
    print(f"Error loading developer Firebase config: {e}")
    dev_firebase_config = {}

# Google OAuth Configuration
google_config = {
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET")
}

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

@app.route('/')
def index():
    # Add debug information to template
    debug_info = {
        "has_dev_config": bool(dev_firebase_config),
        "dev_config_keys": list(dev_firebase_config.keys()) if dev_firebase_config else []
    }
    if 'user' in session:
        user_info = dict(session)['user']
        return render_template('dashboard.html', user=user_info, dev_firebase_config=dev_firebase_config, google_config=google_config, debug_info=debug_info)
    return render_template('login.html', dev_firebase_config=dev_firebase_config, google_config=google_config, debug_info=debug_info)

@app.route('/login')
def login():
    return render_template('login.html', dev_firebase_config=dev_firebase_config)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    
    # Store user info in session
    session['user'] = {
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info['picture'],
        'access_token': token['access_token']  # Store Google access token
    }
    
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', dev_firebase_config=dev_firebase_config, google_config=google_config)

@app.route('/check_rate_limit/<user_id>')
def check_rate_limit(user_id):
    # Check rate limit for developer account users
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        if 'using_dev_account' in user_data and user_data['using_dev_account']:
            today = datetime.now().date()
            updates_today = user_data.get('updates_today', 0)
            last_update = user_data.get('last_update_date')
            
            # Reset counter if it's a new day
            if last_update != str(today):
                user_ref.update({
                    'updates_today': 0,
                    'last_update_date': str(today)
                })
                return jsonify({'remaining': 10})
            
            return jsonify({'remaining': 10 - updates_today})
    
    return jsonify({'remaining': 10})

@app.route('/update_usage/<user_id>')
def update_usage(user_id):
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        if user_data.get('using_dev_account', False):
            today = datetime.now().date()
            updates_today = user_data.get('updates_today', 0) + 1
            
            user_ref.update({
                'updates_today': updates_today,
                'last_update_date': str(today)
            })
    
    return jsonify({'success': True})

@app.route('/check_config')
def check_config():
    """Debug endpoint to check configuration"""
    return jsonify({
        "has_dev_config": bool(dev_firebase_config),
        "dev_config_keys": list(dev_firebase_config.keys()) if dev_firebase_config else [],
        "env_vars_present": {
            "DEV_FIREBASE_API_KEY": bool(os.getenv("DEV_FIREBASE_API_KEY")),
            "DEV_FIREBASE_AUTH_DOMAIN": bool(os.getenv("DEV_FIREBASE_AUTH_DOMAIN")),
            "DEV_FIREBASE_PROJECT_ID": bool(os.getenv("DEV_FIREBASE_PROJECT_ID")),
            "DEV_FIREBASE_STORAGE_BUCKET": bool(os.getenv("DEV_FIREBASE_STORAGE_BUCKET")),
            "DEV_FIREBASE_MESSAGING_SENDER_ID": bool(os.getenv("DEV_FIREBASE_MESSAGING_SENDER_ID")),
            "DEV_FIREBASE_APP_ID": bool(os.getenv("DEV_FIREBASE_APP_ID"))
        }
    })

def get_health_suggestion(temperature, humidity, noise, user_id):
    try:
        # Get user document
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        # Initialize default values if user doc doesn't exist
        if not user_doc.exists:
            user_ref.set({
                'requests_this_hour': 0,
                'last_request_hour': None,
                'using_dev_account': True,
                'created_at': datetime.now().isoformat()
            })
            user_data = {
                'requests_this_hour': 0,
                'last_request_hour': None,
                'using_dev_account': True
            }
        else:
            user_data = user_doc.to_dict()

        # Configure Gemini
        if user_data.get('gemini_api_key'):
            genai.configure(api_key=user_data['gemini_api_key'])
            hourly_limit = 15
        else:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            hourly_limit = 3
        
        # Check rate limits
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        requests_this_hour = user_data.get('requests_this_hour', 0)
        last_request_hour = user_data.get('last_request_hour')
        
        if last_request_hour != current_hour.isoformat():
            requests_this_hour = 0
        
        # if requests_this_hour >= hourly_limit:
        #     return "Rate limit exceeded. Please try again in the next hour."
        
        prompt = f"""
        Analyze these room conditions and provide health suggestions:
        Temperature: {temperature}°C
        Humidity: {humidity}%
        Noise Level: {noise}dB

        Respond ONLY with a JSON object in this exact format, with NO additional text, quotes, or markdown:
        {{
            "immediate_actions": ["action1", "action2"],
            "health_impacts": ["impact1", "impact2"],
            "optimal_ranges": {{
                "temperature": "range in celsius",
                "humidity": "range in percentage",
                "noise": "range in dB"
            }},
            "summary": "brief summary"
        }}

        Keep each list to 2-3 items and the summary under 100 words. Do not include any markdown formatting, backticks, or the word 'json'.
        """
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Clean the response text
        clean_response = response.text.strip()
        if clean_response.startswith('```'):
            clean_response = clean_response.split('```')[1]
        if clean_response.startswith('json'):
            clean_response = clean_response[4:]
        clean_response = clean_response.strip()
        
        # Parse the JSON response
        try:
            suggestion_data = json.loads(clean_response)
        except:
            # If JSON parsing fails, use the raw text
            suggestion_data = {
                "immediate_actions": ["Check response format"],
                "health_impacts": ["Unable to parse response"],
                "optimal_ranges": {
                    "temperature": "N/A",
                    "humidity": "N/A",
                    "noise": "N/A"
                },
                "summary": clean_response
            }

        # Current timestamp
        current_time = datetime.now().isoformat()
        
        # Save to Firestore
        reading_ref = db.collection('sensor_readings').document()
        reading_data = {
            'temperature': temperature,
            'humidity': humidity,
            'noise': noise,
            'timestamp': current_time,
            'userId': user_id,
            'suggestion': suggestion_data,
            'raw_response': response.text,
            'using_custom_key': bool(user_data.get('gemini_api_key')),
            'request_number': requests_this_hour + 1
        }
        
        # Update both the reading and user data
        reading_ref.set(reading_data)
        user_ref.update({
            'requests_this_hour': requests_this_hour + 1,
            'last_request_hour': current_hour.isoformat(),
            'last_reading': reading_data
        })
        
        return suggestion_data
        
    except Exception as e:
        print(f"Error getting Gemini suggestion: {e}")
        return {
            "immediate_actions": ["Error occurred"],
            "health_impacts": ["Unable to generate suggestion"],
            "optimal_ranges": {
                "temperature": "N/A",
                "humidity": "N/A",
                "noise": "N/A"
            },
            "summary": "Unable to generate health suggestion at this time."
        }

@app.route('/api/sensor_data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json
        user_id = data.get('user_id')
        
        print(f"Received sensor data for user: {user_id}")  # Debug print
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
            
        # Validate required fields
        required_fields = ['temperature', 'humidity', 'noise']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get health suggestion
        suggestion = get_health_suggestion(
            data['temperature'],
            data['humidity'],
            data['noise'],
            user_id
        )
        
        # Current timestamp
        current_time = datetime.now().isoformat()
        
        # Save to Firestore
        reading_ref = db.collection('sensor_readings').document()
        reading_data = {
            'temperature': data['temperature'],
            'humidity': data['humidity'],
            'noise': data['noise'],
            'timestamp': current_time,
            'userId': user_id,  # Make sure this matches the field name in the query
            'suggestion': suggestion,
            'using_custom_key': False,  # Default to false
            'request_number': 1  # Default to 1
        }
        
        print(f"Saving reading data: {reading_data}")  # Debug print
        reading_ref.set(reading_data)
        print(f"Data saved with ID: {reading_ref.id}")  # Debug print
        
        return jsonify({
            'success': True,
            'suggestion': suggestion,
            'timestamp': current_time,
            'document_id': reading_ref.id  # Return the document ID for verification
        })
        
    except Exception as e:
        print(f"Error processing sensor data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_gemini_key', methods=['POST'])
def update_gemini_key():
    try:
        data = request.json
        user_id = data.get('user_id')
        api_key = data.get('api_key')
        
        if not user_id or not api_key:
            return jsonify({'error': 'Missing user_id or api_key'}), 400
        
        # Validate API key
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            model.generate_content("Test")
            
            # Update using Firestore transaction
            @firestore.transactional
            def update_key_in_transaction(transaction, user_ref):
                user_doc = user_ref.get(transaction=transaction)
                if not user_doc.exists:
                    transaction.set(user_ref, {
                        'gemini_api_key': api_key,
                        'requests_this_hour': 0,
                        'last_request_hour': None,
                        'created_at': firestore.SERVER_TIMESTAMP
                    })
                else:
                    transaction.update(user_ref, {
                        'gemini_api_key': api_key,
                        'requests_this_hour': 0,
                        'last_request_hour': None
                    })
            
            user_ref = db.collection('users').document(user_id)
            transaction = db.transaction()
            update_key_in_transaction(transaction, user_ref)
            
            return jsonify({'success': True, 'message': 'API key updated successfully'})
        except Exception as e:
            return jsonify({'error': 'Invalid API key'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove_gemini_key', methods=['POST'])
def remove_gemini_key():
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Update using Firestore transaction
        @firestore.transactional
        def remove_key_in_transaction(transaction, user_ref):
            user_doc = user_ref.get(transaction=transaction)
            if user_doc.exists:
                transaction.update(user_ref, {
                    'gemini_api_key': firestore.DELETE_FIELD,
                    'requests_this_hour': 0,
                    'last_request_hour': None
                })
        
        user_ref = db.collection('users').document(user_id)
        transaction = db.transaction()
        remove_key_in_transaction(transaction, user_ref)
        
        return jsonify({'success': True, 'message': 'API key removed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/api/recommendation', methods=['POST'])
# @limiter.limit(RateLimiter().get_limit)
# async def get_recommendation():
#     user_id = get_current_user_id()
#     sensor_data = request.json
    
#     # Validate sensor data
#     if not validate_sensor_data(sensor_data):
#         return jsonify({'error': 'Invalid sensor data'}), 400
    
#     # Store sensor data
#     firebase_service.store_sensor_data(user_id, sensor_data)
    
#     # Get recommendation
#     recommendation = await gemini_service.get_recommendation(user_id, sensor_data)
    
#     # Store recommendation
#     firebase_service.store_recommendation(user_id, recommendation, sensor_data)
    
#     return jsonify({'recommendation': recommendation})

if __name__ == '__main__':
    app.run(debug=True)