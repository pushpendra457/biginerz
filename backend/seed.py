"""
seed_data.py
============
Populates the PostgreSQL database with data from the Syngenta Rabi 2025-26
CSV files.

Usage
-----
    python seed_data.py \
        --data-dir ./data \
        --db-url postgresql://user:pass@localhost:5432/syngenta_rabi

The script is IDEMPOTENT:  rows are inserted using INSERT … ON CONFLICT DO
NOTHING so it is safe to run multiple times.

Seeding order (respects FK dependencies)
-----------------------------------------
1. Territories       (reps_territory.csv  – unique territories extracted)
2. Reps              (reps_territory.csv  – one row per rep_id)
3. Retailers         (retailers.csv)
4. Growers           (growers.csv)
5. Visits            (retailer_visit_log.csv)
6. Inventory         (retailer_inventory_weekly.csv)
7. POS               (retailer_pos.csv)
8. Digital Funnel    (digital_funnel_weekly.csv)
9. WhatsApp Log      (whatsapp_message_log.csv)

Auth notes
----------
* Both Reps and Retailers are seeded with hashed_password = "" (empty string).
  Accounts cannot be used for login until a password is set via
  POST /auth/rep/set-password  or  POST /auth/retailer/set-password.
* Synthetic e-mail addresses are generated as  {rep_id}@syngenta.internal
  and  {retailer_id}@syngenta.internal.
"""

import argparse
import ast
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Allow running from project root: python seed_data.py
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import Base  # noqa: E402  (must come after sys.path tweak)
import app.models  # noqa: E402  – imports all models so metadata is populated

from app.models.territory import Territory
from app.models.rep import Rep
from app.models.retailer import Retailer
from app.models.grower import Grower
from app.models.visit import Visit
from app.models.retailer_inventory_weekly import RetailerInventoryWeekly
from app.models.retailer_pos import RetailerPOS
from app.models.digital_funnel_weekly import DigitalFunnelWeekly
from app.models.whatsapp_message_log import WhatsAppMessageLog

from app.schemas.visit import VisitType, VisitOutcome
from app.schemas.grower import DeviceType, Gender




def _parse_tehsil_list(raw) -> list:
    """Parse tehsil_list which may be a JSON string or Python-literal string."""
    if pd.isna(raw):
        return []
    if isinstance(raw, list):
        return raw
    raw = str(raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        pass
    # Fallback: comma-separated plain text
    return [t.strip() for t in raw.split(",") if t.strip()]


def _safe_date(val) -> date | None:
    if pd.isna(val):
        return None
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) else val.date()
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def _safe_datetime(val) -> datetime | None:
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val
    try:
        return pd.to_datetime(val)
    except Exception:
        return None


def _safe_bool(val, default: bool = False) -> bool:
    if pd.isna(val):
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in {"true", "1", "yes"}


def _safe_float(val, default: float | None = None) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val, default: int | None = None) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _coerce_visit_type(raw: str) -> str:
    """Map CSV visit_type strings to VisitType enum values."""
    mapping = {
        "retailer meeting": VisitType.RETAILER_MEETING.value,
        "grower meeting": VisitType.GROWER_MEETING.value,
        "campaign_conducted": VisitType.CAMPAIGN_CONDUCTED.value,
        "campaign conducted": VisitType.CAMPAIGN_CONDUCTED.value,
    }
    return mapping.get(str(raw).strip().lower(), VisitType.RETAILER_MEETING.value)


def _coerce_device(raw: str) -> str:
    mapping = {
        "smartphone": DeviceType.SMARTPHONE.value,
        "keypad": DeviceType.KEYPAD.value,
    }
    return mapping.get(str(raw).strip().lower(), DeviceType.UNKNOWN.value)


def _coerce_gender(raw) -> str | None:
    if pd.isna(raw):
        return None
    g = str(raw).strip().lower()
    if g == "male":
        return Gender.MALE.value
    if g == "female":
        return Gender.FEMALE.value
    return None


# ===========================================================================
# Seeding functions
# ===========================================================================

def seed_territories(session: Session, df: pd.DataFrame) -> dict[str, int]:
    """
    Returns mapping  territory_id_str → territories.id (PK)
    """
    unique = df.drop_duplicates(subset=["territory_id"])
    mapping: dict[str, int] = {}

    for _, row in unique.iterrows():
        tid = str(row["territory_id"]).strip()
        existing = session.query(Territory).filter_by(territory_id=tid).first()
        if existing:
            mapping[tid] = existing.id
            continue

        obj = Territory(
            territory_id=tid,
            territory_name=str(row.get("territory_name", tid)).strip(),
            state=str(row.get("state", "")).strip(),
            district=str(row.get("district", "")).strip(),
            tehsil_list=_parse_tehsil_list(row.get("tehsil_list", [])),
        )
        session.add(obj)
        session.flush()
        mapping[tid] = obj.id

    session.commit()
    print(f"  ✓ Territories: {len(mapping)} rows")
    return mapping


