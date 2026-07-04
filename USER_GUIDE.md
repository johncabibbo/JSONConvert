# JSON Convert - User Guide

**Version:** 2.2
**Script Version:** 1.47
**Project:** JSONConvert
**Last Updated:** 2026-03-01
**Maintainer:** Cloud Box 9 Inc.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration Guide](#configuration-guide)
4. [Using table2JsonConvert.py](#using-table2jsonconvertpy)
5. [Command-Line Arguments & Automation](#command-line-arguments--automation)
6. [Using json2TableConvert.py](#using-json2tableconvertpy)
7. [Profile Management](#profile-management)
8. [Database-Specific Information](#database-specific-information)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

JSON Convert is a database archival and restoration tool that:
- Exports database table data to JSON format
- Supports both **MySQL** and **Microsoft SQL Server**
- Optionally deletes exported data from source tables
- Restores data from JSON files back to database
- Supports reusable profiles for common export tasks
- Provides validation mode to test exports safely

### Supported Databases

| Database | Versions | Library | Default Port |
|----------|----------|---------|--------------|
| MySQL | 5.7, 8.0+ | mysql-connector-python | 3306 |
| Microsoft SQL Server | 2016, 2019, 2022 | pymssql | 1433 |

### Key Features

**Two Operation Modes:**
- **Manual Mode:** Interactive prompts for one-time exports
- **Profile Mode:** Saved configurations for recurring tasks

**Safety Features:**
- Validation mode (test with 1 row)
- Confirmation before deletion
- Transaction support
- Comprehensive error handling

**Progress Tracking:**
- Row count display
- Progress percentage
- File size estimation
- Real-time updates

---

## Installation

### Prerequisites Checklist

Before installing JSONConvert, ensure you have:

- [ ] Python 3.10 or higher
- [ ] pip (Python package manager)
- [ ] Network access to your database server
- [ ] Database credentials with appropriate permissions

---

### Step 1: Install Python

#### macOS (using Homebrew)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
brew install python@3.12

# Add to PATH (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
python3 --version
# Expected: Python 3.12.x
```

#### Ubuntu/Debian Linux

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Verify installation
python3 --version
pip3 --version
```

#### Windows

1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. **Important:** Check "Add Python to PATH" during installation
4. Verify in Command Prompt:
   ```cmd
   python --version
   pip --version
   ```

---

### Step 2: Install Required Python Libraries

#### Install MySQL Connector (Required for MySQL)

```bash
pip3 install mysql-connector-python
```

#### Install pymssql (Required for SQL Server)

**macOS:**
```bash
# First install FreeTDS (required dependency)
brew install freetds

# Then install pymssql
pip3 install pymssql
```

**Ubuntu/Debian:**
```bash
# First install FreeTDS development files
sudo apt install freetds-dev

# Then install pymssql
pip3 install pymssql
```

**Windows:**
```cmd
pip install pymssql
```

#### Verify Library Installation

```bash
pip3 list | grep -E "mysql-connector|pymssql"
```

**Expected Output:**
```
mysql-connector-python    8.2.0
pymssql                   2.2.11
```

#### Troubleshooting Library Installation

**Error: "Cannot find -lsybdb" (Linux/macOS)**
```bash
# macOS
brew install freetds
export LDFLAGS="-L/opt/homebrew/opt/freetds/lib"
export CPPFLAGS="-I/opt/homebrew/opt/freetds/include"
pip3 install pymssql

# Linux
sudo apt install freetds-dev libssl-dev
pip3 install pymssql
```

**Error: "Microsoft Visual C++ required" (Windows)**
1. Download Visual C++ Build Tools from Microsoft
2. Install with "Desktop development with C++" workload
3. Retry `pip install pymssql`

---

### Step 3: Install CB9Lib

CB9Lib is the Cloud Box 9 utility library that provides consistent UI styling.

```bash
# Create the CB9Lib directory
mkdir -p ~/Documents/script/CB9Lib

# CB9Lib files needed:
# - __init__.py
# - CB9Lib.py
#
# Obtain these files from Cloud Box 9 or copy from another installation
```

**CB9Lib provides these functions:**
- `header(title, version)` - Display styled header
- `color_text(text, fg=COLOR)` - Colored text output
- `pause(message)` - Wait for user input
- `clear_screen()` - Clear terminal

**Verify CB9Lib:**
```bash
python3 -c "import sys; sys.path.insert(0, '$HOME/Documents/script/CB9Lib'); from CB9Lib import *; print('CB9Lib OK')"
```

---

### Step 4: Install JSONConvert

```bash
# Create project directory
mkdir -p ~/Documents/script/JSONConvert/exports

# Navigate to directory
cd ~/Documents/script/JSONConvert

# Copy or download project files:
# - table2JsonConvert.py
# - json2TableConvert.py
# - tableJsonConvert.json
# - README.md
# - USER_GUIDE.md
# - QUICK_REFERENCE.md

# Set execute permissions (macOS/Linux)
chmod +x *.py

# Create logs directory
mkdir -p ~/Documents/logs
```

---

### Step 5: Configure Database Connection

Edit `tableJsonConvert.json` with your database settings.

**For MySQL:**
```json
{
  "database": {
    "type": "MySQL",
    "host": "your-mysql-server.com",
    "user": "your_username",
    "password": "your_password",
    "database": "your_database",
    "port": 3306
  }
}
```

**For SQL Server:**
```json
{
  "database": {
    "type": "SQLServer",
    "host": "your-server.database.windows.net",
    "user": "your_username",
    "password": "your_password",
    "database": "your_database",
    "port": 1433
  }
}
```

---

### Step 6: Verify Installation

```bash
cd ~/Documents/script/JSONConvert/

# Test export script
python3 table2JsonConvert.py
# Should display header and menu

# Test import script
python3 json2TableConvert.py
# Should display header and prompt for file
```

---

### Installation Summary

| Component | Install Command | Verify |
|-----------|-----------------|--------|
| Python 3.10+ | `brew install python@3.12` | `python3 --version` |
| mysql-connector-python | `pip3 install mysql-connector-python` | `pip3 show mysql-connector-python` |
| pymssql | `pip3 install pymssql` | `pip3 show pymssql` |
| FreeTDS (macOS) | `brew install freetds` | `brew info freetds` |
| FreeTDS (Linux) | `sudo apt install freetds-dev` | `dpkg -l freetds-dev` |
| CB9Lib | Manual copy | See Step 3 |

---

## Configuration Guide

### Configuration File: `tableJsonConvert.json`

The configuration file controls all aspects of the JSON Convert system.

#### File Structure

```json
{
  "_metadata": {
    "project": "JSONConvert",
    "version": "2.0",
    "lastUpdated": "2026-01-27",
    "description": "Configuration for table2JsonConvert and json2TableConvert"
  },

  "database": { ... },
  "export": { ... },
  "import": { ... },
  "whereClauseTemplates": { ... },
  "logging": { ... },
  "profiles": [ ... ]
}
```

---

### Database Settings

Default database connection (used when no profile is specified):

#### MySQL Configuration

```json
"database": {
  "type": "MySQL",
  "host": "YOUR_SERVER_IP",
  "user": "YOUR_DB_USER",
  "password": "your_password",
  "database": "docInfo",
  "port": 3306
}
```

#### SQL Server Configuration

```json
"database": {
  "type": "SQLServer",
  "host": "your-server.database.windows.net",
  "user": "sqladmin",
  "password": "your_password",
  "database": "your_database",
  "port": 1433
}
```

**Configuration Options:**

| Setting | Type | Required | Description |
|---------|------|----------|-------------|
| `type` | string | Yes | Database type: `"MySQL"` or `"SQLServer"` |
| `host` | string | Yes | Database server address |
| `user` | string | Yes | Database username |
| `password` | string | Yes | Database password |
| `database` | string | Yes | Database name |
| `port` | integer | No | Port (MySQL: 3306, SQL Server: 1433) |

---

### Export Settings

Controls behavior of table2JsonConvert.py:

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

**Configuration Options:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `defaultOutputPath` | string | Required | Where JSON files are saved |
| `dateFormat` | string | `%Y-%m-%d %H:%M:%S` | Python datetime format |
| `batchSize` | integer | 1000 | Rows processed per batch |
| `confirmBeforeDelete` | boolean | true | Require confirmation before deletion |
| `fileExistsAction` | string | `rename` | Action when export file exists |
| `outputFilePostExt` | string | `""` | Timestamp pattern for output filename |

**fileExistsAction Options:**

| Value | Behavior |
|-------|----------|
| `rename` | Add timestamp suffix to filename (e.g., `file_20260301_143052.json`) |
| `overwrite` | Replace the existing file |
| `skip` | Skip the export, do not create file |

This setting can also be specified per-profile in the profile's `export` section to override the global default.

#### Output File Timestamps (outputFilePostExt)

Add timestamps to export filenames using `outputFilePostExt`:

```json
"export": {
  "outputFile": "~/exports/activityLog.json",
  "outputFilePostExt": "_YYYY_MM_DD"
}
```

**Result:** `activityLog_2026_03_01.json`

Uses the same placeholders as `logPostExt` (YYYY, MM, DD, HH, mm, SS). This is useful when you want dated export files without using the `{date}` placeholder in the filename itself.

**Date Format Examples:**

| Format | Example Output |
|--------|----------------|
| `%Y-%m-%d %H:%M:%S` | 2026-01-10 14:30:45 |
| `%Y-%m-%d` | 2026-01-10 |
| `%m/%d/%Y` | 01/10/2026 |
| `%Y%m%d_%H%M%S` | 20260110_143045 |

---

### Import Settings

Controls behavior of json2TableConvert.py:

```json
"import": {
  "validateOnly": false,
  "stopOnError": true,
  "insertBatchSize": 100
}
```

**Configuration Options:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `validateOnly` | boolean | false | Default mode |
| `stopOnError` | boolean | true | Stop on first error |
| `insertBatchSize` | integer | 100 | Records per batch commit |

---

### Logging Settings

Uses CB9Lib Logger for consistent, formatted logging with automatic script start/end entries.

```json
"logging": {
  "enabled": true,
  "logPath": "~/Documents/logs/jsonConvert.log",
  "logLevel": "INFO",
  "logPostExt": ""
}
```

**Configuration Options:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | boolean | true | Enable/disable logging |
| `logPath` | string | Required | Path to log file |
| `logLevel` | string | INFO | Logging verbosity |
| `logPostExt` | string | "" | Timestamp pattern to insert before file extension |

**Log Levels:**

| Level | What Gets Logged |
|-------|------------------|
| `DEBUG` | Everything (very verbose) |
| `INFO` | Normal operations (**Recommended**) |
| `WARNING` | Warnings and errors only |
| `ERROR` | Errors only |

#### Log Filename Timestamps (logPostExt)

Add timestamps to log filenames to create daily/hourly log files:

```json
"logging": {
  "logPath": "~/Documents/logs/jsonConvert.log",
  "logPostExt": "_YYYY_MM_DD-HHmm"
}
```

**Result:** `jsonConvert_2026_03_01-2230.log`

**Available Placeholders:**

| Placeholder | Example | Description |
|-------------|---------|-------------|
| `YYYY` | 2026 | 4-digit year |
| `MM` | 03 | 2-digit month (zero-padded) |
| `DD` | 01 | 2-digit day (zero-padded) |
| `HH` | 22 | 2-digit hour (24-hour, zero-padded) |
| `mm` | 30 | 2-digit minute (zero-padded) |
| `SS` | 45 | 2-digit second (zero-padded) |

**Examples:**

| Pattern | Output Filename |
|---------|-----------------|
| `""` (empty) | `jsonConvert.log` |
| `_YYYY_MM_DD` | `jsonConvert_2026_03_01.log` |
| `_YYYY_MM_DD-HHmm` | `jsonConvert_2026_03_01-2230.log` |
| `-YYYYMMDD` | `jsonConvert-20260301.log` |

#### Settings Logging

When the script runs, it automatically logs key settings to the log file:

```
2026-03-01 22:30:45 INFO: Script table2JsonConvert started
2026-03-01 22:30:45 INFO: Run mode: Auto (--profile)
2026-03-01 22:30:45 INFO: Profile argument: docInfo-activityLog
2026-03-01 22:30:46 INFO: ----- Profile Settings -----
2026-03-01 22:30:46 INFO: Profile ID: docInfo-activityLog
2026-03-01 22:30:46 INFO: Output file: ~/exports/activityLog_2026-03-01.json
2026-03-01 22:30:46 INFO: Delete after export: True
```

This aids in debugging and provides an audit trail for automated exports.

---

### Profiles Configuration

Profiles are reusable export configurations. Each profile can use either MySQL or SQL Server.

#### MySQL Profile Example

```json
{
  "profileId": "docInfo-activityLog",
  "description": "DocInfo activity log export (MySQL)",
  "export": {
    "dateFormat": "%Y-%m-%d %H:%M:%S",
    "sourceSQL": "SELECT * FROM activityLog WHERE activityDate < '2025-12-01'",
    "outputFile": "~/Documents/script/JSONConvert/exports/activityLog_{date}.json",
    "deleteAfterExport": true
  },
  "database": {
    "type": "MySQL",
    "host": "YOUR_SERVER_IP",
    "user": "YOUR_DB_USER",
    "password": "your_password",
    "database": "docInfo",
    "port": 3306
  },
  "logging": {
    "enabled": true,
    "logPath": "~/Documents/logs/jsonConvert_docInfo-activityLog.log",
    "logLevel": "INFO"
  }
}
```

#### SQL Server Profile Example

```json
{
  "profileId": "analytics-events",
  "description": "Analytics events archive (SQL Server)",
  "export": {
    "dateFormat": "%Y-%m-%d %H:%M:%S",
    "sourceSQL": "SELECT * FROM events WHERE eventDate < '2025-12-01'",
    "outputFile": "~/Documents/script/JSONConvert/exports/events_{date}.json",
    "deleteAfterExport": false
  },
  "database": {
    "type": "SQLServer",
    "host": "analytics.database.windows.net",
    "user": "sqladmin",
    "password": "your_password",
    "database": "AnalyticsDB",
    "port": 1433
  },
  "logging": {
    "enabled": true,
    "logPath": "~/Documents/logs/jsonConvert_analytics.log",
    "logLevel": "INFO"
  }
}
```

#### Profile Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profileId` | string | Yes | Unique identifier |
| `description` | string | No | Human-readable description |
| `export.sourceSQL` | string | **Yes** | SQL SELECT query |
| `export.outputFile` | string | **Yes** | Output path (supports placeholders) |
| `export.deleteAfterExport` | boolean | No | Delete after export (default: false) |
| `export.fileExistsAction` | string | No | `rename`, `overwrite`, or `skip` (overrides global) |
| `database.type` | string | **Yes** | `"MySQL"` or `"SQLServer"` |
| `database.*` | object | Yes | Connection settings |

#### Output File Placeholders

| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{date}` | 2026-01-10 | Current date |
| `{datetime}` | 2026-01-10_143045 | Date and time |
| `{year}` | 2026 | Current year |
| `{month}` | 01 | Current month |
| `{day}` | 10 | Current day |
| `{timestamp}` | 20260110_143045 | Timestamp |

---

## Using table2JsonConvert.py

### Starting the Script

```bash
cd ~/Documents/script/JSONConvert/
python3 table2JsonConvert.py
```

### Main Menu

```
========================================
  Table to JSON Export           v1.35
========================================

Configuration loaded successfully
Connected to MySQL: docInfo

Export Mode:
1. Manual Export (interactive)
2. Profile Export (use saved configuration)

Select mode (1-2):
```

---

### Manual Export Mode

Interactive export for one-time operations.

#### Step 1: Select Manual Mode
```
Select mode (1-2): 1
```

#### Step 2: Enter Table Name
```
Enter table name: activityLog
```

#### Step 3: Select Export Mode
```
Export Mode:
1. By Date (records before cutoff date)
2. By ID (records with ID less than value)
3. Custom WHERE clause
4. All records

Select mode (1-4):
```

#### Step 4: Confirm Deletion
```
Delete 1,523 exported records from table? (yes/no): yes
```

---

### Profile Export Mode

Use saved configurations for recurring exports.

```
=== Available Profiles ===
1. docInfo-activityLog
   DocInfo activity log export (MySQL)
2. analytics-events
   Analytics events archive (SQL Server)

Select profile number: 1

Run Mode:
1. Normal Export (default)
2. Validate Only (test with 1 row)

Select mode (1-2, or press Enter for normal):
```

---

## Command-Line Arguments & Automation

### Overview

The export script supports command-line arguments for automated/unattended operation, making it suitable for cron jobs and scheduled tasks.

### Available Arguments

```bash
python3 table2JsonConvert.py [OPTIONS]
```

| Argument | Short | Description |
|----------|-------|-------------|
| `--profile PROFILE_ID` | `-p` | Profile ID to use for export |
| `--auto` | `-a` | Auto mode - skip all confirmations |
| `--validate` | `-v` | Validate only - test with 1 row |
| `--list` | `-l` | List available profiles and exit |
| `--help` | `-h` | Show help message |

### Usage Examples

#### List Available Profiles

```bash
python3 table2JsonConvert.py --list
```

Output:
```
=== Available Profiles ===
1. docInfo-activityLog
   DocInfo activity log export profile
2. analytics-events
   Analytics events archive
```

#### Run Export with Specific Profile

```bash
# Interactive mode (will prompt for confirmation)
python3 table2JsonConvert.py --profile docInfo-activityLog

# Auto mode (no prompts - for cron)
python3 table2JsonConvert.py --profile docInfo-activityLog --auto

# Short form
python3 table2JsonConvert.py -p docInfo-activityLog -a
```

#### Validate Before Full Export

```bash
# Test with 1 row to verify configuration
python3 table2JsonConvert.py --profile docInfo-activityLog --validate
```

### Cron Job Setup

#### Basic Cron Example

```bash
# Edit crontab
crontab -e

# Add entry to run daily at 2:00 AM
0 2 * * * /opt/homebrew/opt/python@3.12/libexec/bin/python3 /Users/username/Documents/script/JSONConvert/table2JsonConvert.py --profile docInfo-activityLog --auto >> /Users/username/Documents/logs/cron_export.log 2>&1
```

#### Cron with Full Paths

```bash
# Recommended format with full paths
0 2 * * * /full/path/to/python3 /full/path/to/table2JsonConvert.py --profile PROFILE_ID --auto >> /full/path/to/cron.log 2>&1
```

#### Find Python Path

```bash
# macOS with Homebrew
which python3
# Usually: /opt/homebrew/opt/python@3.12/libexec/bin/python3

# Linux
which python3
# Usually: /usr/bin/python3
```

### Interactive vs Auto Mode

| Feature | Interactive Mode | Auto Mode (`--auto`) |
|---------|-----------------|---------------------|
| Delete confirmation | Prompts user | Auto-confirms |
| "Press Enter" prompts | Shows and waits | Skips |
| Screen clearing | Yes | No (better for logs) |
| Exit screen | Shows | Skips |
| Use case | Manual operation | Cron/scripts |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (check logs) |

### Logging for Automated Runs

When running from cron, output is captured to the specified log file. Additionally, the script logs to its configured log file:

```bash
# View recent log entries
tail -50 ~/Documents/logs/jsonConvert.log

# Watch log in real-time
tail -f ~/Documents/logs/jsonConvert.log
```

---

## Using json2TableConvert.py

### Starting the Script

```bash
python3 json2TableConvert.py
```

### Import Process

#### Step 1: Enter JSON File Path
```
Default export path: ~/Documents/script/JSONConvert/exports/
Enter JSON file path: exports/activityLog_2026-01-10.json
```

#### Step 2: Review Metadata
```
=== Export Metadata ===
Table: activityLog
Export Date: 2026-01-10 14:30:45
Record Count: 1,523
Profile ID: docInfo-activityLog
```

#### Step 3: Choose Import Mode
```
Import Mode:
1. Validate Only (dry run)
2. Import Data

Select mode (1-2):
```

---

## Profile Management

### Creating Profiles for Different Databases

You can have profiles for both MySQL and SQL Server in the same config:

```json
"profiles": [
  {
    "profileId": "mysql-users",
    "database": {
      "type": "MySQL",
      "host": "mysql-server.local"
    }
  },
  {
    "profileId": "sqlserver-orders",
    "database": {
      "type": "SQLServer",
      "host": "sqlserver.database.windows.net"
    }
  }
]
```

---

## Database-Specific Information

### MySQL

| Feature | MySQL Implementation |
|---------|---------------------|
| Table Structure | `DESCRIBE tableName` |
| Batch Delete | `DELETE FROM table WHERE ... LIMIT n` |
| Column Quoting | Backticks: `` `columnName` `` |
| Default Port | 3306 |
| Library | mysql-connector-python |

### SQL Server

| Feature | SQL Server Implementation |
|---------|--------------------------|
| Table Structure | `INFORMATION_SCHEMA.COLUMNS` |
| Batch Delete | `DELETE TOP (n) FROM table WHERE ...` |
| Column Quoting | Square brackets: `[columnName]` |
| Default Port | 1433 |
| Library | pymssql |

### SQL Differences to Note

**Date Functions:**
```sql
-- MySQL
WHERE createdDate < DATE_SUB(NOW(), INTERVAL 1 YEAR)

-- SQL Server
WHERE createdDate < DATEADD(year, -1, GETDATE())
```

**LIMIT vs TOP:**
```sql
-- MySQL
SELECT * FROM table LIMIT 100

-- SQL Server
SELECT TOP 100 * FROM table
```

---

## Advanced Features

### Mixed Database Profiles

Export from MySQL, import to SQL Server (or vice versa):

```bash
# Export from MySQL
python3 table2JsonConvert.py
# Use MySQL profile

# Import to SQL Server
python3 json2TableConvert.py
# Select SQL Server profile or manual config
```

### Large Dataset Handling

For exports over 10,000 rows:

1. **Increase batch size:**
   ```json
   "export": { "batchSize": 5000 }
   ```

2. **Monitor disk space:**
   ```bash
   df -h ~/Documents/script/JSONConvert/exports/
   ```

3. **Use validation mode first**

---

## Troubleshooting

### Connection Issues

#### MySQL Connection Failed
```bash
# Test connection
mysql -h HOST -u USER -p

# Check port accessibility
nc -zv HOST 3306
```

#### SQL Server Connection Failed
```bash
# Test with pymssql
python3 -c "import pymssql; conn = pymssql.connect('HOST', 'USER', 'PASS', 'DB'); print('OK')"

# Check port accessibility
nc -zv HOST 1433
```

### Library Issues

#### "ModuleNotFoundError: No module named 'pymssql'"
```bash
pip3 install pymssql
```

#### "ModuleNotFoundError: No module named 'mysql.connector'"
```bash
pip3 install mysql-connector-python
```

#### pymssql Installation Fails on macOS
```bash
brew install freetds
pip3 install pymssql
```

### Import Issues

#### Column Mismatch
Use validation mode to identify differences:
```bash
python3 json2TableConvert.py
# Select: 1 (Validate Only)
```

---

## Best Practices

### Data Safety

1. **Always validate first** - Use validation mode before actual exports/imports
2. **Backup before deletion** - Set `deleteAfterExport: false` initially
3. **Test on development** - Use a dev database for testing new profiles

### Performance

1. **Batch sizes:**
   - Small (< 1,000 rows): `batchSize: 100`
   - Medium (1,000-10,000): `batchSize: 1,000`
   - Large (> 10,000): `batchSize: 5,000`

2. **Run during off-peak hours** for large exports

### Security

1. **Protect configuration:**
   ```bash
   chmod 600 tableJsonConvert.json
   ```

2. **Secure exports:**
   ```bash
   chmod 700 ~/Documents/script/JSONConvert/exports/
   ```

3. **Don't commit passwords to git**

---

## Quick Reference

### Commands

```bash
# Export (interactive)
python3 table2JsonConvert.py

# Export (automated/cron)
python3 table2JsonConvert.py --profile PROFILE_ID --auto

# List profiles
python3 table2JsonConvert.py --list

# Validate export
python3 table2JsonConvert.py --profile PROFILE_ID --validate

# Import
python3 json2TableConvert.py

# Edit config
nano tableJsonConvert.json

# View logs
tail -f ~/Documents/logs/jsonConvert.log
```

### Database Type in Config

```json
"database": {
  "type": "MySQL"      // or "SQLServer"
}
```

---

**Copyright © 2026 Cloud Box 9 Inc. All rights reserved.**
