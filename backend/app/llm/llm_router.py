from app.llm.groq_llm import groq_generate
from app.llm.ollama_llm import ollama_generate

def generate(prompt):
    result = groq_generate(prompt)
    if result:
        return result

    print("⚠️ All 18 Groq keys failed. Falling back to local Ollama...")
    try:
        return ollama_generate(prompt)
    except Exception as e:
        print(f"❌ Ollama also failed: {e}")
        return None