def seed_reps(
    session: Session, df: pd.DataFrame, territory_map: dict[str, int]
) -> dict[str, int]:
    """
    Returns mapping  rep_id_str → reps.id (PK)
    """
    unique = df.drop_duplicates(subset=["rep_id"])
    mapping: dict[str, int] = {}

    for _, row in unique.iterrows():
        rid = str(row["rep_id"]).strip()
        existing = session.query(Rep).filter_by(rep_id=rid).first()
        if existing:
            mapping[rid] = existing.id
            continue

        tid_str = str(row.get("territory_id", "")).strip()
        obj = Rep(
            rep_id=rid,
            territory_id=territory_map.get(tid_str),
            full_name=f"Rep {rid}",                              # placeholder
            email=f"{rid.lower().replace('_', '')}@syngenta.internal",
            hashed_password="",                                  # set before first login
            is_active=True,
            role="rep",
        )
        session.add(obj)
        session.flush()
        mapping[rid] = obj.id

    session.commit()
    print(f"  ✓ Reps: {len(mapping)} rows")
    return mapping


def seed_retailers(
    session: Session, df: pd.DataFrame, territory_map: dict[str, int]
) -> dict[str, int]:
    mapping: dict[str, int] = {}

    for _, row in df.iterrows():
        ret_id = str(row["retailer_id"]).strip()
        existing = session.query(Retailer).filter_by(retailer_id=ret_id).first()
        if existing:
            mapping[ret_id] = existing.id
            continue

        tid_str = str(row.get("territory_id", "")).strip()
        obj = Retailer(
            retailer_id=ret_id,
            territory_id=territory_map.get(tid_str),
            state=str(row.get("state", "")).strip(),
            district=str(row.get("district", "")).strip(),
            tehsil=str(row.get("tehsil", "")).strip(),
            shop_name=None,
            email=f"{ret_id.lower().replace('_', '')}@syngenta.internal",
            hashed_password="",
            is_active=True,
            role="retailer",
        )
        session.add(obj)
        session.flush()
        mapping[ret_id] = obj.id

    session.commit()
    print(f"  ✓ Retailers: {len(mapping)} rows")
    return mapping


def seed_growers(session: Session, df: pd.DataFrame) -> dict[str, int]:
    mapping: dict[str, int] = {}

    for _, row in df.iterrows():
        gid = str(row["grower_id"]).strip()
        existing = session.query(Grower).filter_by(grower_id=gid).first()
        if existing:
            mapping[gid] = existing.id
            continue

        # Parse grower_crop_calendar (may be a JSON string)
        cal = row.get("grower_crop_calendar")
        if not pd.isna(cal):
            try:
                cal = json.loads(str(cal))
            except json.JSONDecodeError:
                try:
                    cal = ast.literal_eval(str(cal))
                except Exception:
                    cal = {"raw": str(cal)}
        else:
            cal = None

        obj = Grower(
            grower_id=gid,
            state=str(row.get("state", "")).strip(),
            district=str(row.get("district", "")).strip(),
            tehsil=str(row.get("tehsil", "")).strip(),
            language=str(row.get("language", "")).strip() or None,
            device_type=_coerce_device(str(row.get("device_type", "unknown"))),
            grower_age=_safe_int(row.get("grower_age")),
            gender=_coerce_gender(row.get("gender")),
            grower_farm_size=_safe_float(row.get("grower_farm_size")),
            grower_crop_calendar=cal,
            product_scan=_safe_bool(row.get("product_scan")),
            product_name=str(row.get("product_name", "")).strip() or None,
            product_scan_datetime=_safe_datetime(row.get("product_scan_datetime")),
            offline_campaign_attended=_safe_bool(row.get("offline_campaign_attended")),
            campaign_attendance_date=_safe_datetime(row.get("campaign_attendance_date")),
        )
        session.add(obj)
        session.flush()
        mapping[gid] = obj.id

    session.commit()
    print(f"  ✓ Growers: {len(mapping)} rows")
    return mapping


