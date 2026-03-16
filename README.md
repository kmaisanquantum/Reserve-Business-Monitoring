# PNG Business Transparency Monitor

A full-stack "Born in the Cloud" web application that monitors foreign vs. local business participation in Papua New Guinea — detecting fronting, RAL violations, and ownership patterns in real time.

---

## Tech Stack

| Layer     | Technology                                      |
|-----------|-------------------------------------------------|
| Frontend  | React 18, Lucide-React (no Tailwind dep needed) |
| Backend   | FastAPI + Uvicorn                               |
| Database  | MongoDB Atlas (Motor async driver)              |
| Scrapers  | BeautifulSoup4 + httpx                          |
| Scheduler | APScheduler (async)                             |
| Hosting   | Render.com (free tier)                          |

---

## Project Structure

```
png-monitor/
├── render.yaml                  ← Render multi-service config
├── backend/
│   ├── main.py                  ← FastAPI app + all API routes
│   ├── scraper.py               ← All scrapers + SA entity linker
│   ├── models.py                ← Pydantic data models
│   ├── database.py              ← Motor/MongoDB connection
│   ├── config.py                ← Settings from env vars
│   ├── seed.py                  ← Seed MongoDB with demo data
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── package.json
    ├── public/index.html
    └── src/
        ├── App.jsx              ← Root component
        ├── index.js / index.css
        ├── services/api.js      ← All fetch calls
        ├── hooks/useApi.js      ← Generic polling hook
        └── components/
            ├── NavBar.jsx       ← Search + refresh
            ├── StatCards.jsx    ← KPI row
            ├── Heatmap.jsx      ← Province SVG map
            ├── EntityLinker.jsx ← Fronting cluster cards
            ├── TrendFeed.jsx    ← NLP news feed
            └── AlertPanel.jsx   ← Regulatory alerts
```

---

## Deploy to Render.com — Step by Step

### 1. MongoDB Atlas (free)

1. Go to https://cloud.mongodb.com → create a free M0 cluster
2. Add a database user with **read/write** permissions
3. Whitelist `0.0.0.0/0` (allow all IPs — required for Render)
4. Copy your connection string:
   ```
   mongodb+srv://<user>:<password>@cluster0.mongodb.net/png_monitor?retryWrites=true&w=majority
   ```

### 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<your-username>/png-monitor.git
git push -u origin main
```

### 3. Deploy on Render.com

1. Go to https://dashboard.render.com → **New → Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates **two services** automatically:
   - `png-monitor-api` (Python web service)
   - `png-monitor-web` (Static site)

4. In the `png-monitor-api` service → **Environment** tab, add:
   ```
   MONGODB_URI = mongodb+srv://...   ← your Atlas connection string
   ```
   All other env vars are set automatically from `render.yaml`.

5. Click **Deploy**. Both services build in ~3 minutes.

### 4. Seed demo data (first run)

Once the backend is live, run the seeder from your local machine:

```bash
cd backend
pip install motor pymongo python-dotenv
MONGODB_URI="your-atlas-uri" python seed.py
```

Or add a one-time job in Render → **Jobs** tab:
- Command: `python seed.py`
- Run once after first deploy

### 5. Update CORS

After deploy, get your frontend URL (e.g. `https://png-monitor-web.onrender.com`)
and set it in the backend env:

```
CORS_ORIGINS = https://png-monitor-web.onrender.com
```

---

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in MONGODB_URI
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
# Create .env.local:
echo "REACT_APP_API_URL=localhost:8000" > .env.local
npm start
```

App: http://localhost:3000

---

## API Reference

| Method | Endpoint                      | Description                      |
|--------|-------------------------------|----------------------------------|
| GET    | `/health`                     | Liveness probe                   |
| GET    | `/api/stats`                  | KPI dashboard numbers            |
| GET    | `/api/provinces`              | Heatmap province data            |
| GET    | `/api/clusters`               | Fronting clusters (SA-optimised) |
| GET    | `/api/trends?category=all`    | NLP trend feed                   |
| GET    | `/api/alerts`                 | Regulatory alerts                |
| POST   | `/api/alerts/{id}/dismiss`    | Dismiss an alert                 |
| POST   | `/api/scrape/trigger`         | Manually trigger scrape          |
| GET    | `/api/scrape/status`          | Last run metadata                |
| GET    | `/api/search?q=company+name`  | Full-text company search         |

---

## Connecting Live Data Sources

The scrapers in `backend/scraper.py` have placeholder URL paths. To connect to live sources:

| Scraper        | Update in `scraper.py`              | Live URL                          |
|----------------|-------------------------------------|-----------------------------------|
| `IPAScraper`   | `SEARCH_PATH`, `FOREIGN_CERT_PATH`  | https://www.ipa.com.pg            |
| `GazetteScraper` | `NOTICES_PATH`                   | https://www.gazette.com.pg        |
| `NPCScraper`   | `AWARDS_PATH`                       | https://www.npc.gov.pg            |
| `NewsScraper`  | `NEWS_PATH`                         | https://www.pngbusinessnews.com   |

Update the CSS selectors in each `scrape()` method to match the live HTML structure.

---

## Scrape Schedule

Default: every **60 minutes** (set `SCRAPE_INTERVAL_MINUTES` env var to change).

Trigger manually via `POST /api/scrape/trigger` or the **Refresh** button in the UI.

---

## License

MIT — built for transparency, accountability, and citizen empowerment in Papua New Guinea.
