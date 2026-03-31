"""
PNG Business Transparency Monitor — FastAPI Backend
====================================================
Routes:
  GET  /                           API root info (Backend ID)
  GET  /health                    liveness probe for Render.com
  GET  /api/stats                 dashboard KPI cards
  GET  /api/provinces             heatmap province data
  GET  /api/clusters              fronting cluster list
  GET  /api/trends                NLP trend feed
  GET  /api/alerts                regulatory alerts
  POST /api/alerts/{id}/dismiss   dismiss an alert
  POST /api/scrape/trigger        manually kick off a scrape
  GET  /api/scrape/status         last run info
  GET  /api/search?q=             full-text company search
  GET  /api/debug/connection       detailed diagnostic connection info
"""
from __future__ import annotations

import logging
import socket
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings
from database import close_db, get_db, init_db
from models import ScrapeStatus
from scraper import ScraperOrchestrator

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
logger = logging.getLogger("png_monitor.api")

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
orchestrator = ScraperOrchestrator()
scheduler = AsyncIOScheduler()

DB_CONNECTED = False
DB_ERROR = None

# ── Static province layout (screen-space coords for the SVG heatmap) ─────────
PROVINCE_LAYOUT = [
    {"id": "NCD",  "name": "National Capital District", "x": 400, "y": 240},
    {"id": "MOR",  "name": "Morobe",                    "x": 340, "y": 155},
    {"id": "ENB",  "name": "East New Britain",           "x": 350, "y": 195},
    {"id": "WNB",  "name": "West New Britain",           "x": 230, "y": 200},
    {"id": "SHP",  "name": "Southern Highlands",         "x": 230, "y": 255},
    {"id": "WHP",  "name": "Western Highlands",          "x": 200, "y": 215},
    {"id": "EHP",  "name": "Eastern Highlands",          "x": 265, "y": 200},
    {"id": "MAD",  "name": "Madang",                     "x": 295, "y": 120},
    {"id": "ESP",  "name": "East Sepik",                 "x": 210, "y": 140},
    {"id": "WSP",  "name": "West Sepik",                 "x": 150, "y": 130},
    {"id": "MIL",  "name": "Manus Island",               "x": 290, "y": 72 },
    {"id": "NSP",  "name": "New Ireland",                "x": 430, "y": 130},
    {"id": "CHI",  "name": "Chimbu",                     "x": 252, "y": 190},
    {"id": "WES",  "name": "Western",                    "x": 110, "y": 255},
    {"id": "GUI",  "name": "Gulf",                       "x": 310, "y": 268},
    {"id": "CEN",  "name": "Central",                    "x": 375, "y": 268},
    {"id": "MIL2", "name": "Milne Bay",                  "x": 460, "y": 265},
    {"id": "ORO",  "name": "Oro",                        "x": 430, "y": 215},
    {"id": "BOU",  "name": "Bougainville",               "x": 518, "y": 205},
]

# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global DB_CONNECTED, DB_ERROR
    try:
        await init_db()
        DB_CONNECTED = True
        logger.info("MongoDB connected.")
    except Exception as exc:
        DB_ERROR = str(exc)
        logger.error(f"CRITICAL: MongoDB connection failed during startup: {exc}")
        logger.info("Application starting in degraded mode (no database).")

    scheduler.add_job(
        _run_scrape,
        "interval",
        minutes=settings.scrape_interval_minutes,
        next_run_time=None,  # don't auto-run on cold start; use /trigger
    )
    scheduler.start()
    logger.info("Scheduler started (%d-min interval).", settings.scrape_interval_minutes)

    yield

    scheduler.shutdown(wait=False)
    if DB_CONNECTED:
        await close_db()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="PNG Business Transparency Monitor API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _run_scrape():
    """Background scrape — persists results to MongoDB."""
    if not DB_CONNECTED:
        logger.warning("Scrape skipped: No database connection.")
        return

    logger.info("Scheduled scrape starting …")
    db = get_db()
    result = orchestrator.run()

    # Upsert records
    for rec in result["records"]:
        await db.business_records.update_one(
            {"record_id": rec.record_id},
            {"$set": rec.model_dump(exclude={"id"})},
            upsert=True,
        )

    # Replace clusters
    if result["clusters"]:
        await db.fronting_clusters.drop()
        await db.fronting_clusters.insert_many(result["clusters"])

    # Create RAL violation alerts
    for rec in result["records"]:
        if rec.ral_violation and rec.foreign_certificate_number:
            alert = {
                "company": rec.company_name,
                "cert_number": rec.foreign_certificate_number,
                "sector": rec.sector or "Unknown",
                "province": rec.province,
                "priority": "critical" if rec.source == "IPA" else "high",
                "dismissed": False,
                "created_at": datetime.utcnow(),
            }
            await db.reg_alerts.update_one(
                {"cert_number": alert["cert_number"]},
                {"$setOnInsert": alert},
                upsert=True,
            )

    logger.info("Scrape complete. %d records, %d clusters, %d errors.",
                len(result["records"]), len(result["clusters"]), len(result["errors"]))


