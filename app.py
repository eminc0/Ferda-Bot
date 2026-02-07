import os
from flask import Flask, request, jsonify
from openai import OpenAI  # DİKKAT: Yeni import şekli bu
import requests
import re

app = Flask(__name__)

# ==============================================================================
# AYARLAR (BURALARI KENDİ BİLGİLERİNLE DOLDUR)
# ==============================================================================

# 1. OpenAI API Anahtarı
OPENAI_API_KEY = "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<x "  # <--- BURAYA KENDİ KEYİNİ YAPIŞTIR

# 2. Meta Page Access Token
PAGE_ACCESS_TOKEN = "EAAMlQjbKub0BQn1YYxk0ZCSGig9vfQUqAH9L3fdkLIow8FkXc1I1QFFZBs1ADGuW9P8fTY1Bg5mf3iZCxfqzkIPtGLJ3m4mZB7WhpYW7JL39qFYpewOEPtwL1WW4z6I9zTg60iORK5aQUMOUDnHNous0BmlsUF4LOwfmdhujxwSYOjyugQFWZAMjK9GgxB9pjT4ZCN9ydHhJoLALiQBWqnptLdPTycQvqZCqbpn38UI63kZD"  # <--- BURAYA KENDİ META TOKENINI YAPIŞTIR

# 3. Webhook Şifresi
VERIFY_TOKEN = "emincdn16"

# --- YENİ İSTEMCİ TANIMLAMASI (v1.0+) ---
client = OpenAI(api_key=OPENAI_API_KEY)

# ==============================================================================
# SİSTEM PROMPT (BOTUN BEYNİ)
# ==============================================================================
SYSTEM_PROMPT = """
SENİN KİMLİĞİN:
Sen Ferda Koçer Güzellik Merkezi'nin deneyimli, güler yüzlü dijital asistanısın. öyle ki konuşmalarında bir yapa zeka değil bilgisyar başındaki gerçek bir çalışan gibi konuşuyorsun, böylece müşteri senin yapay zeka olduğunu anlamıyor.
Amacın: Müşterinin sorularını cevaplamak ve telefon numarasını alıp satış ekibine yönlendirmek.

KONUŞMA TONUN:
1. SAMİMİ VE SICAK: "Selamlar! 🌸 Size nasıl destek olabilirim?"
2. KISA VE NET: 1-2 cümle yeterli.
3. SATIŞ ODAKLI: Cümleyi mutlaka soruyla veya numara isteyerek bitir.

GÖREV:
Numarayı alana kadar nazikçe ısrarcı ol.
"""


# ==============================================================================
# YARDIMCI FONKSİYONLAR
# ==============================================================================

def extract_phone_number(text):
    """Mesajın içinde telefon numarası var mı diye bakar."""
    pattern = r"(\+90|0)?\s*5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}"
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None


def generate_ai_response(user_message):
    """OpenAI GPT Modelinden Cevap Alır (GÜNCELLENMİŞ VERSİYON)"""
    try:
        # Eski kod: openai.ChatCompletion.create(...) ARTIK YOK
        # Yeni kod: client.chat.completions.create(...)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        # Yeni cevap okuma şekli (Obje olarak geliyor)
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Hatası: {e}")
        return "Şu an sistemde yoğunluk var ama mesajınızı aldık! İletişim numaranızı bırakırsanız hemen dönelim 😊"


def send_instagram_message(recipient_id, text):
    """Instagram Graph API üzerinden mesaj gönderir"""
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code != 200:
            print(f"Mesaj Gönderme Hatası: {r.text}")
    except Exception as e:
        print(f"Request Hatası: {e}")


# ==============================================================================
# WEBHOOK ROTASI
# ==============================================================================
@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Doğrulama Başarısız", 403
    return "Merhaba, burası DolunAI Webhook Kapısı", 200


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # ARTIK HEM INSTAGRAM HEM PAGE (FACEBOOK) KABUL EDİYORUZ
    if data.get('object') == 'instagram' or data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging in entry.get('messaging', []):
                if 'message' in messaging and 'text' in messaging['message']:
                    sender_id = messaging['sender']['id']
                    user_message = messaging['message']['text']

                    if messaging['message'].get('is_echo'):
                        continue

                    print(f"\n📩 GELEN MESAJ ({sender_id}): {user_message}")

                    phone = extract_phone_number(user_message)
                    if phone:
                        print(f"💰 LEAD YAKALANDI! Tel: {phone}")

                    ai_reply = generate_ai_response(user_message)
                    print(f"🤖 BOT CEVABI: {ai_reply}")

                    send_instagram_message(sender_id, ai_reply)

        return "EVENT_RECEIVED", 200
    else:
        return "Not Found", 404


if __name__ == '__main__':
    print("🚀 DolunAI Bot Başlatıldı...")
    app.run(port=5000, debug=True)