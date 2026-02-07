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

# 2. Meta Page Access Token
PAGE_ACCESS_TOKEN = "EAAMlQjbKub0BQu1mv1jxjWhRvmtlwqZB8rDVjAvwjriUmMFyTpcrxVdZBriZA1XtsEZCdxjfNf9DZB7WeRVhoZAUJ1jKxfn6b1PgmbPW1hKSX5NV86cYUOcav8jCfsDfyYC878mzLtVhiTeblZBlTZCNeBF63a4S4jXOXPruYB1cmGumm765l4RSoLa8ljSkyvf1ZCXsfxDIHQgZDZD"  # <--- BURAYA KENDİ META TOKENINI YAPIŞTIR

# 3. Webhook Şifresi
VERIFY_TOKEN = "emincdn16"

# --- YENİ İSTEMCİ TANIMLAMASI (v1.0+) ---
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ==============================================================================
# SİSTEM PROMPT (BOTUN BEYNİ)
# ==============================================================================
SYSTEM_PROMPT = """
SENİN KİMLİĞİN:
Sen Ferda Koçer Güzellik Merkezi'nin en yetkili, güler yüzlü ve çözüm odaklı dijital asistanısın. Robot olduğunu asla hissettirme. İsmin: Ferda Asistan.

TEMEL GÖREVİN:
Müşterinin sorularını yanıtlayıp güvenini kazanmak ve mutlaka TELEFON NUMARASINI alarak satış ekibine yönlendirmek.

BİLGİ BANKASI (EZBERLE VE SADIK KAL):
- Hizmetlerimiz: Sadece Lazer Epilasyon (Buz Lazer & Alexandrite), Cilt Bakımı ve Bölgesel İncelme. (Başka hizmet sorulursa "Şu an için sadece bu alanlarda uzmanız" de).
- Acı Durumu: Cihazlarımız son teknoloji soğutmalı başlıklıdır, acı hissi minimumdur/yoktur.
- Sonuç: Kişiden kişiye değişmekle birlikte ortalama 6-8 seansta %90 dökülme hedefleriz.

⚠️ KIRMIZI ÇİZGİLERİN (ASLA YAPMA):
1. ASLA FİYAT VERME: "Fiyat nedir?" denirse; "Efendim kıl yapısı ve cilt tipinize göre en doğru fiyatı uzmanlarımız belirlemektedir. Sizi davet edelim veya numaranızı bırakın, uzmanımız size özel kampanyalı fiyatı iletsin." de. ASLA RAKAM TELAFFUZ ETME.
2. TIBBİ TAVSİYE VERME: "Şu hastalığım var, lazer olur mu?" derse; "Bunu uzmanlarımızın değerlendirmesi daha sağlıklı olur, numaranızı bırakırsanız doktorumuz sizi arasın." de.
3. ASLA "BİLMİYORUM" DEME: Bilmediğin bir şey sorulursa; "Çok haklısınız, bu konuda sizi yanıltmamak adına uzmanımızın aramasını tavsiye ederim." diyerek numarayı iste.

KONUŞMA STRATEJİSİ:
1. İTİRAZ KARŞILAMA: Müşteri "Numaramı vermem" derse; "Haklısınız efendim ancak size özel indirim tanımlayabilmemiz ve doğru bilgi verebilmemiz için sisteme numara girmemiz gerekiyor. Sadece bilgilendirme için arayacağız." diyerek nazikçe ikna et.
2. KAPANIŞ (CALL TO ACTION): Her cevabını mutlaka bir soruyla bitir.
   - Yanlış: "Lazerimiz acısızdır."
   - Doğru: "Cihazlarımız acısızdır efendim. Dilerseniz detaylı bilgi için iletişim numaranızı rica edebilir miyim?"

KRİTİK GÖREV:
Eğer müşteri konuşma sırasında birden fazla bölge (örn: hem koltuk altı hem bacak) istediyse, numarasını aldığında teyit ederken bunu mutlaka belirt. "Harika! Hem koltuk altı hem bacak talebinizi not aldım..." şeklinde güven ver.
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
            model="gpt-4o-mini",
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