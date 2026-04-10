import tkinter as tk
import requests
import re
from deep_translator import GoogleTranslator
from tkinter import scrolledtext

URL = "http://127.0.0.1:5005/webhooks/rest/webhook"

# -------------------------------
# BAD WORD LIST
# -------------------------------
bad_words = [
    "fuck", "shit", "bitch", "ass", "nigga",
    "cunt", "dick", "pussy", "asshole", "fucking"
]

# -------------------------------
# LANGUAGE STORAGE (IMPORTANT FIX)
# -------------------------------
user_lang = "en"

# -------------------------------
# CLEAN UI FILTER (SAFE DISPLAY)
# -------------------------------
def clean_text_ui(text):
    def censor(match):
        return "*" * len(match.group())

    pattern = re.compile(r'\b(' + '|'.join(bad_words) + r')\b', re.IGNORECASE)
    return pattern.sub(censor, text)

# -------------------------------
# STRICT BACKEND FILTER
# -------------------------------
def clean_text_strict(text):
    return re.sub(
        r'\b(fuck|shit|bitch|ass)\w*\b',
        '****',
        text,
        flags=re.IGNORECASE
    )

# -------------------------------
# STEP 1: DETECT LANGUAGE PROPERLY
# -------------------------------
def detect_language(text):
    global user_lang
    try:
        lang = GoogleTranslator(source='auto', target='en').detect(text)
        user_lang = lang
        return lang
    except:
        user_lang = "en"
        return "en"

# -------------------------------
# STEP 2: TRANSLATE TO ENGLISH
# -------------------------------
def translate_to_english(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text

# -------------------------------
# STEP 3: TRANSLATE BACK TO USER LANGUAGE
# -------------------------------
def translate_back(text):
    global user_lang
    try:
        if user_lang == "en":
            return text
        return GoogleTranslator(source='en', target=user_lang).translate(text)
    except:
        return text

# -------------------------------
# SEND MESSAGE FUNCTION
# -------------------------------
def send_message():
    user_msg = entry.get().strip()
    if not user_msg:
        return

    # Detect language FIRST
    detect_language(user_msg)

    # UI display (cleaned user input)
    cleaned_user_msg = clean_text_ui(user_msg)

    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, "You: " + cleaned_user_msg + "\n", "user")
    entry.delete(0, tk.END)

    # Translate to English for Rasa
    translated = translate_to_english(user_msg)

    # Strict clean before sending to Rasa
    cleaned_input = clean_text_strict(translated.lower())

    print("Original:", user_msg)
    print("Detected Language:", user_lang)
    print("Translated:", translated)
    print("Backend Cleaned:", cleaned_input)

    # Send to Rasa
    try:
        response = requests.post(URL, json={
            "sender": "user",
            "message": cleaned_input
        })
        data = response.json()
    except Exception:
        chat_box.insert(tk.END, "Bot: [Error connecting to Rasa]\n", "bot")
        chat_box.config(state=tk.DISABLED)
        return

    # Bot response
    for msg in data:
        bot_reply = msg.get("text", "")

        # clean bot message
        bot_reply = clean_text_ui(bot_reply)

        # translate BACK to SAME language user used
        final_reply = translate_back(bot_reply)

        chat_box.insert(tk.END, "Bot: " + final_reply + "\n\n", "bot")

    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)

# -------------------------------
# GUI
# -------------------------------
root = tk.Tk()
root.title("Smart Multilingual Chatbot")
root.geometry("500x600")
root.configure(bg="#2C2F33")

chat_frame = tk.Frame(root, bg="#2C2F33")
chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

chat_box = scrolledtext.ScrolledText(
    chat_frame,
    wrap=tk.WORD,
    state=tk.DISABLED,
    bg="#23272A",
    fg="white",
    font=("Arial", 11),
    padx=10,
    pady=10
)
chat_box.pack(fill=tk.BOTH, expand=True)

chat_box.tag_config("user", foreground="#00BFFF")
chat_box.tag_config("bot", foreground="#7CFC00")

input_frame = tk.Frame(root, bg="#2C2F33")
input_frame.pack(fill=tk.X, padx=10, pady=10)

entry = tk.Entry(
    input_frame,
    font=("Arial", 12),
    bg="#40444B",
    fg="white",
    insertbackground="white"
)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
entry.bind("<Return>", lambda event: send_message())

send_btn = tk.Button(
    input_frame,
    text="Send",
    command=send_message,
    bg="#7289DA",
    fg="white",
    activebackground="#5b6eae",
    relief=tk.FLAT,
    padx=15,
    pady=5
)
send_btn.pack(side=tk.RIGHT)

root.mainloop()