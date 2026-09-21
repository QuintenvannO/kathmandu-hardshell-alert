import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# INSTELLINGEN
# ============================================================

TARGET_MODEL = "Patagonia Triolet"
TARGET_SIZE = "M"

MAX_TOTAL_PRICE = 380.00
MIN_PRICE_DROP_PERCENT = 10.0

STATE_FILE = Path("state.json")

REQUEST_DELAY = 2

TIMEOUT = 25

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
}


# ============================================================
# PRODUCTPAGINA'S
#
# We gebruiken bewust directe productpagina's.
# Zoekpagina's worden door sommige webshops geblokkeerd.
# ============================================================

PRODUCTS = [

    # --------------------------------------------------------
    # KATHMANDU
    # --------------------------------------------------------

    {
        "store": "Kathmandu",
        "name": "Patagonia Triolet Black",
        "url": (
            "https://www.kathmandu.nl/"
            "patagonia-triolet-jacket-83403-blk-021464"
        ),
        "shipping_mode": "free",
    },

    {
        "store": "Kathmandu",
        "name": "Patagonia Triolet Cascade Green",
        "url": (
            "https://www.kathmandu.nl/"
            "patagonia-triolet-jkt-83403-casg-026684"
        ),
        "shipping_mode": "free",
    },


    # --------------------------------------------------------
    # RONALD ADVENTURE SHOP
    # --------------------------------------------------------

    {
        "store": "Ronald Adventure Shop",
        "name": "Patagonia Triolet Jacket",
        "url": (
            "https://www.ronaldadventureshop.nl/"
            "patagonia-triolet-jacket-veelzijdige-3-laags-"
            "gore-tex-regenjas-voor-heren.html"
        ),
        "shipping_mode": "threshold",
        "free_shipping_from": 50.00,
        "shipping_cost": 5.00,
    },


    # --------------------------------------------------------
    # BEVER
    # --------------------------------------------------------

    {
        "store": "Bever",
        "name": "Patagonia Triolet Mid Green",
        "url": (
            "https://www.bever.nl/"
            "p/patagonia-triolet-hardshell-jas-B12AE90417.html"
            "?colour=2374"
        ),
        "shipping_mode": "free",
    },

    {
        "store": "Bever",
        "name": "Patagonia Triolet Mid Blue",
        "url": (
            "https://www.bever.nl/"
            "p/patagonia-triolet-hardshell-jas-B12AE90417.html"
            "?colour=4168"
        ),
        "shipping_mode": "free",
    },

    {
        "store": "Bever",
        "name": "Patagonia Triolet",
        "url": (
            "https://www.bever.nl/"
            "p/patagonia-triolet-hardshell-jas-B12AE90417.html"
        ),
        "shipping_mode": "free",
    },


    # --------------------------------------------------------
    # ZALANDO
    # --------------------------------------------------------

    {
        "store": "Zalando",
        "name": "Patagonia Triolet Black",
        "url": (
            "https://www.zalando.nl/"
            "patagonia-triolet-outdoorjas-black-pa941f04b-q11.html"
        ),
        "shipping_mode": "free",
    },

    {
        "store": "Zalando",
        "name": "Patagonia Triolet Black",
        "url": (
            "https://www.zalando.nl/"
            "patagonia-triolet-outdoorjas-black-pa942f04w-q11.html"
        ),
        "shipping_mode": "free",
    },


    # --------------------------------------------------------
    # BERGZEIT
    # --------------------------------------------------------

    {
        "store": "Bergzeit",
        "name": "Patagonia Triolet Heren",
        "url": (
            "https://www.bergzeit.nl/"
            "p/patagonia-heren-triolet-jas/1119573/"
        ),
        "shipping_mode": "unknown",
    },


    # --------------------------------------------------------
    # SNOWLEADER
    # --------------------------------------------------------

    {
        "store": "Snowleader",
        "name": "Patagonia Triolet Black",
        "url": (
            "https://www.snowleader.nl/"
            "nl/m-s-triolet-jkt-black.html"
        ),
        "shipping_mode": "unknown",
    },

    {
        "store": "Snowleader",
        "name": "Patagonia Triolet Forge Grey / P6 Blue",
        "url": (
            "https://www.snowleader.nl/"
            "nl/m-s-triolet-jkt-forge-grey-w-p6-blue-PATA04615.html"
        ),
        "shipping_mode": "unknown",
    },

    {
        "store": "Snowleader",
        "name": "Patagonia Triolet Clement Blue",
        "url": (
            "https://www.snowleader.nl/"
            "nl/m-s-triolet-jkt-clement-blue-PATA04957.html"
        ),
        "shipping_mode": "unknown",
    },

    {
        "store": "Snowleader",
        "name": "Patagonia Triolet Caper Green",
        "url": (
            "https://www.snowleader.nl/"
            "nl/m-s-triolet-jkt-caper-green-PATA04958.html"
        ),
        "shipping_mode": "unknown",
    },

    {
        "store": "Snowleader",
        "name": "Patagonia Triolet Touring Red",
        "url": (
            "https://www.snowleader.nl/"
            "nl/m-s-triolet-jkt-touring-red-PATA03711.html"
        ),
        "shipping_mode": "unknown",
    },


    # --------------------------------------------------------
    # EKOSPORT
    # --------------------------------------------------------

    {
        "store": "Ekosport",
        "name": "Patagonia Triolet Amanita Red",
        "url": (
            "https://www.ekosport.nl/"
            "patagonia-m-s-triolet-jacket-p-K104172"
        ),
        "shipping_mode": "unknown",
    },

    {
        "store": "Ekosport",
        "name": "Patagonia Triolet Clement Blue",
        "url": (
            "https://www.ekosport.nl/"
            "patagonia-m-s-triolet-jacket-p-K104173"
        ),
        "shipping_mode": "unknown",
    },

    {
        "store": "Ekosport",
        "name": "Patagonia Triolet Pine Needle Green",
        "url": (
            "https://www.ekosport.nl/"
            "patagonia-m-s-triolet-jacket-p-9-165868"
        ),
        "shipping_mode": "unknown",
    },


    # --------------------------------------------------------
    # BERGFREUNDE
    # --------------------------------------------------------

    {
        "store": "Bergfreunde",
        "name": "Patagonia Triolet Jacket",
        "url": (
            "https://www.bergfreunde.nl/"
            "patagonia-triolet-jacket-regenjas-bf/"
        ),
        "shipping_mode": "free",
    },


    # --------------------------------------------------------
    # BIKE24
    # --------------------------------------------------------

    {
        "store": "Bike24",
        "name": "Patagonia Triolet Heren Forge Grey / P6 Blue",
        "url": (
            "https://www.bike24.nl/"
            "producten/938771"
        ),
        "shipping_mode": "unknown",
    },

]


