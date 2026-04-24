def ollama_generate(prompt: str):
    try:
        import ollama
        response = ollama.chat(
            model="llama3",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        print("Ollama Failed →", e)
        return None