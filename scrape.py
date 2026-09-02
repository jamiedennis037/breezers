#!/usr/bin/env python3
"""Upcoming Breezers - cloud scraper (Racing Post B2B API)."""

import os
import re
import json
import sys
from datetime import datetime, timedelta, date

import urllib.request
import urllib.error

RP_API_KEY = os.environ.get("RP_API_KEY", "").strip()
RP_JWT_KEY = os.environ.get("RP_JWT_KEY", "").strip()
EXPECTED_FOALING_YEAR = 2024

DB_PATH = "breezers_db.json"
OUT_PATH = "breezer_matches.json"

COUNTRY_RE = re.compile(r"\((IRE|GB|FR|USA|GER|ITY|SPA|JPN|AUS|NZ)\)")
NONALNUM_RE = re.compile(r"[^A-Z0-9 ]")
WS_RE = re.compile(r"\s+")


def normalize(name):
    if not name:
        return ""
    x = name.upper()
    x = COUNTRY_RE.sub("", x)
    x = NONALNUM_RE.sub(" ", x)
    x = WS_RE.sub(" ", x)
    return x.strip()


def race_category(title, group_desc):
    n = f"{title} {group_desc}".lower()
    if "nursery" in n:
        return "Nursery"
    if "handicap" in n:
        return "Handicap"
    if "maiden" in n:
        return "Maiden"
    if "novice" in n:
        return "Novice"
    if "selling" in n or "seller" in n:
        return "Selling"
    if "claiming" in n or "claimer" in n:
        return "Claiming"
    if any(k in n for k in ("group", "grade", "listed", "stakes")):
        return "Black Type"
    return "Other"


def off_time(dt_str):
    try:
        d = datetime.fromisoformat(dt_str)
        h = d.hour % 12
        if h == 0:
            h = 12
        return f"{h}:{d.minute:02d}"
    except Exception:
        return ""


