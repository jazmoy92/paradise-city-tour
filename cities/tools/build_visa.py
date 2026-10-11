#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_visa.py  —  يبني ملف  visa.json  (شروط الفيزا حسب جواز المسافر) بحجم صغير.
المصدر: مشروع Passport Index Data (رخصة MIT):  https://github.com/imorte/passport-index-data
الاستعمال اليدوي (اختياري):
    python tools/build_visa.py                      # يحمّل اخر نسخة من الانترنت
    python tools/build_visa.py passport-index.json  # او من ملف عندك
المخرج: visa.json بجذر المستودع.
"""
import json
import os
import re
import sys
import time
import urllib.request

BASE = "https://raw.githubusercontent.com/imorte/passport-index-data/main/"
OUT = "visa.json"
KEYS = {"visa free": "vf", "visa on arrival": "voa", "eta": "eta", "e-visa": "ev"}
PLAIN = {"visa required": "vr", "no admission": "na"}


def load(src):
    if src and os.path.isfile(src):
        with open(src, "r", encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(BASE + "passport-index.json", headers={"User-Agent": "paradise-city-tour"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def data_date():
    """تاريخ آخر تحديث للمصدر من ملف README عنده (اذا فشل: تاريخ اليوم)."""
    try:
        req = urllib.request.Request(BASE + "README.md", headers={"User-Agent": "paradise-city-tour"})
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode("utf-8")
        m = re.search(r"Last updated:\s*\*{0,2}\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", txt)
        if m:
            t = time.strptime("%s %s %s" % (m.group(1), m.group(2)[:3], m.group(3)), "%d %b %Y")
            return time.strftime("%Y-%m-%d", t)
    except Exception:
        pass
    return time.strftime("%Y-%m-%d", time.gmtime())


def build(raw, date):
    out = {}
    for p, dests in sorted(raw.items()):
        row = {}
        grp = {}
        plain = {}
        for d, v in sorted(dests.items()):
            if d == p or not isinstance(v, dict):
                continue
            st = str(v.get("status", "")).strip().lower()
            if st in KEYS:
                days = v.get("days")
                dk = str(int(days)) if isinstance(days, (int, float)) else "0"
                grp.setdefault(KEYS[st], {}).setdefault(dk, []).append(d)
            elif st in PLAIN:
                plain.setdefault(PLAIN[st], []).append(d)
        for k, m in grp.items():
            row[k] = {dk: ",".join(codes) for dk, codes in sorted(m.items(), key=lambda x: int(x[0]))}
        for k, codes in plain.items():
            row[k] = ",".join(codes)
        out[p] = row
    return {
        "v": 1,
        "updated": date,
        "src": "Passport Index (passportindex.org) via imorte/passport-index-data",
        "p": out,
    }


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else ""
    date = sys.argv[2] if len(sys.argv) > 2 else data_date()
    raw = load(src)
    res = build(raw, date)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    print("تم: %d جواز، حجم الملف %.1f KB، تاريخ البيانات %s" % (len(res["p"]), os.path.getsize(OUT) / 1024.0, date))


if __name__ == "__main__":
    main()
