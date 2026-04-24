import os
import logging
import time

logger = logging.getLogger("bidgenius.groq")

GROQ_KEYS = [
    k for k in [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
        os.getenv("GROQ_API_KEY_5"),
        os.getenv("GROQ_API_KEY_6"),
        os.getenv("GROQ_API_KEY_7"),
        os.getenv("GROQ_API_KEY_8"),
        os.getenv("GROQ_API_KEY_9"),
        os.getenv("GROQ_API_KEY_10"),
        os.getenv("GROQ_API_KEY_11"),
        os.getenv("GROQ_API_KEY_12"),
        os.getenv("GROQ_API_KEY_13"),
        os.getenv("GROQ_API_KEY_14"),
        os.getenv("GROQ_API_KEY_15"),
        os.getenv("GROQ_API_KEY_16"),
        os.getenv("GROQ_API_KEY_17"),
        os.getenv("GROQ_API_KEY_18"),
    ]
    if k
]

if not GROQ_KEYS:
    raise ValueError("No GROQ_API_KEY_* found in environment")

_key_index = 0

def _rotate():
    global _key_index
    _key_index = (_key_index + 1) % len(GROQ_KEYS)
    logger.info(f"Rotated to Groq key slot {_key_index + 1}/{len(GROQ_KEYS)}")

def groq_generate(prompt: str) -> str | None:
    from groq import Groq, RateLimitError

    for attempt in range(len(GROQ_KEYS)):
        try:
            client = Groq(api_key=GROQ_KEYS[_key_index])
            response = client.chat.completions.create(
                model="gemma2-9b-it",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3,
            )
            time.sleep(2)
            return response.choices[0].message.content

        except RateLimitError:
            logger.warning(f"Rate limit on key slot {_key_index + 1} — rotating")
            _rotate()
            time.sleep(2)
            continue

        except Exception as e:
            logger.error(f"Groq error (key slot {_key_index + 1}): {e}")
            _rotate()
            break

    return None