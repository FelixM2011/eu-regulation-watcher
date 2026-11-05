---
name: eu-regulation-watcher
category: research
version: 1.0.0
author: Felix Morocutti (https://github.com/FelixM2011)
description: Better-Regulation watcher for new EU regulation initiatives.
metadata:
  hermes:
    tags: [eu, regulation, consultations, better-regulation, watcher]
    related_skills: []
---

## When to Use
Use when asked which current/newest EU legislative or regulatory initiatives are currently open for public comment ("Have your say"). The skill's script fetches the newest announced measures from the official Better-Regulation "Have your say" portal, formats them as a readable German Markdown digest, and can be delivered via cron.

# EU Regulation Watcher

The latest announced measures at [ec.europa.eu Better Regulation – Have Your Say](https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en). This uses the public JSON API behind that SPA, so no key is required. (In German: "Regulierungsvorhaben öffentlich kommentierbar".)

## Running the digest
```bash
python3 <this-skill>/scripts/eu_regulation_watcher.py \
    [--lang de|en] [--limit 10] [--summary-limit N]
```
Stdlib only (urllib), no API key. Output is printed to stdout — suitable for cron delivery as-is.
- `--limit` number of recent items (default 10 = one page on the website, max 50).
- Output: Markdown containing status (offen/demnächst/fristerfüllt), comment period in dd.MM.yyyy format, topic area, a short dossier summary if available (English-only), and per-item link.

## Verified endpoints (November 2026)
Base `https://ec.europa.eu/info/law/better-regulation`:
- **List** `GET /brpapi/searchInitiatives?language=<ISO>&page=<n>&size=10`
  → JSON at `initiativeResultDtoPage`: each item includes `reference`, `unit`, `id` (float), `shortTitle`, `currentStatuses[]: feedbackStartDate/feedbackEndDate/receivingFeedbackStatus` (`OPEN|UPCOMING|CLOSED`), `initiativeTranslations[field/value/language]`, `topics[]{code,label}`.
- **Detail** `GET /brpapi/groupInitiatives/<intId>` → larger object, including English-only `dossierSummary`, full topic list with labels, stage, publications (no auth needed).
- **URL slug** `GET /brpapi/findInitiativePathByReference?reference=<ref>` → returns e.g. `<id>-Title-Capitalized`; the item page is `.../have-your-say/initiatives/<slug>_<lang2>`, where lang2 ∈ {de,en,fr,fi}.

## Pitfalls / Notes
- The **list does not carry any summary**; the script calls groupInitiatives per item (about 1 second each) and fails gracefully (missing summary line).
- `dossierSummary` is always **English-only**, even if you request another language; translate it when delivering in German.
- **The API slug endpoint determines URL form**: ec.europa.eu's English item URLs commonly use an additional path fragment like `_e1`; the script uses findInitiativePathByReference, so never hand-craft links (the API slug endpoint returns something like `...-purposes` and the suffix is added as needed).