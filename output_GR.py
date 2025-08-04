import os
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME
import json  # Add this at the top

client = Groq(api_key=GROQ_API_KEY)

with open("prompts/output_policies.json", "r", encoding="utf-8") as f:
    POLICIES = json.load(f)

def output_sensitive_keyword_check(sql_code: str, history: list = []) -> str:
    sensitive_keywords = ["TRUNCATE", "DROP", "ALTER", "GRANT", "REVOKE"]
    for keyword in sensitive_keywords:
        if keyword in sql_code.upper():
            return "NO"
    return "OK"

def output_all_checks_combined(nl_input: str, sql_code: str, history: list = []) -> dict:
    if not sql_code.strip():
        return {
            "Syntax": "NO",
            "Intent Alignment": "NO",
            "Sensitive Keywords": "NO"
        }

    system_prompt = POLICIES["output_validation_policy"]
    combined_input = f"User Input: {nl_input}\nGenerated SQL: {sql_code}"

    messages = history + [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": combined_input}
    ]

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            temperature=0
        )
        reply = response.choices[0].message.content.strip()
        parsed = eval(reply)  # Note: Use json.loads() with valid JSON in production

        # Add sensitive keyword result from local function
        parsed["Sensitive Keywords"] = output_sensitive_keyword_check(sql_code)
        return parsed
    except Exception as e:
        return {
            "Syntax": f"[Groq Error] {str(e)}",
            "Intent Alignment": "NO",
            "Sensitive Keywords": "NO"
        }

def run_output_guardrails(nl_input: str, sql_code: str, history: list = []) -> list:
    results_dict = output_all_checks_combined(nl_input, sql_code, history)
    return [(name, result.strip().upper()) for name, result in results_dict.items()]
