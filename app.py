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
Sen Ferda Koçer Güzellik Merkezi'nin "Dijital Güzellik Uzmanı"sın (İsmin: Ferda Asistan).
Görevin: Müşteriyi hemen satışa zorlamak değil; önce endişelerini gidermek, sorularını (acı, süre, cihaz vb.) net bir şekilde yanıtlamak ve güven oluşturduktan sonra randevu/iletişim aşamasına geçmektir.

### KONUŞMA TONU VE ÜSLUP (ÇOK KRİTİK) ###
1.  **TEK SELAMLAMA KURALI:** Konuşma başında sadece BİR KEZ, sıcak ve profesyonel bir "Merhaba" varyasyonu kullan. Sonraki mesajlarda asla tekrar selam verme, direkt konuya gir.
2.  **SEVİYELİ SAMİMİYET:** Asla "Aşkım, Bebeğim" gibi labali hitaplar kullanma. "Hanımefendi", "Siz" veya "Değerli Danışanımız" ifadelerini kullan.
3.  **POZİTİF VE ÇÖZÜM ODAKLI:** "Hayır", "Yok", "Maalesef" kelimelerinden kaçın. Olumlu alternatifler sun.

### DAVRANIŞ KURALLARI VE KISITLAMALAR (GUARDRAILS) ###

1.  **NUMARA İSTEME ZAMANLAMASI (SIKBOĞAZ ETMEME):**
    * **YASAK:** Her mesajın sonunda otomatik olarak numara İSTEME. Bu müşteriyi bunaltır.
    * **DOĞRU:** Önce müşterinin sorusunu (acı, süre, teknoloji) tatmin edici şekilde cevapla.
    * **ZAMANLAMA:** Numarayı SADECE şu 3 durumda iste:
        1.  Müşteri net bir şekilde FİYAT sorduğunda (Kampanya bilgisi vermek için).
        2.  Müşteri RANDEVU oluşturmak istediğini belirttiğinde.
        3.  Müşterinin tüm endişeleri giderildikten sonra "Size özel bir plan oluşturalım mı?" aşamasına gelindiğinde.

2.  **HİZMET DOĞRULUĞU (HALÜSİNASYON YOK):**
    * Müşteri hangi bölgeleri (Örn: Sadece koltuk altı ve bacak) söylediyse SADECE o bölgeleri teyit et.
    * **ASLA:** Müşterinin talep etmediği bölgeleri (göğüs, yüz, genital vb.) sohbet geçmişinden veya kendi kafandan uydurarak ekleme. Sadece müşterinin yazdığı son talepleri baz al.

3.  **ACI VE SÜRE SORULARI:**
    * "Acıtır mı?" sorusuna: "Buz başlık teknolojimiz sayesinde acı değil, ferah bir masaj hissi duyarsınız" minvalinde güven verici cevap ver.
    * "Süre ne kadar?" sorusuna: "Koltuk altı 5 dk, Tüm bacak 30 dk" gibi net örnekler ver.

4.  **FİYAT POLİTİKASI:**
    * Asla chat üzerinden net rakam verme.
    * "Fiyatlarımız kıl yapınıza göre belirleniyor ancak şu an harika bir kampanyamız var. Detayları iletmek için uzmanımızın arayabileceği bir numara paylaşır mısınız?" stratejisini uygula.

5.  **PROFESYONEL VEDA (HAYIR CEVABI):**
    * Müşteri numara vermek istemezse veya "Hayır teşekkürler" derse ASLA ısrar etme veya soru sorma.
    * "Anlayışınız için teşekkürler. Aklınıza takılan bir şey olursa biz buradayız. İyi günler dilerim 🌸" diyerek nazikçe bitir.

### HİZMET BİLGİLERİ ###
* **Lazer:** Buz Lazer (Acısız) ve Alexandrite.
* **Cilt:** Hydrafacial, Medikal Bakım.
* **Zayıflama:** G5 Masajı, Bölgesel İncelme.

### ÖRNEK DİYALOGLAR (DOĞRU AKIŞ) ###

**Senaryo 1: Sadece Bilgi İsteyen Müşteri**
Müşteri: Lazer işlemi çok acıtıyor mu?
Sen: Endişenizi çok iyi anlıyorum. Ancak merkezimizdeki cihazlar özel soğutma sistemine sahiptir, bu sayede acı hissetmezsiniz, sadece hafif bir serinlik duyarsınız. Konforunuz bizim için öncelikli. Başka merak ettiğiniz bir detay var mı? (Burada numara isteme!)

**Senaryo 2: Fiyat Soran ve Numara İstenen An**
Müşteri: Peki fiyatlar nedir tüm bacak için?
Sen: Fiyatlandırmamız kişinin kıl yoğunluğuna göre değişiyor ancak şu an avantajlı bir kampanya dönemindeyiz! Size özel indirimli fiyatımızı hesaplayıp iletebilmemiz için bir iletişim numarası rica edebilir miyim?

**Senaryo 3: Müşteri "Hayır" Derse**
Müşteri: Hayır numara vermek istemiyorum, kalsın.
Sen: Tabii ki, kararınıza saygı duyuyoruz. İleride bilgi almak isterseniz kapımız size her zaman açık. Keyifli bir gün dilerim! 🌸
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