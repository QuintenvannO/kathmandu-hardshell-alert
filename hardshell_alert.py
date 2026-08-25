import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# INSTELLINGEN
# ============================================================

BASE_URL = "https://www.kathmandu.nl"

# Modellen die we willen volgen.
# De zoektermen worden gebruikt om Kathmandu-pagina's te vinden.
MODELS = {
    "Rab Latok Alpine": [
        "Rab Latok Alpine GTX Jacket",
        "RAB Latok Alpine GTX Jacket",
    ],
    "Rab Latok Mountain": [
        "Rab Latok Mountain GTX Jacket",
        "RAB Latok Mountain GTX Jacket",
    ],
    "Patagonia Triolet": [
        "Patagonia Triolet Jacket",
        "Patagonia Triolet",
    ],
}

# Jij wilt maat M en L, ongeacht kleur.
SIZES = {"M", "L"}

# Meldingen:
# - Iedere aanbieding onder deze prijs -> melding
# - Daarnaast melding bij grote prijsdaling.
MAX_PRICE = 400.00
MIN_PRICE_DROP_PERCENT = 10.0

# Alleen herenproducten.
REQUIRE_MEN = True

# Bestand waarin vorige prijzen/voorraad worden opgeslagen.
STATE_FILE = Path("state.json")

# Kathmandu niet onnodig hard belasten.
REQUEST_DELAY = 2


# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def telegram_message(text):
    """Stuur een bericht naar Telegram."""

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram secrets ontbreken; melding wordt alleen gelogd.")
        print(text)
        return

    url = (
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )

    response.raise_for_status()


# ============================================================
# HTTP
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}


session = requests.Session()
session.headers.update(HEADERS)


def get_page(url):
    """Download een Kathmandu-pagina."""

    print(f"GET {url}")

    response = session.get(url, timeout=30)
    response.raise_for_status()

    time.sleep(REQUEST_DELAY)

    return response.text


# ============================================================
# HULPFUNCTIES
# ============================================================

def normalize_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_url(url):
    if not url:
        return None

    return urljoin(BASE_URL, url)


def parse_price(text):

    if not text:
        return None

    text = text.strip()

    match = re.search(
        r'(\d{1,4}(?:[.,]\d{2}))',
        text
    )

    if not match:
        return None

    value = match.group(1)

    value = value.replace(",", ".")

    return float(value)
    
def find_sizes(text):
    """
    Zoek naar expliciete maatvermeldingen.
    """

    found = set()

    for size in ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]:
        pattern = rf"(?<![A-Za-z]){re.escape(size)}(?![A-Za-z])"

        if re.search(pattern, text, flags=re.I):
            found.add(size.upper())

    return found


# ============================================================
# PRODUCTEN VINDEN
# ============================================================

def search_kathmandu_products():
    """
    Vaste Kathmandu-productpagina's controleren.
    Elke kleurvariant heeft een eigen URL.
    """

    return [

        {
            "model": "Rab Latok Alpine GTX",
            "url": "https://www.kathmandu.nl/rab-latok-alpine-gtx-jacket-qwi-39-dpl-026735"
        },

        {
            "model": "Rab Latok Mountain GTX",
            "url": "https://www.kathmandu.nl/rab-latok-mountain-gtx-jacket-qwh-24-asa-029095"
        },

        {
            "model": "Patagonia Triolet - Cascade Green",
            "url": "https://www.kathmandu.nl/patagonia-triolet-jkt-83403-casg-026684"
        },

        {
            "model": "Patagonia Triolet - Black",
            "url": "https://www.kathmandu.nl/patagonia-triolet-jacket-83403-blk-021464"
        },

        {
            "model": "Rab Kangri GTX - TMB",
            "url": "https://www.kathmandu.nl/rab-kangri-gtx-jacket-qwi-48-tmb-028204"
        },

        {
            "model": "Rab Kangri GTX - Black",
            "url": "https://www.kathmandu.nl/rab-kangri-gtx-jacket-qwi-48-blk-026739"
        },

        {
            "model": "Rab Latok GTX",
            "url": "https://www.kathmandu.nl/rab-latok-gtx-jacket-qwi-38-tmb-026734"
        },

    ]
def get_color_from_url(url):

    colors = {
        "blk": "Black",
        "tmb": "Tempest Blue",
        "dpl": "Deep Lake",
        "asa": "Anthracite",
        "casg": "Cascade Green",
    }

    for code, name in colors.items():
        if f"-{code}-" in url:
            return name

    return None
    
