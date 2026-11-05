#!/usr/bin/env python3
"""EU Regulation Watcher - Better Regulation 'Have your say' latest initiatives.

Endpoint (official SPA backend, no key):
  GET {BASE}/brpapi/searchInitiatives?language=<LANG>&page=<n>&size=<n>

For each item the script additionally loads:
  GET {BASE}/brpapi/groupInitiatives/<id>            -> dossierSummary (EN) + topics/stage
  GET .../brpapi/findInitiativePathByReference?...   -> canonical initiative path for web URLs

Stdlib only. Usage:
  python3 eu_regulation_watcher.py [--lang de|en|...] [--limit 10] [--summary-limit N]
"""
import argparse, json, re, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://ec.europa.eu/info/law/better-regulation"
WEB = BASE + "/have-your-say/initiatives"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126",
      "Accept": "*/*"}


def http_get(url, timeout=25):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read().decode("utf-8", "ignore")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f"Fehler bei {url}: {last}")


def fmt_date(raw):
    # "2026-11-27" (ISO date part) -> dd.MM.yyyy
    d = re.match(r"(\d{4})[-/](\d{2})[-/](\d{2})", (raw or "").strip())
    if d:
        return f"{int(d.group(3)):02d}.{int(d.group(2)):02d}.{d.group(1)}"
    return (raw or "")[:16]



def get_item_url(language, item):
    ref = item.get("reference") or ""
    path = None
    if ref:
        try:
            path = http_get(BASE + "/brpapi/findInitiativePathByReference?reference=" + urllib.parse.quote(ref)).strip()
        except SystemExit:
            pass
    if not path:  # fallback: id + title-cased slugged shortTitle (as the site builds it)
        title = item.get("shortTitle") or ""
        slug = "-".join(w.capitalize() for w in re.split(r"[\s\-]+", title.strip()) if w)
        path = f"{str(item.get('id'))}-{slug}"
    lang_suffix = language.lower()[:2]  # matches site slugs exactly for our languages (e1/de/fr/fi)
    return f"{WEB}/{urllib.parse.quote(path, safe='-')}_{lang_suffix}"

def translate_short_title(item, language):
    up = language.upper()[:2].upper()
    for t in item.get("initiativeTranslations") or []:
        if t.get("field", "").upper() == "SHORT_TITLE" and (t.get("language") or "").upper().startswith(up[:1]):
            if t.get("language").upper() == up[:2] or t.get("language").upper() == language.upper():
                return (t.get("value") or "").strip()
    for t in item.get("initiativeTranslations") or []:
        if t.get("field", "").upper() == "SHORT_TITLE" and (t.get("language") or "").upper() == language.upper():
            return (t.get("value") or "").strip()
    # fallback EN then base
    for lng in ("EN",):
        for t in item.get("initiativeTranslations") or []:
            if t.get("field", "").upper() == "SHORT_TITLE" and (t.get("language") or "").upper().startswith(lng[:1]):
                return (t.get("value") or "").strip()
    return (item.get("shortTitle") or "").strip()


def summarize(text, limit):
    text = re.sub(r"\s+", " ", text or "").strip()
    if limit and len(text) > limit:
        cut = text[:limit]
        for sep in (".", " -", ","):
            i = cut.rfind(sep)
            if i > int(limit * 0.6):
                cut = cut[:i + 1]
                break
        return cut.replace("\n", " ") + " …"
    return text


def main():
    ap = argparse.ArgumentParser(description="Latest EU Better-Regulation initiatives (Have your say)")
    ap.add_argument("--lang", default="en", help="ISO language for titles/summary labels, e.g. en de fr fi")
    ap.add_argument("--limit", type=int, default=10, help="number of newest items (default 10 = website page 1)")
    ap.add_argument("--summary-limit", type=int, default=0, help="truncate summary to N chars (0 = full text)")
    args = ap.parse_args()

    lang = args.lang.strip().lower()[:2] or "en"
    limit = max(1, min(args.limit, 50))
    pages = -(-limit // 10)
    items = []
    for p in range(pages):
        url = f"{BASE}/brpapi/searchInitiatives?language={lang.upper()}&page={p}&size=10"
        data = json.loads(http_get(url))
        page = data.get("initiativeResultDtoPage") or {}
        content = page.get("content") or []
        items.extend(content)
        if p + 1 >= page.get("totalPages", pages):
            break
    items = items[:limit]

    total = len(items)
    out = [f"# Neueste EU-Regulierungsinitiativen (Better Regulation / Have your say, Sprache: {lang.upper()})"]
    labels_open = {"OPEN": "**Stellungnahmen offen**", "UPCOMING": "demnächst offen für Stellungnahmen", "CLOSED": "Fristerfüllt"}
    for idx, item in enumerate(items, 1):
        st = (item.get("currentStatuses") or [{}])[0]
        title = translate_short_title(item, lang)
        topics = "; ".join((t.get("label") or t.get("code", "")) for t in (item.get("topics") or []))
        fb_start = fmt_date(st.get("feedbackStartDate"))
        fb_end = fmt_date(st.get("feedbackEndDate"))
        status = st.get("receivingFeedbackStatus", "?")

        summary = ""
        try:
            detail = json.loads(http_get(BASE + f"/brpapi/groupInitiatives/{int(float(item['id']))}"))
            summary = summarize(detail.get("dossierSummary"), args.summary_limit)
        except (SystemExit, ValueError, KeyError):
            pass

        url = get_item_url(lang, item)
        out.append("")
        out.append(f"**{idx}. {title}**")
        line2_bits = []
        if st.get("receivingFeedbackStatus"):
            line2_bits.append(labels_open.get(status, f"Status: {status}"))
        if fb_start and fb_end:
            line2_bits.append(f"Stellungnahmen {fb_start} – {fb_end}")
        out.append(" · ".join(line2_bits))
        if topics:
            out.append(f"**Thema:** {topics}")
        if summary:
            out.append(f"**Zusammenfassung:** {summary}")
        out.append(f"**Link:** {url}")

    print("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
