import os
import json
import google.generativeai as genai


class GeminiService:
    def __init__(self):
        self.default_api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.default_api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def configure_with_key(self, api_key=None):
        """Configure Gemini with either user API key or default key"""
        key = api_key if api_key else self.default_api_key
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def get_health_suggestion(self, temperature, humidity, noise):
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

        try:
            response = self.model.generate_content(prompt)

            # Clean the response text
            clean_response = response.text.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
            clean_response = clean_response.strip()

            # Parse the JSON response
            suggestion_data = json.loads(clean_response)
            return suggestion_data, response.text
        except Exception as e:
            print(f"Error generating suggestion: {e}")
            return self._get_error_response(), str(e)

    def validate_api_key(self, api_key):
        """Test if an API key is valid"""
        try:
            genai.configure(api_key=api_key)
            test_model = genai.GenerativeModel("gemini-2.0-flash")
            test_model.generate_content("Test")
            # Restore original configuration
            self.configure_with_key()
            return True
        except:
            # Restore original configuration
            self.configure_with_key()
            return False

    def _get_error_response(self):
        """Return a default error response"""
        return {
            "immediate_actions": ["Error occurred"],
            "health_impacts": ["Unable to generate suggestion"],
            "optimal_ranges": {"temperature": "N/A", "humidity": "N/A", "noise": "N/A"},
            "summary": "Unable to generate health suggestion at this time.",
        }
