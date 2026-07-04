# JSON Convert - Quick Reference Card

**Version:** 2.2 | **Script:** 1.47 | **Project:** JSONConvert | **Maintainer:** Cloud Box 9 Inc.

---

## Installation Quick Start

### Install Dependencies

```bash
# Python libraries
pip3 install mysql-connector-python    # For MySQL
pip3 install pymssql                    # For SQL Server

# macOS only - install FreeTDS first for SQL Server
brew install freetds
pip3 install pymssql
```

### Verify Installation

```bash
pip3 list | grep -E "mysql-connector|pymssql"
```

---

## Common Commands

```bash
# Start export tool (interactive)
python3 table2JsonConvert.py

# Export with profile (automated/cron)
python3 table2JsonConvert.py --profile PROFILE_ID --auto

# List available profiles
python3 table2JsonConvert.py --list

# Validate export (test with 1 row)
python3 table2JsonConvert.py --profile PROFILE_ID --validate

# Start import tool
python3 json2TableConvert.py

# Edit configuration
nano tableJsonConvert.json

# View logs
tail -f ~/Documents/logs/jsonConvert.log
```

---

## Database Configuration

### MySQL
```json
"database": {
  "type": "MySQL",
  "host": "hostname",
  "user": "username",
  "password": "password",
  "database": "dbname",
  "port": 3306
}
```

### SQL Server
```json
"database": {
  "type": "SQLServer",
  "host": "hostname",
  "user": "username",
  "password": "password",
  "database": "dbname",
  "port": 1433
}
```

---

## Export Workflow

### Manual Export (One-Time)
```
1. Run: python3 table2JsonConvert.py
2. Select: 1 (Manual Export)
3. Enter: Table name
4. Select: Export mode (Date/ID/Custom/All)
5. Confirm: Deletion (yes/no)
```

### Profile Export (Recurring)
```
1. Run: python3 table2JsonConvert.py
2. Select: 2 (Profile Export)
3. Select: Profile number
4. Select: 1 (Normal) or 2 (Validate)
5. Review: Results
```

---

## Import Workflow

```
1. Run: python3 json2TableConvert.py
2. Enter: JSON file path
3. Review: Metadata and validation
4. Select: 1 (Validate) or 2 (Import)
5. Confirm: Import (yes/no)
```

---

## Command-Line Arguments

```bash
python3 table2JsonConvert.py [OPTIONS]
```

| Argument | Short | Description |
|----------|-------|-------------|
| `--profile ID` | `-p` | Profile ID to use |
| `--auto` | `-a` | Skip all confirmations (for cron) |
| `--validate` | `-v` | Test with 1 row only |
| `--list` | `-l` | List profiles and exit |
| `--help` | `-h` | Show help |

### Cron Example

```bash
# Daily at 2 AM
0 2 * * * /usr/bin/python3 /path/to/table2JsonConvert.py --profile myProfile --auto >> /path/to/cron.log 2>&1
```

---

## File Exists Handling

```json
"export": {
  "fileExistsAction": "rename"
}
```

| Value | Behavior |
|-------|----------|
| `rename` | Add timestamp suffix (default) |
| `overwrite` | Replace existing file |
| `skip` | Skip export if file exists |

*Can be set globally or per-profile in `export` section*

---

## Database Comparison

| Feature | MySQL | SQL Server |
|---------|-------|------------|
| **Type Value** | `"MySQL"` | `"SQLServer"` |
| **Default Port** | 3306 | 1433 |
| **Library** | mysql-connector-python | pymssql |
| **Column Quoting** | \`backticks\` | [brackets] |
| **Batch Delete** | `LIMIT n` | `TOP (n)` |

---

## Configuration Settings

### Export Settings
```json
"export": {
  "defaultOutputPath": "~/exports/",
  "dateFormat": "%Y-%m-%d %H:%M:%S",
  "batchSize": 1000,
  "confirmBeforeDelete": true,
  "fileExistsAction": "rename",
  "outputFilePostExt": ""
}
```

### Logging Settings
```json
"logging": {
  "enabled": true,
  "logPath": "~/Documents/logs/jsonConvert.log",
  "logLevel": "INFO",
  "logPostExt": "_YYYY_MM_DD-HHmm"
}
```

### Log Levels (Most to Least Verbose)
```
DEBUG    - Everything (development/troubleshooting)
INFO     - Normal operations (RECOMMENDED)
WARNING  - Warnings and errors only
ERROR    - Errors only
```

### Timestamp Placeholders (logPostExt / outputFilePostExt)
```
YYYY  →  2026     (4-digit year)
MM    →  03       (2-digit month)
DD    →  01       (2-digit day)
HH    →  22       (2-digit hour 24h)
mm    →  30       (2-digit minute)
SS    →  45       (2-digit second)
```

**Example:** `logPostExt: "_YYYY_MM_DD"` → `jsonConvert_2026_03_01.log`

### Date Format Codes
```
%Y-%m-%d %H:%M:%S  →  2026-01-10 14:30:45
%Y-%m-%d           →  2026-01-10
%m/%d/%Y           →  01/10/2026
%Y%m%d_%H%M%S      →  20260110_143045
```

### Filename Placeholders
```
{date}      →  2026-01-10
{datetime}  →  2026-01-10_143045
{year}      →  2026
{month}     →  01
{day}       →  10
{timestamp} →  20260110_143045
```

---

## Profile Template

### MySQL Profile
```json
{
  "profileId": "database-table-purpose",
  "description": "Description of what this exports",
  "export": {
    "sourceSQL": "SELECT * FROM tableName WHERE condition",
    "outputFile": "~/exports/filename_{date}.json",
    "deleteAfterExport": false,
    "fileExistsAction": "rename"
  },
  "database": {
    "type": "MySQL",
    "host": "localhost",
    "user": "username",
    "password": "password",
    "database": "database_name",
    "port": 3306
  }
}
```

### SQL Server Profile
```json
{
  "profileId": "database-table-purpose",
  "description": "Description of what this exports",
  "export": {
    "sourceSQL": "SELECT * FROM tableName WHERE condition",
    "outputFile": "~/exports/filename_{date}.json",
    "deleteAfterExport": false,
    "fileExistsAction": "rename"
  },
  "database": {
    "type": "SQLServer",
    "host": "server.database.windows.net",
    "user": "username",
    "password": "password",
    "database": "database_name",
    "port": 1433
  }
}
```

---

## Troubleshooting

### Connection Failed

**MySQL:**
```bash
# Test connection
mysql -h HOST -u USER -p

