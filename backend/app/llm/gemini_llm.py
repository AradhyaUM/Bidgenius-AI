import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def gemini_generate(prompt: str):
    model = genai.GenerativeModel("gemini-2.0-flash")  # ✅ FIXED
    response = model.generate_content(prompt)
    return response.text