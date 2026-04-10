import tkinter as tk
import requests
import re
from deep_translator import GoogleTranslator
from langdetect import detect
from tkinter import scrolledtext

URL = "http://127.0.0.1:5005/webhooks/rest/webhook"

# -------------------------------
# BAD WORD LIST
# -------------------------------
bad_words = ["fuck", "shit", "bitch", "ass", "nigga", "cunt", "dick", "pussy", "asshole", "fucking"]

# -------------------------------
# UI CLEAN FILTER (SAFE)
# -------------------------------
def clean_text_ui(text):
    def censor(match):
        return "*" * len(match.group())

    # ONLY exact words (prevents "assist" issue)
    pattern = re.compile(r'\b(' + '|'.join(bad_words) + r')\b', re.IGNORECASE)
    return pattern.sub(censor, text)

# -------------------------------
# BACKEND FILTER (STRICT)
# -------------------------------
def clean_text_strict(text):
    # Blocks variations like "fucking"
    return re.sub(r'\b(fuck|shit|bitch|ass)\w*\b', '****', text, flags=re.IGNORECASE)

# -------------------------------
# LANGUAGE DETECTION
# -------------------------------
def detect_language(text):
    text = text.lower().strip()

    if len(text) <= 3:
        return "en"

    malay_keywords = [
        "apa", "saya", "awak", "boleh", "tak", "ya", "tidak",
        "kenapa", "macam", "mana", "nak", "lah", "ni"
    ]

    if any(word in text for word in malay_keywords):
        return "ms"

    try:
        lang = detect(text)
        if lang in ["en", "ms", "zh-cn"]:
            return lang
    except:
        pass

    return "en"

# -------------------------------
# TRANSLATION
# -------------------------------
def translate_to_english(text, source_lang):
    try:
        if source_lang == "en":
            return text
        return GoogleTranslator(source=source_lang, target='en').translate(text)
    except:
        return text

def translate_from_english(text, target_lang):
    try:
        if target_lang == "en":
            return text
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except:
        return text

# -------------------------------
# SEND MESSAGE
# -------------------------------
def send_message():
    user_msg = entry.get().strip()
    if not user_msg:
        return

    # UI CLEAN (user sees censored version)
    cleaned_user_msg = clean_text_ui(user_msg)

    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, "You: " + cleaned_user_msg + "\n", "user")
    entry.delete(0, tk.END)

    # Detect language
    detected_lang = detect_language(user_msg)

    # Translate
    translated = translate_to_english(user_msg, detected_lang)

    # STRICT CLEAN (for backend safety)
    cleaned_input = clean_text_strict(translated.lower())

    # Debug
    print("Original:", user_msg)
    print("Detected:", detected_lang)
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

    # Show bot reply
    for msg in data:
        bot_reply = msg.get("text", "")

        # UI clean (no "assist" bug)
        bot_reply = clean_text_ui(bot_reply)

        # Translate back
        final_reply = translate_from_english(bot_reply, detected_lang)

        chat_box.insert(tk.END, "Bot: " + final_reply + "\n\n", "bot")

    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)

# -------------------------------
# GUI
# -------------------------------
root = tk.Tk()
root.title("Smart Chatbot")
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