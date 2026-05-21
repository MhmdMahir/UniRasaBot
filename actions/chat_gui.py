import tkinter as tk
import requests
import re
from langdetect import detect
from deep_translator import GoogleTranslator
from tkinter import scrolledtext

URL = "http://127.0.0.1:5005/webhooks/rest/webhook"

# listing ssome bad words 
bad_words = [
    "fuck", "shit", "bitch", "ass", "nigga",
    "cunt", "dick", "pussy", "asshole", "fucking"
]

# defoult english
user_lang = "en"

def clean_text_ui(text):
    def censor(match):
        return "*" * len(match.group())

    pattern = re.compile(r'\b(' + '|'.join(bad_words) + r')\b', re.IGNORECASE)
    return pattern.sub(censor, text)

def clean_text_strict(text):
    return re.sub(
        r'\b(fuck|shit|bitch|ass|nigga|cunt|dick|pussy|asshole|fucking)\w*\b',
        '****',
        text,
        flags=re.IGNORECASE
    )

def normalize_lang_code(lang_code):
    """Convert langdetect format (zh-cn) to GoogleTranslator format (zh-CN)"""
    if '-' in lang_code:
        parts = lang_code.split('-')
        return parts[0].lower() + '-' + parts[1].upper()
    return lang_code.lower()

def detect_language(text):
    global user_lang
    try:
        lang = detect(text)
        lang = normalize_lang_code(lang)
        user_lang = lang
        print(f"[DEBUG-LANG] Language detected: {lang} for text: '{text[:30]}...'")
        return lang
    except Exception as e:
        print(f"[DEBUG-LANG] ERROR detecting language: {type(e).__name__}: {str(e)}")
        user_lang = "en"
        return "en"


def translate_to_english(text):
    try:
        result = GoogleTranslator(source='auto', target='en').translate(text)
        print(f"[DEBUG-TRANS] Translated to EN: '{text[:30]}...' → '{result[:30]}...'")
        return result
    except Exception as e:
        print(f"[DEBUG-TRANS] ERROR translating to English: {type(e).__name__}: {str(e)}")
        return text

def translate_back(text):
    global user_lang
    try:
        if user_lang == "en":
            print(f"[DEBUG-TRANS] No translation needed (user lang is EN)")
            return text
        result = GoogleTranslator(source='en', target=user_lang).translate(text)
        print(f"[DEBUG-TRANS] Translated back to {user_lang}: '{text[:30]}...' → '{result[:30]}...'")
        return result
    except Exception as e:
        print(f"[DEBUG-TRANS] ERROR translating back to {user_lang}: {type(e).__name__}: {str(e)}")
        return text

def send_message():
    user_msg = entry.get().strip()
    if not user_msg:
        return

    print(f"[DEBUG] 1. Raw user input: '{user_msg}'")
    
    # Detect language first 
    detected_lang = detect_language(user_msg)
    print(f"[DEBUG] 2. Detected language: {detected_lang}")

    
    cleaned_user_msg = clean_text_ui(user_msg)
    print(f"[DEBUG] 3. Cleaned for UI: '{cleaned_user_msg}'")

    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, "You: " + cleaned_user_msg + "\n", "user")
    entry.delete(0, tk.END)

    # Translate to English for Rasa
    translated = translate_to_english(user_msg)
    print(f"[DEBUG] 4. Translated to English: '{translated}'")

    # Strict clean before sending to Rasa
    cleaned_input = clean_text_strict(translated.lower())
    print(f"[DEBUG] 5. Strict cleaned for Rasa: '{cleaned_input}'")

    # Send to Rasa
    try:
        print(f"[DEBUG] 6. Sending request to Rasa: {URL}")
        print(f"[DEBUG] 7. Payload: {{'sender': 'user', 'message': '{cleaned_input}'}}")
        
        response = requests.post(URL, json={
            "sender": "user",
            "message": cleaned_input
        })
        
        print(f"[DEBUG] 8. Rasa response status: {response.status_code}")
        data = response.json()
        print(f"[DEBUG] 9. Rasa response data: {data}")
    except Exception as e:
        print(f"[DEBUG] ERROR connecting to Rasa: {type(e).__name__}: {str(e)}")
        chat_box.insert(tk.END, "Bot: [Error connecting to Rasa]\n", "bot")
        chat_box.config(state=tk.DISABLED)
        return

    # Bot response
    print(f"[DEBUG] 10. Processing {len(data)} response(s) from Rasa")
    for i, msg in enumerate(data):
        bot_reply = msg.get("text", "")
        print(f"[DEBUG] 11.{i} Raw bot reply: '{bot_reply}'")

        # clean bot message
        bot_reply = clean_text_ui(bot_reply)
        print(f"[DEBUG] 12.{i} Cleaned bot reply: '{bot_reply}'")

        # translate back to the same language user used
        final_reply = translate_back(bot_reply)
        print(f"[DEBUG] 13.{i} Translated back to {user_lang}: '{final_reply}'")

        chat_box.insert(tk.END, "Bot: " + final_reply + "\n\n", "bot")

    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)
    print(f"[DEBUG] 14. Message processing complete\n")


# gui itself
root = tk.Tk()
root.title("TARUMT FAQ Chatbot")
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

chat_box.config(state=tk.NORMAL)
chat_box.insert(tk.END, "Bot: Hello! How can I help you?\n\n", "bot")
chat_box.config(state=tk.DISABLED)

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