def parse_product(model, url):

    html = get_page(url)

    soup = BeautifulSoup(html, "html.parser")

    text = normalize_text(
        soup.get_text(" ", strip=True)
    )

    title = None

    if soup.title:
        title = normalize_text(
            soup.title.get_text()
        )

    price = None

    price_candidates = soup.select(
    '#jq-productpagina-prijs .amount'
)

  
    for element in price_candidates:

        candidate = normalize_text(
            element.get_text(" ", strip=True)
        )

        parsed = parse_price(candidate)

        if parsed is not None:
            price = parsed
            break

    if price is None:
        price = parse_price(text)


    color = model.split(" - ")[-1] if " - " in model else None

    color_patterns = [
        r"kleur\s*:?\s*([A-Za-zÀ-ÿ0-9 /&\-]+)",
        r"color\s*:?\s*([A-Za-zÀ-ÿ0-9 /&\-]+)",
    ]

    for pattern in color_patterns:

        match = re.search(
            pattern,
            text,
            flags=re.I
        )

        if match:
            color = normalize_text(
                match.group(1)
            )
            break


    sizes = find_sizes(text)


    unavailable_words = [
        "uitverkocht",
        "niet beschikbaar",
        "out of stock",
        "sold out",
    ]

    lower_text = text.lower()

    online_unavailable = any(
        word in lower_text
        for word in unavailable_words
    )


    return {
        "model": model,
        "url": url,
        "title": title,
        "price": price,
        "color": color,
        "sizes": sorted(sizes),
        "online_unavailable": online_unavailable,
    }

# ============================================================
# STATE
# ============================================================

def load_state():
    
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return {}      
        
def save_state(state):

    STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )


# ============================================================
# ALERT LOGICA
# ============================================================

def product_key(product):
    return product["url"]


def should_alert(product, old):

    price = product["price"]

    if price is None:
        return False, None

    # Geen melding als product boven €400 staat,
    # tenzij de prijs significant is gedaald.
    under_limit = price <= MAX_PRICE

    price_drop = False
    drop_percent = 0

    if old and old.get("price"):

        old_price = old["price"]

        if old_price > price:

            drop_percent = (
                (old_price - price)
                / old_price
                * 100
            )

            if drop_percent >= MIN_PRICE_DROP_PERCENT:
                price_drop = True

    # Maat M/L gevonden.
    available_sizes = (
        set(product["sizes"])
        & SIZES
    )

    has_target_size = bool(
        available_sizes
    )

    if under_limit and has_target_size:
        return True, "PRICE"

    if price_drop and has_target_size:
        return True, "DROP"

    return False, None


def format_alert(product, alert_type, old):

    model = product["model"]
    color = product["color"] or "kleur onbekend"
    price = product["price"]

    available_sizes = sorted(
        set(product["sizes"]) & SIZES
    )

    if alert_type == "PRICE":
        headline = "🔥 HARDSHELL DEAL"

    else:
        headline = "📉 HARDSHELL PRIJS GEDAALD"

    old_price_text = ""

    if old and old.get("price"):

        old_price = old["price"]

        if old_price > price:

            old_price_text = (
                f"\nWas: €{old_price:.2f}"
            )

    return (
        f"{headline}\n\n"
        f"{model}\n"
        f"Kleur: {color}\n"
        f"Maat: {', '.join(available_sizes)}\n\n"
        f"€{price:.2f}"
        f"{old_price_text}\n\n"
        f"{product['url']}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("===================================")
    print("Kathmandu Hardshell Price Monitor")
    print("===================================")

    state = load_state()

    if not isinstance(state, dict):
        state = {}

    products = search_kathmandu_products()
 
    print(
        f"{len(products)} productpagina's gevonden."
    )

    current_state = dict(state)

    alerts = []

    for product_ref in products:

        try:

            product = parse_product(
                product_ref["model"],
                product_ref["url"]
            )

            print(
                f"{product['model']} | "
                f"{product['color']} | "
                f"€{product['price']} | "
                f"M/L: {product['sizes']}"
            )

            key = product_key(product)

            old = state.get(key)

            should, alert_type = should_alert(
                product,
                old
            )

            print(
                "DEBUG ALERT:",
                product["model"],
                "OLD:",
                old,
                "NEW:",
                product,
                "SHOULD:",
                should,
                "TYPE:",
                alert_type
            )

            if should:

                alerts.append(
                    format_alert(
                        product,
                        alert_type,
                        old
                    )
                )

            current_state[key] = {
                "model": product["model"],
                "url": product["url"],
                "color": product["color"],
                "price": product["price"],
                "sizes": product["sizes"],
                "checked_at": time.time(),
            }

        except Exception as exc:

            print(
                f"FOUT bij {product_ref['url']}: "
                f"{exc}"
            )

    # --------------------------------------------------------
    # Telegram
    # --------------------------------------------------------

    for alert in alerts:

        try:
            telegram_message(alert)
        except Exception as exc:
            print(
                f"Telegram fout: {exc}"
            )

    # --------------------------------------------------------
    # State opslaan
    # --------------------------------------------------------
    
    save_state(current_state)

    print(
        f"Klaar. {len(alerts)} alerts verstuurd."
    )


if __name__ == "__main__":
    main()
