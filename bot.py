import os
import time
import threading
import requests
from flask import Flask

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

PRODUCT_ID = "1072938817"

STORES_TO_CHECK = [
    {"name": "Toysino Augsburg - City Galerie", "id": "86153"},
    {"name": "Thalia Leoben - LCS", "id": "8700"}
]

CHECK_INTERVAL = 120
notified_stores = set()

def check_stock():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for store in STORES_TO_CHECK:
        url = f"https://www.thalia.de/shop/home/artikeldetails/{PRODUCT_ID}/filialverfuegbarkeit"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            is_available = response.status_code == 200 and "verfügbar" in response.text.lower()

            if is_available and store["id"] not in notified_stores:
                send_discord_alert(store["name"], "Verfügbar", store["id"])
                notified_stores.add(store["id"])
            elif not is_available and store["id"] in notified_stores:
                notified_stores.remove(store["id"])
        except Exception as e:
            print(f"Fehler: {e}")

def send_discord_alert(store_name, status, store_id):
    if not DISCORD_WEBHOOK_URL:
        print("Kein Webhook konfiguriert!")
        return

    embed = {
        "username": "Thalia Instore Restock",
        "embeds": [{
            "title": "30 Jahre Pokémon Kollektion DE",
            "color": 3066993,
            "fields": [
                {"name": "Store", "value": store_name, "inline": True},
                {"name": "Stock", "value": status, "inline": True},
                {"name": "PLZ / Adresse", "value": store_id, "inline": False}
            ],
            "footer": {"text": "TCG Alerts • Instant Restock Pings"}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=embed)

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
