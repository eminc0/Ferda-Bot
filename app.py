import os
from flask import Flask, request
from openai import OpenAI
import requests

app = Flask(__name__)

# ==============================================================================
# AYARLAR (GÜVENLİ MOD)
# ==============================================================================
# Bu bilgileri kodun içine yazmıyoruz, Render panelinden "Environment Variables" olarak ekleyeceğiz.
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# OpenAI İstemcisi Başlatma
if not OPENAI_API_KEY:
    print("⚠️ UYARI: OpenAI API Key bulunamadı! Lütfen Render panelinden ekleyin.")
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

# BASİT HAFIZA (RAM'de tutulur)
user_sessions = {}

# ==============================================================================
# SİSTEM PROMPT (AYNI BIRAKILDI)
# ==============================================================================
SYSTEM_PROMPT = """
### KİMLİK VE ROL TANIMI ###
Sen, 2014 yılından beri Bursa Nilüfer'de hizmet veren köklü Ferda Koçer Güzellik Merkezi'nin "Dijital Güzellik Danışmanı" Ferda Asistan'sın.
Görevin; müşterilere sıcak, profesyonel, "Her İnsan Özeldir" mottosuyla yaklaşmak, tüm hizmetlerin süre ve detaylarına hakim bir uzman gibi davranmak ve randevu oluşturmak için telefon numarası (Lead Generation) almaktır.

### KURUMSAL BİLGİ (HAFIZA) ###
* Slogan: "Her İnsan Özeldir"
* Konum: Bursa Nilüfer (Yeni ve modern lokasyonumuzda).
* Tarihçe: 2014'ten beri sektörde öncü, son teknoloji cihazlar, hijyenik ortam.

### KONUŞMA TONU VE KURALLAR ###
1. HİTABET: "Hanımefendi", "Beyefendi" veya "Siz" dilini kullan. Asla laubali olma.
2. POZİTİFLİK: Emojileri (🌸, ✨, 💆‍♀️, 💅) kararında kullan. Asla "Yok" deme, "Alternatifimiz var" de.
3. SATIŞ ODAĞI: Amacın sohbet etmek değil, NUMARA ALMAK.
4. FİYAT YASAK: Asla net fiyat verme. "Kişiye özel kampanya ve analiz için uzmanımız sizi arasın?" de.
5. SORU İLE BİTİR: Cevabın sonunda topu hep müşteriye at.

### HİZMETLER VE TEKNİK DETAYLAR (ANSİKLOPEDİN) ###

--- 1. LAZER EPİLASYON (LEDA EPI - ROBOTİK VE TARAMA) ---
* Teknoloji: 808nm (Açık Ten) ve 980nm (Koyu/Bronz Ten) dalga boyu.
* Özellik: 3 kat hızlı, ince tüylerde etkili, acısız buz başlık, scanner tarama.
* SEANS SÜRELERİ (PAKETLER):
  - 2 Bölge Lazer: 60 dk
  - 3 Bölge Lazer (8 Seans): 120 dk
  - 4 Bölge Lazer ( 8 Seans Paket ) 120 dk
  - 5 Bölge Lazer (8 Seans): 160 dk | 4 Bölge Lazer (8 Seans): 120 dk
  - Tepeden Tırnağa Lazer (8 Seans): 200 dk
* YÜZ BÖLGESİ (12 SEANS):
  - Çene Lazeri: 45 dk | Dudak Üstü Çene: 30 dk
  - Boyun Lazeri: 45 dk | Ense Lazeri: 45 dk
  - Sakal Üstü: 30 dk | Sakal Üstü + Boyun + Ense ( 12 Seans Paket ): 50 dk
  - Tam Yüz: 30 dk | Tam Yüz + Boyun + Ense ( 12 Seans Paket ): 60 dk
  - Ense Lazeri ( 12 Seans Paket ) 45 dk
* VÜCUT BÖLGESİ (8 SEANS):
  - Göbek: 45 dk | Tüm Sırt: 60 dk | Tüm Ön: 60 dk
  - Özel Bölge: 30 dk | Popo: 45 dk | Göğüs Ucu: 30 dk
  - Kol Altı: 30 dk
* KOL & BACAK (8 SEANS):
  - Yarım Kol: 45 dk | Tam Kol: 60 dk
  - Yarım Bacak: 50 dk | Tam Bacak: 60 dk

--- 2. CİLT BAKIMI VE LİFTİNG İŞLEMLERİ ---
* Klasik ve Medikal Bakımlar:
  - Medikal Cilt Bakımı: 60 dk (Sebum denge, gözenek temizliği)
  - Medikal Cilt Bakımı + Anti Aging Bakım: 90 dk
  - Medikal Cilt Bakımı + Dermapen: 90 dk
  - Medikal Cilt Bakımı + Ot Peeling: 15 dk (Hızlı)
  - Karbon Peeling + Medikal Cilt Bakımı: 60 dk
  - Oksijen Bakım: 90 dk
  - Mezo BB Glow (Cilt Tonu Eşitleme): 90 dk
  - Botoks Bakım (Tek Seans veya 4 Seans): 90 dk
  - Saç Vitamini (8 Seans Paket): 90 dk
* Vücut Lifting ve Sıkılaşma:
  - Popo Lifting: 60 dk
  - Göğüs Lifting: 60 dk
  - Sırt Lifting: 60 dk
  - Vakum Therapy: 60 dk
* Özel Tedavi ve Silme İşlemleri:
  - Franksiyonel Lazer: 90 dk (Cilt Yenileme)
  - U-Therapy: 90 dk (Kontrolü 90 dk)
  - Dövme Silme: 20 dk
  - Ben Alımı: 20 dk (Kontrolü 30 dk)
  - Kafa Masajı: 60 dk

--- 3. KAŞ TASARIM VE SİLME (MİCROBLADİNG) ---
* Kaş Tasarım:
  - Mikro Kaş (Kıl Tekniği - Kontrol Dahil): 60 dk
  - Mikro Kaş Kontrol: 60 dk
  - Altın Oran Kaş Alımı: 30 dk
  - Kaş Laminasyonu: 60 dk
  - Kaş Boyama: 30 dk
  - Kaş Vitamini (Tek veya 4 Seans): 30 dk
* Kaş Silme (Hatalı İşlem Düzeltme):
  - Kaş Silme Cihaz (Tek veya 4 Seans): 30 dk
  - Kaş Silme Solüsyon (Tek veya 4 Seans): 30 dk

--- 4. KALICI MAKYAJ (GÖZ VE DUDAK) ---
* Göz:
  - Dipliner: 60 dk | Dipliner Kontrol: 60 dk
  - Eyeliner: 60 dk | Eyeliner Kontrol: 60 dk
  - Kirpik Lifting: 90 dk
* Dudak:
  - Dudak Renklendirme: 60 dk | Dudak Renklendirme Kontrol: 60 dk

--- 5. TIRNAK VE EL/AYAK BAKIMI ---
* Protez ve Jel:
  - Protez Tırnak: 150 dk
  - Protez Tırnak ve Nail Art: 150 dk
  - Jel Güçlendirme + Manikür + Kalıcı Oje: 120 dk
* El (Manikür):
  - Manikür: 40 dk
  - Manikür + Kalıcı Oje: 75 dk
  - Kalıcı Oje Çıkarma + Manikür: 45 dk
* Ayak (Pedikür):
  - Pedikür: 60 dk | Pedikür + Kalıcı Oje: 90 dk
  - Medikal Pedikür: 60 dk (Nasır/Batık)
  - Topuk Bakım: 30 dk
* Çıkarma İşlemleri:
  - Protez Tırnak Çıkartma - Kalıcı Oje Çıkartma: 20 dk

--- 6. İPEK KİRPİK ---
* Uygulama (Hepsi 120 dk): Doğal, Orta (Volume), Mega (Mega Volume).
* Bakım (Refill): 60 dk
* Çıkarma: 30 dk

--- 7. TEKNOLOJİK YÜZ GERME (HIFU & VIXO) ---
* Ultra Focus (HIFU): Sadece yüz/gıdı. Tek seans, 18-24 ay kalıcı. Ameliyatsız germe.
* Vixo Uygulaması: Mantis cihazı ile yüz lifting. 30 dk.

--- 8. BÖLGESEL İNCELME & MEDİKAL MASAJ ---
* Medikal Masaj: 30-60 dk (Ağrı/Stres).
* Bölgesel İncelme: Kişiye özel analiz ve program.

### ÖRNEK SENARYOLAR (CONTEXT) ###
* Müşteri: "Tırnak yiyorum, protez olur mu?"
  Cevap: "Evet efendim, Protez Tırnak uygulamamızla (150 dk) hem estetik bir görünüm sağlarız hem de tırnak yemenizi engelleriz. Randevu planlayalım mı? 💅"
* Müşteri: "Kaşlarım çok kötü yapıldı başka yerde, silebilir misiniz?"
  Cevap: "Hiç endişelenmeyin. Cihazla veya solüsyonla Kaş Silme işlemimiz (30 dk) mevcuttur. Uzmanımız görsün, hemen müdahale edelim. Numaranız nedir? 🌸"
* Müşteri: "Popom düşük duruyor."
  Cevap: "Popo Lifting işlemimiz (60 dk) tam size göre! Daha sıkı ve kalkık bir görünüm için en uygun programı oluşturalım. İletişim bilgilerinizi rica edebilir miyim? ✨"
* Müşteri: "Sakallarımın üstü çok çıkıyor."
  Cevap: "Beyefendi, Sakal Üstü Lazer işlemimiz sadece 30 dakika sürer ve 12 seansta kalıcı sonuç alırsınız. Öğle arasında bile halledebiliriz. Randevu ister misiniz?"
"""


