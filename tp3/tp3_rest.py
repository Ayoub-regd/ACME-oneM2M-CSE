#!/usr/bin/env python3
"""Automatisation des requêtes REST demandées dans le TP3 R505."""
from __future__ import annotations
import json
import random
import sys
import time
import requests

BASE = "http://127.0.0.1:8080"
ADMIN = "CAdmin"
AE_ORIGINATOR = "CSMART-METER"

def headers(originator: str, ty: int | None = None) -> dict[str, str]:
    h = {
        "X-M2M-Origin": originator,
        "X-M2M-RI": f"tp3-{random.randint(100000,999999)}",
        "X-M2M-RVI": "3",
        "Accept": "application/json",
    }
    if ty is not None:
        h["Content-Type"] = f"application/json;ty={ty}"
    else:
        h["Content-Type"] = "application/json"
    return h

def show(title: str, response: requests.Response) -> None:
    print("\n" + "=" * 80)
    print(title)
    print(f"{response.request.method} {response.request.url}")
    print(f"HTTP {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(response.text)
    print("=" * 80)

def req(method: str, path: str, originator: str, *, ty: int | None = None, body=None,
        ok=(200, 201, 204)) -> requests.Response:
    r = requests.request(method, BASE + path, headers=headers(originator, ty), json=body, timeout=10)
    show(f"{method} {path}", r)
    if r.status_code not in ok:
        raise RuntimeError(f"Echec {method} {path}: HTTP {r.status_code}")
    return r

def main() -> int:
    # 5a - Obtenir la CSEBase
    req("GET", "/id-in", ADMIN)

    # Nettoyage pour rendre le script relançable.
    r = requests.delete(BASE + "/cse-in/SMART-METER", headers=headers(AE_ORIGINATOR), timeout=5)
    if r.status_code in (200, 204):
        print("\nAncienne ressource SMART-METER supprimée.")
        time.sleep(1)

    # 5b - AE SMART-METER (ty=2)
    req(
        "POST", "/cse-in", AE_ORIGINATOR, ty=2,
        body={"m2m:ae": {
            "rn": "SMART-METER",
            "api": "NSMART-METER",
            "rr": True,
            "srv": ["3"],
        }}
    )

    # Container DATA (ty=3)
    req(
        "POST", "/cse-in/SMART-METER", AE_ORIGINATOR, ty=3,
        body={"m2m:cnt": {"rn": "DATA"}}
    )

    # Deux Content Instances (ty=4)
    for idx, value in ((1, 42), (2, 57)):
        req(
            "POST", "/cse-in/SMART-METER/DATA", AE_ORIGINATOR, ty=4,
            body={"m2m:cin": {
                "rn": f"MEASUREMENT_{idx}",
                "con": json.dumps({"value": value, "unit": "W"})
            }}
        )

    # 5c - Subscription (ty=23)
    req(
        "POST", "/cse-in/SMART-METER/DATA", AE_ORIGINATOR, ty=23,
        body={"m2m:sub": {
            "rn": "USER-SUBSCRIPTION",
            "nu": ["http://127.0.0.1:5000/notify"],
            "enc": {"net": [3]}
        }}
    )

    # Une nouvelle CIN après la souscription => notification attendue.
    req(
        "POST", "/cse-in/SMART-METER/DATA", AE_ORIGINATOR, ty=4,
        body={"m2m:cin": {
            "rn": "MEASUREMENT_AFTER_SUB",
            "con": json.dumps({"value": 61, "unit": "W"})
        }}
    )

    # Vérification finale.
    req("GET", "/cse-in/SMART-METER", AE_ORIGINATOR)
    req("GET", "/cse-in/SMART-METER/DATA", AE_ORIGINATOR)

    print("\n✅ Partie REST terminée : AE + CNT + CIN + SUB créés.")
    print("Vérifie aussi tp3/notifications.log pour la notification envoyée après la souscription.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\n❌ {exc}", file=sys.stderr)
        raise
