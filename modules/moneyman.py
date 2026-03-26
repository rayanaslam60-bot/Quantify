# modules/moneyman.py — MoneyMan AI chat

import streamlit as st
import urllib.request
import json

MM_SYS = """You are MoneyMan — 30-year veteran hedge fund manager, Goldman Sachs macro desk.
Speak directly. No disclaimers. Real trading terminology. Think risk/reward, sizing, catalysts.
Know everything: technicals, fundamentals, options flow, macro, Fed, sector rotation.
Trade ideas: your view, key levels, downside risk, upside, thesis invalidation.
Blunt. Pro to pro. No emojis. Sharp answers."""

QUICK_ASKS = [
    "Market outlook?", "Position sizing?", "Support & resistance?",
    "Best indicators?", "Trading earnings?", "Options flow?",
    "Smart money moves?", "Reading the VIX?", "Trade entry checklist?",
    "Biggest retail mistake?",
]

def call_mm(messages, key=""):
    secret_key = st.secrets.get("ANTHROPIC_API_KEY", "").strip()
    active = secret_key if secret_key else key.strip()
    if not active:
        return "Add your API key to activate MoneyMan."
    try:
        payload = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1024,
            "system": MM_SYS,
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=payload,
            headers={"Content-Type": "application/json",
                     "x-api-key": active,
                     "anthropic-version": "2023-06-01"},
            method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 401: return "Invalid API key."
        if e.code == 400: return f"400: {body[:300]}"
        if e.code == 429: return "Rate limit. Try again."
        return f"Error {e.code}: {body[:200]}"
    except Exception as e:
        return f"Error: {str(e)}"
