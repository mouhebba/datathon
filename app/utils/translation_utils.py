import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def translate_keywords_gpt(keywords, target_lang):
    """Translate a list of keywords using GPT."""
    if not keywords:
        return []

    prompt = (
        f"Translate the following keywords into {target_lang}. "
        "Return only a comma-separated list.\n\n"
        f"{', '.join(keywords)}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",   # cheap + fast, change if needed
        messages=[
            {"role": "system", "content": "You are a translation assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0,
    )

    translated = response.choices[0].message.content
    return [k.strip() for k in translated.split(",")]
