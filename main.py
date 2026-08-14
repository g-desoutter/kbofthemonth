#!/usr/bin/env python3
"""Extrait les KB de sécurité Windows Server du flux CVRF du MSRC."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api.msrc.microsoft.com/cvrf/v3.0/cvrf"
OUTPUT = Path("docs/kbs.json")
TARGETS = [
    "Windows Server 2016",
    "Windows Server 2019",
    "Windows Server 2022",
    "Windows Server 2025",
]
REMEDIATION_SECURITY_UPDATE = 2


def log(msg):
    print(msg, file=sys.stderr)


def previous_month(dt):
    return dt.replace(day=1) - (dt.replace(day=1) - dt.replace(day=1)).__class__(days=1) \
        if False else (dt.replace(day=1).toordinal() and _prev(dt))


def _prev(dt):
    year, month = (dt.year - 1, 12) if dt.month == 1 else (dt.year, dt.month - 1)
    return dt.replace(year=year, month=month, day=1)


def fetch_cvrf(dt):
    """Retourne le document CVRF du mois, ou None s'il n'est pas encore publié."""
    label = dt.strftime("%Y-%b")
    log(f"Fetching {label}...")
    r = requests.get(
        f"{API}/{label}",
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if r.status_code == 404:
        log(f"  {label} not published yet")
        return None
    r.raise_for_status()
    return label, r.json()


def filter_products(data):
    """Ne garde que les Windows Server ciblés, hors éditions Server Core."""
    products = {}
    for p in data["ProductTree"]["FullProductName"]:
        name = p["Value"]
        if not any(t in name for t in TARGETS):
            continue
        if "server core" in name.lower():
            continue
        products[p["ProductID"]] = name
    return products


def collect_kbs(data, products):
    """Associe à chaque produit ses KB de sécurité (hors hotpatch)."""
    kbs = {pid: set() for pid in products}
    for vuln in data.get("Vulnerability", []):
        for rem in vuln.get("Remediations", []):
            if rem.get("Type") != REMEDIATION_SECURITY_UPDATE:
                continue
            if "Hotpatch" in rem.get("SubType", ""):
                continue
            for pid in rem.get("ProductID", []):
                if pid in kbs:
                    kbs[pid].add(rem["Description"]["Value"])
    return {
        products[pid]: sorted(f"KB{kb}" for kb in kb_set)
        for pid, kb_set in sorted(kbs.items(), key=lambda i: products[i[0]])
    }


def unchanged(new_kbs, new_month):
    """Vrai si le contenu utile est identique au fichier déjà publié."""
    if not OUTPUT.exists():
        return False
    try:
        old = json.loads(OUTPUT.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return old.get("kbs") == new_kbs and old.get("month") == new_month


def main():
    now = datetime.now(timezone.utc)

    result = fetch_cvrf(now) or fetch_cvrf(_prev(now))
    if result is None:
        log("No CVRF document available for current or previous month")
        return 1

    month, data = result

    if not data.get("Vulnerability"):
        log(f"{month}: document contains no vulnerability data")
        return 1

    products = filter_products(data)
    if not products:
        log(f"{month}: no matching Windows Server products found")
        return 1

    kbs = collect_kbs(data, products)
    total = sum(len(v) for v in kbs.values())
    log(f"{month}: {len(products)} products, {total} KB references")

    if unchanged(kbs, month):
        log("No change since last run, leaving file untouched")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "month": month,
                "kbs": kbs,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    log(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
