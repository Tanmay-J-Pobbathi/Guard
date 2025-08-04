import os
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_NAM_LLM

SYSTEM_PROMPT = """
You are a SQL assistant. Convert natural language requests into safe SQL queries using the following schema:

- customers(id, name, email, country)
- orders(id, customer_id, product_id, order_date, amount)
- products(id, name, price)
- sales(id, sale_date, product_id, quantity, total_amount)
- employees (id, name, department)

Rules:
- Use only the above tables/fields.
- Sort results when user asks for "top" or "bottom".
- Use LIMIT for top/bottom entries.
- Do not invent fields.
- Always use valid SQL syntax.
Return only a single SQL query — no explanations.
"""

client = Groq(api_key=GROQ_API_KEY)

def trim_history(hist, max_len=6):
    """Trim chat history to the most recent N exchanges."""
    return hist[-max_len:] if len(hist) > max_len else hist

def groq_llm(prompt: str, history: list = []) -> str:
    trimmed_history = trim_history(history)

    messages = trimmed_history + [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAM_LLM,
            messages=messages,
            temperature=0.3,
            top_p=0.9,
            max_tokens=300
        )
        reply = response.choices[0].message.content.strip()
        return reply if reply else "[Groq LLM Error] Empty response"
    except Exception as e:
        return f"[Groq LLM Error] {str(e)}"
