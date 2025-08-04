import streamlit as st
import requests

st.set_page_config(page_title="SQL Assistant", layout="centered")

st.title("🧠 SQL Assistant (Groq + FastAPI)")
st.write("Enter a natural language prompt and get back a SQL query.")

# Initialize chat history
if "history" not in st.session_state:
    st.session_state.history = []

API_URL = "http://localhost:8000/process"

# User input box
user_input = st.text_input("💬 Your input:", placeholder="e.g., Show top 10 products by sales")

if st.button("Submit") and user_input.strip():
    with st.spinner("Processing..."):
        # Format payload
        payload = {
            "text": user_input,
            "history": st.session_state.history
        }

        try:
            res = requests.post(API_URL, json=payload)
            res.raise_for_status()
            data = res.json()

            # Save to history
            st.session_state.history.append({"role": "user", "content": user_input})
            if data["validated"]:
                st.session_state.history.append({"role": "assistant", "content": data["query"]})
            else:
                st.session_state.history.append({"role": "assistant", "content": data["rewritten_suggestion"]})

            # Display checks
            st.subheader("🛡 Guardrail Results")
            for name, result in data["checks"]:
                icon = "✅" if result.strip().upper() == "OK" else "❌"
                st.write(f"{icon} {name}: `{result}`")

            # Show final result
            st.subheader("🧾 Final Output")
            if data["validated"]:
                st.code(data["query"], language="sql")
            else:
                st.warning("Input did not pass guardrails. Here's a rewritten suggestion:")
                st.info(data["rewritten_suggestion"])

        except Exception as e:
            st.error(f"Error: {str(e)}")

# Show chat history
if st.session_state.history:
    st.subheader("🕓 Conversation History")
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Assistant:** {msg['content']}")
