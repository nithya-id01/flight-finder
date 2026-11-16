# Cheapest flight finder (Python)

Enter a route, tap Check, get fares in INR cheapest first.

## Run it on your computer
1. Install Python 3.9 or newer.
2. Get a free API key at https://serpapi.com (the free plan has a monthly search limit).
3. In this folder run:
   pip install -r requirements.txt
   SERPAPI_KEY=your_key_here python app.py
   (Windows PowerShell: $env:SERPAPI_KEY="your_key_here"; python app.py)
4. Open http://localhost:3000

## Put it online
Deploy this folder to Render, Railway or Fly.io as a Python web service.
Build command: pip install -r requirements.txt
Start command: gunicorn app:app
Add an environment variable named SERPAPI_KEY. Never put the key in the HTML.

## Notes
- Results are cached for 10 minutes to save your search quota.
- Data comes from Google Flights, so it compares airlines and fares, not individual booking sites.
