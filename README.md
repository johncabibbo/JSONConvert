# JSON Convert

Database table export/import utility for MySQL and Microsoft SQL Server. Export table data to JSON files and reimport when needed.

## Project Information

- **Version:** 2.2
- **Script Version:** 1.47
- **Created:** 2026-01-10
- **Last Updated:** 2026-03-01
- **Maintainer:** Cloud Box 9 Inc.

## Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user guide with configuration details
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card for common tasks
- **[README.md](README.md)** - This file (project overview)

## Overview

This project provides two complementary Python scripts for archiving and restoring database table data:

1. **table2JsonConvert.py** - Export table data to JSON and delete from source
2. **json2TableConvert.py** - Import JSON data back into table with validation

### Supported Databases

| Database | Version | Library |
|----------|---------|---------|
| MySQL | 5.7+ | mysql-connector-python |
| Microsoft SQL Server | 2016+ | pymssql |

## Features

### table2JsonConvert.py
- **Two Export Modes:**
  - Manual Mode: Interactive prompts for one-time exports
  - Profile Mode: Saved configurations for recurring tasks
- **Command-Line Arguments:** Run automated exports from cron
  - `--profile <id>` - Specify profile to use
  - `--auto` - Skip all confirmations (for cron jobs)
  - `--validate` - Test with 1 row only
  - `--list` - List available profiles
- **Multi-Database Support:** MySQL and SQL Server
- **Validation Mode:** Test exports with 1 row before full export
- **File Exists Handling:** Configure behavior when export file exists
  - `rename` - Add timestamp suffix (default)
  - `overwrite` - Replace existing file
  - `skip` - Skip export if file exists
- **Progress Tracking:** Real-time row counts and percentages
- **File Size Display:** Shows actual and estimated export sizes
- Export by date, ID, custom WHERE clause, or all records
- Batch processing for large datasets (20% batches, max 100K per batch)
- Optional confirmation before deletion
- Transaction support for data integrity

### json2TableConvert.py
- **Auto Profile Detection:** Uses export profile settings automatically
- **Multi-Database Support:** MySQL and SQL Server
- Validation mode (dry run without import)
- Column mapping validation
- Batch insert processing with progress reporting
- Comprehensive error handling
- Duplicate detection and reporting
- Transaction rollback on error

---

## Installation on a New Computer

### Step 1: Install Python 3.10+

**macOS (using Homebrew):**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.12

# Verify installation
python3 --version
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip

# Verify installation
python3 --version
```

**Windows:**
1. Download Python from https://www.python.org/downloads/
2. Run installer, check "Add Python to PATH"
3. Verify: `python --version`

---

### Step 2: Install Required Python Libraries

```bash
# MySQL connector (required for MySQL databases)
pip3 install mysql-connector-python

# SQL Server connector (required for SQL Server databases)
pip3 install pymssql

# Verify installations
pip3 list | grep -E "mysql-connector|pymssql"
```

**Expected Output:**
```
mysql-connector-python    8.x.x
pymssql                   2.x.x
```

#### Troubleshooting Library Installation

**macOS - pymssql installation issues:**
```bash
# Install FreeTDS (required for pymssql)
brew install freetds

# Then install pymssql
pip3 install pymssql
```

**Ubuntu/Debian - pymssql installation issues:**
```bash
# Install FreeTDS development files
sudo apt install freetds-dev

# Then install pymssql
pip3 install pymssql
```

**Windows - pymssql installation issues:**
```bash
# Use pre-built wheel
pip install pymssql
```

---

### Step 3: Install CB9Lib (Cloud Box 9 Utility Library)

CB9Lib provides consistent UI styling across all Cloud Box 9 scripts.

```bash
# Create CB9Lib directory
mkdir -p ~/Documents/script/CB9Lib

# Copy CB9Lib files (obtain from Cloud Box 9)
# CB9Lib should contain:
#   - __init__.py
#   - CB9Lib.py (with color_text, header, pause, clear_screen functions)
```

**Verify CB9Lib:**
```bash
ls ~/Documents/script/CB9Lib/
# Should show: __init__.py, CB9Lib.py (or similar)
```

---

### Step 4: Install JSONConvert Scripts

```bash
# Create project directory
mkdir -p ~/Documents/script/JSONConvert/exports

# Copy project files to directory:
#   - table2JsonConvert.py
#   - json2TableConvert.py
#   - tableJsonConvert.json
#   - README.md
#   - USER_GUIDE.md
#   - QUICK_REFERENCE.md

