import os

def gemini_generate(prompt: str):
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except ImportError:
        print("⚠️ google-generativeai not installed — Gemini unavailable")
        return None
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return None