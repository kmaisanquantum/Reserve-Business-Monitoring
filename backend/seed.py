"""
Seed MongoDB with realistic demo data so the dashboard works immediately
after deployment — before any live scrapes complete.

Run:  python seed.py
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
import random
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

PROVINCES = [
    ("NCD",  "National Capital District"),
    ("MOR",  "Morobe"),
    ("ENB",  "East New Britain"),
    ("WNB",  "West New Britain"),
    ("SHP",  "Southern Highlands"),
    ("WHP",  "Western Highlands"),
    ("EHP",  "Eastern Highlands"),
    ("MAD",  "Madang"),
    ("ESP",  "East Sepik"),
    ("BOU",  "Bougainville"),
    ("CEN",  "Central"),
    ("MIL2", "Milne Bay"),
    ("ORO",  "Oro"),
    ("GUI",  "Gulf"),
]

SECTORS = [
    "retail trade", "wholesale trade", "small-scale agriculture",
    "passenger transport", "cleaning services", "security services",
    "trade store", "bakery", "construction", "mining support",
    "telecommunications", "financial services", "tourism",
]

RAL = {
    "retail trade","wholesale trade","small-scale agriculture",
    "passenger transport","cleaning services","security services",
    "trade store","bakery",
}

COMPANIES = [
    ("Pacific Trade Ltd", ["Li Wei Zhang"], True),
    ("Mountain Resources PNG", ["Li Wei Zhang"], True),
    ("Highlands Supplies Co", ["Chen Xiao Ming"], True),
    ("Sunny Mart PNG", ["Huang Jian Fang"], True),
    ("Port Moresby General Goods", ["Huang Jian Fang"], True),
    ("Island Fresh Farms", ["Khor Beng Huat"], True),
    ("Coastal Agriculture Ltd", ["Khor Beng Huat"], True),
    ("Nasfund Superannuation Ltd", ["John Paska", "Mary Kapi"], False),
    ("PNG Fresh Produce Markets", ["Peter Kila", "Susan Nane"], False),
    ("Goroka SME Hub Ltd", ["David Oa", "Rebecca Yasi"], False),
    ("Momase Vanilla Exports", ["George Waim"], False),
    ("Lae Industrial Services", ["Robert Boe", "Kevin Kaia"], False),
    ("National Security Group PNG", ["Ahmad Razak"], True),
    ("Pacific Clean Services", ["Ahmad Razak"], True),
    ("Coastal Transport Services", ["Tan Sri Lim"], True),
    ("Oro Valley Farms Ltd", ["Nguyen Van Minh"], True),
    ("Coral Coast Security PNG", ["Patel Rajesh"], True),
    ("Highlands Fresh Market Co", ["Wang Lei"], True),
    ("Pacific Valley Traders Ltd", ["Zhang Fang"], True),
]

TREND_HEADLINES = [
    ("Malaysian firm acquires majority stake in Port Moresby retail chain", "Foreign Takeover", "PNG Business News"),
    ("Local SME coalition launches new agri-processing hub in Goroka", "Local Growth", "Gazette"),
    ("IPA warns of 500% increase in fronting complaints from citizen traders", "Foreign Takeover", "IPA Notice"),
    ("NPC reports skills gap in construction project management", "Skills Gap", "NPC"),
    ("PNG entrepreneur wins export licence for vanilla farming", "Local Growth", "PNG Business News"),
    ("Chinese conglomerate eyes second supermarket chain expansion", "Foreign Takeover", "Gazette"),
    ("Business Council calls for more expat skills transfer provisions", "Skills Gap", "BPNG"),
    ("Momase region farmers cooperative registers 140 new members", "Local Growth", "PNG Business News"),
    ("Foreign retailers outnumber locals in NCD trade stores — report", "Foreign Takeover", "IPA Notice"),
    ("Youth entrepreneurship program graduates 200 new PNG business owners", "Local Growth", "Gazette"),
    ("Skills shortage halts three major infrastructure projects", "Skills Gap", "NPC"),
    ("Bougainville region sees surge in foreign mining support companies", "Foreign Takeover", "PNG Business News"),
]

ALERTS_DATA = [
    ("Pacific Valley Traders Ltd", "FEC-2024-0441", "Retail Trade", "NCD", "critical"),
    ("Highlands Fresh Market Co",  "FEC-2024-0438", "Trade Store Operations", "Western Highlands", "critical"),
    ("Coral Coast Security PNG",   "FEC-2024-0432", "Security Services", "Morobe", "high"),
    ("Oro Valley Farms Ltd",       "FEC-2024-0428", "Small-Scale Agriculture", "Oro", "high"),
    ("Coastal Transport Services", "FEC-2024-0421", "Passenger Transport", "Milne Bay", "medium"),
]


async def seed():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.png_monitor

    print("Seeding business_records …")
    records = []
    for i, (name, directors, is_foreign) in enumerate(COMPANIES):
        sector = SECTORS[i % len(SECTORS)]
        province_id, province_name = PROVINCES[i % len(PROVINCES)]
        ral_violation = is_foreign and sector in RAL
        records.append({
            "record_id": f"seed_{i:04d}",
            "source": random.choice(["IPA", "Gazette", "NPC"]),
            "company_name": name,
            "directors": directors,
            "sector": sector,
            "province": province_name,
            "is_foreign": is_foreign,
            "foreign_certificate_number": f"FEC-2024-0{400+i}" if is_foreign else None,
            "ral_violation": ral_violation,
            "scraped_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
        })

    for r in records:
        await db.business_records.update_one(
            {"record_id": r["record_id"]}, {"$set": r}, upsert=True
        )

    print("Seeding trend_feed …")
    await db.trend_feed.drop()
    for i, (headline, cat, src) in enumerate(TREND_HEADLINES):
        await db.trend_feed.insert_one({
            "headline": headline,
            "category": cat,
            "source": src,
            "scraped_at": (datetime.utcnow() - timedelta(hours=i*2)).isoformat(),
        })

    print("Seeding reg_alerts …")
    await db.reg_alerts.drop()
    for company, cert, sector, province, priority in ALERTS_DATA:
        await db.reg_alerts.insert_one({
            "company": company,
            "cert_number": cert,
            "sector": sector,
            "province": province,
            "priority": priority,
            "dismissed": False,
            "created_at": datetime.utcnow().isoformat(),
        })

    print("Seeding fronting_clusters …")
    await db.fronting_clusters.drop()
    clusters = [
        {
            "trigger": "shared_director",
            "shared_value": "Li Wei Zhang",
            "companies": ["Pacific Trade Ltd", "Mountain Resources PNG", "Highlands Supplies Co"],
            "sectors": ["retail trade", "wholesale trade"],
            "risk_score": 75,
            "sa_confidence": 94,
            "detected_at": datetime.utcnow().isoformat(),
        },
        {
            "trigger": "shared_address",
            "shared_value": "14 Waigani Drive, NCD",
            "companies": ["Sunny Mart PNG", "Port Moresby General Goods"],
            "sectors": ["trade store", "market vendor"],
            "risk_score": 52,
            "sa_confidence": 87,
            "detected_at": datetime.utcnow().isoformat(),
        },
        {
            "trigger": "shared_director",
            "shared_value": "Khor Beng Huat",
            "companies": ["Island Fresh Farms", "Coastal Agriculture Ltd"],
            "sectors": ["small-scale agriculture"],
            "risk_score": 48,
            "sa_confidence": 91,
            "detected_at": datetime.utcnow().isoformat(),
        },
        {
            "trigger": "shared_address",
            "shared_value": "22 Boroko Street, NCD",
            "companies": ["Pacific Clean Services", "National Security Group PNG"],
            "sectors": ["cleaning services", "security services"],
            "risk_score": 38,
            "sa_confidence": 79,
            "detected_at": datetime.utcnow().isoformat(),
        },
    ]
    await db.fronting_clusters.insert_many(clusters)

    client.close()
    print("✅ Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
