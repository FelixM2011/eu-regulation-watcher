# EU Regulation Watcher 🇪🇺📋

A [Hermes agent skill](https://hermes-agent.nousresearch.com/docs) that monitors new EU regulatory initiatives on the official **Better-Regulation „Have your say"** portal, lists the newest measures whose public comment period is open (or opening soon), reads each proposal's dossier summary from Commission data directly, and delivers a compact German Markdown digest with direct links to every initiative.

> Author: Felix [Morocutti](https://github.com/FelixM2011) · License: [MIT](LICENSE)

## What it does

- Queries the public JSON API behind `ec.europa.eu` Better Regulations – Have Your Say (**no key, stdlib only**)
- Fetches the most recent announced measures (default 10, max 50), in German or English labels (`--lang de|en`)
- Classifies each as *offen / demnächst / fristerfüllt* and shows the exact comment period in `dd.MM.yyyy` format
- Loads every initiative detail record for: topic area + short dossier summary (Commission text, not invented — EN source, translated on delivery)
- Builds official item links via the API's canonical path endpoint

See [`references/sample-digest.md`](references/sample-digest.md) for a real sample output.

## Install (Hermes)

```bash
git clone https://github.com/FelixM2011/eu-regulation-watcher.git ~/.hermes/skills/eu-regulation-watcher
chmod +x ~/.hermes/skills/eu-regulation-watcher/scripts/eu_regulation_watcher.py
```

Required toolsets: none beyond `bash` (script is stdlib-only Python 3). Tagged in the skill frontmatter, so Hermes picks it up directly.

## Usage

- Interactively — ask e.g.: *„Welche EU-Regularien stehen gerade zur Konsultation offen?"* or *"Liste die aktuellsten Better-Regulation-Vorhaben mit Fristen"*
- As a scheduled cron job: attach this skill to a recurring job (e.g. twice weekly); when nothing new comes up the digest simply lists fewer items — or answer `[SILENT]` and the scheduler suppresses delivery automatically.

```bash
python3 ~/.hermes/skills/eu-regulation-watcher/scripts/eu_regulation_watcher.py \
    [--lang de|en] [--limit 10] [--summary-limit N]
```

## Output format (excerpt)

```markdown
# Neueste EU-Regulierungsinitiativen (Better Regulation / Have your say, Sprache: DE)

**1. <Titel des Vorhabens>**
**Stellungnahmen offen** · Stellungnahmen DD.MM.YYYY – DD.MM.YYYY
**Thema:** Topic area
**Zusammenfassung:** 2–3 Sätze aus dem offiziellen Dossier (EN-Quelle)
**Link:** https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/<slug>_<lang2>
```

## Verified endpoints (November 2026, base `https://ec.europa.eu/info/law/better-regulation`)

| Endpoint | Use |
|---|---|
| `GET /brpapi/searchInitiatives?language=<ISO>&page=<n>&size=10` | Latest measures: statuses (OPEN/UPCOMING/CLOSED), dates, topics, translations |
| `GET /brpapi/groupInitiatives/<intId>` | Per-item detail incl. English-only `dossierSummary`, full topic list, stage, publications |
| `GET /brpapi/findInitiativePathByReference?reference=<ref>` | Canonical URL slug for the public item page (never hand-craft links) |

## Notes & pitfalls

- The **list call carries no summary** — the script does one detailed ~1 s request per item and skips gracefully if a detail fails
- `dossierSummary` is always in English regardless of `--lang`; translate for German delivery
- Detail calls take roughly 2–3 min total at default limit; keep cron timeouts generous (≥ 5 min)
