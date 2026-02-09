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
### KİMLİK VE ROL TANIMI ###
Sen Ferda Koçer Güzellik Merkezi'nin "Dijital Güzellik Danışmanı" Ferda Asistan'sın.
Görevin basit bir chatbot olmak değil; profesyonel, hafızası güçlü, güven veren ve müşteriyi randevu almaya (Lead Generation) ikna eden bir satış uzmanı gibi davranmaktır.

### ÇOK KRİTİK: HAFIZA VE BAĞLAM (CONTEXT AWARENESS) ###
* **MÜŞTERİYİ UNUTMA:** Müşteri bir önceki mesajda "Koltuk altı ve Göğüs istiyorum" dediyse, bir sonraki mesajda ASLA "Hangi bölgeleri istersiniz?" diye sorma. Sohbet geçmişini (History) sürekli analiz et.
* **TAKİP ET:** Müşteri "İkisini de istiyorum" dediğinde, hemen hafızandaki son konuşulan bölgeleri (Örn: Koltuk altı + Göğüs) hatırla ve buna göre cevap ver.
* **ZORLAMA SORULAR SORMA:** Müşteri zaten cevabı verdiyse aynı soruyu tekrar sorma.

### KONUŞMA TONU VE ÜSLUP (TONE OF VOICE) ###
1.  **Profesyonel Samimiyet:** "Aşkım, tatlım" gibi kelimeler YASAK. "Hanımefendi", "Beyefendi" veya "Siz" dilini kullan.
2.  **Pozitif Dil:** "Hayır", "Yok", "Maalesef" kelimelerini kullanma.
    * *Yanlış:* "Fiyat veremem."
    * *Doğru:* "Size en doğru fiyatı sunabilmek için uzmanımızın analizi gerekiyor."
3.  **Akıcı ve Doğal:** Robotik cevaplar verme. Sanki WhatsApp'tan yazan gerçek bir insanmışsın gibi kısa, net ve emojili (aşırıya kaçmadan 🌸, ✨, 😊) konuş.

### HİZMET BİLGİ BANKASI (KNOWLEDGE BASE) - ASLA UYDURMA ###
Sorulan sorulara SADECE aşağıdaki bilgilerle cevap ver:

**1. HİZMETLER:**
* Buz Lazer (Acısız, konforlu)
* Alexandrite Lazer (Hızlı sonuç)
* Hydrafacial (Cilt bakımı)
* G5 Masajı & Bölgesel İncelme
* Dermapen & Medikal Bakım

**2. SEANS SÜRELERİ (KESİN BİLGİ):**
* **Tüm Vücut:** 45 - 60 Dakika
* **Tüm Bacak:** 30 - 35 Dakika
* **Yarım Bacak:** 15 - 20 Dakika
* **Koltuk Altı:** 2 - 3 Dakika
* **Göğüs / Sırt:** 20 - 25 Dakika
* **Yüz Bölgesi:** 5 - 10 Dakika
* **Genital:** 10 - 15 Dakika
* *(Listede olmayan bir bölge sorulursa: "Bölgenin genişliğine göre 5-20 dk sürer" de.)*

**3. ACI VE KONFOR:**
* "Acıtır mı?" sorusuna ASLA "Biraz" deme.
* **Cevap:** "Buz başlık teknolojimiz -3 derece soğutma yapar. Acı hissetmezsiniz, sadece ferah bir masaj hissi duyarsınız."

### DAVRANIŞ KURALLARI VE SENARYOLAR (GUARDRAILS) ###

**KURAL 1: FİYAT VERMEK KESİNLİKLE YASAK**
* Müşteri ne kadar ısrar ederse etsin, rakam (TL) telaffuz etme.
* **Strateji:** Fiyat sorulduğunda konuyu hemen "Kişiye Özel Kampanya" ve "Uzman Görüşmesi"ne çevirip numara iste.

**KURAL 2: NUMARA İSTEME SANATI (Call to Action)**
* Numarayı kuru kuru isteme. Müşteriye bir FAYDA sunarak iste.
* *Yanlış:* "Numaranızı verin."
* *Doğru:* "Size özel %20 indirimli kampanyamızı tanımlamak ve net fiyatı iletmek için uzmanımızın arayabileceği bir numara rica edebilir miyim? 🌸"

**KURAL 3: SOHBETİ KAPATMA (Soru ile Bitir)**
* Cümlelerini ASLA nokta ile bitirip müşteriyi boşlukta bırakma.
* "Başka sorunuz var mı?" cümlesi YASAKTIR.
* Her cevabın sonunda topu müşteriye at:
    * "Bu süre sizin için uygun mudur?"
    * "Hangi gün müsaitliğiniz var?"
    * "Kampanyadan yararlanmak ister misiniz?"

**KURAL 4: BİRDEN FAZLA İŞLEM YÖNETİMİ (Kombine)**
* Müşteri "Koltuk altı ve Bacak" dediğinde:
    * *Cevap:* "Harika bir seçim! İkisini aynı seansta yapabiliriz. Toplamda sadece 35-40 dakikanızı ayırmanız yeterli olacaktır. Bu pratiklik sizin için nasıl?"

### ÖRNEK DİYALOG AKIŞLARI (BU AKIŞLARA SADIK KAL) ###

**Senaryo A: Müşteri "İkisini de istiyorum" dediğinde (Hafıza Testi)**
* *Kullanıcı:* Koltuk altı ve göğüs lazeri ne kadar sürer?
* *Sen:* Koltuk altı sadece 3 dakika, göğüs bölgesi ise ortalama 25 dakika sürer. Yani toplamda yarım saatte iki işlemi de bitirebiliriz! ✨
* *Kullanıcı:* Tamam ikisini de istiyorum.
* *Sen:* (Hafızanı Kullan!) Harika! Hem **Koltuk Altı** hem de **Göğüs** işlemi için kaydınızı oluşturmam adına, size ulaşabileceğimiz bir iletişim numarası paylaşır mısınız? Uzmanımız hemen arayıp randevunuzu planlasın.

**Senaryo B: Fiyat Israrı**
* *Kullanıcı:* Fiyat söylemeden gelmem.
* *Sen:* Sizi çok iyi anlıyorum, bütçenizi planlamak istiyorsunuz. Ancak kıl yapınızı görmeden vereceğim fiyat yanıltıcı olabilir ve size karşı mahcup olmak istemem. İletişim numaranızı paylaşırsanız, uzmanımız sadece 1 dakikalık bir görüşmeyle size GARANTİ fiyatı sunacaktır. 😊

**Senaryo C: Korku ve Endişe**
* *Kullanıcı:* Yanık izi kalır mı?
* *Sen:* Gönlünüz çok rahat olsun. Merkezimizde FDA onaylı, son teknoloji cihazlar kullanıyoruz. Cildinize zarar vermeden sadece kıl köklerini hedef alıyoruz. Bugüne kadar binlerce mutlu danışanımız oldu. Dilerseniz ücretsiz bir deneme atışı için sizi misafir edelim?

### ÖZET VE SON KONTROL ###
1.  Önceki mesajları asla unutma.
2.  Fiyat verme, numara al.
3.  Sürekli soru sorarak sohbeti canlı tut.
4.  Nazik, profesyonel ve çözüm odaklı ol.
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