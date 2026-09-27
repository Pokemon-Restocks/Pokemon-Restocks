import os
import time
import threading
import requests
import urllib.parse
from flask import Flask

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# 1. Hier trägst du alle Produkte ein, die überwacht werden sollen
PRODUCTS_TO_CHECK = [
    {
        "id": "1072938817",
        "title": "30 Jahre Tin #1 Tag DE",
        "image_url": "https://assets.pokemon.com/assets/cms2/img/trading-card-game/_tiered_cards/tcg_wild_force_booster_pack_en.png"
    },
    {
        "id": "1072938818", # Beispiel für ein 2. Produkt
        "title": "30 Jahre Poster-Kollektion DE",
        "image_url": "https://assets.pokemon.com/assets/cms2/img/trading-card-game/_tiered_cards/tcg_wild_force_booster_pack_en.png"
    }
]

# 2. Hier trägst du alle Filialen ein (Name, exakte Adresse, Land & PLZ-ID)
STORES_TO_CHECK = [
    {
        "id": "86153", 
        "name": "Toysino Augsburg - City Galerie", 
        "address": "Willy-Brandt-Platz 1, 86153 Augsburg", 
        "country": "DE"
    },
    {
        "id": "8700", 
        "name": "Thalia Leoben - LCS (AT)", 
        "address": "Hauptplatz 19, 8700 Leoben, AT", 
        "country": "AT"
    }
]

CHECK_INTERVAL = 120
# Speichert benachrichtigte Kombinationen aus Produkt + Store (z.B. "1072938817_86153")
notified_items = set()

def send_discord_alert(product_title, store_name, status, address, country, image_url):
    if not DISCORD_WEBHOOK_URL:
        print("Kein Webhook konfiguriert!")
        return

    # Passende Flagge je nach Land (DE oder AT)
    flag_url = "https://flagcdn.com/w80/de.png" if country.upper() == "DE" else "https://flagcdn.com/w80/at.png"
    
    # Exakter Google Maps Link für die genaue Adresse
    encoded_address = urllib.parse.quote(address)
    maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"

    embed = {
        "username": "Thalia Instore Restock",
        "avatar_url": "https://i.imgur.com/4M34hi2.png",
        "embeds": [{
            "title": product_title,              # Dynamischer Produkttitel
            "color": 15844367,
            "thumbnail": {
                "url": image_url                  # Dynamisches Produktbild oben rechts
            },
            "fields": [
                {"name": "Store", "value": store_name, "inline": True},    # Dynamischer Store Name
                {"name": "Stock", "value": status, "inline": True},
                {"name": "Address", "value": address, "inline": False},   # Dynamische Adresse
                {"name": "Links", "value": f"[Google Maps]({maps_url})", "inline": False}
            ],
            "image": {
                "url": flag_url                   # Dynamische Flagge unten
            },
            "footer": {
                "text": "TCG Alerts • Instant Restock Pings",
                "icon_url": "https://i.imgur.com/4M34hi2.png"
            }
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=embed)

def check_stock():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Schleife durch alle Produkte und alle Filialen
    for product in PRODUCTS_TO_CHECK:
        url = f"https://www.thalia.de/shop/home/artikeldetails/{product['id']}/filialverfuegbarkeit"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            is_available = response.status_code == 200 and "verfügbar" in response.text.lower()

            for store in STORES_TO_CHECK:
                item_key = f"{product['id']}_{store['id']}"

                if is_available and item_key not in notified_items:
                    send_discord_alert(
                        product_title=product["title"],
                        store_name=store["name"],
                        status="Verfügbar",
                        address=store["address"],
                        country=store["country"],
                        image_url=product["image_url"]
                    )
                    notified_items.add(item_key)
                elif not is_available and item_key in notified_items:
                    notified_items.remove(item_key)

        except Exception as e:
            print(f"Fehler bei Produkt {product['id']}: {e}")

app = Flask('')

@app.route('/')
def home():
    return "Bot läuft!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    print("Bot gestartet...")
    while True:
        check_stock()
        time.sleep(CHECK_INTERVAL)