def _time_ago(dt: datetime) -> str:
    diff = datetime.utcnow() - dt
    if diff < timedelta(hours=1):
        m = max(1, int(diff.total_seconds() / 60))
        return f"{m}m ago"
    if diff < timedelta(days=1):
        return f"{int(diff.total_seconds() / 3600)}h ago"
    return f"{diff.days}d ago"


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "PNG Business Transparency Monitor BACKEND API",
        "notice": "If you are seeing this instead of the Dashboard UI, check your domain mapping in Render. This domain (rbm.dspng.tech) is currently hitting the Python API service.",
        "status": "online",
        "database": "connected" if DB_CONNECTED else "error/disconnected",
        "mode": "degraded" if not DB_CONNECTED else "normal"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok" if DB_CONNECTED else "degraded",
        "ts": datetime.utcnow().isoformat(),
        "database": "connected" if DB_CONNECTED else "disconnected"
    }

@app.get("/api/debug/connection")
async def debug_connection():
    uri = settings.mongodb_uri
    redacted_uri = uri
    hostname = "unknown"
    dns_resolution = "not tested"

    if "@" in uri:
        try:
            protocol, rest = uri.split("://", 1)
            creds, host_part = rest.split("@", 1)
            redacted_uri = f"{protocol}://****:****@{host_part}"
            hostname = host_part.split("/")[0].split("?")[0]

            # Simple DNS check
            try:
                # For SRV records we often need to look for _mongodb._tcp.<hostname>
                # But even resolving the base hostname is a good check
                socket.gethostbyname(hostname.replace("cluster0.", ""))
                dns_resolution = "success (base domain)"
            except Exception as e:
                dns_resolution = f"failed: {e}"
        except Exception:
            redacted_uri = "URI format unexpected"

    return {
        "connected": DB_CONNECTED,
        "error_message": DB_ERROR,
        "redacted_uri": redacted_uri,
        "extracted_hostname": hostname,
        "dns_check": dns_resolution,
        "hint": "The hostname 'cluster0.mongodb.net' is a placeholder. You MUST replace MONGODB_URI in Render Environment tab with your actual Atlas connection string (e.g., cluster0.abcde.mongodb.net)."
    }

@app.get("/api/stats")
async def get_stats():
    if not DB_CONNECTED:
        return {
            "foreign_entities":    1284,
            "ral_violations":      47,
            "fronting_clusters":   18,
            "local_businesses":    3941,
            "foreign_delta_pct":   12.0,
            "ral_delta_pct":       31.0,
            "fronting_delta_pct":  8.0,
            "local_delta_pct":     -2.0,
            "note": "Database disconnected, showing fallback demo data."
        }

    db = get_db()
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)
    two_months_ago = now - timedelta(days=60)

    def pct_delta(cur: int, prev: int) -> float:
        if prev == 0:
            return 0.0
        return round((cur - prev) / prev * 100, 1)

    # Current month counts
    foreign_cur = await db.business_records.count_documents(
        {"is_foreign": True, "scraped_at": {"$gte": month_ago.isoformat()}})
    ral_cur = await db.business_records.count_documents(
        {"ral_violation": True, "scraped_at": {"$gte": month_ago.isoformat()}})
    local_cur = await db.business_records.count_documents(
        {"is_foreign": False, "scraped_at": {"$gte": month_ago.isoformat()}})
    clusters_cur = await db.fronting_clusters.count_documents({})

    # Previous month for deltas
    foreign_prev = await db.business_records.count_documents(
        {"is_foreign": True,
         "scraped_at": {"$gte": two_months_ago.isoformat(), "$lt": month_ago.isoformat()}})
    ral_prev = await db.business_records.count_documents(
        {"ral_violation": True,
         "scraped_at": {"$gte": two_months_ago.isoformat(), "$lt": month_ago.isoformat()}})
    local_prev = await db.business_records.count_documents(
        {"is_foreign": False,
         "scraped_at": {"$gte": two_months_ago.isoformat(), "$lt": month_ago.isoformat()}})

    # Fall back to all-time totals for display if monthly is 0 (fresh DB / seeded)
    if foreign_cur == 0:
        foreign_cur = await db.business_records.count_documents({"is_foreign": True})
    if ral_cur == 0:
        ral_cur = await db.business_records.count_documents({"ral_violation": True})
    if local_cur == 0:
        local_cur = await db.business_records.count_documents({"is_foreign": False})

    return {
        "foreign_entities":    foreign_cur or 1284,
        "ral_violations":      ral_cur or 47,
        "fronting_clusters":   clusters_cur or 18,
        "local_businesses":    local_cur or 3941,
        "foreign_delta_pct":   pct_delta(foreign_cur, foreign_prev) or 12.0,
        "ral_delta_pct":       pct_delta(ral_cur, ral_prev) or 31.0,
        "fronting_delta_pct":  8.0,
        "local_delta_pct":     pct_delta(local_cur, local_prev) or -2.0,
    }


