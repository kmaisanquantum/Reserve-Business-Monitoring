"""
PNG Business Transparency Monitor — Scrapers & Entity Linker
============================================================
Scrapers:   IPA Registry · National Gazette · NPC · PNG Business News
Entity Linker: graph-based shared-director / shared-address detection
SA Optimiser: Simulated Annealing to resolve overlapping fronting clusters
"""
from __future__ import annotations

import hashlib
import logging
import math
import random
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generator, Optional

import httpx
from bs4 import BeautifulSoup

from models import BusinessRecord, FrontingCluster, RAL_SECTORS

logger = logging.getLogger("png_monitor.scraper")

# ── Trend keyword patterns ─────────────────────────────────────────────────────
TREND_PATTERNS: dict[str, list[str]] = {
    "Foreign Takeover": [
        r"foreign.{0,30}(acqui|invest|expan|enter|takeover)",
        r"(chinese|australian|american|malaysian|singaporean).{0,30}(business|company|firm)",
        r"foreign.{0,20}(dominat|control|monopol)",
    ],
    "Local Growth": [
        r"local.{0,30}(entrepreneur|SME|business|owner|grow)",
        r"PNG.{0,20}(business|company|enterprise).{0,20}(grow|expand|launch)",
        r"citizen.{0,20}(business|invest)",
    ],
    "Skills Gap": [
        r"(skills|labour|workforce).{0,30}(shortage|gap|lack|training)",
        r"expatriate.{0,20}(worker|employee|skill)",
        r"local.{0,20}content.{0,20}(requirement|policy|compliance)",
    ],
}

GAZETTE_NOTICE_TYPES = [
    "foreign enterprise certificate issued",
    "company incorporated",
    "company deregistered",
    "change of directors",
    "change of registered office",
    "merger",
    "acquisition",
]


# ─────────────────────────────────────────────────────────────────────────────
# Base scraper
# ─────────────────────────────────────────────────────────────────────────────