# ============================================================
# HTTP
# ============================================================

def fetch(url):
    print(f"GET {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    return response.text


# ============================================================
# HULPFUNCTIES
# ============================================================

def clean_text(text):
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()


def normalize_price(value):
    """
    Zet verschillende prijsformaten om naar float.

    Voorbeelden:
    €419,95
    419,95
    € 419.95
    419.95
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    # Valuta verwijderen
    value = re.sub(r"[^\d,.]", "", value)

    if not value:
        return None

    # Nederlands formaat: 419,95
    if "," in value and "." in value:
        # 1.419,95
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "")
            value = value.replace(",", ".")
        else:
            # 1,419.95
            value = value.replace(",", "")

    elif "," in value:
        value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


def is_valid_triolet(text):
    text = clean_text(text).lower()

    return (
        "patagonia" in text
        and "triolet" in text
        and (
            "jacket" in text
            or "jas" in text
            or "jkt" in text
            or "hardshell" in text
            or "outdoor" in text
        )
    )


def is_mens_product(text):
    text = clean_text(text).lower()

    positive = [
        "heren",
        "herenjas",
        "men",
        "men's",
        "mens",
        "m's",
        "herren",
        "homme",
    ]

    negative = [
        "dames",
        "damesjas",
        "women",
        "women's",
        "womens",
        "w's",
        "damen",
        "femme",
    ]

    has_positive = any(x in text for x in positive)
    has_negative = any(x in text for x in negative)

    if has_negative and not has_positive:
        return False

    return has_positive


# ============================================================
# JSON-LD
# ============================================================

def get_json_ld_objects(soup):
    objects = []

    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text()

        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        if isinstance(data, list):
            objects.extend(data)
        else:
            objects.append(data)

    return objects


def extract_json_ld_product(soup):
    products = []

    for obj in get_json_ld_objects(soup):

        if not isinstance(obj, dict):
            continue

        obj_type = obj.get("@type")

        if isinstance(obj_type, list):
            types = obj_type
        else:
            types = [obj_type]

        if "Product" in types:
            products.append(obj)

        graph = obj.get("@graph")

        if isinstance(graph, list):
            for item in graph:
                if (
                    isinstance(item, dict)
                    and item.get("@type") == "Product"
                ):
                    products.append(item)

    return products


def price_from_json_ld(soup):
    products = extract_json_ld_product(soup)

    for product in products:

        offers = product.get("offers")

        if isinstance(offers, dict):
            offers = [offers]

        if not isinstance(offers, list):
            continue

        for offer in offers:

            if not isinstance(offer, dict):
                continue

            price = normalize_price(
                offer.get("price")
            )

            if price is not None and price > 0:
                return price

    return None


# ============================================================
# PRIJS UIT HTML
# ============================================================

PRICE_PATTERNS = [
    r"€\s*([0-9]{1,4}(?:[.,][0-9]{2})?)",
    r"EUR\s*([0-9]{1,4}(?:[.,][0-9]{2})?)",
]


def extract_prices_from_text(text):
    prices = []

    for pattern in PRICE_PATTERNS:
        for match in re.findall(pattern, text, flags=re.I):
            price = normalize_price(match)

            if price is None:
                continue

            # Alleen realistische kledingprijzen
            if 50 <= price <= 2000:
                prices.append(price)

    return prices


def price_from_meta(soup):
    meta_names = [
        "product:price:amount",
        "og:price:amount",
        "price",
    ]

    for name in meta_names:
        tag = soup.find(
            "meta",
            attrs={"property": name},
        )

        if not tag:
            tag = soup.find(
                "meta",
                attrs={"name": name},
            )

        if tag:
            price = normalize_price(
                tag.get("content")
            )

            if price is not None and price > 0:
                return price

    return None


def extract_price(soup):
    # 1. JSON-LD
    price = price_from_json_ld(soup)

    if price is not None:
        return price

    # 2. Meta tags
    price = price_from_meta(soup)

    if price is not None:
        return price

    # 3. Specifieke prijs-elementen
    selectors = [
        "[itemprop='price']",
        "[data-testid*='price']",
        "[class*='price']",
        "[class*='Price']",
        "[class*='prijs']",
        "[class*='Price']",
    ]

    candidates = []

    for selector in selectors:

        try:
            elements = soup.select(selector)
        except Exception:
            continue

        for element in elements:

            text = clean_text(
                element.get_text(" ", strip=True)
            )

            if not text:
                continue

            candidates.extend(
                extract_prices_from_text(text)
            )

            content = element.get("content")

            if content:
                p = normalize_price(content)

                if p is not None:
                    candidates.append(p)

    if candidates:

        # We kiezen de laagste geldige prijs.
        #
        # Dit is belangrijk bij pagina's die bijvoorbeeld
        # zowel "€419,95" als "€251,97" tonen.
        return min(candidates)

    return None


# ============================================================
# MAAT M
# ============================================================

SIZE_WORDS = {
    "XS",
    "S",
    "M",
    "L",
    "XL",
    "XXL",
}


def element_is_disabled(element):
    """
    Controleert of een maatknop/selectie duidelijk
    disabled of uitverkocht is.
    """

    attrs = " ".join(
        [
            str(element.get("class", "")),
            str(element.get("aria-disabled", "")),
            str(element.get("disabled", "")),
            str(element.get("data-disabled", "")),
            str(element.get("data-available", "")),
            str(element.get("data-stock", "")),
        ]
    ).lower()

    disabled_words = [
        "disabled",
        "unavailable",
        "out-of-stock",
        "outofstock",
        "sold-out",
        "soldout",
        "niet beschikbaar",
        "uitverkocht",
    ]

    if "disabled" in element.attrs:
        return True

    return any(
        word in attrs
        for word in disabled_words
    )


def find_size_m(soup, full_text):
    """
    Probeert eerst echte maatselectoren te vinden.

    BELANGRIJK:
    We gebruiken NIET meer simpelweg:
        \\bM\\b

    omdat dat bijvoorbeeld "model draagt maat M"
    als voorraad kan interpreteren.
    """

    # --------------------------------------------------------
    # 1. Buttons
    # --------------------------------------------------------

    for element in soup.find_all("button"):

        text = clean_text(
            element.get_text(" ", strip=True)
        ).upper()

        if text != TARGET_SIZE:
            continue

        if not element_is_disabled(element):
            return True

    # --------------------------------------------------------
    # 2. Links
    # --------------------------------------------------------

    for element in soup.find_all("a"):

        text = clean_text(
            element.get_text(" ", strip=True)
        ).upper()

        if text != TARGET_SIZE:
            continue

        if not element_is_disabled(element):
            return True

    # --------------------------------------------------------
    # 3. Option elementen
    # --------------------------------------------------------

    for element in soup.find_all("option"):

        text = clean_text(
            element.get_text(" ", strip=True)
        ).upper()

        if text != TARGET_SIZE:
            continue

        if not element_is_disabled(element):
            return True

    # --------------------------------------------------------
    # 4. Inputs
    # --------------------------------------------------------

    for element in soup.find_all("input"):

        value = str(
            element.get("value", "")
        ).strip().upper()

        aria = str(
            element.get("aria-label", "")
        ).strip().upper()

        label = str(
            element.get("data-label", "")
        ).strip().upper()

        values = {
            value,
            aria,
            label,
        }

        if TARGET_SIZE in values:

            if not element_is_disabled(element):
                return True

    # --------------------------------------------------------
    # 5. Gestructureerde maatdata in HTML
    # --------------------------------------------------------

    size_patterns = [
        r'data-size=["\']M["\']',
        r'data-value=["\']M["\']',
        r'data-label=["\']M["\']',
        r'data-option=["\']M["\']',
        r'["\']size["\']\s*:\s*["\']M["\']',
        r'["\']value["\']\s*:\s*["\']M["\']',
    ]

    html = str(soup)

    for pattern in size_patterns:

        matches = re.finditer(
            pattern,
            html,
            flags=re.I,
        )

        for match in matches:

            start = max(
                0,
                match.start() - 500,
            )

            end = min(
                len(html),
                match.end() + 500,
            )

            context = html[start:end].lower()

            unavailable = [
                "disabled",
                "unavailable",
                "outofstock",
                "out-of-stock",
                "soldout",
                "sold-out",
                "niet beschikbaar",
                "uitverkocht",
            ]

            if not any(
                word in context
                for word in unavailable
            ):
                return True

    return False


# ============================================================
# BESCHIKBAARHEID
# ============================================================

def detect_out_of_stock(soup, text):
    combined = clean_text(
        text
    ).lower()

    phrases = [
        "uitverkocht",
        "niet beschikbaar",
        "out of stock",
        "sold out",
        "currently unavailable",
        "momenteel niet beschikbaar",
    ]

    # Alleen gebruiken als er ook geen echte M-selector is.
    for phrase in phrases:

        if phrase in combined:
            return True

    return False


# ============================================================
# VERZENDING
# ============================================================

def calculate_shipping(product, price):

    mode = product.get(
        "shipping_mode",
        "unknown",
    )

    if mode == "free":
        return 0.0

    if mode == "threshold":

        threshold = product.get(
            "free_shipping_from"
        )

        shipping_cost = product.get(
            "shipping_cost"
        )

        if (
            threshold is None
            or shipping_cost is None
        ):
            return None

        if price >= threshold:
            return 0.0

        return float(shipping_cost)

    # We gaan GEEN verzendkosten gokken.
    return None


# ============================================================
# PRODUCT PARSEN
# ============================================================

def parse_product(product, html):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    page_text = clean_text(
        soup.get_text(" ", strip=True)
    )

    title = ""

    if soup.title:
        title = clean_text(
            soup.title.get_text()
        )

    # JSON-LD productinformatie
    json_products = extract_json_ld_product(
        soup
    )

    json_name = ""

    for jp in json_products:

        name = jp.get("name")

        if name:
            json_name = clean_text(
                str(name)
            )
            break

    identity_text = " ".join(
        [
            product.get("name", ""),
            title,
            json_name,
            page_text[:5000],
        ]
    )

    is_triolet = is_valid_triolet(
        identity_text
    )

    is_mens = is_mens_product(
        identity_text
    )

    price = extract_price(soup)

    size_m_available = find_size_m(
        soup,
        page_text,
    )

    out_of_stock = detect_out_of_stock(
        soup,
        page_text,
    )

    # Als de pagina expliciet uitverkocht zegt,
    # markeren we M niet als beschikbaar.
    if out_of_stock:
        size_m_available = False

    shipping = calculate_shipping(
        product,
        price,
    )

    if (
        price is not None
        and shipping is not None
    ):
        total_price = round(
            price + shipping,
            2,
        )
    else:
        total_price = None

    return {
        "store": product["store"],
        "name": product["name"],
        "url": product["url"],
        "price": price,
        "shipping": shipping,
        "total_price": total_price,
        "size_m_available": size_m_available,
        "is_triolet": is_triolet,
        "is_mens": is_mens,
        "out_of_stock": out_of_stock,
    }


# ============================================================
# STATE
# ============================================================

def load_state():

    if not STATE_FILE.exists():
        return {}

    try:
        with STATE_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    except Exception as exc:

        print(
            f"WAARSCHUWING: state.json kon niet "
            f"worden gelezen: {exc}"
        )

        return {}


def save_state(state):

    with STATE_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            state,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# ALERT LOGICA
# ============================================================

def should_alert(product, old):

    price = product.get(
        "price"
    )

    total_price = product.get(
        "total_price"
    )

    if price is None:
        return False, None

    if total_price is None:
        return False, None

    if not product.get(
        "size_m_available",
        False,
    ):
        return False, None

    # --------------------------------------------------------
    # Eerste keer gezien
    # --------------------------------------------------------

    if old is None:

        if total_price <= MAX_TOTAL_PRICE:
            return True, "PRICE"

        return False, None

    old_total = old.get(
        "total_price"
    )

    if old_total is None:
        old_total = old.get(
            "price"
        )

    if old_total is None:
        return False, None

    # --------------------------------------------------------
    # Onder de grens gekomen
    # --------------------------------------------------------

    if (
        old_total > MAX_TOTAL_PRICE
        and total_price <= MAX_TOTAL_PRICE
    ):
        return True, "PRICE"

    # --------------------------------------------------------
    # 10%+ prijsdaling
    # --------------------------------------------------------

    if total_price < old_total:

        drop_percent = (
            (old_total - total_price)
            / old_total
            * 100
        )

        if drop_percent >= MIN_PRICE_DROP_PERCENT:
            return True, "DROP"

    return False, None


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    import os

    token = os.environ.get(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.environ.get(
        "TELEGRAM_CHAT_ID"
    )

    if not token or not chat_id:

        print(
            "WAARSCHUWING: Telegram secrets "
            "ontbreken. Geen bericht verzonden."
        )

        return

    url = (
        f"https://api.telegram.org/bot"
        f"{token}/sendMessage"
    )

    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": False,
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=20,
        )

        response.raise_for_status()

        print("Telegram alert verzonden.")

    except Exception as exc:

        print(
            f"FOUT bij Telegram: {exc}"
        )


def format_alert(product, alert_type):

    if alert_type == "DROP":
        title = "📉 PATAGONIA TRIOLET PRIJSVAL"

    else:
        title = "🔥 PATAGONIA TRIOLET DEAL"

    price = product["price"]
    total = product["total_price"]

    message = (
        f"{title}\n\n"
        f"🏪 {product['store']}\n"
        f"🧥 {product['name']}\n"
        f"📏 Maat: M\n"
        f"💰 Productprijs: €{price:.2f}\n"
    )

    shipping = product.get(
        "shipping"
    )

    if shipping is not None:

        message += (
            f"🚚 Verzending: "
            f"€{shipping:.2f}\n"
        )

    message += (
        f"💶 Totaal: €{total:.2f}\n"
        f"🎯 Jouw grens: "
        f"€{MAX_TOTAL_PRICE:.2f}\n\n"
        f"🔗 {product['url']}"
    )

    return message


# ============================================================
# HOOFDPROGRAMMA
# ============================================================

def main():

    print()
    print("=" * 42)
    print("PATAGONIA TRIOLET M PRICE MONITOR")
    print("=" * 42)
    print(
        f"Max totaalprijs: "
        f"€{MAX_TOTAL_PRICE:.2f}"
    )
    print(
        f"Gezochte maat: {TARGET_SIZE}"
    )
    print(
        f"Prijsdaling alert: "
        f"{MIN_PRICE_DROP_PERCENT:.1f}%"
    )
    print(
        f"Aantal productpagina's: "
        f"{len(PRODUCTS)}"
    )
    print("-" * 42)

    state = load_state()

    new_state = dict(state)

    found = 0
    errors = 0
    alerts = 0

    for product in PRODUCTS:

        print()
        print("-" * 42)
        print(
            f"{product['store']} — "
            f"{product['name']}"
        )
        print("-" * 42)

        try:

            html = fetch(
                product["url"]
            )

            parsed = parse_product(
                product,
                html,
            )

            found += 1

            key = (
                f"{product['store']}|"
                f"{product['url']}"
            )

            old = state.get(key)

            print(
                f"Product: "
                f"{parsed['name']}"
            )

            print(
                f"Prijs: "
                f"{parsed['price']}"
            )

            print(
                f"Verzending: "
                f"{parsed['shipping']}"
            )

            print(
                f"Totaal: "
                f"{parsed['total_price']}"
            )

            print(
                f"Triolet gedetecteerd: "
                f"{parsed['is_triolet']}"
            )

            print(
                f"Herenmodel: "
                f"{parsed['is_mens']}"
            )

            print(
                f"Maat M beschikbaar: "
                f"{parsed['size_m_available']}"
            )

            print(
                f"Uitverkocht: "
                f"{parsed['out_of_stock']}"
            )

            # ------------------------------------------------
            # Veiligheidscontrole
            # ------------------------------------------------

            if not parsed["is_triolet"]:

                print(
                    "WAARSCHUWING: dit lijkt "
                    "geen Triolet-product."
                )

            if not parsed["is_mens"]:

                print(
                    "WAARSCHUWING: herenmodel "
                    "niet bevestigd."
                )

            alert, alert_type = (
                should_alert(
                    parsed,
                    old,
                )
            )

            print(
                f"ALERT: {alert}"
            )

            print(
                f"TYPE: {alert_type}"
            )

            if alert:

                # Extra veiligheidscontrole:
                # alleen echte heren-Triolet.
                if (
                    parsed["is_triolet"]
                    and parsed["is_mens"]
                ):

                    message = format_alert(
                        parsed,
                        alert_type,
                    )

                    send_telegram(
                        message
                    )

                    alerts += 1

                else:

                    print(
                        "ALERT onderdrukt: "
                        "productidentiteit niet "
                        "voldoende bevestigd."
                    )

            # ------------------------------------------------
            # State opslaan
            # ------------------------------------------------

            new_state[key] = {
                "store": parsed["store"],
                "name": parsed["name"],
                "url": parsed["url"],
                "price": parsed["price"],
                "shipping": parsed["shipping"],
                "total_price": parsed["total_price"],
                "size_m_available": (
                    parsed[
                        "size_m_available"
                    ]
                ),
                "is_triolet": (
                    parsed["is_triolet"]
                ),
                "is_mens": (
                    parsed["is_mens"]
                ),
            }

        except Exception as exc:

            errors += 1

            print(
                f"FOUT bij "
                f"{product['store']}: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

        time.sleep(
            REQUEST_DELAY
        )

    save_state(
        new_state
    )

    print()
    print("=" * 42)
    print("MONITOR KLAAR")
    print("=" * 42)

    print(
        f"Pagina's verwerkt: {found}"
    )

    print(
        f"Fouten: {errors}"
    )

    print(
        f"Alerts: {alerts}"
    )

    print(
        f"State opgeslagen in: "
        f"{STATE_FILE}"
    )


if __name__ == "__main__":
    main()
