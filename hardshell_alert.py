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

TARGET_MODEL = "Patagonia Triolet"

# ALLEEN MAAT M
TARGET_SIZE = "M"

# Maximale TOTALE PRIJS inclusief verzending naar Nederland
MAX_TOTAL_PRICE = 380.00

# Ook melden wanneer de totale prijs minimaal 10% daalt
MIN_PRICE_DROP_PERCENT = 10.0

# Statebestand
STATE_FILE = Path("state.json")

# Tijd tussen requests
REQUEST_DELAY = 2


# ============================================================
# WEBSHOPS
# ============================================================

STORES = {

    # --------------------------------------------------------
    # KATHMANDU
    # --------------------------------------------------------

    "Kathmandu": {
        "base_url": "https://www.kathmandu.nl",

        "urls": [
            "https://www.kathmandu.nl/patagonia-triolet-jacket-83403-blk-021464",
            "https://www.kathmandu.nl/patagonia-triolet-jkt-83403-casg-026684",
        ],

        # Gratis verzending vanaf €30
        "free_shipping_from": 30.00,
        "shipping_cost": 4.95,
    },


    # --------------------------------------------------------
    # RONALD ADVENTURE SHOP
    # --------------------------------------------------------

    "Ronald Adventure Shop": {
        "base_url": "https://www.ronaldadventureshop.nl",

        "search_url": (
            "https://www.ronaldadventureshop.nl/patagonia"
        ),

        # Gratis vanaf €50
        "free_shipping_from": 50.00,
        "shipping_cost": 5.00,
    },


    # --------------------------------------------------------
    # BEVER
    # --------------------------------------------------------

    "Bever": {
        "base_url": "https://www.bever.nl",

        "search_url": (
            "https://www.bever.nl/c/heren/jassen/"
            "?q=patagonia%20triolet"
        ),

        # Wordt conservatief ingesteld.
        # Als verzending niet betrouwbaar bepaald kan worden,
        # wordt GEEN alert gestuurd.
        "shipping_unknown": True,
    },


    # --------------------------------------------------------
    # ZALANDO
    # --------------------------------------------------------

    "Zalando": {
        "base_url": "https://www.zalando.nl",

        "search_url": (
            "https://www.zalando.nl/catalog/?q="
            "patagonia%20triolet"
        ),

        "shipping_unknown": True,
    },


    # --------------------------------------------------------
    # BERGZEIT
    # --------------------------------------------------------

    "Bergzeit": {
        "base_url": "https://www.bergzeit.nl",

        "search_url": (
            "https://www.bergzeit.nl/search?sSearch="
            "Patagonia%20Triolet"
        ),

        "shipping_unknown": True,
    },


    # --------------------------------------------------------
    # SNOWLEADER
    # --------------------------------------------------------

    "Snowleader": {
        "base_url": "https://www.snowleader.nl",

        "search_url": (
            "https://www.snowleader.nl/nl/"
            "search?s=Patagonia%20Triolet"
        ),

        "shipping_unknown": True,
    },


    # --------------------------------------------------------
    # EKOSPORT
    # --------------------------------------------------------

    "Ekosport": {
        "base_url": "https://www.ekosport.nl",

        "search_url": (
            "https://www.ekosport.nl/search/"
            "?q=Patagonia%20Triolet"
        ),

        "shipping_unknown": True,
    },


    # --------------------------------------------------------
    # BERGFREUNDE
    # --------------------------------------------------------

    "Bergfreunde": {
        "base_url": "https://www.bergfreunde.nl",

        "search_url": (
            "https://www.bergfreunde.nl/"
            "search/?q=Patagonia%20Triolet"
        ),

        # Gratis verzending vanaf €69 in NL
        "free_shipping_from": 69.00,
        "shipping_cost": 4.95,
    },


    # --------------------------------------------------------
    # BIKE24
    # --------------------------------------------------------

    "Bike24": {
        "base_url": "https://www.bike24.nl",

        "search_url": (
            "https://www.bike24.nl/search-result"
            "?q=Patagonia%20Triolet"
        ),

        "shipping_unknown": True,
    },
}


# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.environ.get(
    "TELEGRAM_CHAT_ID"
)


def telegram_message(text):
    """Stuur bericht naar Telegram."""

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:

        print(
            "Telegram secrets ontbreken."
        )

        print(text)

        return

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
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
    "Accept-Language": (
        "nl-NL,nl;q=0.9,en;q=0.8"
    ),
}


session = requests.Session()
session.headers.update(HEADERS)


def get_page(url):
    """Download een pagina."""

    print(f"GET {url}")

    response = session.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    time.sleep(REQUEST_DELAY)

    return response.text


# ============================================================
# HULPFUNCTIES
# ============================================================

def normalize_text(text):
    return re.sub(
        r"\s+",
        " ",
        text or ""
    ).strip()


def parse_price(text):
    """
    Parse Nederlandse en internationale prijzen.

    Voorbeelden:
    €419,95
    419,95
    €1.299,95
    419.95
    """

    if not text:
        return None

    text = str(text).strip()

    # Nederlandse notatie
    match = re.search(
        r"€?\s*"
        r"(\d{1,3}(?:\.\d{3})*"
        r"(?:,\d{2})"
        r"|\d+(?:,\d{2})?)",
        text
    )

    if match:

        value = match.group(1)

        value = value.replace(
            ".",
            ""
        )

        value = value.replace(
            ",",
            "."
        )

        try:
            return float(value)
        except ValueError:
            pass

    # Internationale notatie
    match = re.search(
        r"€?\s*(\d+(?:\.\d{2}))",
        text
    )

    if match:

        try:
            return float(
                match.group(1)
            )
        except ValueError:
            pass

    return None


def is_triolet(text):
    """
    Controleert of tekst daadwerkelijk over een
    Patagonia Triolet gaat.
    """

    if not text:
        return False

    text = text.lower()

    return (
        "patagonia" in text
        and "triolet" in text
    )


def is_mens_product(text):
    """
    Controleer of het om heren gaat.

    We accepteren meerdere benamingen.
    """

    if not text:
        return False

    text = text.lower()

    positive = [
        "heren",
        "men",
        "mens",
        "m's",
        "herren",
    ]

    negative = [
        "dames",
        "women",
        "womens",
        "w's",
        "damen",
    ]

    has_positive = any(
        word in text
        for word in positive
    )

    has_negative = any(
        word in text
        for word in negative
    )

    if has_negative and not has_positive:
        return False

    return has_positive


def find_size_m(text):
    """
    Zoek expliciet naar maat M.

    LET OP:
    Dit is alleen een fallback.
    Per webshop proberen we eerst
    product-specifieke informatie te gebruiken.
    """

    if not text:
        return False

    patterns = [

        r"\bmaat\s*M\b",

        r"\bsize\s*M\b",

        r"\bM\s*(?:op voorraad|beschikbaar)\b",

        r"\bM\s*(?:in stock|available)\b",

        r"\bM\b",
    ]

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            flags=re.I
        ):
            return True

    return False


def extract_json_ld(soup):
    """
    Haal JSON-LD productinformatie uit een pagina.
    """

    results = []

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        raw = (
            script.string
            or script.get_text()
        )

        if not raw:
            continue

        try:

            data = json.loads(
                raw
            )

        except Exception:
            continue

        if isinstance(data, list):

            results.extend(
                data
            )

        else:

            results.append(
                data
            )

    return results


def find_json_ld_price(soup):
    """
    Zoek prijs in Product/Offer JSON-LD.
    """

    for item in extract_json_ld(soup):

        if not isinstance(
            item,
            dict
        ):
            continue

        offers = item.get(
            "offers"
        )

        if isinstance(
            offers,
            dict
        ):

            price = offers.get(
                "price"
            )

            parsed = parse_price(
                price
            )

            if parsed is not None:
                return parsed

        if isinstance(
            offers,
            list
        ):

            for offer in offers:

                if not isinstance(
                    offer,
                    dict
                ):
                    continue

                price = offer.get(
                    "price"
                )

                parsed = parse_price(
                    price
                )

                if parsed is not None:
                    return parsed

    return None


