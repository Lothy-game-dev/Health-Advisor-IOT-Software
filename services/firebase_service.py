from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseService:
    def __init__(self, credential_path):
        try:
            cred = credentials.Certificate(credential_path)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            print("Firebase Admin SDK initialized successfully")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")
            raise e

    def get_user_data(self, user_id):
        """Get user data, create if doesn't exist"""
        user_ref = self.db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            default_data = {
                "requests_this_hour": 0,
                "last_request_hour": None,
                "using_dev_account": True,
                "created_at": datetime.now().isoformat(),
            }
            user_ref.set(default_data)
            return default_data

        return user_doc.to_dict()

    def save_sensor_reading(self, user_id, reading_data):
        """Save sensor reading to database"""
        reading_ref = self.db.collection("sensor_readings").document()
        reading_ref.set(reading_data)
        return reading_ref.id

    def update_user_usage(self, user_id, reading_data):
        """Update user's usage data"""
        user_ref = self.db.collection("users").document(user_id)
        current_hour = (
            datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()
        )

        user_ref.update(
            {
                "requests_this_hour": firestore.Increment(1),
                "last_request_hour": current_hour,
                "last_reading": reading_data,
            }
        )

    def update_gemini_key(self, user_id, api_key):
        """Update user's Gemini API key using transaction"""
        user_ref = self.db.collection("users").document(user_id)

        @firestore.transactional
        def update_key_transaction(transaction, ref):
            doc = ref.get(transaction=transaction)
            if not doc.exists:
                transaction.set(
                    ref,
                    {
                        "gemini_api_key": api_key,
                        "requests_this_hour": 0,
                        "last_request_hour": None,
                        "created_at": firestore.SERVER_TIMESTAMP,
                    },
                )
            else:
                transaction.update(
                    ref,
                    {
                        "gemini_api_key": api_key,
                        "requests_this_hour": 0,
                        "last_request_hour": None,
                    },
                )

        transaction = self.db.transaction()
        update_key_transaction(transaction, user_ref)

    def remove_gemini_key(self, user_id):
        """Remove user's Gemini API key using transaction"""
        user_ref = self.db.collection("users").document(user_id)

        @firestore.transactional
        def remove_key_transaction(transaction, ref):
            doc = ref.get(transaction=transaction)
            if doc.exists:
                transaction.update(
                    ref,
                    {
                        "gemini_api_key": firestore.DELETE_FIELD,
                        "requests_this_hour": 0,
                        "last_request_hour": None,
                    },
                )

        transaction = self.db.transaction()
        remove_key_transaction(transaction, user_ref)
