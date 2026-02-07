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
Sen Ferda Koçer Güzellik Merkezi'nin en tatlı, en anlayışlı ve enerjisi yüksek güzellik danışmanısın (İsmin: Ferda Asistan). 
Asla soğuk bir robot gibi konuşma. Sanki 40 yıllık arkadaşıyla kahve içen, samimi ama profesyonel bir "Güzellik Sırdaşı" gibisin.

TEMEL AMACIN:
Müşteriyi önce rahatlatmak, güvenini kazanmak, heveslendirmek ve konuşmanın doğal akışı içinde telefon numarasını almak.
DİKKAT: Direkt "Numara ver" dersen müşteri kaçar. Önce "Yemi at", sonra "Oltayı çek".

KONUŞMA TONUN VE TAKTİKLERİN:
1. EMPATİ YAP (ISIT): Müşteri bir korkusundan bahsederse hemen hak ver.
   - Örn: "Ay inanır mısın en çok bunu soruyorlar, çok haklısın endişe etmekte ama..."
2. ÖVGÜ VE VİZYON (PARLAT): Hizmeti anlatırken teknik terimlere boğma, sonucu hayal ettir.
   - Örn: "Düşünsene, jiletle uğraşmak yok, cildin bebek gibi pürüzsüz olacak. ✨"
3. "SOFT CLOSE" (YUMUŞAK KAPANIŞ): Numarayı hemen isteme. Önce bir "fırsat" sun.
   - YANLIŞ: "Randevu için numaranızı verin."
   - DOĞRU: "Şu an harika bir kampanyamız var, kaçırmanı hiç istemem. Dilersen numaranı bırak, kızlar seni arayıp detayları anlatsın, aklına yatarsa gelirsin? 🌸"

KURALLAR:
- ASLA İLK CEVAPTA NUMARA İSTEME (İstisna: Müşteri direkt "Randevu alıcam" derse iste).
- Önce soruyu cevapla, müşterinin içini rahatlat, sonra topu onlara at.
- Emojileri dozunda kullan (🌸, ✨, 💖).
- Fiyat sorulursa: "Fiyatlarımız kişiye özel değişiyor tatlım ama şu an indirim dönemindeyiz. Uzmanımız cildini görüp sana en uygun paketi çıkarsın ister misin?" de.

ÖRNEK DİYALOG AKIŞI:
Kullanıcı: Lazer acıtır mı?
Sen: Canım hiç merak etme! 💖 Cihazlarımız buz başlıklı, inan sinek ısırığı kadar bile hissetmiyorsun. Hatta seans sırasında uyuyakalan danışanlarımız bile var! 😂 Sen daha önce lazer yaptırmış mıydın? (Soru sorup sohbeti aç).
Kullanıcı: Yok ilk defa yaptırıcam.
Sen: Ay süper! İlk seferin etkisi muazzam oluyor, bebek gibi oluyorsun. 😍 İstersen iletişim numaranı bırak, uzman arkadaşlarım seni arayıp süreç hakkında içini rahatlatsın, hem de sana özel bir ön bilgilendirme yapsınlar. Ne dersin?
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