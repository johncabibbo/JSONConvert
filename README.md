# JSON Convert

**Export MySQL table rows to JSON (and prune them), then import them back — a simple archive/restore pair.**

JSON Convert is two complementary tools:

- **`table2JsonConvert.py`** — exports rows from a MySQL table to a JSON file, then deletes the exported rows from the source table (great for archiving/aging out old data).
- **`json2TableConvert.py`** — imports rows from a JSON file back into a MySQL table (restore, or move data between tables/databases).

Both are profile-driven, batch-processed, transactional, and fully logged. CB9Lib is bundled.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Alias Setup — Run From Anywhere](#alias-setup--run-from-anywhere)
6. [Configuration](#configuration)
7. [Usage & Examples](#usage--examples)
8. [Troubleshooting](#troubleshooting)
9. [Documentation](#documentation)
10. [License / Copyright](#license--copyright)

---

## Overview

Use the **export** tool to move old rows (e.g. an `activityLog` older than N days) out of a busy table into a JSON archive, freeing the table while keeping the data. Use the **import** tool to restore that JSON — into the same table, a different table, or another database. Always validate first.

---

## Features

- **Export by date or ID** with custom `WHERE` clauses.
- **Deletes after successful export** (archive-and-prune) — transactional.
- **Import with validation mode** (dry run) before writing.
- **Batch processing** for large datasets, with progress + commit-every-N-rows.
- **Profile selection** — pick source/target connections from config; import to a different table than the export.
- **Comprehensive logging** and before/after row counts.
- **Automation flags** for cron.

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| **Python 3.8+** | macOS / Linux (bundled CB9Lib for the UI). |
| **pymysql** | MySQL connectivity. |
| **pymssql** *(optional)* | Only if connecting to SQL Server profiles. |
| **A MySQL/MariaDB server** | With a user permitted to select/delete/insert on the target tables. |

```bash
pip install pymysql          # add pymssql only if you use SQL Server
```

---

## Installation

```bash
git clone <REPOSITORY_URL> JSONConvert
cd JSONConvert
python3 table2JsonConvert.py --list
```

---

## Alias Setup — Run From Anywhere

Create two aliases — one per tool.

### macOS / Linux (zsh or bash)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias table2json='python3 ~/path/to/JSONConvert/table2JsonConvert.py'
alias json2table='python3 ~/path/to/JSONConvert/json2TableConvert.py'
```

Reload and run:

```bash
source ~/.zshrc
table2json --list
```

### Windows (PowerShell)

Add to your PowerShell `$PROFILE`:

```powershell
function table2json { python "C:\path\to\JSONConvert\table2JsonConvert.py" @args }
function json2table { python "C:\path\to\JSONConvert\json2TableConvert.py" @args }
```

---

## Configuration

Edit **`tableJsonConvert.json`** (a sanitized `tableJsonConvert.sample.json` is included). It holds database connection profiles plus export/import defaults (table, WHERE clause, batch size, log file, output folder).

> **Never commit real credentials.** Copy the sample, fill in your own, and keep the live config out of version control.

---

## Usage & Examples

### Export (and prune)

```bash
python3 table2JsonConvert.py                          # interactive
python3 table2JsonConvert.py --list                   # list profiles
python3 table2JsonConvert.py --profile <id> --validate  # test with 1 row, no export
python3 table2JsonConvert.py --profile <id> --auto      # non-interactive (cron)
```

**Cron example — archive nightly at 2 AM:**

```cron
0 2 * * * /usr/bin/python3 ~/path/to/JSONConvert/table2JsonConvert.py --profile activityLog --auto >> ~/Documents/log/jsonConvert.log 2>&1
```

### Import (restore)

```bash
python3 json2TableConvert.py     # interactive; prompts for file, profile, and target table
```

> Run **validation mode first** to confirm data integrity before importing.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: pymysql` | `pip install pymysql` (add `pymssql` for SQL Server). |
| Rows deleted but export looked empty | Always `--validate` first; export/delete is transactional but verify your WHERE clause. |
| Duplicate key errors on import | Reported per-row but don't stop the import; resolve conflicts or import to a fresh table. |
| Wrong table on import | You're prompted for the target table (default from metadata) — pick the intended one. |

---

## Documentation

| File | Contents |
|------|----------|
| `USER_GUIDE.md` | Full walkthrough of both tools |
| `QUICK_REFERENCE.md` | Flags and common commands |

---

## License / Copyright

---
**Version:** table2JsonConvert 1.47 · json2TableConvert 1.25
**Author:** Cloud Box 9 Inc.
**Maintainer / Owner:** Cloud Box 9 Inc.
**Last Updated:** Jul 5, 2026

Copyright © 2026 Cloud Box 9 Inc. All rights reserved.
