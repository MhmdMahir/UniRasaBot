import tkinter as tk
import requests
from deep_translator import GoogleTranslator
from langdetect import detect

URL = "http://127.0.0.1:5005/webhooks/rest/webhook"

# Simple bad word list
bad_words = ["fuck", "shit", "bitch", "ass"]

def clean_text(text):
    """Replace bad words with asterisks."""
    words = text.split()
    cleaned = []
    for w in words:
        if w.lower() in bad_words:
            cleaned.append("*" * len(w))
        else:
            cleaned.append(w)
    return " ".join(cleaned)

def send_message():
    user_msg = entry.get()
    if not user_msg.strip():
        return

    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, "You: " + user_msg + "\n")
    entry.delete(0, tk.END)

    # Detect user language with langdetect
    try:
        detected_lang = detect(user_msg)
    except:
        detected_lang = "en"  # fallback to English

    # Translate user input to English for Rasa
    try:
        translated = GoogleTranslator(source=detected_lang, target='en').translate(user_msg)
    except:
        translated = user_msg

    # Clean bad words from translated input
    cleaned_input = clean_text(translated)

    # Send message to Rasa REST webhook
    try:
        response = requests.post(URL, json={
            "sender": "user",
            "message": cleaned_input
        })
        data = response.json()
    except Exception:
        chat_box.insert(tk.END, "Bot: [Error connecting to Rasa]\n")
        chat_box.config(state=tk.DISABLED)
        return

    # Translate Rasa response back to user language if needed
    for msg in data:
        bot_reply = msg.get("text", "")
        try:
            if detected_lang != "en":
                final_reply = GoogleTranslator(source='en', target=detected_lang).translate(bot_reply)
            else:
                final_reply = bot_reply
        except:
            final_reply = bot_reply

        chat_box.insert(tk.END, "Bot: " + final_reply + "\n")

    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)

# GUI Setup
root = tk.Tk()
root.title("Smart Chatbot")

chat_box = tk.Text(root, height=20, width=50, state=tk.DISABLED)
chat_box.pack(padx=10, pady=10)

entry = tk.Entry(root, width=40)
entry.pack(side=tk.LEFT, padx=10, pady=10)
entry.bind("<Return>", lambda event: send_message())

send_btn = tk.Button(root, text="Send", command=send_message)
send_btn.pack(side=tk.LEFT)

root.mainloop()