# Check port
nc -zv HOST 3306
```

**SQL Server:**
```bash
# Test connection
python3 -c "import pymssql; conn = pymssql.connect('HOST', 'USER', 'PASS', 'DB')"

# Check port
nc -zv HOST 1433
```

### Missing Libraries
```bash
# MySQL library
pip3 install mysql-connector-python

# SQL Server library (macOS)
brew install freetds
pip3 install pymssql

# SQL Server library (Linux)
sudo apt install freetds-dev
pip3 install pymssql
```

### File Permissions
```bash
# Export directory
mkdir -p ~/Documents/script/JSONConvert/exports/
chmod 755 ~/Documents/script/JSONConvert/exports/

# Config file
chmod 600 tableJsonConvert.json
```

### View Logs
```bash
# Main log
tail -50 ~/Documents/logs/jsonConvert.log

# Search errors
grep "ERROR" ~/Documents/logs/jsonConvert.log

# Profile-specific
tail -50 ~/Documents/logs/jsonConvert_profileId.log
```

---

## Best Practices

### Before Exporting
- [ ] Use validate mode first
- [ ] Backup database
- [ ] Test SQL query
- [ ] Check disk space

### Before Importing
- [ ] Use validate mode
- [ ] Verify table exists
- [ ] Test on development database
- [ ] Backup target table

### Safety
- [ ] Set `deleteAfterExport: false` initially
- [ ] Test profiles before enabling deletion
- [ ] Keep configuration file secure
- [ ] Review logs regularly

---

## File Locations

```
~/Documents/script/JSONConvert/
├── table2JsonConvert.py           - Export script
├── json2TableConvert.py           - Import script
├── tableJsonConvert.json          - Configuration
├── exports/                       - Exported JSON files
├── USER_GUIDE.md                  - Full documentation
├── QUICK_REFERENCE.md             - This file
└── README.md                      - Project overview

~/Documents/logs/
├── jsonConvert.log                - Main log
└── jsonConvert_profileId.log      - Profile logs
```

---

## Dependencies Summary

| Component | Purpose | Install |
|-----------|---------|---------|
| Python 3.10+ | Runtime | `brew install python@3.12` |
| mysql-connector-python | MySQL | `pip3 install mysql-connector-python` |
| pymssql | SQL Server | `pip3 install pymssql` |
| FreeTDS | pymssql dep (macOS) | `brew install freetds` |
| CB9Lib | UI utilities | Copy to `~/Documents/script/CB9Lib/` |

---

## Export Modes Comparison

| Mode | Use Case | Example |
|------|----------|---------|
| **By Date** | Archive old records | Records before 2025-01-01 |
| **By ID** | Numeric ranges | IDs less than 10000 |
| **Custom WHERE** | Complex conditions | status='archived' AND age>365 |
| **All Records** | Full table export | Backup entire table |

---

## Profile vs Manual

| Feature | Manual | Profile |
|---------|--------|---------|
| **Setup** | None needed | Configure once |
| **Reusable** | No | Yes |
| **SQL Query** | Table-based | Custom SQL |
| **Cron/Automation** | Not supported | `--profile ID --auto` |
| **Database Type** | Default config | Per-profile |
| **Use Case** | One-time exports | Recurring tasks |

---

## Common SQL Examples

### MySQL
```sql
-- Archive old records
SELECT * FROM logs WHERE createdDate < '2025-01-01'

-- Date subtraction
WHERE createdDate < DATE_SUB(NOW(), INTERVAL 1 YEAR)
```

### SQL Server
```sql
-- Archive old records
SELECT * FROM logs WHERE createdDate < '2025-01-01'

-- Date subtraction
WHERE createdDate < DATEADD(year, -1, GETDATE())
```

---

## Performance Tips

### Small Datasets (< 1,000 rows)
```json
"batchSize": 100
"insertBatchSize": 100
```

### Medium Datasets (1,000-10,000 rows)
```json
"batchSize": 1000
"insertBatchSize": 500
```

### Large Datasets (> 10,000 rows)
```json
"batchSize": 5000
"insertBatchSize": 1000
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (check logs) |
| `^C` | User cancelled (Ctrl+C) |

---

## Support Resources

1. **Full Documentation:** `USER_GUIDE.md`
2. **Log Files:** `~/Documents/logs/jsonConvert*.log`
3. **Project README:** `README.md`
4. **Configuration:** `tableJsonConvert.json`

---

**Copyright © 2026 Cloud Box 9 Inc. All rights reserved.**