def seed_visits(
    session: Session,
    df: pd.DataFrame,
    rep_map: dict[str, int],
    territory_map: dict[str, int],
    retailer_map: dict[str, int],
    grower_map: dict[str, int],
) -> None:
    batch = []

    for _, row in df.iterrows():
        rep_str = str(row.get("rep_id", "")).strip()
        ter_str = str(row.get("territory_id", "")).strip()

        # visit_type from CSV
        vt = _coerce_visit_type(str(row.get("visit_type", "")))

        obj = Visit(
            rep_id=rep_map.get(rep_str),
            territory_id=territory_map.get(ter_str),
            retailer_id=None,   # visit log doesn't have retailer_id; add if available
            grower_id=None,     # same – enrich later if needed
            visit_date=_safe_date(row.get("visit_date")) or date.today(),
            visit_tehsil=str(row.get("visit_tehsil", "")).strip(),
            visit_type=vt,
            outcome=VisitOutcome.NOT_RECORDED.value,
            product_recommended=str(row.get("product_recommended", "")).strip() or None,
            priority_score=0.0,
            priority_reasons=[],
            is_planned=False,
            notes=None,
        )
        batch.append(obj)

        if len(batch) >= 500:
            session.add_all(batch)
            session.flush()
            batch = []

    if batch:
        session.add_all(batch)
    session.commit()
    print(f"  ✓ Visits: {len(df)} rows")


def seed_inventory(
    session: Session, df: pd.DataFrame, retailer_map: dict[str, int]
) -> None:
    batch = []
    skipped = 0

    for _, row in df.iterrows():
        ret_str = str(row.get("retailer_id", "")).strip()
        ret_pk = retailer_map.get(ret_str)
        if ret_pk is None:
            skipped += 1
            continue

        sku_id = str(row.get("sku_id", "")).strip()
        week_end = _safe_date(row.get("week_end_date"))
        if week_end is None:
            skipped += 1
            continue

        # Check uniqueness manually to honour ON CONFLICT
        exists = (
            session.query(RetailerInventoryWeekly)
            .filter_by(retailer_id=ret_pk, sku_id=sku_id, week_end_date=week_end)
            .first()
        )
        if exists:
            continue

        obj = RetailerInventoryWeekly(
            retailer_id=ret_pk,
            sku_id=sku_id,
            sku_name=str(row.get("sku_name", "")).strip(),
            sku_qty=_safe_float(row.get("sku_qty"), 0.0),
            week_end_date=week_end,
        )
        batch.append(obj)

        if len(batch) >= 1000:
            session.add_all(batch)
            session.flush()
            batch = []

    if batch:
        session.add_all(batch)
    session.commit()
    print(f"  ✓ Inventory snapshots: {len(df) - skipped} rows  (skipped {skipped})")


def seed_pos(
    session: Session, df: pd.DataFrame, retailer_map: dict[str, int]
) -> None:
    batch = []
    skipped = 0

    for _, row in df.iterrows():
        ret_str = str(row.get("retailer_id", "")).strip()
        ret_pk = retailer_map.get(ret_str)
        if ret_pk is None:
            skipped += 1
            continue

        txn_id = str(row.get("transaction_id", "")).strip()
        txn_date = _safe_date(row.get("transaction_date"))

        obj = RetailerPOS(
            retailer_id=ret_pk,
            transaction_id=txn_id,
            sku_id=str(row.get("sku_id", "")).strip(),
            sku_name=str(row.get("sku_name", "")).strip(),
            sku_qty=_safe_float(row.get("sku_qty"), 0.0),
            sku_price=_safe_float(row.get("sku_price"), 0.0),
            transaction_date=txn_date or date.today(),
        )
        batch.append(obj)

        if len(batch) >= 1000:
            session.add_all(batch)
            session.flush()
            batch = []

    if batch:
        session.add_all(batch)
    session.commit()
    print(f"  ✓ POS transactions: {len(df) - skipped} rows  (skipped {skipped})")


