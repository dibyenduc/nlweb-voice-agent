print("Script starting...")

import sys
print("Python path:", sys.path)

try:
    import requests
    print("✅ requests imported successfully")
except ImportError as e:
    print("❌ requests import failed:", e)

try:
    import speech_recognition as sr
    print("✅ speech_recognition imported successfully")
except ImportError as e:
    print("❌ speech_recognition import failed:", e)

try:
    import pyttsx3
    print("✅ pyttsx3 imported successfully")
except ImportError as e:
    print("❌ pyttsx3 import failed:", e)

print("All imports checked. Testing basic functionality...")

# Test NLWeb connection
try:
    response = requests.get("http://localhost:8000", timeout=5)
    print(f"✅ NLWeb server responded with status: {response.status_code}")
except Exception as e:
    print(f"❌ NLWeb connection failed: {e}")

print("Script completed.")
