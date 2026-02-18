import google.generativeai as genai

# PASTE YOUR KEY DIRECTLY HERE
TEST_KEY = "AIzaSyB0hq6ReqzNWBQtahrew7mVFpwBLQz3agw" 

print("1. Configuring API...")
genai.configure(api_key=TEST_KEY)

print("2. Connecting to Gemini Model...")
try:
    # Try the standard model first
    model = genai.GenerativeModel('gemini-pro')
    
    print("3. Sending message...")
    response = model.generate_content("Hello, are you working?")
    
    print("\n✅ SUCCESS! The AI replied:")
    print(response.text)

except Exception as e:
    print("\n❌ FAILED. Here is the exact error:")
    print(e)
    print("\n------------------------------------------------")
    print("HOW TO FIX IT:")
    error_msg = str(e)
    if "400" in error_msg:
        print("-> Your API Key is invalid. Go to https://aistudio.google.com/app/apikey and create a new one.")
    elif "403" in error_msg:
        print("-> Your Key is valid, but the API is blocked. Go to Google Cloud Console > APIs & Services > Enable 'Generative Language API'.")
    elif "404" in error_msg:
        print("-> Run this command in terminal: pip install --upgrade google-generativeai")