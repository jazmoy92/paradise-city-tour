#!/usr/bin/env python3
"""يحوّل visa.json الى ملف VisaBundle.gd (نسخة احتياطية داخل التطبيق).
الاستعمال:  python3 make_visa_bundle.py <visa.json> <VisaBundle.gd>
"""
import json
import sys

src, dst = sys.argv[1], sys.argv[2]
raw = open(src, encoding="utf-8").read()
data = json.loads(raw)
assert isinstance(data.get("p"), dict) and len(data["p"]) > 50, "visa.json looks wrong"
text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
# GDScript: نص بين علامتين مفردتين ('...') نحتاج نهرّب \ و '
text = text.replace("\\", "\\\\").replace("'", "\\'")
step = 3000
chunks = [text[i:i + step] for i in range(0, len(text), step)]
upd = str(data.get("updated", ""))
out = []
out.append("extends RefCounted")
out.append("# =====================================================================")
out.append("#  VisaBundle.gd  —  نسخة احتياطية من بيانات الفيزا (Passport Index) داخل التطبيق")
out.append("#  تخلي فحص الفيزا يشتغل فوراً حتى بدون نت او بدون ملف visa.json بالمستودع.")
out.append("#  اذا رفعت visa.json بمستودعك ينزّل التطبيق النسخة الاحدث ويستعملها تلقائياً.")
out.append("#  لا تعدّل هذا الملف يدوياً (مولَّد بالاداة make_visa_bundle.py).")
out.append("# =====================================================================")
out.append('const UPDATED = "%s"' % upd)
out.append("const PARTS = [")
for i, c in enumerate(chunks):
    out.append("'" + c + "'" + ("," if i < len(chunks) - 1 else ""))
out.append("]")
open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("countries:", len(data["p"]), "chunks:", len(chunks), "bytes:", len(text))
