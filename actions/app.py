import streamlit as st  # type: ignore[reportMissingImports]
import requests
import re

URL = "https://mohamedmahir-rasa-backend.hf.space/webhooks/rest/webhook"

# Bad words list
bad_words = [
    "fuck", "shit", "bitch", "ass", "nigga",
    "cunt", "dick", "pussy", "asshole", "fucking"
]


# -----------------------------
# Cleaning Functions
# -----------------------------
def clean_text_ui(text):

    def censor(match):
        return "*" * len(match.group())

    pattern = re.compile(
        r'\b(' + '|'.join(bad_words) + r')\b',
        re.IGNORECASE
    )

    return pattern.sub(censor, text)


def clean_text_strict(text):

    return re.sub(
        r'\b(fuck|shit|bitch|ass|nigga|cunt|dick|pussy|asshole|fucking)\w*\b',
        '****',
        text,
        flags=re.IGNORECASE
    )


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="TARUMT FAQ Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 TARUMT FAQ Chatbot")


# Initialize chat history
if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "bot",
            "content": "Hello! How can I help you?"
        }
    ]


# Display previous messages
for msg in st.session_state.messages:

    if msg["role"] == "user":

        with st.chat_message("user"):
            st.write(msg["content"])

    else:

        with st.chat_message("assistant"):
            st.write(msg["content"])


# User input
user_msg = st.chat_input("Type your message...")


# -----------------------------
# Send Message
# -----------------------------
if user_msg:

    print(f"[DEBUG] Raw input: {user_msg}")

    # Clean for UI
    cleaned_user_msg = clean_text_ui(user_msg)

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": cleaned_user_msg
    })

    with st.chat_message("user"):
        st.write(cleaned_user_msg)

    # Strict clean before sending to Rasa
    cleaned_input = clean_text_strict(
        user_msg.lower()
    )

    print(f"[DEBUG] Sending to Rasa: {cleaned_input}")

    # Send request to Rasa
    try:

        response = requests.post(
            URL,
            json={
                "sender": "user",
                "message": cleaned_input
            }
        )

        data = response.json()

        print(f"[DEBUG] Rasa response: {data}")

    except Exception as e:

        error_msg = f"[Error connecting to Rasa] {e}"

        st.session_state.messages.append({
            "role": "bot",
            "content": error_msg
        })

        with st.chat_message("assistant"):
            st.error(error_msg)

        st.stop()

    # Display bot responses
    for msg in data:

        bot_reply = msg.get("text", "")

        # Clean bot reply
        bot_reply = clean_text_ui(bot_reply)

        print(f"[DEBUG] Bot reply: {bot_reply}")

        # Save to history
        st.session_state.messages.append({
            "role": "bot",
            "content": bot_reply
        })

        # Display reply
        with st.chat_message("assistant"):
            st.write(bot_reply)