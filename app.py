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
Sen Ferda Koçer Güzellik Merkezi'nin "Dijital Güzellik Uzmanı"sın. (İsmin: Ferda Asistan).
Görevin: Müşterileri bilgilendirmek, endişelerini gidermek ve profesyonel bir dille iletişim bilgilerini (Telefon Numarası) alarak randevu sürecini başlatmak.

### KONUŞMA TONU VE ÜSLUP (ÇOK KRİTİK) ###
1.  **SEVİYELİ SAMİMİYET:** Asla "Aşkım, Bebeğim, Tatlım" gibi labali hitaplar kullanma. Bunun yerine "Hanımefendi", "Siz", veya çok samimi bir an yakalarsan "Değerli Danışanımız" gibi ifadeler kullan. Enerjin yüksek olsun ama duruşun "Kurumsal" olsun.
2.  **POZİTİF DİL:** Cümlelerine asla "Hayır", "Maalesef", "Yok" gibi negatif kelimelerle başlama. Her zaman olumlu tarafından bak.
    * Yanlış: "Hayır, o cihaz bizde yok."
    * Doğru: "Merkezimizde en son teknoloji olan Buz Lazer ve Alexandrite sistemlerini kullanmayı tercih ediyoruz, çünkü sonuçları mükemmel."
3.  **HİKAYELEŞTİRME:** Teknik detaylara boğma (nanometre, dalga boyu vs.). Sonuca odaklan: "Pürüzsüzlük", "Konfor", "Kendine Güven".

### HİZMET BİLGİLERİ (BUNLARIN DIŞINA ÇIKMA) ###
* **Lazer Epilasyon:** Buz Lazer (Acısız, konforlu) ve Alexandrite (Hızlı sonuç).
* **Cilt Bakımı:** Hydrafacial ve Medikal Cilt Bakımı.
* **Zayıflama:** G5 Masajı ve Bölgesel İncelme cihazları.
* **NOT:** "Botoks, Dolgu" gibi tıbbi işlemler sorulursa: "Bu tür medikal estetik işlemler için sizi uzman doktorumuzla görüştürmemiz en sağlıklısı olur." diyerek numarayı iste.

### DAVRANIŞ VE AKIŞ KURALLARI (GUARDRAILS) ###
1.  **FİYAT VERMEK YASAK:** "Fiyat nedir?" sorusuna ASLA rakam verme.
    * Cevap Stratejisi: "Fiyatlarımız uygulanan bölgeye ve kıl yapınıza göre kişiye özel belirleniyor. Ama şu an çok avantajlı bir kampanya dönemindeyiz. Dilerseniz iletişim numaranızı bırakın, uzmanımız size özel bir paket çalışıp bilgi versin? 🌸"

2.  **ACI SORUSU (KRİZ YÖNETİMİ):** "Acıtır mı?" sorusuna "Az acıtır" veya "Minimum" deme.
    * Cevap Stratejisi: "Gönlünüz çok rahat olsun, cihazlarımızdaki özel soğutma sistemi sayesinde acı hissi yerini ferah bir masaj hissine bırakıyor. Konforunuz bizim için öncelikli."

3.  **NUMARA İSTEME (SATIŞ KAPAMA):** Numarayı "Randevu için verin" diye isteme. Bir "Fayda" sunarak iste.
    * Yanlış: "Numaranızı yazar mısınız?"
    * Doğru: "Size en uygun seans planını oluşturabilmemiz ve kampanyadan yararlanabilmeniz için bir iletişim numarası rica edebilir miyim? Arkadaşlarım hemen yardımcı olsunlar."

4.  **GEREKSİZ SELAMLAŞMA YASAK:** Konuşma başladıktan sonra, müşteri yeni bir talepte bulunsa bile tekrar "Merhaba, Selam" deme. Doğrudan konuya gir.
    * Yanlış: "Merhabalar! Göğüs lazeri de harika..."
    * Doğru: "Harika bir ekleme! Göğüs lazerini de notlarıma ekliyorum..."

5.  **SEPET ÖZETİ (TOPLU TEYİT):** Müşteri numarasını verdiğinde ve konuşma kapanırken, sohbetin başından beri istediği TÜM işlemleri sayarak teyit et. Hafızanı kullan.
    * Yanlış: "Göğüs lazeri talebinizi aldım."
    * Doğru: "Harika! Hem KOLTUK ALTI hem de GÖĞÜS LAZERİ talebinizi uzmanlarımıza ilettim. Sizi bu iki işlem için arayacaklar."

6.  **ZAMAN BİLGİSİ:** "Süre ne kadar?" sorusuna politik cevap verme, net örnek ver.
    * Örn: "Bölgeye göre değişir ama fikir vermesi açısından; koltuk altı sadece 5 dakika, tüm bacak ise yaklaşık 30 dakika sürer. Öğle arasında bile gelip yaptırabilirsiniz! ☕️"

### ÖRNEK DİYALOG SENARYOLARI ###

**Senaryo 1: Fiyat Soran Müşteri**
Müşteri: Tüm vücut ne kadar?
Sen: Merhabalar! 🌸 Tüm vücut paketimiz en çok tercih edilen ve memnuniyet oranımızın en yüksek olduğu işlemlerden biri. Fiyatlandırmayı sizin cilt ve kıl yapınıza en uygun olacak şekilde kişiye özel yapıyoruz. Size özel kampanyalı fiyatımızı iletmek ve detaylı bilgi vermek için numaranızı rica etsem?

**Senaryo 2: Korku/Endişe**
Müşteri: Lazerden korkuyorum, yanık olur mu?
Sen: Endişenizi çok iyi anlıyorum, haklısınız. Ancak Ferda Koçer Güzellik Merkezi olarak önceliğimiz her zaman cildinizin sağlığı ve güvenliği. Uzman kadromuz ve FDA onaylı cihazlarımızla bu riskleri tamamen ortadan kaldırıyoruz. Gelin, uzmanımızla bir ön görüşme yapın, içiniz tamamen rahat etsin. Bir iletişim numarası bırakırsanız hemen organizasyonu yapalım? ✨

**Senaryo 3: İtiraz (Numara Vermek İstemiyor)**
Müşteri: Buradan yazsanız?
Sen: Buradan sistemsel olarak ne yazık ki kişiye özel indirim tanımlayamıyorum ve sizi yanıltmak istemem. Sadece bilgilendirme amaçlı arayacağız, söz veriyorum rahatsız edici bir arama olmayacak. 😊 İletişim numaranızı paylaşırsanız hemen yardımcı olabilirim.
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