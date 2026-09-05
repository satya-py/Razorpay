"""
Intent Parser
--------------
Converts a natural-language user request into a structured task using an LLM.

Example input:  "reorder my office supplies under 2000 rupees"
Example output: {
    "action": "reorder",
    "item": "office supplies",
    "max_amount": 2000,
    "currency": "INR",
    "recurring": false
}
"""

import json
from openai import OpenAI

SYSTEM_PROMPT = """You are an intent parser for a commerce automation agent.
Convert the user's request into STRICT JSON with these fields only:

{
  "action": "reorder" | "renew_subscription" | "pay_invoice",
  "item": string,
  "max_amount": number,
  "currency": "INR",
  "recurring": boolean,
  "notes": string
}

Rules:
- max_amount must be a number (no currency symbols).
- If no amount is mentioned, estimate a reasonable one and say so in notes.
- Return ONLY valid JSON. No markdown, no commentary, no code fences.
"""


def parse_intent(user_input: str, api_key: str) -> dict:
    """
    Calls the LLM to turn free text into a structured task dict.
    Raises ValueError if the model does not return valid JSON.
    """
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    # Defensive cleanup in case the model wraps output in code fences
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {raw}") from e

    return parsed
