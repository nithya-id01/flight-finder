"""Flight price comparison backend (Python / Flask).

Uses the free Travelpayouts (Aviasales) Data API. It returns the cheapest fares
recently found by Aviasales users for a route and date, sorted cheapest first.
"""
import os
import re
import time
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

TOKEN = os.environ.get("TRAVELPAYOUTS_TOKEN")
API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
CACHE_SECONDS = 10 * 60
_cache = {}  # key -> (timestamp, data)

AIRLINES = {
    "6E": "IndiGo", "AI": "Air India", "IX": "Air India Express", "QP": "Akasa Air",
    "SG": "SpiceJet", "S5": "Star Air", "9I": "Alliance Air", "I5": "AIX Connect",
    "UK": "Vistara", "G8": "Go First", "EK": "Emirates", "QR": "Qatar Airways",
    "EY": "Etihad", "BA": "British Airways", "VS": "Virgin Atlantic", "LH": "Lufthansa",
    "SQ": "Singapore Airlines", "TK": "Turkish Airlines",
}


@app.route("/")
def home():
    # Works whether index.html is in a "public" folder or next to app.py
    for folder in (os.path.join(BASE, "public"), BASE):
        if os.path.exists(os.path.join(folder, "index.html")):
            return send_from_directory(folder, "index.html")
    return "index.html not found. Put it next to app.py or in a folder named public.", 404


@app.route("/api/search")
def search():
    origin = request.args.get("from", "").strip().upper()
    dest = request.args.get("to", "").strip().upper()
    date = request.args.get("date", "").strip()

    if not re.fullmatch(r"[A-Z]{3}", origin) or not re.fullmatch(r"[A-Z]{3}", dest):
        return jsonify(error="Use 3-letter airport codes, e.g. BLR and HYD."), 400
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return jsonify(error="Pick a valid date."), 400
    if not TOKEN:
        return jsonify(error="Server has no TRAVELPAYOUTS_TOKEN set."), 500

    key = f"{origin}-{dest}-{date}"
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return jsonify(hit[1])

    params = {
        "origin": origin,
        "destination": dest,
        "departure_at": date,
        "one_way": "true",
        "unique": "false",
        "sorting": "price",
        "currency": "inr",
        "limit": 30,
        "token": TOKEN,
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=20)
        j = resp.json()
    except (requests.RequestException, ValueError):
        return jsonify(error="Could not reach the price provider. Try again."), 502

    if not j.get("success", False):
        return jsonify(error=str(j.get("error") or "The price provider returned an error.")), 502

    offers = []
    for t in j.get("data") or []:
        price = t.get("price")
        if not isinstance(price, (int, float)):
            continue
        code = t.get("airline") or ""
        offers.append({
            "price": price,
            "airline": AIRLINES.get(code, code or "Unknown airline"),
            "stops": t.get("transfers", 0) or 0,
            "departs": (t.get("departure_at") or "")[11:16],
            "minutes": t.get("duration"),
            "link": ("https://www.aviasales.com" + t["link"]) if t.get("link") else None,
        })
    offers.sort(key=lambda o: o["price"])

    data = {
        "from": origin,
        "to": dest,
        "date": date,
        "currency": "INR",
        "offers": offers,
        "bookUrl": offers[0]["link"] if offers else None,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }
    _cache[key] = (time.time(), data)
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))