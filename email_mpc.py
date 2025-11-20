from fastmcp import FastMCP
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, List, Dict, Any
import requests
from datetime import datetime, timedelta, timezone
import feedparser

mcp = FastMCP(name="Email Sender MCP")
# need to decide on oh idk an actual email client I can use
#  I can add more i just, idk many crypto influencers
CRYPTO_FEEDS = [
    "https://news.google.com/rss/search?q=cryptocurrency&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=ethereum&hl=en-US&gl=US&ceid=US:en",
]

COIN_ID_MAP = {
    "bitcoin": "bitcoin",
    "btc": "bitcoin",
    "ethereum": "ethereum",
    "eth": "ethereum",
    "solana": "solana",
    "sol": "solana",
    "dogecoin": "dogecoin",
    "doge": "dogecoin",
}

def _normalise_coin(coin: str) -> Optional[str]:
    if not coin:
        return None
    key = coin.strip().lower()
    return COIN_ID_MAP.get(key)
def fetch_headlines(coin: str = "", max_items: int = 8) -> List[Dict[str, Any]]:
    """
    If coin is provided, query Google News for that coin.
    Otherwise, use the general crypto feeds.
    """
    collected: List[Dict[str, Any]] = []

    if coin:
        # Focused feed just for this coin
        query = coin.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={query}+cryptocurrency&hl=en-US&gl=US&ceid=US:en"
        feeds = [url]
    else:
        feeds = CRYPTO_FEEDS

    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:
            collected.append(
                {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "source": getattr(entry.get("source", {}), "title", None)
                    or entry.get("source", {}).get("title", "Unknown"),
                    "published": entry.get("published", ""),
                }
            )

    # Deduplicate by title a bit
    seen_titles = set()
    unique_items = []
    for item in collected:
        t = item["title"]
        if t not in seen_titles:
            seen_titles.add(t)
            unique_items.append(item)

    return unique_items[:max_items]


def summarize_items(items):
    if not items:
        return "No crypto news found."

    summary = "Here’s what’s happening in the crypto world:\n\n"
    for i, item in enumerate(items, 1):
        summary += f"{i}. **{item['title']}**\n"
        summary += f"   {item['link']}\n\n"

    summary += (
        "\nGeneral caution: Crypto markets are more like a casino, "
        "so treat headlines as glamourised politicians. "
        "Stay diversified and avoid making stupid decisions."
        "And... of course TRUST US with your safety"
        "- VOX Tech"
    )
    return summary

def fetch_price(coin: str) -> Optional[Dict[str, Any]]:
    """
    Fetch current price for a given coin using CoinGecko.
    Returns None if the coin is unknown or the request fails.
    """
    coin_id = _normalise_coin(coin)
    if not coin_id:
        return None

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if coin_id not in data:
            return None

        price = data[coin_id].get("usd")
        return {
            "coin": coin,
            "coingecko_id": coin_id,
            "price_usd": price,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "source": "coingecko",
        }
    except Exception:
        return None

@mcp.tool()
def crypto_news_summary(trigger: str = "now", coin: str = "", max_chars: int = 500):
    """
    trigger options:
    - "now": return headlines immediately
    - "morning": use this in a scheduler for before work stuff
    - "evening": use this for late night opportunities
    """
    items = fetch_headlines()
    return {
        "trigger": trigger,
        "coin": coin,
        "summary": summarize_items(items),
        "items": items
    }

def _get_env(name: str, required: bool = True) -> Optional[str]:
    val = os.environ.get(name)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def _split_list(s: str) -> List[str]:
    return [p.strip() for p in s.split(",") if p.strip()] if s else []

def summarize_items(items: List[Dict[str, Any]], coin: str = "") -> str:
    if not items:
        return "No crypto news found."

    topic = coin if coin else "the crypto world"
    summary = f"Here’s what’s happening around {topic}:\n\n"
    for i, item in enumerate(items, 1):
        summary += f"{i}. {item['title']}\n"
        summary += f"   {item['link']}\n\n"

    summary += (
        "\nGeneral caution: Crypto markets are a delightful little chaos pit. "
        "Headlines scream, traders panic, and everyone pretends they know what’s going on. "
        "Try not to let the FOMO gremlins puppeteer your wallet, my loyal sinners — "
        "and remember, this is *absolutely not* personalized financial advice. "
        "Just me, Vox, a face you can TRUST in the chaos~ \n"
        "https://static.wikia.nocookie.net/hazbinhotel/images/f/f7/Vox.png"

    )
    return summary


def build_commentary(coin: str, price_info: Optional[Dict[str, Any]], items: List[Dict[str, Any]]) -> str:
    """
    Lightweight explanation + generic advice.
    This is is like gambling lol, just context-y text.
    """
    lines = []

    if price_info and price_info.get("price_usd") is not None:
        price = price_info["price_usd"]
        coin_label = (coin or "the market").capitalize()
        lines.append(f"{coin_label} is currently around ${price:,.2f} (USD).")
    elif coin:
        lines.append(
            f"I couldn’t fetch a reliable live price for {coin} right now, "
            "but here’s what the news is talking about."
        )

    if items:
        top_titles = [i["title"] for i in items[:3]]
        lines.append(
            "Recent headlines that may be influencing sentiment include:\n"
            + "\n".join(f"- {t}" for t in top_titles)
        )

    lines.append(
        "\nFellow Viewers, I want to advise you to make good decisions:\n"
        "- Fake news can be anywhere, you know?.\n"
        "- We at VOX tech, care about your well-being and safety. \n"
        "- Trust US with your safety and monetary decisions"
    )

    return "\n".join(lines)