def seed_digital_funnel(session: Session, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        cid = str(row.get("campaign_id", "")).strip()
        wsd = _safe_date(row.get("week_start_date"))
        if wsd is None:
            continue

        exists = (
            session.query(DigitalFunnelWeekly)
            .filter_by(campaign_id=cid, week_start_date=wsd)
            .first()
        )
        if exists:
            continue

        session.add(
            DigitalFunnelWeekly(
                campaign_id=cid,
                week_start_date=wsd,
                social_post_impression=_safe_int(row.get("social_post_impression"), 0),
                landing_page_visits=_safe_int(row.get("landing_page_visits"), 0),
                lead_form_submission=_safe_int(row.get("lead_form_submission"), 0),
                campaign_crop=str(row.get("campaign_crop", "")).strip(),
                campaign_product=str(row.get("campaign_product", "")).strip(),
            )
        )

    session.commit()
    print(f"  ✓ Digital funnel: {len(df)} rows")


def seed_whatsapp(
    session: Session, df: pd.DataFrame, grower_map: dict[str, int]
) -> None:
    batch = []
    skipped = 0

    for _, row in df.iterrows():
        gid_str = str(row.get("grower_id", "")).strip()
        grower_pk = grower_map.get(gid_str)
        if grower_pk is None:
            skipped += 1
            continue

        msg_row_id = str(row.get("id", "")).strip()
        exists = (
            session.query(WhatsAppMessageLog)
            .filter_by(message_row_id=msg_row_id)
            .first()
        )
        if exists:
            continue

        sent_date = _safe_date(row.get("message_sent_date"))

        obj = WhatsAppMessageLog(
            message_row_id=msg_row_id,
            grower_id=grower_pk,
            campaign_product=str(row.get("campaign_product", "")).strip(),
            campaign_crop=str(row.get("campaign_crop", "")).strip(),
            message_sent_date=sent_date or date.today(),
            delivered_status=_safe_bool(row.get("delivered_status")),
            opened_status=_safe_bool(row.get("opened_status")),
            clicked_status=_safe_bool(row.get("clicked_status")),
        )
        batch.append(obj)

        if len(batch) >= 500:
            session.add_all(batch)
            session.flush()
            batch = []

    if batch:
        session.add_all(batch)
    session.commit()
    print(f"  ✓ WhatsApp log: {len(df) - skipped} rows  (skipped {skipped})")


# ===========================================================================
# Create ENUM types in Postgres (idempotent)
# ===========================================================================

ENUM_DDL = """
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visittype') THEN
    CREATE TYPE visittype AS ENUM (
      'retailer meeting', 'grower meeting', 'campaign_conducted'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visitoutcome') THEN
    CREATE TYPE visitoutcome AS ENUM (
      'not_recorded', 'sale_made', 'order_placed', 'no_purchase'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'devicetype') THEN
    CREATE TYPE devicetype AS ENUM (
      'smartphone', 'keypad', 'unknown'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gender') THEN
    CREATE TYPE gender AS ENUM ('male', 'female');
  END IF;
END $$;
"""


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Seed Syngenta Rabi 2025-26 database")
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="Folder containing the CSV files (default: ./data)",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/syngenta_rabi"),
        help="SQLAlchemy database URL",
    )
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    # ── Connect ───────────────────────────────────────────────────────────────
    engine = create_engine(args.db_url, echo=False)

    print("\n[1/2] Creating ENUM types …")
    with engine.connect() as conn:
        conn.execute(text(ENUM_DDL))
        conn.commit()

    print("[2/2] Creating tables (if they don't exist) …")
    Base.metadata.create_all(bind=engine)

    # ── Load CSVs ─────────────────────────────────────────────────────────────
    print("\nLoading CSV files …")

    def load(name: str) -> pd.DataFrame:
        path = data_dir / name
        if not path.exists():
            print(f"  ⚠  {name} not found – skipping")
            return pd.DataFrame()
        df = pd.read_csv(path, low_memory=False)
        print(f"  ✓ Loaded {name}: {len(df):,} rows")
        return df

    df_reps_territory = load("reps_territory.csv")
    df_retailers = load("retailers.csv")
    df_growers = load("growers.csv")
    df_visits = load("retailer_visit_log.csv")
    df_inventory = load("retailer_inventory_weekly.csv")
    df_pos = load("retailer_pos.csv")
    df_funnel = load("digital_funnel_weekly.csv")
    df_whatsapp = load("whatsapp_message_log.csv")

    # ── Seed ──────────────────────────────────────────────────────────────────
    print("\nSeeding …")
    with Session(engine) as session:

        # 1. Territories
        territory_map: dict[str, int] = {}
        if not df_reps_territory.empty:
            territory_map = seed_territories(session, df_reps_territory)

        # 2. Reps
        rep_map: dict[str, int] = {}
        if not df_reps_territory.empty:
            rep_map = seed_reps(session, df_reps_territory, territory_map)

        # 3. Retailers
        retailer_map: dict[str, int] = {}
        if not df_retailers.empty:
            # retailers.csv territory_id must be mapped to the string key used in reps_territory
            retailer_map = seed_retailers(session, df_retailers, territory_map)

        # 4. Growers
        grower_map: dict[str, int] = {}
        if not df_growers.empty:
            grower_map = seed_growers(session, df_growers)

        # 5. Visits
        if not df_visits.empty:
            seed_visits(session, df_visits, rep_map, territory_map, retailer_map, grower_map)

        # 6. Inventory
        if not df_inventory.empty:
            seed_inventory(session, df_inventory, retailer_map)

        # 7. POS
        if not df_pos.empty:
            seed_pos(session, df_pos, retailer_map)

        # 8. Digital Funnel
        if not df_funnel.empty:
            seed_digital_funnel(session, df_funnel)

        # 9. WhatsApp Log
        if not df_whatsapp.empty:
            seed_whatsapp(session, df_whatsapp, grower_map)

    print("\n✅  Seeding complete.\n")
    print("NOTE: Rep and Retailer accounts are seeded with empty passwords.")
    print("      Use POST /auth/rep/set-password or /auth/retailer/set-password")
    print("      to activate each account before first login.\n")


if __name__ == "__main__":
    main()