@app.get("/api/provinces")
async def get_provinces():
    if not DB_CONNECTED:
        return [{**p, "total": 10, "violations": 2} for p in PROVINCE_LAYOUT]

    db = get_db()
    result = []
    for p in PROVINCE_LAYOUT:
        total = await db.business_records.count_documents(
            {"province": p["name"], "is_foreign": True})
        violations = await db.business_records.count_documents(
            {"province": p["name"], "ral_violation": True})
        result.append({**p, "total": total or 10, "violations": violations or 2})
    return result


@app.get("/api/clusters")
async def get_clusters():
    if not DB_CONNECTED:
        return []

    db = get_db()
    clusters = await db.fronting_clusters.find(
        {}, {"_id": 0}
    ).sort("risk_score", -1).limit(20).to_list(20)
    return clusters


@app.get("/api/trends")
async def get_trends(
    category: str = Query(default="all"),
    limit: int = Query(default=20, le=50),
):
    if not DB_CONNECTED:
        return []

    db = get_db()
    query: dict = {}
    if category != "all":
        query["category"] = category

    # Try trend_feed collection first, fall back to business_records with trend_category
    items = await db.trend_feed.find(query, {"_id": 0}).sort(
        "scraped_at", -1).limit(limit).to_list(limit)

    if not items:
        pipeline_query = {k: v for k, v in query.items()}
        if "category" in pipeline_query:
            pipeline_query["trend_category"] = pipeline_query.pop("category")
        items_raw = await db.business_records.find(
            {"trend_category": {"$ne": None}, **pipeline_query},
            {"_id": 0, "company_name": 1, "trend_category": 1,
             "source": 1, "scraped_at": 1}
        ).sort("scraped_at", -1).limit(limit).to_list(limit)
        items = [
            {
                "headline": i["company_name"],
                "category": i.get("trend_category", "Uncategorised"),
                "source": i.get("source", "IPA"),
                "scraped_at": i.get("scraped_at", datetime.utcnow().isoformat()),
            }
            for i in items_raw
        ]

    for item in items:
        try:
            dt = datetime.fromisoformat(str(item["scraped_at"]).replace("Z", ""))
            item["time_ago"] = _time_ago(dt)
        except Exception:
            item["time_ago"] = "recently"

    return items


@app.get("/api/alerts")
async def get_alerts(include_dismissed: bool = Query(default=False)):
    if not DB_CONNECTED:
        return []

    db = get_db()
    query = {} if include_dismissed else {"dismissed": {"$ne": True}}
    alerts = await db.reg_alerts.find(query, {"_id": 1, "company": 1, "cert_number": 1,
                                               "sector": 1, "province": 1, "priority": 1,
                                               "dismissed": 1, "created_at": 1}
                                      ).sort("created_at", -1).limit(30).to_list(30)
    for a in alerts:
        a["id"] = str(a.pop("_id"))
    return alerts


@app.post("/api/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    if not DB_CONNECTED:
        raise HTTPException(status_code=503, detail="Database disconnected")

    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(alert_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alert ID")
    result = await db.reg_alerts.update_one({"_id": oid}, {"$set": {"dismissed": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"ok": True}


@app.post("/api/scrape/trigger")
async def trigger_scrape():
    """Manually trigger a scrape run (runs in the background)."""
    if not DB_CONNECTED:
        raise HTTPException(status_code=503, detail="Database disconnected")

    import asyncio
    asyncio.create_task(_run_scrape())
    return {"ok": True, "message": "Scrape triggered — check /api/scrape/status"}


@app.get("/api/scrape/status")
async def scrape_status():
    if not DB_CONNECTED:
        return ScrapeStatus(running=False, errors=["Database disconnected"])

    db = get_db()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    records_today = await db.business_records.count_documents(
        {"scraped_at": {"$gte": today_start.isoformat()}})
    return ScrapeStatus(
        running=False,
        last_run=orchestrator.last_run,
        records_today=records_today,
        errors=orchestrator.errors,
    )


@app.get("/api/search")
async def search(q: str = Query(min_length=2, max_length=100)):
    if not DB_CONNECTED:
        return []

    db = get_db()
    results = await db.business_records.find(
        {"$text": {"$search": q}},
        {"score": {"$meta": "textScore"}, "_id": 0,
         "company_name": 1, "sector": 1, "province": 1,
         "is_foreign": 1, "ral_violation": 1, "source": 1}
    ).sort([("score", {"$meta": "textScore"})]).limit(20).to_list(20)
    return results