@mcp.tool()
def crypto_news_summary(trigger: str = "now", coin: str = "") -> Dict[str, Any]:
    """
    Get a crypto news + price snapshot.

    trigger options:
    - "now": immediate snapshot (e.g. user says: "tell me right now")
    - "morning": for a morning digest
    - "evening": for an evening digest

    coin: optional. Example values:
      - "" (empty) -> general crypto sentiment
      - "bitcoin", "btc"
      - "ethereum", "eth"
      - "solana", "sol"
      - "dogecoin", "doge"
    """
    items = fetch_headlines(coin=coin)
    price_info = fetch_price(coin) if coin else None
    summary_text = summarize_items(items, coin=coin)
    commentary = build_commentary(coin, price_info, items)

    return {
        "trigger": trigger,
        "coin": coin,
        "summary": summary_text,
        "price": price_info,
        "advice": commentary,
        "items": items,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
):
    """
    Sends a fresh looking HTML email with a Vox Tek footer.
    """

    try:
        host = _get_env("SMTP_HOST")
        port = int(_get_env("SMTP_PORT"))
        user = _get_env("SMTP_USER")
        password = _get_env("SMTP_PASS")
        from_addr = _get_env("SMTP_FROM")
        agent_intro = os.environ.get("USER_INTRO", "Email tool")

        # My Company logo jkjk
        footer = f"""
        <hr style="margin-top:20px; opacity:0.4;">
        <div style="font-family:Arial; font-size:13px; color:#666; text-align:center; margin-top:10px;">
            <p>Trust <b>Vox Tech</b> with your information, safety, and monetary problems.</p>
            <img src="https://static.wikia.nocookie.net/hazbinhotel/images/7/71/Voxtek.IMG_20251114_165011.jpg/revision/latest?cb=20251114195134"
                 alt="Vox Logo"
                 width="90"
                 style="margin-top:8px; opacity:0.9;">
        </div>
        """


        full_html_body = f"""
        <html>
            <body style="font-family:Arial; font-size:14px; color:#222;">
                {body}
                {footer}
            </body>
        </html>
        """

        # --- Build Email ---
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        msg["Subject"] = subject

        # ✨ Send both text and HTML (best practice)
        msg.set_content(body)                   # plain text fallback
        msg.add_alternative(full_html_body, subtype="html")  # HTML body

        # Collect recipients
        all_recipients = _split_list(to) + _split_list(cc) + _split_list(bcc)
        if not all_recipients:
            return {"ok": False, "error": "No recipients provided."}

        # --- SMTP Send ---
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(user, password)
                resp = server.send_message(msg, from_addr=from_addr, to_addrs=all_recipients)
        else:
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                try:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                except smtplib.SMTPNotSupportedError:
                    pass
                server.login(user, password)
                resp = server.send_message(msg, from_addr=from_addr, to_addrs=all_recipients)

        if resp:
            return {"ok": False, "error": f"Some recipients were refused: {resp}"}

        mid = msg.get("Message-ID") or "<local-generated>"
        return {
            "ok": True,
            "message_id": str(mid),
            "recipients": all_recipients,
            "agent": agent_intro,
        }

    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

@mcp.tool()
def create_task(
    title: str,
    description: str,
    xp: int,
    category: str = "Main",
    important: bool = False,
    attribute: str = "MA",
    attribute_points: int = 10,
):
    """
    Create a single quest/task in my task system.

    This calls POST {TASK_API_BASE}/api/add-task with a payload like:
    {
        "Title": title,
        "Description": description,
        "XP": xp,
        "Category": category,
        "Important": important,
        "Attribute": attribute,
        "AttributePoints": attribute_points
    }

    Use this when the user describes something they want to do and/or assigns XP.

    Attribute meanings (for the model):
    - VI: good sleep, eating well
    - ST: strength, muscle activities
    - MA: coding or studying (magic / intellect)
    - AT: social connection, making allies, talking to people
    - RES: resilience, stronger mindsets, dealing with anxiety/sadness
    - EN: walking, running, athletic things
    - INTELLIGENCE: learning new things, reading, practicing skills
    - FAI: positivity, affirmations, manifestation, prayer
    - INS: learning from experiences, reflecting on people/situations
    - ARC: networking, new opportunities, being well-rounded
    - HONOUR: doing good even when it’s hard
    - DOM: being more assertive and dominant
    - ECHOES: creating content / business / money things
    - DEX: efficiency, diligence in completing tasks
    - LOVE: appreciating and caring for people around you

    Example:
    User: "my boss wants me to look into automated testing, i think 15000xp for
    setting up cypress to run and then register data from aws and then another
    7000xp to have a meeting about this"

    Assistant should respond by calling this tool twice, e.g.:

    1) title="Set up Cypress automated tests"
       description="Install Cypress, write a basic test suite, hook it into AWS data."
       xp=15000
       category="Work"
       important=True
       attribute="MA"
       attribute_points=14

    2) title="Meet with boss about Cypress rollout"
       description="Review test results, plan automation strategy and responsibilities."
       xp=7000
       category="Work"
       important=True
       attribute="AT"
       attribute_points=10
    """
    base = _get_env("TASK_API_BASE").rstrip("/")
    url = f"{base}/api/add-task"

    payload = {
        "Title": title,
        "Description": description,
        "XP": xp,
        "Category": category,
        "Important": important,
        "Attribute": attribute,
        "AttributePoints": attribute_points,
    }

    headers = {"Content-Type": "application/json"}
    token = _get_env("TASK_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        try:
            api_json = resp.json()
        except Exception:
            api_json = {"raw_text": resp.text}

        return {
            "ok": True,
            "task": payload,
            "api_response": api_json,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
            "task": payload,
        }


if __name__ == "__main__":
    mcp.run()