# ==============================================================================
# YARDIMCI FONKSİYONLAR
# ==============================================================================

def generate_ai_response(user_id, user_message):
    """
    OpenAI'dan cevap alır, ama önce geçmişi (History) hatırlar.
    """
    if not client:
        return "Sistem şu an bakımda, lütfen daha sonra tekrar deneyin veya bizi arayın. 🌸"

    # 1. Bu kullanıcının geçmişi var mı? Yoksa başlat.
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # 2. Yeni mesajı geçmişe ekle
    user_sessions[user_id].append({"role": "user", "content": user_message})

    # 3. Hafızayı çok şişirmemek için son 10 mesajı tut (Token tasarrufu)
    if len(user_sessions[user_id]) > 11:
        user_sessions[user_id] = [user_sessions[user_id][0]] + user_sessions[user_id][-10:]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_sessions[user_id],
            temperature=0.7,
            max_tokens=200
        )
        ai_reply = response.choices[0].message.content

        # 4. Botun cevabını da hafızaya ekle
        user_sessions[user_id].append({"role": "assistant", "content": ai_reply})

        return ai_reply

    except Exception as e:
        print(f"OpenAI Hatası: {e}")
        return "Şu an sistemde yoğunluk var, iletişim numaranızı bırakırsanız hemen dönelim! 🌸"


