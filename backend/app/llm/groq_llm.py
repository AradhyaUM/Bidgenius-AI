import os
import logging
import time

logger = logging.getLogger("bidgenius.groq")


def groq_generate(prompt: str) -> str | None:
    # Read key EVERY call — not at import time.
    # On Railway, env vars are injected after the module first loads,
    # so caching at module level causes "MISSING" forever.
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        logger.error("No GROQ_API_KEY set")
        return None

    try:
        from groq import Groq, RateLimitError

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        return response.choices[0].message.content

    except RateLimitError:
        logger.warning("Groq rate limit hit — waiting 5s and retrying")
        time.sleep(5)
        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq retry failed: {e}")
            return None

    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None