#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_search_index.py  —  يبني ملف  search_index.json  من كل ملفات المدن بمستودع GitHub.
هذا الملف هو اللي يخلّي "البحث الشامل" بالتطبيق يلقى اي فندق او مكان او جولة باسمها بكل مدن العالم.

الاستعمال (تلقائي): ملف  .github/workflows/search_index.yml  يشغّله لحاله كل ما ترفع/تعدّل ملف مدينة.
الاستعمال اليدوي (اختياري):   python tools/build_search_index.py        (من جذر المستودع)
"""
import json
import os
import sys
import time

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
CITIES_DIR = os.path.join(ROOT, "cities")
OUT = os.path.join(ROOT, "search_index.json")
CATS = ["hotels", "places", "tours", "restaurants", "beaches", "cars", "airports"]


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # ملف خربان: نتجاهله ونكمل
        print("  ! تجاهلنا ملف غير صالح:", path, "->", exc)
        return None


def clean(s):
    return "".join(ch if ch.isalnum() else "_" for ch in str(s).strip().lower()).strip("_")


def loc3(v, fallback=""):
    """يرجّع [ar, en, tr] من نص او قاموس لغات."""
    if isinstance(v, dict):
        en = str(v.get("en", "") or "")
        ar = str(v.get("ar", "") or "")
        tr = str(v.get("tr", "") or "")
        base = en or ar or tr or fallback
        return [ar or base, en or base, tr or base]
    s = str(v).strip() if v not in (None, "") else fallback
    return [s, s, s]


def unwrap(raw, cid):
    """ملف المدينة قد يكون مباشر او داخل {"cities": {id: {...}}}."""
    if not isinstance(raw, dict):
        return {}
    want = clean(cid)
    if isinstance(raw.get("cities"), dict):
        for k, v in raw["cities"].items():
            if clean(k) == want and isinstance(v, dict):
                return v
    for k, v in raw.items():
        if clean(k) == want and isinstance(v, dict):
            return v
    return raw


def main():
    if not os.path.isdir(CITIES_DIR):
        print("ما لقينا مجلد cities/ بهذا المسار:", CITIES_DIR)
        sys.exit(1)
    cities = []
    items = []
    sections = {}
    city_names = {}
    # 1) قوائم المدن  cities/<country>.json
    for fn in sorted(os.listdir(CITIES_DIR)):
        if not fn.endswith(".json"):
            continue
        slug = clean(fn[:-5])
        data = read_json(os.path.join(CITIES_DIR, fn))
        cm = data.get("cities") if isinstance(data, dict) else None
        if not isinstance(cm, dict):
            continue
        for cid, cv in cm.items():
            if not isinstance(cv, dict):
                continue
            if cv.get("enabled", True) is False:
                continue
            nm = loc3(cv.get("names", cv.get("name")), str(cid).replace("_", " ").title())
            city_names[(slug, clean(cid))] = nm
    # 2) ملفات المدن  cities/<country>/<city>.json
    for dn in sorted(os.listdir(CITIES_DIR)):
        cdir = os.path.join(CITIES_DIR, dn)
        if not os.path.isdir(cdir):
            continue
        slug = clean(dn)
        for fn in sorted(os.listdir(cdir)):
            if not fn.endswith(".json"):
                continue
            cid = clean(fn[:-5])
            raw = read_json(os.path.join(cdir, fn))
            info = unwrap(raw, cid)
            if not info:
                continue
            nm = city_names.get((slug, cid))
            if nm is None:
                nm = loc3(info.get("names", info.get("name")), cid.replace("_", " ").title())
                city_names[(slug, cid)] = nm
            for cat in CATS:
                arr = info.get(cat)
                if not isinstance(arr, list):
                    continue
                for i, it in enumerate(arr):
                    add_item(items, slug, cid, cat, i, it)
            secs = info.get("sections")
            if isinstance(secs, list):
                for sdef in secs:
                    if not isinstance(sdef, dict):
                        continue
                    sk = clean(sdef.get("key", sdef.get("id", "")))
                    its = sdef.get("items")
                    if not sk or not isinstance(its, list):
                        continue
                    key = "x_" + sk
                    sections[key] = loc3(sdef.get("title", sdef.get("name", sk)), sk)
                    for i, it in enumerate(its):
                        add_item(items, slug, cid, key, i, it)
    for (slug, cid), nm in sorted(city_names.items()):
        cities.append([slug, cid, nm[0], nm[1], nm[2]])
    out = {"v": 1, "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cities": cities, "items": items, "sections": sections}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("تم: %d مدينة، %d عنصر، حجم الملف %.1f KB" % (len(cities), len(items), os.path.getsize(OUT) / 1024.0))


def add_item(items, slug, cid, cat, i, it):
    if not isinstance(it, dict) or it.get("enabled", True) is False:
        return
    nm = loc3(it.get("name", it.get("title")), "")
    if not (nm[0] or nm[1]):
        return
    area = loc3(it.get("area", it.get("district", "")), "")
    area_txt = (area[0] + " " + area[1]).strip()
    row = [slug, cid, cat, i, nm[0], nm[1], nm[2]]
    if area_txt:
        row.append(area_txt[:60])
    items.append(row)


if __name__ == "__main__":
    main()