def api_get(url):
    req = urllib.request.Request(url, headers={
        "x-api-key": RP_API_KEY,
        "x-jwt-key": RP_JWT_KEY,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_matches_for_day(date_str, day_label, lookup):
    out = []
    print(f"  Fetching racecards for {date_str} ({day_label})...")
    try:
        meeting = api_get(f"https://api.rpb2b.io/horses/racecards/date/{date_str}")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return out

    listing = (meeting.get("data") or {}).get("list") or {}
    if not listing:
        print(f"  [WARN] No meetings for {day_label}.")
        return out

    races = []
    for course_uid, mt in listing.items():
        cc = str(mt.get("country_code") or "")
        if cc not in ("GB", "IRE"):
            continue
        course_name = mt.get("course_style_name") or mt.get("course_name") or ""
        for race in (mt.get("races") or []):
            races.append({
                "courseName": course_name,
                "region": cc,
                "raceId": race.get("race_instance_uid"),
                "title": str(race.get("race_instance_title") or ""),
                "groupDesc": str(race.get("race_group_desc") or ""),
                "offDt": str(race.get("race_datetime") or ""),
                "fieldSize": race.get("no_of_runners"),
                "ages": str(race.get("rp_ages_allowed_desc") or ""),
            })
    print(f"  GB/IRE races ({day_label}): {len(races)}")

    for r in races:
        if r["ages"] and "2yo" not in r["ages"]:
            continue
        try:
            rr = api_get(f"https://api.rpb2b.io/horses/racecards/runners/{r['raceId']}")
        except Exception as e:
            print(f"  [WARN] runners fetch failed for {r['raceId']}: {e}")
            continue
        runners = (rr.get("data") or {}).get("runners") or {}
        if not runners:
            continue

        cat = race_category(r["title"], r["groupDesc"])
        ot = off_time(r["offDt"])

        for _, run in runners.items():
            if run.get("non_runner"):
                continue
            if str(run.get("horse_age")) != "2":
                continue
            dob = run.get("horse_date_of_birth")
            foal_year = None
            if dob:
                try:
                    foal_year = datetime.fromisoformat(dob).year
                except Exception:
                    foal_year = None
            if foal_year != EXPECTED_FOALING_YEAR:
                continue
            sire = normalize(str(run.get("sire_name") or ""))
            dam = normalize(str(run.get("dam_name") or ""))
            if not sire or not dam:
                continue
            key = sire + "|" + dam
            hit = lookup.get(key)
            if not hit:
                continue
            out.append({
                "horse": str(run.get("horse_name") or ""),
                "sire": str(run.get("sire_name") or ""),
                "dam": str(run.get("dam_name") or ""),
                "foaling_year": foal_year,
                "course": r["courseName"],
                "off_time": ot,
                "off_dt": r["offDt"],
                "region": r["region"],
                "race_name": r["title"],
                "race_cat": cat,
                "field_size": str(r["fieldSize"]),
                "sale": hit.get("sale", ""),
                "lot": str(hit.get("lot", "")),
                "overall": str(hit.get("overall", "")),
                "overall_rank": str(hit.get("overall_rank", "")),
                "day": day_label,
                "match_type": "sire+dam+year",
            })
            print(f"  MATCH ({day_label}): {run.get('horse_name')} | "
                  f"{hit.get('sale')} Lot {hit.get('lot')} | {r['courseName']} {ot} | {cat}")
    return out


def match_key(m):
    return f"{m.get('horse','')}|{m.get('off_dt','')}".lower()


def main():
    if not RP_API_KEY or not RP_JWT_KEY:
        print("[ERROR] RP_API_KEY / RP_JWT_KEY not set.")
        sys.exit(1)

    with open(DB_PATH, encoding="utf-8-sig") as f:
        db = json.load(f)
    lookup = {}
    for b in db.get("breezers", []):
        s, d = b.get("sire"), b.get("dam")
        if not s or not d:
            continue
        k = s + "|" + d
        lookup.setdefault(k, b)
    print(f"Loaded {len(db.get('breezers', []))} breezers ({len(lookup)} unique sire+dam)")

    today = date.today()
    tomorrow = today + timedelta(days=1)

    results = []
    results += get_matches_for_day(today.strftime("%Y-%m-%d"), "today", lookup)
    results += get_matches_for_day(tomorrow.strftime("%Y-%m-%d"), "tomorrow", lookup)

    now = datetime.now().astimezone()
    merged = {match_key(m): m for m in results}

    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH, encoding="utf-8-sig") as f:
                prev = json.load(f)
            for pm in prev.get("matches", []):
                k = match_key(pm)
                if k in merged:
                    continue
                try:
                    rt = datetime.fromisoformat(pm.get("off_dt"))
                except Exception:
                    rt = None
                if rt and rt > now:
                    rd = rt.date()
                    if rd == today:
                        pm["day"] = "today"
                    elif rd == tomorrow:
                        pm["day"] = "tomorrow"
                    else:
                        pm["day"] = "tomorrow"
                    merged[k] = pm
                    print(f"  KEPT (carried forward): {pm.get('horse')} | "
                          f"{pm.get('course')} {pm.get('off_time')} [{pm['day']}]")
        except Exception as e:
            print(f"  [WARN] could not read previous matches: {e}")

    def sort_key(m):
        try:
            return datetime.fromisoformat(m.get("off_dt"))
        except Exception:
            return datetime.max.replace(tzinfo=now.tzinfo)

    final = sorted(merged.values(), key=sort_key)
    today_n = sum(1 for m in final if m.get("day") == "today")
    tom_n = sum(1 for m in final if m.get("day") == "tomorrow")
    print(f"Total breezer matches: {len(final)}  (today {today_n}, tomorrow {tom_n})")

    out = {
        "updated_at": now.isoformat(),
        "match_count": len(final),
        "matches": final,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Wrote breezer_matches.json")


if __name__ == "__main__":
    main()