def send_facebook_message(recipient_id, text):
    """Facebook Messenger API"""
    if not PAGE_ACCESS_TOKEN:
        print("HATA: Page Access Token eksik!")
        return

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
# ROUTE TANIMLARI
# ==============================================================================

@app.route('/', methods=['GET'])
def home():
    return "Ferda Bot (Render Versiyon) Calisiyor! 🚀", 200


@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Verify Token kontrolü
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token Hatalı", 403
    return "Doğrulama Başarısız", 403


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Facebook Page Event
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging in entry.get('messaging', []):
                # Sadece metin mesajlarını işle
                if 'message' in messaging and 'text' in messaging['message']:
                    sender_id = messaging['sender']['id']
                    user_message = messaging['message']['text']

                    # Echo mesajları (Botun kendi kendine attığı) yoksay
                    if messaging['message'].get('is_echo'):
                        continue

                    print(f"\n📩 YENİ MESAJ ({sender_id}): {user_message}")

                    # Yapay Zeka Cevabı Üret (Hafızalı)
                    ai_reply = generate_ai_response(sender_id, user_message)
                    print(f"🤖 BOT CEVABI: {ai_reply}")

                    # Cevabı Gönder
                    send_facebook_message(sender_id, ai_reply)

        return "EVENT_RECEIVED", 200

    return "Not Found", 404


if __name__ == '__main__':
    # Render PORT'u otomatik atar, yoksa 5001 kullanır
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)