# Set execute permissions
chmod +x ~/Documents/script/JSONConvert/*.py
```

---

### Step 5: Configure Database Connection

Edit `tableJsonConvert.json` with your database settings:

**For MySQL:**
```json
"database": {
  "type": "MySQL",
  "host": "your-mysql-server.com",
  "user": "your_username",
  "password": "your_password",
  "database": "your_database",
  "port": 3306
}
```

**For SQL Server:**
```json
"database": {
  "type": "SQLServer",
  "host": "your-sqlserver.database.windows.net",
  "user": "your_username",
  "password": "your_password",
  "database": "your_database",
  "port": 1433
}
```

---

### Step 6: Verify Installation

```bash
cd ~/Documents/script/JSONConvert/

# Test export script
python3 table2JsonConvert.py
# Should display header and main menu

# Test import script
python3 json2TableConvert.py
# Should display header and prompt for file path
```

---

## Dependencies Summary

| Dependency | Purpose | Install Command |
|------------|---------|-----------------|
| Python 3.10+ | Core runtime | See Step 1 |
| mysql-connector-python | MySQL database connectivity | `pip3 install mysql-connector-python` |
| pymssql | SQL Server database connectivity | `pip3 install pymssql` |
| CB9Lib | UI utilities (header, colors, etc.) | Copy to `~/Documents/script/CB9Lib/` |

### System Dependencies (for pymssql)

| OS | Dependency | Install Command |
|----|------------|-----------------|
| macOS | FreeTDS | `brew install freetds` |
| Ubuntu/Debian | FreeTDS Dev | `sudo apt install freetds-dev` |
| Windows | None | Pre-built wheels available |

---

## Configuration

The `tableJsonConvert.json` file controls all aspects of the tool:

### Database Settings

```json
"database": {
  "type": "MySQL",           // "MySQL" or "SQLServer"
  "host": "hostname",
  "user": "username",
  "password": "password",
  "database": "dbname",
  "port": 3306               // 3306 for MySQL, 1433 for SQL Server
}
```

### Core Settings
- **Export:** Output paths, date formats, batch sizes, deletion confirmation, file exists handling
- **Import:** Validation defaults, error handling, batch sizes
- **Logging:** Enable/disable, log paths, log levels (DEBUG, INFO, WARNING, ERROR)

### Export Settings Example

```json
"export": {
  "defaultOutputPath": "~/Documents/script/JSONConvert/exports/",
  "dateFormat": "%Y-%m-%d %H:%M:%S",
  "batchSize": 1000,
  "confirmBeforeDelete": true,
  "fileExistsAction": "rename",
  "outputFilePostExt": ""
}
```

| Setting | Values | Description |
|---------|--------|-------------|
| `fileExistsAction` | `rename` | Add timestamp suffix to filename (default) |
| | `overwrite` | Replace existing file |
| | `skip` | Skip export if file exists |
| `outputFilePostExt` | `""` | Timestamp to insert before file extension |

### Output File Timestamps (outputFilePostExt)

Add timestamps to output filenames using the `outputFilePostExt` setting:

```json
"export": {
  "outputFile": "~/exports/activityLog.json",
  "outputFilePostExt": "_YYYY_MM_DD"
}
```

**Result:** `activityLog_2026_03_01.json`

Uses the same placeholders as `logPostExt` (YYYY, MM, DD, HH, mm, SS).

### Profiles
Reusable export configurations with:
- Custom SQL queries (`sourceSQL`)
- Dynamic output filenames with placeholders (`{date}`, `{datetime}`, etc.)
- Per-profile database connections (can mix MySQL and SQL Server)
- Deletion control (`deleteAfterExport`)
- Individual logging settings

**See [USER_GUIDE.md](USER_GUIDE.md) for complete configuration reference.**

---

## Quick Start

### Export with Profile (Interactive)

```bash
python3 table2JsonConvert.py
# Select: 2 (Profile Export)
# Select: Profile number
# Select: 2 (Validate Only) - First time
# Review results, then run again with mode 1 (Normal Export)
```

### Export with Profile (Command-Line / Cron)

```bash
# List available profiles
python3 table2JsonConvert.py --list

# Run export with auto-confirmation (for cron)
python3 table2JsonConvert.py --profile docInfo-activityLog --auto

# Validate only (test with 1 row)
python3 table2JsonConvert.py --profile docInfo-activityLog --validate

# Cron example (runs daily at 2 AM)
0 2 * * * /usr/bin/python3 /path/to/table2JsonConvert.py --profile myProfile --auto >> /path/to/cron.log 2>&1
```

### Manual Export (One-Time)

```bash
python3 table2JsonConvert.py
# Select: 1 (Manual Export)
# Follow interactive prompts
```

### Import Data

```bash
python3 json2TableConvert.py
# Enter JSON file path
# Select: 1 (Validate Only) - First time
# Review results, then run again with mode 2 (Import Data)
```

**For detailed usage instructions, see [USER_GUIDE.md](USER_GUIDE.md)**
**For quick commands, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md)**

---

## File Structure

```
JSONConvert/
├── table2JsonConvert.py       # Export script
├── json2TableConvert.py       # Import script
├── tableJsonConvert.json      # Configuration file
├── exports/                   # Default export directory
├── README.md                  # This file
├── USER_GUIDE.md              # Comprehensive user guide
└── QUICK_REFERENCE.md         # Quick reference card
```

---

## Exported JSON Format

```json
{
  "_metadata": {
    "exportDate": "2026-01-10 21:55:00",
    "tableName": "exampleTable",
    "recordCount": 150,
    "whereClause": "createdDate < '2025-01-01'"
  },
  "records": [
    {
      "id": 1,
      "name": "Example",
      "createdDate": "2024-12-15 10:30:00"
    }
  ]
}
```

---

## Database-Specific Notes

### MySQL
- Uses `DESCRIBE` for table structure
- Uses `DELETE ... LIMIT n` for batch deletion
- Column quoting: backticks (`` `column` ``)
- Default port: 3306

### SQL Server
- Uses `INFORMATION_SCHEMA.COLUMNS` for table structure
- Uses `DELETE TOP (n)` for batch deletion
- Column quoting: square brackets (`[column]`)
- Default port: 1433

---

## Logging

All operations are logged using the CB9Lib Logger for consistent formatting.

### Default Log Location
```
~/Documents/logs/jsonConvert.log
```

### Log Filename Timestamps (logPostExt)

Add timestamps to log filenames using the `logPostExt` setting:

```json
"logging": {
  "enabled": true,
  "logPath": "~/Documents/logs/jsonConvert.log",
  "logLevel": "INFO",
  "logPostExt": "_YYYY_MM_DD-HHmm"
}
```

**Result:** `jsonConvert_2026_03_01-2230.log`

**Available Placeholders:**
| Placeholder | Example | Description |
|-------------|---------|-------------|
| `YYYY` | 2026 | 4-digit year |
| `MM` | 03 | 2-digit month |
| `DD` | 01 | 2-digit day |
| `HH` | 22 | 2-digit hour (24h) |
| `mm` | 30 | 2-digit minute |
| `SS` | 45 | 2-digit second |

### Log Entries Include
- **Script start/end** with CB9Lib Logger
- **Run mode** (Interactive or Auto --profile)
- **Profile settings** (ID, output file, delete flag)
- Export operations with record counts
- Import operations with success/error counts
- Full table counts at start and end
- Validation results
- Error messages
- Timestamps and duration

---

## Error Handling

### Export Script
- Database connection errors (MySQL and SQL Server)
- Invalid table names
- Query execution failures
- File write permissions

### Import Script
- Missing or invalid JSON files
- Column mismatches
- Data type incompatibilities
- Duplicate key violations
- Database constraint errors

---

## Troubleshooting

**Problem:** "Config file not found"
- **Solution:** Ensure `tableJsonConvert.json` is in the same directory as scripts

**Problem:** "MySQL connection error"
- **Solution:** Verify credentials, check if MySQL server is running, verify port 3306

**Problem:** "SQL Server connection error"
- **Solution:** Verify credentials, check if SQL Server allows remote connections, verify port 1433

**Problem:** "Column mismatch during import"
- **Solution:** Use validation mode to identify incompatible columns

**Problem:** "pymssql installation fails"
- **Solution:** Install FreeTDS first (see Step 2 troubleshooting)

**Problem:** "ModuleNotFoundError: No module named 'pymssql'"
- **Solution:** Run `pip3 install pymssql`

---

## License

Copyright © 2026 Cloud Box 9 Inc. All rights reserved.

## Support

For issues or questions, contact Cloud Box 9 Inc.
