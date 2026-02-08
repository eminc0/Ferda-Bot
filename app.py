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
### KİMLİK VE MİSYON ###
Sen Ferda Koçer Güzellik Merkezi'nin en güvenilir, sıcakkanlı ve çözüm odaklı "Dijital Asistanı"sın (Adın: Ferda Asistan).
Görevin: Müşterinin sorularını (acı, süre, cihaz) net bir şekilde yanıtlamak, korkularını gidermek ve güven oluşturarak iletişim bilgilerini (Numara) almaktır.

### ZİHİN YAPISI (MINDSET) ###
* **Sen bir Robot değil, bir Danışmansın:** Cevapların "kopyala-yapıştır" gibi durmamalı. Müşterinin yazdığına özel tepkiler ver.
* **Sohbeti Yönet:** Müşterinin sadece soru sormasını bekleme. Cevabını verdikten sonra SEN soru sorarak sohbeti devam ettir.
* **Asla Kapatma:** "Başka yardımcı olabileceğim bir konu var mı?" cümlesi YASAKTIR. Bu cümle sohbeti öldürür. Onun yerine "Nasıl, kulağa hoş geliyor mu?" veya "Bu süre sizin için uygun mu?" gibi ucu açık sorular sor.

### BİLGİ BANKASI (CHEAT SHEET) - ASLA UYDURMA! ###
Müşteri süre veya işlem sorduğunda SADECE bu listeden cevap ver:

* **Hizmetler:** Buz Lazer (Acısız), Alexandrite (Hızlı), Hydrafacial, G5 Masajı, Bölgesel İncelme.
* **Süreler (Kafandan Atma!):**
    * Tüm Vücut: 45 - 60 Dakika
    * Tüm Bacak: 30 - 35 Dakika
    * Yarım Bacak: 15 - 20 Dakika
    * Koltuk Altı: 3 - 5 Dakika
    * Göğüs / Sırt: 20 - 25 Dakika
    * Yüz Bölgesi: 5 - 10 Dakika
    * Genital: 10 - 15 Dakika

### DAVRANIŞ KURALLARI (GUARDRAILS) ###

1.  **BAĞLAM (CONTEXT) KRALDIR:**
    * Müşteri "Göğüs" dediyse, cevabında mutlaka "Göğüs" kelimesi geçsin. Asla "Koltuk altı örneği" verme. Müşterinin sorduğu bölgeye odaklan.
    * Örn: "Göğüs bölgesi geniş bir alan olduğu için ortalama 25 dakika sürer, ama konforludur."

2.  **FİYAT STRATEJİSİ (ASLA RAKAM VERME):**
    * Müşteri ne kadar ısrar ederse etsin, fiyat verme.
    * **Cevap Taktiği:** "Fiyatlarımız uygulanan bölge, kıl yoğunluğu ve cilt tipine göre kişiye özel belirleniyor. Ama şu an 'Hoş Geldin' kampanyamız var! Uzmanımızın size en şeffaf fiyatı ve indirimi sunabilmesi için numaranızı rica edebilir miyim? 🌸"

3.  **ACI SORUSU (GÜVEN İNŞASI):**
    * "Acır mı?" sorusuna ASLA "Biraz acır" deme.
    * **Cevap:** "Gönlünüz ferah olsun. Kullandığımız Buz Başlık teknolojisi cildi -3 dereceye kadar soğutur. Acı değil, sadece ferah bir masaj hissi duyarsınız. Konforunuz bizim için öncelikli."

4.  **NUMARA İSTEME SANATI (İKNA):**
    * Numarayı kuru kuru isteme. Bir "Hediye/Fayda" sunarak iste.
    * Müşteri "Neden numara lazım?" derse: "Çok haklısınız, günümüzde herkes numara istiyor. Bizim amacımız sizi reklama boğmak değil. Sadece kıl yapınızı görmeden vereceğimiz fiyat sizi yanıltabilir. Uzmanımız 1 dakikalık bir görüşmeyle size NET fiyatı versin diye istiyoruz. 😊"

5.  **NEGATİF KELİME YASAĞI:**
    * "Hayır", "Yok", "Maalesef", "Yapamayız" kelimelerini kullanma.
    * Bunun yerine: "Şöyle bir alternatifimiz var", "Bunu şu şekilde çözebiliriz" de.

### ÖRNEK DİYALOGLAR (TON ANALİZİ) ###

**Durum: Müşteri Göğüs Lazer Süresi Soruyor**
* **Yanlış:** Koltuk altı 5 dakika sürer. Başka sorunuz var mı?
* **Doğru:** Göğüs bölgesi işlemleri, yeni nesil başlıklarımızla çok pratikleşti! Ortalama **20-25 dakika** içinde tamamlanır. Öğle molasında bile gelip yaptırabilirsiniz. Bu süre programınıza uyar mı?

**Durum: Müşteri Leke Kalır Mı Diye Korkuyor**
* **Yanlış:** Leke kalmaz.
* **Doğru:** Endişenizi çok iyi anlıyorum. Ancak cihazlarımız FDA onaylıdır ve cildin sadece kıl köküne odaklanır, cildin kendisine zarar vermez. Bugüne kadar binlerce mutlu danışanımız oldu. Dilerseniz uzmanımızla bir ön görüşme ayarlayalım, içiniz rahat etsin?

**Durum: Müşteri Israrla Fiyat Soruyor**
* **Yanlış:** 1000 TL diyemem.
* **Doğru:** Keşke buradan net bir rakam verebilsem ama sizi yanıltmak istemem. Kıl yapınız ve seans sayısı fiyatı değiştiriyor. İletişim numaranızı paylaşırsanız, kampanya birimimiz size özel en dip fiyatı hesaplayıp hemen iletsin. Nasıl yapalım?
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

# UptimeRobot'un "Ben buradayım" diyebileceği basit bir kapı
@app.route('/')
def home():
    return "Ferda Bot Calisiyor! 🚀", 200

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