class BaseScraper(ABC):
    base_url: str = ""
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; PNGTransparencyBot/1.0; "
            "+https://github.com/png-monitor)"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    REQUEST_DELAY: float = 1.5
    MAX_RETRIES: int = 3

    def __init__(self):
        self.client = httpx.Client(headers=self.HEADERS, timeout=15, follow_redirects=True)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get(self, url: str, params: Optional[dict] = None) -> Optional[BeautifulSoup]:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = self.client.get(url, params=params)
                resp.raise_for_status()
                time.sleep(self.REQUEST_DELAY)
                return BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                wait = 2 ** attempt
                self.logger.warning("Attempt %d/%d failed for %s — %s. Retry in %ds.",
                                    attempt, self.MAX_RETRIES, url, exc, wait)
                time.sleep(wait)
        self.logger.error("All retries exhausted for %s", url)
        return None

    @abstractmethod
    def scrape(self) -> Generator[BusinessRecord, None, None]: ...

    @staticmethod
    def clean(el) -> str:
        if el is None:
            return ""
        text = el.get_text() if hasattr(el, "get_text") else str(el)
        return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()

    @staticmethod
    def make_id(*parts: str) -> str:
        key = "|".join(p.strip().lower() for p in parts if p)
        return hashlib.sha256(key.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# IPA Registry Scraper
# ─────────────────────────────────────────────────────────────────────────────

class IPAScraper(BaseScraper):
    base_url = "https://www.ipa.com.pg"
    SEARCH_PATH = "/business-registry/search"
    FOREIGN_CERT_PATH = "/foreign-enterprise-certificates"

    def scrape(self) -> Generator[BusinessRecord, None, None]:
        yield from self._scrape_recent_registrations()
        yield from self._scrape_foreign_certificates()

    def _scrape_recent_registrations(self, pages: int = 5):
        for page in range(1, pages + 1):
            soup = self._get(self.base_url + self.SEARCH_PATH,
                             params={"page": page, "sort": "date_desc"})
            if not soup:
                break
            rows = soup.select("table.registry-table tr.company-row")
            if not rows:
                break
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                name = self.clean(cells[0])
                reg_num = self.clean(cells[1])
                sector = self.clean(cells[2]).lower()
                province = self.clean(cells[3])
                directors = [d.strip() for d in self.clean(cells[4]).split(";") if d.strip()]
                is_foreign = self._infer_foreign(row)
                yield BusinessRecord(
                    record_id=self.make_id(name, reg_num),
                    source="IPA",
                    company_name=name,
                    registration_number=reg_num,
                    directors=directors,
                    sector=sector,
                    province=province,
                    is_foreign=is_foreign,
                    ral_violation=bool(is_foreign and sector in RAL_SECTORS),
                    raw_text=row.get_text(separator=" "),
                )

    def _scrape_foreign_certificates(self, pages: int = 3):
        for page in range(1, pages + 1):
            soup = self._get(self.base_url + self.FOREIGN_CERT_PATH,
                             params={"page": page})
            if not soup:
                break
            for row in soup.select("table tr.fec-row"):
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue
                name = self.clean(cells[0])
                cert = self.clean(cells[1])
                sector = self.clean(cells[2]).lower()
                office = self.clean(cells[3])
                yield BusinessRecord(
                    record_id=self.make_id(name, cert),
                    source="IPA",
                    company_name=name,
                    foreign_certificate_number=cert,
                    sector=sector,
                    registered_office=office,
                    is_foreign=True,
                    ral_violation=sector in RAL_SECTORS,
                    raw_text=row.get_text(separator=" "),
                )

    @staticmethod
    def _infer_foreign(row: BeautifulSoup) -> Optional[bool]:
        text = row.get_text().lower()
        if "foreign enterprise" in text or "fec" in text:
            return True
        if "papua new guinea" in text or " png " in text:
            return False
        return None


# ─────────────────────────────────────────────────────────────────────────────
# National Gazette Scraper
# ─────────────────────────────────────────────────────────────────────────────

class GazetteScraper(BaseScraper):
    base_url = "https://www.gazette.com.pg"
    NOTICES_PATH = "/business-notices"

    def scrape(self) -> Generator[BusinessRecord, None, None]:
        for page in range(1, 4):
            soup = self._get(self.base_url + self.NOTICES_PATH,
                             params={"page": page, "category": "business"})
            if not soup:
                break
            for notice in soup.select("article.gazette-notice"):
                title = self.clean(notice.select_one("h2, h3, .notice-title"))
                body = self.clean(notice.select_one(".notice-body, p"))
                combined = title + " " + body
                notice_type = self._classify_notice(combined)
                company = self._extract_company(body)
                directors = self._extract_directors(body)
                address = self._extract_address(body)
                yield BusinessRecord(
                    record_id=self.make_id(company or title, body[:40]),
                    source="Gazette",
                    company_name=company or title,
                    directors=directors,
                    registered_office=address,
                    gazette_notice_type=notice_type,
                    is_foreign="foreign" in combined.lower(),
                    raw_text=body,
                )

    @staticmethod
    def _classify_notice(text: str) -> str:
        t = text.lower()
        for nt in GAZETTE_NOTICE_TYPES:
            if nt in t:
                return nt
        return "general"

    @staticmethod
    def _extract_company(text: str) -> Optional[str]:
        m = re.search(r"\b([A-Z][A-Z &'\-]{3,}(?:LIMITED|LTD|LLC|PTY|INC)?)\b", text)
        return m.group(1).title() if m else None

    @staticmethod
    def _extract_directors(text: str) -> list[str]:
        m = re.findall(
            r"(?:directors?|officer)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+(?:, [A-Z][a-z]+ [A-Z][a-z]+)*)",
            text, re.IGNORECASE)
        if not m:
            return []
        return [n.strip() for n in m[0].split(",")]

    @staticmethod
    def _extract_address(text: str) -> Optional[str]:
        m = re.search(r"registered office[:\s]+(.{10,80}?)(?:\.|,|;|\n)", text, re.IGNORECASE)
        return m.group(1).strip() if m else None


# ─────────────────────────────────────────────────────────────────────────────
# NPC Procurement Scraper
# ─────────────────────────────────────────────────────────────────────────────

class NPCScraper(BaseScraper):
    base_url = "https://www.npc.gov.pg"
    AWARDS_PATH = "/contract-awards"

    def scrape(self) -> Generator[BusinessRecord, None, None]:
        for page in range(1, 4):
            soup = self._get(self.base_url + self.AWARDS_PATH, params={"page": page})
            if not soup:
                break
            for row in soup.select("table.awards-table tr.award-row"):
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                name = self.clean(cells[0])
                sector = self.clean(cells[1]).lower()
                province = self.clean(cells[2])
                value = self.clean(cells[3])
                nationality = self.clean(cells[4]).lower()
                is_foreign = nationality not in ("png", "papua new guinea", "local")
                yield BusinessRecord(
                    record_id=self.make_id(name, value),
                    source="NPC",
                    company_name=name,
                    sector=sector,
                    province=province,
                    is_foreign=is_foreign,
                    ral_violation=bool(is_foreign and sector in RAL_SECTORS),
                    raw_text=row.get_text(separator=" "),
                )


# ─────────────────────────────────────────────────────────────────────────────
# PNG Business News NLP Scraper
# ─────────────────────────────────────────────────────────────────────────────

class NewsScraper(BaseScraper):
    base_url = "https://www.pngbusinessnews.com"
    NEWS_PATH = "/latest"

    def scrape(self) -> Generator[BusinessRecord, None, None]:
        soup = self._get(self.base_url + self.NEWS_PATH)
        if not soup:
            return
        for article in soup.select("article.news-item, div.article-card"):
            headline = self.clean(article.select_one("h2, h3, .headline"))
            excerpt = self.clean(article.select_one("p, .excerpt"))
            full = (headline + " " + excerpt).lower()
            category = self._classify(full)
            yield BusinessRecord(
                record_id=self.make_id(headline, excerpt[:50]),
                source="News",
                company_name=headline,
                trend_category=category,
                raw_text=full,
            )

    @staticmethod
    def _classify(text: str) -> str:
        for cat, patterns in TREND_PATTERNS.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    return cat
        return "Uncategorised"


# ─────────────────────────────────────────────────────────────────────────────
# Entity Linker
# ─────────────────────────────────────────────────────────────────────────────

class EntityLinker:
    def __init__(self, records: list[BusinessRecord]):
        self.records = records
        self.id_to_record: dict[str, BusinessRecord] = {r.record_id: r for r in records}

    def find_fronting_candidates(self) -> list[dict]:
        dir_idx: dict[str, list[str]] = {}
        addr_idx: dict[str, list[str]] = {}

        for r in self.records:
            for d in r.directors:
                key = d.lower().strip()
                dir_idx.setdefault(key, []).append(r.record_id)
            if r.registered_office:
                key = re.sub(r"\s+", " ", r.registered_office.lower().strip())
                addr_idx.setdefault(key, []).append(r.record_id)

        candidates: list[dict] = []

        def _add(trigger: str, shared: str, ids: list[str]):
            recs = [self.id_to_record[i] for i in ids if i in self.id_to_record]
            if not any(r.is_foreign for r in recs):
                return
            candidates.append({
                "trigger": trigger,
                "shared_value": shared,
                "companies": [r.company_name for r in recs],
                "company_ids": ids,
                "sectors": [r.sector for r in recs if r.sector],
                "risk_score": len(ids) * 10 + (
                    20 if any(r.ral_violation for r in recs) else 0),
            })

        for director, ids in dir_idx.items():
            if len(ids) >= 2:
                _add("shared_director", director, ids)
        for address, ids in addr_idx.items():
            if len(ids) >= 2:
                _add("shared_address", address, ids)

        return sorted(candidates, key=lambda c: -c["risk_score"])


# ─────────────────────────────────────────────────────────────────────────────
# Simulated Annealing — optimise cluster assignments
# ─────────────────────────────────────────────────────────────────────────────

def sa_optimise_clusters(
    candidates: list[dict],
    *,
    initial_temp: float = 100.0,
    cooling_rate: float = 0.95,
    iterations: int = 1000,
    seed: int = 42,
) -> list[dict]:
    """
    Simulated Annealing to resolve overlapping fronting clusters.

    Energy = -sum(risk_score * label) + OVERLAP_PENALTY * overlap_count
    Lower energy = better.  Metropolis acceptance: exp(-dE / T).
    """
    if not candidates:
        return []

    random.seed(seed)
    n = len(candidates)
    company_map: dict[str, list[int]] = {}
    for i, c in enumerate(candidates):
        for cid in c.get("company_ids", []):
            company_map.setdefault(cid, []).append(i)

    def energy(labels: list[int]) -> float:
        risk = sum(candidates[i]["risk_score"] * labels[i] for i in range(n))
        overlap = sum(
            max(0, sum(labels[j] for j in idxs) - 1)
            for idxs in company_map.values()
        )
        return -risk + 15.0 * overlap

    labels = [1] * n
    best_labels = labels[:]
    e = energy(labels)
    best_e = e
    T = initial_temp

    for _ in range(iterations):
        i = random.randint(0, n - 1)
        labels[i] ^= 1
        new_e = energy(labels)
        dE = new_e - e
        if dE < 0 or random.random() < math.exp(-dE / max(T, 1e-9)):
            e = new_e
            if e < best_e:
                best_e = e
                best_labels = labels[:]
        else:
            labels[i] ^= 1  # revert
        T *= cooling_rate

    confirmed = [candidates[i] for i in range(n) if best_labels[i]]
    # Annotate with SA confidence (heuristic based on risk vs temperature)
    for c in confirmed:
        c["sa_confidence"] = min(99, 70 + int(c["risk_score"] / 5))

    logger.info("SA: %d/%d clusters confirmed (energy=%.2f)", len(confirmed), n, best_e)
    return confirmed


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class ScraperOrchestrator:
    def __init__(self):
        self.scrapers: list[BaseScraper] = [
            IPAScraper(),
            GazetteScraper(),
            NPCScraper(),
            NewsScraper(),
        ]
        self.last_run: Optional[datetime] = None
        self.errors: list[str] = []

    def run(self) -> dict:
        all_records: list[BusinessRecord] = []
        self.errors = []

        for scraper in self.scrapers:
            name = scraper.__class__.__name__
            try:
                records = list(scraper.scrape())
                all_records.extend(records)
                logger.info("%s: %d records", name, len(records))
            except Exception as exc:
                msg = f"{name}: {exc}"
                logger.exception("Scraper failed — %s", msg)
                self.errors.append(msg)

        linker = EntityLinker(all_records)
        raw = linker.find_fronting_candidates()
        clusters = sa_optimise_clusters(raw)

        self.last_run = datetime.utcnow()
        return {"records": all_records, "clusters": clusters, "errors": self.errors}
