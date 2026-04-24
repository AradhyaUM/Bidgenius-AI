from app.llm.groq_llm import groq_generate

def generate(prompt):
    result = groq_generate(prompt)
    if result:
        return result

    print("⚠️ All Groq keys failed. Trying optional Ollama fallback...")
    try:
        # Import lazily so cloud runtimes (like Vercel) don't crash
        # when local-only Ollama is not installed.
        from app.llm.ollama_llm import ollama_generate
        return ollama_generate(prompt)
    except Exception as e:
        print(f"❌ Ollama also failed: {e}")
        return None