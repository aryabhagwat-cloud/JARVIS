import google.generativeai as genai

# Configure with your API Key
genai.configure(api_key="AIzaSyDsdFdIRn_5AfYFIJgqO2jeQoEqaOHwgak")

print("--- LIST OF AVAILABLE MODELS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")