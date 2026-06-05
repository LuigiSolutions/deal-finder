"""
Lead scraper using free sources only.
No SerpAPI needed — scrapes directly or uses free search APIs.

Sources:
- Zillow FSBO (via their public API-like endpoint)
- BizBuySell (public listings)
- Google Maps (via free places scraping)
- Craigslist (real estate for sale by owner)
- Michigan county assessor data (public)
"""

import streamlit as st
import requests
import time
import re
from urllib.parse import quote_plus
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

NMI_CITIES = [
    "Traverse City, MI",
    "Petoskey, MI",
    "Charlevoix, MI",
    "Elk Rapids, MI",
    "Boyne City, MI",
    "Cadillac, MI",
    "Bellaire, MI",
    "Suttons Bay, MI",
    "Leland, MI",
    "Frankfort, MI",
]


def scrape_craigslist_re(city_slug: str = "nmi") -> str:
    """
    Scrape Craigslist Northern Michigan FSBO listings.
    city_slug: 'nmi' = Northern Michigan Craigslist
    Returns raw text for Gemini to parse.
    """
    url = f"https://{city_slug}.craigslist.org/search/rea?s=0&query=for+sale+by+owner&sort=date"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            # Basic text extraction
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text)
            return text[:8000]
    except Exception as e:
        return f"Craigslist scrape error: {e}"
    return ""


def scrape_bizbuysell(location: str = "traverse-city-mi") -> str:
    """
    BizBuySell public listings — free, no auth required.
    Returns raw text summary for Gemini to parse.
    """
    url = f"https://www.bizbuysell.com/businesses-for-sale/{location}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text)
            # Focus on the listings section
            idx = text.find("listing")
            if idx > 0:
                text = text[max(0, idx-200):idx+6000]
            return text[:8000]
    except Exception as e:
        return f"BizBuySell scrape error: {e}"
    return ""


def search_google_free(query: str, num: int = 10) -> str:
    """
    Use DuckDuckGo's free instant answer API as a search fallback.
    No API key required.
    """
    # DuckDuckGo HTML search (no JS, scrapeable)
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text)
            return text[:8000]
    except Exception as e:
        return f"Search error: {e}"
    return ""


def get_re_search_data(city: str, search_type: str = "fsbo") -> str:
    """
    Aggregate real estate search data for a Northern Michigan city.
    Combines multiple free sources.
    """
    results = []

    # Craigslist FSBO
    cl_data = scrape_craigslist_re("nmi")
    if cl_data:
        results.append(f"=== CRAIGSLIST FSBO ===\n{cl_data}")

    # DuckDuckGo search
    queries = [
        f"for sale by owner {city} real estate motivated seller",
        f"{city} Michigan seller financing owner financing property for sale",
        f"{city} MI estate sale property price reduced motivated seller",
    ]
    for q in queries[:2]:  # Limit to 2 searches to avoid rate limiting
        data = search_google_free(q)
        if data:
            results.append(f"=== SEARCH: {q} ===\n{data}")
        time.sleep(1)  # Be polite

    return "\n\n".join(results)[:12000]


def get_biz_search_data(city: str) -> str:
    """
    Aggregate business acquisition search data.
    """
    results = []

    # BizBuySell
    slug = city.lower().replace(" ", "-").replace(",", "")
    bbs_data = scrape_bizbuysell(f"{slug}-mi")
    if bbs_data:
        results.append(f"=== BIZBUYSELL ===\n{bbs_data}")

    # DuckDuckGo
    queries = [
        f"business for sale {city} Michigan owner retiring",
        f"{city} MI small business for sale by owner SBA",
        f"established business for sale {city} Michigan owner financing",
    ]
    for q in queries[:2]:
        data = search_google_free(q)
        if data:
            results.append(f"=== SEARCH: {q} ===\n{data}")
        time.sleep(1)

    return "\n\n".join(results)[:12000]


