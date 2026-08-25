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
    """
    Herkent bijvoorbeeld:
    €419,00
    419,00
    € 419.95
    """

    if not text:
        return None

    match = re.search(
        r"€\s*([0-9][0-9\.,]*)",
        text
    )

    if not match:
        return None

    value = match.group(1)

    # Nederlandse prijsnotatie.
    value = value.replace(".", "").replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


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
