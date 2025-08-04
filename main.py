from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from input_GR import run_input_guardrails, rewrite_if_flagged
from Groq_Client import groq_llm, trim_history
from output_GR import run_output_guardrails  # ✅ NEW import

app = FastAPI()

class UserInput(BaseModel):
    text: str
    history: List[dict] = []

@app.post("/process")
async def process_input(user_input: UserInput):
    input_text = user_input.text

    # Trim history
    history_for_guardrails = trim_history(user_input.history, max_len=2)
    history_for_llm = trim_history(user_input.history, max_len=6)

    # ✅ STEP 1: Input Guardrails
    input_passed, input_checks = run_input_guardrails(input_text, history_for_guardrails)

    if not input_passed:
        reason = next((res for _, res in input_checks if res.strip().upper() != "OK"), "NO")
        rewritten = rewrite_if_flagged(input_text, reason)
        return {
            "status": "rejected",
            "stage": "input",
            "validated": False,
            "checks": input_checks,
            "original_input": input_text,
            "rewritten_suggestion": rewritten
        }

    # ✅ STEP 2: Generate SQL with Groq LLM
    sql_response = groq_llm(input_text, history_for_llm)

    # ✅ STEP 3: Output Guardrails
    output_checks = run_output_guardrails(input_text, sql_response, history_for_guardrails)
    output_passed = all(result == "OK" for _, result in output_checks)

    if not output_passed:
        return {
            "status": "rejected",
            "stage": "output",
            "validated": False,
            "checks": input_checks + output_checks,
            "original_input": input_text,
            "llm_output": sql_response,
            "output_issues": output_checks
        }

    # ✅ STEP 4: Return final result
    return {
        "status": "success",
        "validated": True,
        "checks": input_checks + output_checks,
        "original_input": input_text,
        "query": sql_response
    }