def get_demo_re_leads() -> list:
    """
    Return realistic demo leads for when scraping is unavailable.
    Used in UI demo/testing mode.
    """
    return [
        {
            "name": "3BR/2BA Farmhouse - 7 acres",
            "address": "4821 Supply Rd",
            "city": "Traverse City, MI",
            "owner_name": "Robert Hensley",
            "owner_email": "rhensley@gmail.com",
            "owner_phone": "(231) 555-0142",
            "source": "Craigslist FSBO",
            "source_url": "https://nmi.craigslist.org/rea/example",
            "score": 8,
            "deal_type": "seller_finance",
            "price_asking": "$285,000",
            "motivated_signals": ["FSBO 180+ days", "Price reduced 3x", "Owner retiring to Florida"],
            "notes": "Long DOM + multiple price cuts = highly motivated. Good seller finance candidate.",
            "type": "real_estate",
        },
        {
            "name": "Commercial Rental Unit (4-plex)",
            "address": "1102 E Front St",
            "city": "Traverse City, MI",
            "owner_name": "Margaret Thornton",
            "owner_email": None,
            "owner_phone": "(231) 555-0189",
            "source": "DuckDuckGo Search",
            "source_url": None,
            "score": 9,
            "deal_type": "dscr",
            "price_asking": "$420,000",
            "motivated_signals": ["Estate sale", "Probate listing", "Units currently occupied"],
            "notes": "Estate sale 4-plex with tenants in place. DSCR loan candidate — rent covers debt service.",
            "type": "real_estate",
        },
        {
            "name": "Lakefront Cottage",
            "address": "8830 Torch Lake Dr",
            "city": "Elk Rapids, MI",
            "owner_name": "Dale Kuiper",
            "owner_email": "dkuiper55@yahoo.com",
            "owner_phone": None,
            "source": "Craigslist FSBO",
            "source_url": None,
            "score": 6,
            "deal_type": "lease_option",
            "price_asking": "$195,000",
            "motivated_signals": ["Seasonal, vacant in winter", "FSBO 90 days"],
            "notes": "Seasonal property with motivated owner. Lease-option possible for vacation rental play.",
            "type": "real_estate",
        },
    ]


def get_demo_biz_leads() -> list:
    """
    Return realistic demo business leads.
    """
    return [
        {
            "name": "Northwoods Heating & Cooling",
            "address": "2214 US-31 N",
            "city": "Petoskey, MI",
            "business_type": "HVAC Service",
            "owner_name": "Gary Steffens",
            "owner_email": "gary@northwoodshvac.com",
            "owner_phone": "(231) 555-0211",
            "source": "BizBuySell",
            "source_url": "https://bizbuysell.com/example",
            "score": 9,
            "asking_price": "$340,000",
            "annual_revenue": "$680,000",
            "acquisition_method": "sba_plus_seller_carry",
            "exit_signals": ["Owner age 64", "Listed 6 months", "No family succession"],
            "notes": "Recession-resistant, 22-year established business. SBA 7(a) qualifies easily at this revenue.",
            "type": "business",
        },
        {
            "name": "Traverse Bay Laundromat",
            "address": "1440 S Airport Rd W",
            "city": "Traverse City, MI",
            "business_type": "Laundromat",
            "owner_name": "Linda Voss",
            "owner_email": None,
            "owner_phone": "(231) 555-0177",
            "source": "DuckDuckGo Search",
            "source_url": None,
            "score": 8,
            "asking_price": "$180,000",
            "annual_revenue": "$142,000",
            "acquisition_method": "seller_finance",
            "exit_signals": ["Owner semi-retired", "Absentee managed", "Equipment aging"],
            "notes": "Laundromats are classic cash flow businesses. Seller carry likely given age of owner.",
            "type": "business",
        },
        {
            "name": "Cedar Creek Auto Repair",
            "address": "6601 M-72 E",
            "city": "Traverse City, MI",
            "business_type": "Auto Repair",
            "owner_name": "Mike Palazzolo",
            "owner_email": "mikepauto@gmail.com",
            "owner_phone": "(231) 555-0155",
            "source": "BizBuySell",
            "source_url": None,
            "score": 7,
            "asking_price": "$275,000",
            "annual_revenue": "$510,000",
            "acquisition_method": "sba_7a",
            "exit_signals": ["Listed for sale", "Owner has health issues", "30-year reputation"],
            "notes": "Strong recurring revenue. SBA 7(a) + seller training period. Excellent NMI reputation.",
            "type": "business",
        },
    ]
