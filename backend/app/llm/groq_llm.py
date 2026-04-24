import os
import logging
import time

logger = logging.getLogger("bidgenius.groq")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found in environment — LLM calls will fail")


def groq_generate(prompt: str) -> str | None:
    if not GROQ_API_KEY:
        logger.error("No GROQ_API_KEY set")
        return None

    try:
        from groq import Groq, RateLimitError

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3,
        )
        return response.choices[0].message.content

    except RateLimitError:
        logger.warning("Groq rate limit hit — waiting 5s and retrying")
        time.sleep(5)
        try:
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq retry failed: {e}")
            return None

    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None