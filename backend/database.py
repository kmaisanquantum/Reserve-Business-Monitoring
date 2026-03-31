"""
Async MongoDB connection via Motor.
Call init_db() once at app startup; use get_db() everywhere else.
"""
from __future__ import annotations
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import get_settings

logger = logging.getLogger("png_monitor.database")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_db() -> None:
    global _client, _db
    settings = get_settings()

    # Redact credentials for logging
    if "@" in settings.mongodb_uri:
        try:
            protocol, rest = settings.mongodb_uri.split("://", 1)
            creds, host_part = rest.split("@", 1)
            redacted_uri = f"{protocol}://****:****@{host_part}"
            logger.info(f"Connecting to MongoDB: {redacted_uri}")
        except Exception:
            logger.info("Connecting to MongoDB (URI format unexpected, redact failed)")
    else:
        logger.info(f"Connecting to MongoDB: {settings.mongodb_uri}")

    # Use certifi for SSL certificates if available
    client_kwargs = {
        "serverSelectionTimeoutMS": 5000,
    }

    try:
        import certifi
        client_kwargs["tlsCAFile"] = certifi.where()
    except ImportError:
        pass

    _client = AsyncIOMotorClient(settings.mongodb_uri, **client_kwargs)
    _db = _client.png_monitor

    # Indexes
    await _db.business_records.create_index("record_id", unique=True)
    await _db.business_records.create_index([("company_name", "text"), ("raw_text", "text")])
    await _db.business_records.create_index("scraped_at")
    await _db.business_records.create_index("ral_violation")
    await _db.business_records.create_index("is_foreign")
    await _db.business_records.create_index("province")
    await _db.reg_alerts.create_index("created_at")
    await _db.fronting_clusters.create_index("detected_at")


async def close_db() -> None:
    if _client:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised — call init_db() first.")
    return _db
