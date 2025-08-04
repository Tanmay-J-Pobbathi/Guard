# input_GR.py

import os
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME
import json

client = Groq(api_key=GROQ_API_KEY)

with open("prompts/input_policies.json", "r", encoding="utf-8") as f:
    POLICIES = json.load(f)

def input_security_and_toxicity_check(text_to_check: str, history: list = []) -> dict:
    system_prompt = POLICIES["security_policy"]

    messages = history + [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text_to_check}
    ]

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            temperature=0
        )
        reply = response.choices[0].message.content.strip()
        return eval(reply)  # Replace with safe parser in prod
    except Exception as e:
        return {
            "Prompt Injection": f"[Groq Error] {str(e)}",
            "Unauthorized Table Access": "NO",
            "Toxicity": "NO"
        }


def input_quality_and_intent_check(text_to_check: str, history: list = []) -> dict:
    system_prompt = POLICIES["intent_policy"]


    messages = history + [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text_to_check}
    ]

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            temperature=0
        )
        reply = response.choices[0].message.content.strip()
        return eval(reply)  # Replace with `json.loads()` in prod if returned format is strict JSON
    except Exception as e:
        return {
            "SQL Intent": f"[Groq Error] {str(e)}",
            "Language": "NO"
        }

def rewrite_if_flagged(original_text: str, validation_response: str) -> str:
    if validation_response.strip().upper() == "OK":
        return original_text

    rewrite_prompt = POLICIES["rewrite_policy"] + f"\n\nOriginal: {original_text}\n\nRewritten:"

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": rewrite_prompt}],
            model=GROQ_MODEL_NAME,
            temperature=0.5,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Rewrite Error] {str(e)}"

def run_input_guardrails(user_input: str, history: list) -> tuple[bool, list[tuple[str, str]]]:
    all_passed = True
    results = []

    # Check 1: Security and Toxicity
    sec_check = input_security_and_toxicity_check(user_input, history)
    for name, result in sec_check.items():
        results.append((name, result))
        if result.strip().upper() != "OK":
            all_passed = False

    # Check 2: SQL Intent + Language
    intent_check = input_quality_and_intent_check(user_input, history)
    for name, result in intent_check.items():
        results.append((name, result))
        if result.strip().upper() != "OK":
            all_passed = False

    return all_passed, results
