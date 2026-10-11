#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
optimize_images.py  —  يصغّر ويضغط صور المستودع حتى تنزل بالتطبيق أسرع بكثير.

شنو يسوي (بدون ما يغيّر اسم أي ملف ولا امتداده، فروابط الصور بملفات JSON تبقى شغالة):
  • الصورة اللي أكبر من 1600 بكسل بأطول ضلع  ->  تتصغّر إلى 1600
  • JPG  -> يعاد حفظه بجودة 80 (تقريباً ما تنلاحظ) + progressive
  • PNG  -> يتحسّن الضغط؛ والصور الكبيرة الغير شفافة (اكثر من 450KB) تنضغط ألوانها (256 لون)
  • WEBP -> يعاد حفظه بجودة 80
  • الملف يتبدّل فقط إذا صار اصغر بوضوح. الملفات الصغيرة (اقل من 200KB) ما تنلمس.
  • تشغيله مرة ثانية على نفس الصور = ما يغيّر شي (آمن).

الاستعمال (تلقائي): ملف  .github/workflows/optimize_images.yml  يشغّله لحاله لما ترفع صور جديدة.
الاستعمال اليدوي (اختياري):   pip install pillow   ثم   python tools/optimize_images.py        (من جذر المستودع)
"""
import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    print("نحتاج مكتبة Pillow:  pip install pillow")
    sys.exit(1)

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
MAX_DIM = int(os.environ.get("PCT_MAX_DIM", "1600"))          # أطول ضلع
MIN_BYTES = int(os.environ.get("PCT_MIN_BYTES", "204800"))    # اقل من هذا الحجم ما نلمسه (200KB)
JPG_QUALITY = int(os.environ.get("PCT_JPG_QUALITY", "80"))
PNG_QUANTIZE_OVER = int(os.environ.get("PCT_PNG_QUANTIZE_OVER", "460800"))  # 450KB
KEEP_RATIO = 0.92                                              # نبدّل الملف فقط إذا صار اقل من 92% من حجمه
SKIP_DIRS = {".git", ".github", "tools", "samples", "node_modules"}
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def has_real_alpha(im):
    if im.mode in ("RGBA", "LA"):
        a = im.getchannel("A")
        lo, _hi = a.getextrema()
        return lo < 250
    if im.mode == "P" and "transparency" in im.info:
        return True
    return False


def optimize(path):
    ext = os.path.splitext(path)[1].lower()
    old = os.path.getsize(path)
    try:
        im = Image.open(path)
        im.load()
    except Exception as exc:
        print("  ! تجاهلنا (ما انفتح):", path, "->", exc)
        return 0
    im = ImageOps.exif_transpose(im)
    w, h = im.size
    big_dim = max(w, h) > MAX_DIM
    if old < MIN_BYTES and not big_dim:
        return 0
    if big_dim:
        k = MAX_DIM / float(max(w, h))
        im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    tmp = path + ".opt_tmp"
    try:
        if ext in (".jpg", ".jpeg"):
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            im.save(tmp, "JPEG", quality=JPG_QUALITY, optimize=True, progressive=True)
        elif ext == ".webp":
            im.save(tmp, "WEBP", quality=JPG_QUALITY, method=6)
        else:  # png
            alpha = has_real_alpha(im)
            if not alpha and old > PNG_QUANTIZE_OVER:
                q = im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
                q.save(tmp, "PNG", optimize=True)
            else:
                if im.mode == "P":
                    im = im.convert("RGBA" if alpha else "RGB")
                im.save(tmp, "PNG", optimize=True)
        new = os.path.getsize(tmp)
        if big_dim or new < old * KEEP_RATIO:
            if new < old or big_dim:
                os.replace(tmp, path)
                print("  ✓ %-60s %7.0f KB -> %7.0f KB" % (path[-60:], old / 1024.0, new / 1024.0))
                return old - new
        os.remove(tmp)
    except Exception as exc:
        print("  ! فشل ضغط:", path, "->", exc)
        if os.path.exists(tmp):
            os.remove(tmp)
    return 0


def main():
    saved = 0
    count = 0
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in sorted(fns):
            if os.path.splitext(fn)[1].lower() in EXTS:
                s = optimize(os.path.join(dp, fn))
                if s:
                    count += 1
                    saved += s
    print("تم: %d صورة انضغطت، وفّرنا %.1f MB" % (count, saved / 1048576.0))


if __name__ == "__main__":
    main()