def find_json_ld_url(soup):
    """
    Zoek product-URL uit JSON-LD.
    """

    for item in extract_json_ld(soup):

        if not isinstance(
            item,
            dict
        ):
            continue

        url = item.get(
            "url"
        )

        if url:
            return url

    return None


def calculate_shipping(
    store_name,
    price
):
    """
    Bereken verzendkosten.

    Als we het niet betrouwbaar weten,
    retourneren we None.
    """

    config = STORES[
        store_name
    ]

    if price is None:
        return None

    if config.get(
        "shipping_unknown"
    ):
        return None

    free_shipping_from = config.get(
        "free_shipping_from"
    )

    shipping_cost = config.get(
        "shipping_cost"
    )

    if (
        free_shipping_from is not None
        and price >= free_shipping_from
    ):
        return 0.00

    if shipping_cost is not None:
        return shipping_cost

    return None


# ============================================================
# GENERIEKE LINK-VIND FUNCTIE
# ============================================================

def find_triolet_links(
    html,
    base_url
):
    """
    Zoek Triolet-productlinks in een zoek-
    of categoriepagina.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    results = []

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link.get(
            "href"
        )

        if not href:
            continue

        text = normalize_text(
            link.get_text(
                " ",
                strip=True
            )
        )

        combined = (
            f"{text} {href}"
        ).lower()

        if not is_triolet(
            combined
        ):
            continue

        # Geen damesproducten
        if any(
            word in combined
            for word in [
                "women",
                "womens",
                "w's",
                "dames",
                "damen",
            ]
        ):

            continue

        url = urljoin(
            base_url,
            href
        )

        if url not in results:

            results.append(
                url
            )

    return results


# ============================================================
# KATHMANDU PARSER
# ============================================================

def search_kathmandu():

    store = STORES[
        "Kathmandu"
    ]

    products = []

    for url in store["urls"]:

        products.append({
            "store": "Kathmandu",
            "model": TARGET_MODEL,
            "url": url,
        })

    return products


def parse_kathmandu(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = None

    for element in soup.select(
        "#jq-productpagina-prijs .amount"
    ):

        price = parse_price(
            element.get_text(
                " ",
                strip=True
            )
        )

        if price is not None:
            break

    if price is None:

        price = find_json_ld_price(
            soup
        )

    size_m = find_size_m(
        text
    )

    shipping = calculate_shipping(
        "Kathmandu",
        price
    )

    total = (
        price + shipping
        if price is not None
        and shipping is not None
        else None
    )

    return {
        "store": "Kathmandu",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": shipping,
        "total_price": total,
        "size_m_available": size_m,
    }


# ============================================================
# RONALD ADVENTURE SHOP PARSER
# ============================================================

def search_ronald():

    store = STORES[
        "Ronald Adventure Shop"
    ]

    html = get_page(
        store["search_url"]
    )

    links = find_triolet_links(
        html,
        store["base_url"]
    )

    return [
        {
            "store": "Ronald Adventure Shop",
            "model": TARGET_MODEL,
            "url": url,
        }
        for url in links
    ]


def parse_ronald(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:

        selectors = [
            ".price",
            ".product-price",
            ".special-price",
            ".final-price",
        ]

        for selector in selectors:

            for element in soup.select(
                selector
            ):

                price = parse_price(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                if price is not None:
                    break

            if price is not None:
                break

    if price is None:
        price = parse_price(
            text
        )

    size_m = find_size_m(
        text
    )

    shipping = calculate_shipping(
        "Ronald Adventure Shop",
        price
    )

    total = (
        price + shipping
        if price is not None
        and shipping is not None
        else None
    )

    return {
        "store": "Ronald Adventure Shop",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": shipping,
        "total_price": total,
        "size_m_available": size_m,
    }


# ============================================================
# BEVER PARSER
# ============================================================

def search_bever():

    store = STORES[
        "Bever"
    ]

    html = get_page(
        store["search_url"]
    )

    links = find_triolet_links(
        html,
        store["base_url"]
    )

    return [
        {
            "store": "Bever",
            "model": TARGET_MODEL,
            "url": url,
        }
        for url in links
    ]


def parse_bever(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:

        # Veel gebruikte prijsselectors
        selectors = [
            '[data-testid*="price"]',
            '[class*="price"]',
            '[data-test*="price"]',
        ]

        for selector in selectors:

            for element in soup.select(
                selector
            ):

                candidate = normalize_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                if "€" not in candidate:
                    continue

                price = parse_price(
                    candidate
                )

                if price is not None:
                    break

            if price is not None:
                break

    size_m = find_size_m(
        text
    )

    # Bever verzendkosten worden bewust
    # niet gegokt.
    shipping = None

    return {
        "store": "Bever",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": shipping,
        "total_price": None,
        "size_m_available": size_m,
    }


# ============================================================
# ZALANDO PARSER
# ============================================================

def search_zalando():

    store = STORES[
        "Zalando"
    ]

    html = get_page(
        store["search_url"]
    )

    links = find_triolet_links(
        html,
        store["base_url"]
    )

    return [
        {
            "store": "Zalando",
            "model": TARGET_MODEL,
            "url": url,
        }
        for url in links
    ]


def parse_zalando(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:

        # Zalando gebruikt regelmatig
        # meta/itemprop prijsinformatie.
        meta_selectors = [
            'meta[property="product:price:amount"]',
            'meta[itemprop="price"]',
        ]

        for selector in meta_selectors:

            element = soup.select_one(
                selector
            )

            if element:

                value = (
                    element.get("content")
                    or element.get("value")
                    or element.get_text()
                )

                price = parse_price(
                    value
                )

                if price is not None:
                    break

    size_m = find_size_m(
        text
    )

    return {
        "store": "Zalando",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": None,
        "total_price": None,
        "size_m_available": size_m,
    }


# ============================================================
# BERGZEIT PARSER
# ============================================================

def search_bergzeit():

    store = STORES[
        "Bergzeit"
    ]

    # De actuele herenpagina is stabieler
    # dan de algemene zoekpagina.
    url = (
        "https://www.bergzeit.nl/p/"
        "patagonia-heren-triolet-jas/1119573/"
    )

    return [
        {
            "store": "Bergzeit",
            "model": TARGET_MODEL,
            "url": url,
        }
    ]


def parse_bergzeit(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:
        price = parse_price(
            text
        )

    size_m = find_size_m(
        text
    )

    return {
        "store": "Bergzeit",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": None,
        "total_price": None,
        "size_m_available": size_m,
    }


# ============================================================
# SNOWLEADER PARSER
# ============================================================

def search_snowleader():

    store = STORES[
        "Snowleader"
    ]

    html = get_page(
        store["search_url"]
    )

    links = find_triolet_links(
        html,
        store["base_url"]
    )

    return [
        {
            "store": "Snowleader",
            "model": TARGET_MODEL,
            "url": url,
        }
        for url in links
    ]


def parse_snowleader(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:

        # Snowleader gebruikt meerdere
        # prijsblokken.
        selectors = [
            '[itemprop="price"]',
            '[data-price]',
            ".price",
        ]

        for selector in selectors:

            for element in soup.select(
                selector
            ):

                value = (
                    element.get(
                        "content"
                    )
                    or element.get(
                        "data-price"
                    )
                    or element.get_text(
                        " ",
                        strip=True
                    )
                )

                price = parse_price(
                    value
                )

                if price is not None:
                    break

            if price is not None:
                break

    size_m = find_size_m(
        text
    )

    return {
        "store": "Snowleader",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": None,
        "total_price": None,
        "size_m_available": size_m,
    }


# ============================================================
# EKOSPORT PARSER
# ============================================================

def search_ekosport():

    store = STORES[
        "Ekosport"
    ]

    html = get_page(
        store["search_url"]
    )

    links = find_triolet_links(
        html,
        store["base_url"]
    )

    return [
        {
            "store": "Ekosport",
            "model": TARGET_MODEL,
            "url": url,
        }
        for url in links
    ]


def parse_ekosport(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:

        selectors = [
            '[itemprop="price"]',
            '[data-price]',
            ".price",
        ]

        for selector in selectors:

            for element in soup.select(
                selector
            ):

                value = (
                    element.get(
                        "content"
                    )
                    or element.get(
                        "data-price"
                    )
                    or element.get_text(
                        " ",
                        strip=True
                    )
                )

                price = parse_price(
                    value
                )

                if price is not None:
                    break

            if price is not None:
                break

    size_m = find_size_m(
        text
    )

    return {
        "store": "Ekosport",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": None,
        "total_price": None,
        "size_m_available": size_m,
    }


# ============================================================
# BERGFREUNDE PARSER
# ============================================================

def search_bergfreunde():

    store = STORES[
        "Bergfreunde"
    ]

    # Actuele heren-Trioletpagina
    url = (
        "https://www.bergfreunde.nl/"
        "patagonia-triolet-jacket-regenjas-bf/"
    )

    return [
        {
            "store": "Bergfreunde",
            "model": TARGET_MODEL,
            "url": url,
        }
    ]


def parse_bergfreunde(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:

        selectors = [
            '[itemprop="price"]',
            '[data-testid*="price"]',
            ".price",
        ]

        for selector in selectors:

            for element in soup.select(
                selector
            ):

                value = (
                    element.get(
                        "content"
                    )
                    or element.get_text(
                        " ",
                        strip=True
                    )
                )

                price = parse_price(
                    value
                )

                if price is not None:
                    break

            if price is not None:
                break

    size_m = find_size_m(
        text
    )

    shipping = calculate_shipping(
        "Bergfreunde",
        price
    )

    total = (
        price + shipping
        if price is not None
        and shipping is not None
        else None
    )

    return {
        "store": "Bergfreunde",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": shipping,
        "total_price": total,
        "size_m_available": size_m,
    }


# ============================================================
# BIKE24 PARSER
# ============================================================

def search_bike24():

    store = STORES[
        "Bike24"
    ]

    html = get_page(
        store["search_url"]
    )

    links = find_triolet_links(
        html,
        store["base_url"]
    )

    return [
        {
            "store": "Bike24",
            "model": TARGET_MODEL,
            "url": url,
        }
        for url in links
    ]


def parse_bike24(
    product_ref
):

    html = get_page(
        product_ref["url"]
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = (
        normalize_text(
            soup.title.get_text()
        )
        if soup.title
        else None
    )

    price = find_json_ld_price(
        soup
    )

    if price is None:

        selectors = [
            '[itemprop="price"]',
            '[data-price]',
            ".price",
        ]

        for selector in selectors:

            for element in soup.select(
                selector
            ):

                value = (
                    element.get(
                        "content"
                    )
                    or element.get(
                        "data-price"
                    )
                    or element.get_text(
                        " ",
                        strip=True
                    )
                )

                price = parse_price(
                    value
                )

                if price is not None:
                    break

            if price is not None:
                break

    size_m = find_size_m(
        text
    )

    return {
        "store": "Bike24",
        "model": TARGET_MODEL,
        "url": product_ref["url"],
        "title": title,
        "price": price,
        "shipping": None,
        "total_price": None,
        "size_m_available": size_m,
    }


# ============================================================
# ZOEKFUNCTIES ALLE WEBSHOPS
# ============================================================

SEARCH_FUNCTIONS = {

    "Kathmandu": search_kathmandu,

    "Ronald Adventure Shop":
        search_ronald,

    "Bever":
        search_bever,

    "Zalando":
        search_zalando,

    "Bergzeit":
        search_bergzeit,

    "Snowleader":
        search_snowleader,

    "Ekosport":
        search_ekosport,

    "Bergfreunde":
        search_bergfreunde,

    "Bike24":
        search_bike24,
}


# ============================================================
# PARSERFUNCTIES ALLE WEBSHOPS
# ============================================================

PARSER_FUNCTIONS = {

    "Kathmandu":
        parse_kathmandu,

    "Ronald Adventure Shop":
        parse_ronald,

    "Bever":
        parse_bever,

    "Zalando":
        parse_zalando,

    "Bergzeit":
        parse_bergzeit,

    "Snowleader":
        parse_snowleader,

    "Ekosport":
        parse_ekosport,

    "Bergfreunde":
        parse_bergfreunde,

    "Bike24":
        parse_bike24,
}


# ============================================================
# ALLE PRODUCTEN ZOEKEN
# ============================================================

def search_all_products():

    products = []

    for store_name, search_function in (
        SEARCH_FUNCTIONS.items()
    ):

        print(
            "\n------------------------------------------"
        )

        print(
            f"Zoeken bij: {store_name}"
        )

        print(
            "------------------------------------------"
        )

        try:

            found = search_function()

            print(
                f"{store_name}: "
                f"{len(found)} productpagina(s)"
            )

            products.extend(
                found
            )

        except Exception as exc:

            print(
                f"FOUT bij zoeken "
                f"{store_name}: {exc}"
            )

    return products


# ============================================================
# PRODUCT PARSEN
# ============================================================

def parse_product(
    product_ref
):

    store = product_ref[
        "store"
    ]

    parser = PARSER_FUNCTIONS.get(
        store
    )

    if parser is None:

        raise ValueError(
            f"Geen parser voor {store}"
        )

    return parser(
        product_ref
    )


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
# PRODUCT KEY
# ============================================================

def product_key(
    product
):

    return (
        f"{product['store']}|"
        f"{product['url']}"
    )


# ============================================================
# ALERT LOGICA
# ============================================================

def should_alert(
    product,
    old
):

    price = product.get(
        "price"
    )

    total_price = product.get(
        "total_price"
    )

    # --------------------------------------------------------
    # Geen betrouwbare totaalprijs
    # --------------------------------------------------------

    if (
        price is None
        or total_price is None
    ):

        return False, None

    # --------------------------------------------------------
    # Alleen maat M
    # --------------------------------------------------------

    if not product.get(
        "size_m_available",
        False
    ):

        return False, None

    # --------------------------------------------------------
    # Onder limiet
    # --------------------------------------------------------

    under_limit = (
        total_price <= MAX_TOTAL_PRICE
    )

    # --------------------------------------------------------
    # Grote prijsdaling
    # --------------------------------------------------------

    price_drop = False

    if old:

        old_total = old.get(
            "total_price"
        )

        if (
            old_total is not None
            and old_total > total_price
        ):

            drop_percent = (
                (
                    old_total
                    - total_price
                )
                / old_total
                * 100
            )

            if (
                drop_percent
                >= MIN_PRICE_DROP_PERCENT
            ):

                price_drop = True

    # --------------------------------------------------------
    # Nieuwe aanbieding
    # --------------------------------------------------------

    if (
        old is None
        and under_limit
    ):

        return True, "PRICE"

    # --------------------------------------------------------
    # Prijs passeert de limiet
    # --------------------------------------------------------

    if old:

        old_total = old.get(
            "total_price"
        )

        if (
            old_total is not None
            and old_total > MAX_TOTAL_PRICE
            and under_limit
        ):

            return True, "PRICE"

    # --------------------------------------------------------
    # Grote daling
    # --------------------------------------------------------

    if price_drop:

        return True, "DROP"

    return False, None


# ============================================================
# TELEGRAM MELDING
# ============================================================

def format_alert(
    product,
    alert_type,
    old
):

    store = product[
        "store"
    ]

    price = product[
        "price"
    ]

    shipping = product[
        "shipping"
    ]

    total = product[
        "total_price"
    ]

    if alert_type == "PRICE":

        headline = (
            "🔥 PATAGONIA TRIOLET DEAL"
        )

    else:

        headline = (
            "📉 PATAGONIA TRIOLET "
            "PRIJS GEDAALD"
        )

    old_text = ""

    if old:

        old_total = old.get(
            "total_price"
        )

        if (
            old_total is not None
            and old_total > total
        ):

            old_text = (
                f"\nWas: €{old_total:.2f}"
            )

    shipping_text = (
        f"€{shipping:.2f}"
        if shipping is not None
        else "onbekend"
    )

    return (
        f"{headline}\n\n"
        f"{TARGET_MODEL}\n"
        f"Winkel: {store}\n"
        f"Maat: M\n\n"
        f"Product: €{price:.2f}\n"
        f"Verzending: {shipping_text}\n"
        f"Totaal: €{total:.2f}"
        f"{old_text}\n\n"
        f"{product['url']}"
    )


# ============================================================
# DEBUG OUTPUT
# ============================================================

def print_product_result(
    product
):

    print(
        f"\n{product['store']}"
    )

    print(
        f"  Product: "
        f"{product['model']}"
    )

    print(
        f"  URL: "
        f"{product['url']}"
    )

    print(
        f"  Prijs: "
        f"{product['price']}"
    )

    print(
        f"  Verzending: "
        f"{product['shipping']}"
    )

    print(
        f"  Totaal: "
        f"{product['total_price']}"
    )

    print(
        f"  M beschikbaar: "
        f"{product['size_m_available']}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=========================================="
    )

    print(
        "PATAGONIA TRIOLET M PRICE MONITOR"
    )

    print(
        "=========================================="
    )

    print(
        f"Max totaalprijs: "
        f"€{MAX_TOTAL_PRICE:.2f}"
    )

    print(
        f"Gezochte maat: "
        f"{TARGET_SIZE}"
    )

    print(
        f"Prijsdaling alert: "
        f"{MIN_PRICE_DROP_PERCENT:.1f}%"
    )

    print(
        "Aantal winkels: "
        f"{len(STORES)}"
    )

    state = load_state()

    if not isinstance(
        state,
        dict
    ):

        state = {}

    # --------------------------------------------------------
    # PRODUCTEN ZOEKEN
    # --------------------------------------------------------

    products = search_all_products()

    print(
        "\n=========================================="
    )

    print(
        f"Totaal gevonden: "
        f"{len(products)} productpagina's"
    )

    print(
        "=========================================="
    )

    current_state = dict(
        state
    )

    alerts = []

    # --------------------------------------------------------
    # PRODUCTEN CONTROLEREN
    # --------------------------------------------------------

    for product_ref in products:

        try:

            product = parse_product(
                product_ref
            )

            print_product_result(
                product
            )

            key = product_key(
                product
            )

            old = state.get(
                key
            )

            should, alert_type = (
                should_alert(
                    product,
                    old
                )
            )

            print(
                f"  ALERT: "
                f"{should}"
            )

            print(
                f"  TYPE: "
                f"{alert_type}"
            )

            # ------------------------------------------------
            # TELEGRAM ALERT
            # ------------------------------------------------

            if should:

                alerts.append(
                    format_alert(
                        product,
                        alert_type,
                        old
                    )
                )

            # ------------------------------------------------
            # STATE
            # ------------------------------------------------

            current_state[key] = {

                "store":
                    product["store"],

                "model":
                    product["model"],

                "url":
                    product["url"],

                "price":
                    product["price"],

                "shipping":
                    product["shipping"],

                "total_price":
                    product["total_price"],

                "size_m_available":
                    product[
                        "size_m_available"
                    ],

                "checked_at":
                    time.time(),
            }

        except Exception as exc:

            print(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )

            print(
                f"FOUT bij "
                f"{product_ref.get('store')}"
            )

            print(
                product_ref.get(
                    "url"
                )
            )

            print(
                f"Foutmelding: {exc}"
            )

            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )

    # --------------------------------------------------------
    # TELEGRAM
    # --------------------------------------------------------

    print(
        "\n=========================================="
    )

    print(
        f"Alerts: {len(alerts)}"
    )

    print(
        "=========================================="
    )

    for alert in alerts:

        try:

            telegram_message(
                alert
            )

        except Exception as exc:

            print(
                f"Telegram fout: {exc}"
            )

    # --------------------------------------------------------
    # STATE OPSLAAN
    # --------------------------------------------------------

    save_state(
        current_state
    )

    print(
        "\nKlaar."
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
