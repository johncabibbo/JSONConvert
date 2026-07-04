#!/opt/homebrew/opt/python@3.12/libexec/bin/python3
# =============================================================================
# Filename: table2JsonConvert.py
# Project: JSONConvert
# Version: 1.47
# Last Modified Date: 2026-03-01
# Category: Database Utilities
# OS: Mac/Linux
# Maintainer: Cloud Box 9
# -----------------------------------------------------------------------------
# Description:
#   Exports data from a MySQL table to JSON file and deletes exported records.
#
#   Features:
#     • Configurable database connection via JSON config file
#     • Export by date or ID with custom WHERE clauses
#     • Batch processing for large datasets
#     • Optional confirmation before deletion
#     • Comprehensive error handling and logging
#     • Transaction support for data integrity
#
# Usage:
#   Interactive:  python3 table2JsonConvert.py
#   Automated:    python3 table2JsonConvert.py --profile <profileId> --auto
#
#   Arguments:
#     --profile, -p <id>  Profile ID to use (from config file)
#     --auto, -a          Auto mode - skip all confirmations (for cron)
#     --validate, -v      Validate only - test with 1 row, no export
#     --list, -l          List available profiles and exit
#
#   Cron Example:
#     0 2 * * * /path/to/python3 /path/to/table2JsonConvert.py --profile docInfo-activityLog --auto >> /path/to/cron.log 2>&1
#
# Configuration:
#   Edit tableJsonConvert.json for database settings and defaults
#
# Notes:
#   • Exported data is deleted from source table after successful export
#   • Use json2TableConvert.py to restore data from JSON files
#   • All operations are logged to configured log file
# -----------------------------------------------------------------------------
# Revision History:
#   v1.47 — 2026-03-01 — Added settings logging: logs run mode, profile info, output file, SQL preview,
#                        and export settings to log file at script start and before export
#   v1.46 — 2026-03-01 — Added outputFilePostExt config field for export files (same pattern as logPostExt),
#                        refactored timestamp pattern logic into reusable applyPostExt() function
#   v1.45 — 2026-03-01 — Added logPostExt config field to insert timestamp before log file extension
#                        Supports: YYYY (year), MM (month), DD (day), HH (hour), mm (minutes), SS (seconds)
#   v1.44 — 2026-03-01 — Made logging CB9Lib compliant: replaced writeLog with CB9Lib Logger class,
#                        added script start/end logging with log level support (DEBUG/INFO/WARNING/ERROR)
#   v1.43 — 2026-03-01 — Fixed SQL Server support: added fetchAllAsDict() helper for dict results,
#                        updated table name regex to support [db].[schema].[table] syntax,
#                        fixed cursor(dictionary=True) which pymssql doesn't support
#   v1.42 — 2026-03-01 — Fixed pymssql compatibility: getDatabaseConnection now returns (conn, dbType) tuple
#                        instead of setting conn._db_type attribute (pymssql doesn't support custom attributes)
#   v1.41 — 2026-03-01 — Added fileExistsAction setting (overwrite/rename/skip) for handling existing export files
#   v1.40 — 2026-03-01 — Added command-line arguments for cron/automation (--profile, --auto, --validate, --list)
#                        Added "Press Enter to continue" at end of interactive sessions
#   v1.36 — 2026-03-01 — Fixed missing tableName in profile export metadata (caused import to fail with "Unknown" table)
#   v1.35 — 2026-01-11 — Capped batch deletion at maximum 100,000 records per batch
#   v1.34 — 2026-01-11 — Implemented batch deletion (20% at a time) to prevent hangs on large deletions
#   v1.33 — 2026-01-11 — Added full table count (SELECT COUNT(*) FROM table) at start and end with logging
#   v1.32 — 2026-01-11 — Implemented auto-deletion logic for profile exports with DELETE generation
#   v1.31 — 2026-01-11 — Enhanced log message for rows remaining after delete
#   v1.3 — 2026-01-11 — Added row counts (before/after export) and timestamps to log and screen
#   v1.2 — 2026-01-10 — Added validate mode with test export and progress tracking
#   v1.1 — 2026-01-10 — Added profile support with sourceSQL and date placeholders
#   v1.0 — 2026-01-10 — Initial creation
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # bundled CB9Lib (self-contained)
from CB9Lib import *

import json
import argparse
import mysql.connector
import pymssql
from datetime import datetime
from pathlib import Path

VERSION = "1.47"
CONFIG_FILE = "tableJsonConvert.json"
SCRIPT_NAME = "Table to JSON Export"

# Global logger instance (initialized when config is loaded)
logger = None


def applyPostExt(filePath, postExtPattern):
    """Apply a timestamp pattern to a filename, inserting before the extension.

    Args:
        filePath: The file path to modify
        postExtPattern: Pattern with placeholders (YYYY, MM, DD, HH, mm, SS)

    Returns:
        Modified file path with timestamp inserted before extension

    Example:
        applyPostExt("/path/to/file.json", "_YYYY_MM_DD-HHmm")
        -> "/path/to/file_2026_03_01-2315.json"
    """
    if not postExtPattern:
        return filePath

    # Replace date/time placeholders with actual values
    now = datetime.now()
    postExt = postExtPattern
    postExt = postExt.replace('YYYY', now.strftime('%Y'))
    postExt = postExt.replace('MM', now.strftime('%m'))    # Month (must come before mm)
    postExt = postExt.replace('DD', now.strftime('%d'))
    postExt = postExt.replace('HH', now.strftime('%H'))
    postExt = postExt.replace('mm', now.strftime('%M'))    # Minutes (lowercase)
    postExt = postExt.replace('SS', now.strftime('%S'))

    # Insert before file extension
    pathObj = Path(filePath)
    return str(pathObj.parent / f"{pathObj.stem}{postExt}{pathObj.suffix}")


def initLogger(config):
    """Initialize the CB9Lib Logger based on config settings."""
    global logger

    if not config.get('logging', {}).get('enabled', False):
        logger = None
        return None

    logPath = os.path.expanduser(config['logging']['logPath'])

    # Handle logPostExt - insert timestamp before file extension
    logPostExt = config['logging'].get('logPostExt', '')
    logPath = applyPostExt(logPath, logPostExt)

    logDir = os.path.dirname(logPath)
    if logDir and not os.path.exists(logDir):
        os.makedirs(logDir)

    # Map config logLevel to CB9Lib log level
    levelMap = {
        'DEBUG': DEBUG,
        'INFO': INFO,
        'WARNING': WARNING,
        'ERROR': ERROR,
        'CRITICAL': CRITICAL
    }
    configLevel = config['logging'].get('logLevel', 'INFO').upper()
    logLevel = levelMap.get(configLevel, INFO)

    logger = Logger(
        name=SCRIPT_NAME,
        level=logLevel,
        filename=logPath,
        console=False,  # Don't print to console, we handle that separately
        colored=False
    )

    return logger


def loadConfig():
    """Load configuration from JSON file."""
    try:
        configPath = Path(__file__).parent / CONFIG_FILE
        with open(configPath, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(color_text(f"Error: Config file '{CONFIG_FILE}' not found", fg=RED))
        return None
    except json.JSONDecodeError as e:
        print(color_text(f"Error: Invalid JSON in config file: {e}", fg=RED))
        return None


def getDatabaseConnection(config):
    """Establish database connection using config settings. Supports MySQL and SQL Server.

    Returns:
        tuple: (connection, dbType) where dbType is 'MYSQL' or 'SQLSERVER'
               Returns (None, None) on connection failure
    """
    try:
        dbConfig = config['database']
        dbType = dbConfig.get('type', 'MySQL').upper()

        if dbType == 'SQLSERVER':
            # SQL Server connection using pymssql
            conn = pymssql.connect(
                server=dbConfig['host'],
                user=dbConfig['user'],
                password=dbConfig['password'],
                database=dbConfig['database'],
                port=dbConfig.get('port', 1433)
            )
            print(color_text(f"Connected to SQL Server: {dbConfig['database']}", fg=GREEN))
        else:
            # MySQL connection (default)
            dbType = 'MYSQL'
            conn = mysql.connector.connect(
                host=dbConfig['host'],
                user=dbConfig['user'],
                password=dbConfig['password'],
                database=dbConfig['database'],
                port=dbConfig.get('port', 3306)
            )
            print(color_text(f"Connected to MySQL: {dbConfig['database']}", fg=GREEN))

        return conn, dbType
    except mysql.connector.Error as err:
        print(color_text(f"MySQL connection error: {err}", fg=RED))
        return None, None
    except pymssql.Error as err:
        print(color_text(f"SQL Server connection error: {err}", fg=RED))
        return None, None


def fetchAllAsDict(cursor, dbType='MYSQL'):
    """Fetch all rows from cursor as list of dictionaries.

    MySQL connector supports dictionary=True on cursor, but pymssql does not.
    This function provides consistent dict output for both database types.
    """
    rows = cursor.fetchall()
    if not rows:
        return []

    if dbType == 'MYSQL':
        # MySQL with dictionary cursor already returns dicts
        return rows
    else:
        # SQL Server: convert tuples to dicts using column names
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]


def getTableColumns(cursor, tableName, dbType='MYSQL'):
    """Get column names for the specified table. Supports MySQL and SQL Server."""
    try:
        if dbType == 'SQLSERVER':
            # SQL Server: use INFORMATION_SCHEMA
            cursor.execute(f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{tableName}'
                ORDER BY ORDINAL_POSITION
            """)
            columns = [row[0] for row in cursor.fetchall()]
        else:
            # MySQL: use DESCRIBE
            cursor.execute(f"DESCRIBE {tableName}")
            columns = [row[0] for row in cursor.fetchall()]
        return columns
    except (mysql.connector.Error, pymssql.Error) as err:
        print(color_text(f"Error getting table columns: {err}", fg=RED))
        return None


def buildWhereClause(mode, value, customClause=""):
    """Build WHERE clause based on export mode."""
    if customClause:
        return customClause, {}

    if mode == "date":
        return "createdDate < %s", [value]
    elif mode == "id":
        # Assume primary key is first column or 'id'
        return "id < %s", [value]
    else:
        return "", []


def exportTableData(conn, tableName, whereClause, params, outputFile, config, dbType='MYSQL'):
    """Export table data to JSON file."""
    # MySQL supports dictionary=True, pymssql does not
    if dbType == 'MYSQL':
        cursor = conn.cursor(dictionary=True)
    else:
        cursor = conn.cursor()

    try:
        # Build SELECT query
        sql = f"SELECT * FROM {tableName}"
        if whereClause:
            sql += f" WHERE {whereClause}"

        print(color_text(f"\nExecuting query: {sql}", fg=CYAN))
        if params:
            print(color_text(f"Parameters: {params}", fg=CYAN))

        cursor.execute(sql, params)
        rows = fetchAllAsDict(cursor, dbType)

        if not rows:
            print(color_text("No records found matching criteria", fg=YELLOW))
            return 0

        print(color_text(f"Found {len(rows)} records to export", fg=GREEN))

        # Convert datetime objects to strings for JSON serialization
        for row in rows:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.strftime(config['export']['dateFormat'])

        # Create export data structure
        exportData = {
            "_metadata": {
                "exportDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tableName": tableName,
                "recordCount": len(rows),
                "whereClause": whereClause if whereClause else "None"
            },
            "records": rows
        }

        # Ensure output directory exists
        outputPath = Path(outputFile)
        outputPath.parent.mkdir(parents=True, exist_ok=True)

        # Write to JSON file
        with open(outputFile, 'w') as f:
            json.dump(exportData, f, indent=2, default=str)

        print(color_text(f"Data exported to: {outputFile}", fg=GREEN))
        return len(rows)

    except (mysql.connector.Error, pymssql.Error) as err:
        print(color_text(f"Error exporting data: {err}", fg=RED))
        return 0
    finally:
        cursor.close()


def deleteExportedRecords(conn, tableName, whereClause, params, dbType='MYSQL'):
    """Delete exported records from the table in batches of 20%. Supports MySQL and SQL Server."""
    cursor = conn.cursor()

    try:
        # First, count how many records will be deleted
        countSql = f"SELECT COUNT(*) FROM {tableName}"
        if whereClause:
            countSql += f" WHERE {whereClause}"

        if params:
            cursor.execute(countSql, params)
        else:
            cursor.execute(countSql)

        totalToDelete = cursor.fetchone()[0]

        if totalToDelete == 0:
            print(color_text("\nNo records to delete", fg=YELLOW))
            return 0

        print(color_text(f"\n=== Batch Deletion ===", fg=CYAN))
        print(color_text(f"Total records to delete: {totalToDelete}", fg=CYAN))

        # Calculate batch size (20% of total, but max 100,000)
        calculatedBatchSize = int(totalToDelete * 0.20)
        batchSize = max(1, min(calculatedBatchSize, 100000))
        print(color_text(f"Batch size (20%, max 100K): {batchSize} records per batch", fg=CYAN))

        totalDeleted = 0
        batchNum = 0

        # Delete in batches until all records are gone
        while True:
            batchNum += 1

            # Build DELETE with batch limit (syntax differs by database)
            if dbType == 'SQLSERVER':
                # SQL Server uses DELETE TOP (n)
                sql = f"DELETE TOP ({batchSize}) FROM {tableName}"
                if whereClause:
                    sql += f" WHERE {whereClause}"
            else:
                # MySQL uses DELETE ... LIMIT n
                sql = f"DELETE FROM {tableName}"
                if whereClause:
                    sql += f" WHERE {whereClause}"
                sql += f" LIMIT {batchSize}"

            print(color_text(f"\nBatch {batchNum}: Deleting up to {batchSize} records...", fg=CYAN))

            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            deletedInBatch = cursor.rowcount
            conn.commit()

            totalDeleted += deletedInBatch
            print(color_text(f"  Deleted {deletedInBatch} records (Total: {totalDeleted}/{totalToDelete})", fg=GREEN))

            # If we deleted fewer records than batch size, we're done
            if deletedInBatch < batchSize or deletedInBatch == 0:
                break

            # Small delay between batches to reduce load
            import time
            time.sleep(0.5)

        print(color_text(f"\nTotal deleted: {totalDeleted} records in {batchNum} batch(es)", fg=GREEN))
        return totalDeleted

    except (mysql.connector.Error, pymssql.Error) as err:
        conn.rollback()
        print(color_text(f"Error deleting records: {err}", fg=RED))
        return totalDeleted if 'totalDeleted' in locals() else 0
    finally:
        cursor.close()


def getRowCount(conn, tableName, whereClause="", params=None):
    """Get count of rows in table matching the WHERE clause. Supports MySQL and SQL Server."""
    cursor = conn.cursor()
    try:
        sql = f"SELECT COUNT(*) FROM {tableName}"
        if whereClause:
            sql += f" WHERE {whereClause}"

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        count = cursor.fetchone()[0]
        return count
    except (mysql.connector.Error, pymssql.Error) as err:
        print(color_text(f"Error counting rows: {err}", fg=RED))
        return 0
    finally:
        cursor.close()


def writeLog(config, message, level='INFO'):
    """Write message to log file using CB9Lib Logger.

    Args:
        config: Configuration dictionary (used to check if logging enabled)
        message: Log message
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    global logger

    if logger is None:
        return

    level = level.upper()
    if level == 'DEBUG':
        logger.debug(message)
    elif level == 'WARNING':
        logger.warning(message)
    elif level == 'ERROR':
        logger.error(message)
    elif level == 'CRITICAL':
        logger.critical(message)
    else:
        logger.info(message)


def handleExistingFile(outputFile, config, profileExport=None):
    """Handle existing file based on fileExistsAction setting.

    Args:
        outputFile: The target output file path
        config: Main configuration dictionary
        profileExport: Profile-specific export settings (optional, overrides config)

    Returns:
        tuple: (finalPath, action) where action is 'proceed', 'renamed', or 'skip'
               Returns (None, 'skip') if export should be skipped
    """
    # Check if file exists
    if not os.path.exists(outputFile):
        return outputFile, 'proceed'

    # Get fileExistsAction setting (profile overrides global)
    if profileExport and 'fileExistsAction' in profileExport:
        action = profileExport['fileExistsAction'].lower()
    else:
        action = config.get('export', {}).get('fileExistsAction', 'rename').lower()

    if action == 'overwrite':
        print(color_text(f"File exists: {outputFile}", fg=YELLOW))
        print(color_text("Action: Overwriting existing file", fg=YELLOW))
        return outputFile, 'overwrite'

    elif action == 'skip':
        print(color_text(f"File exists: {outputFile}", fg=YELLOW))
        print(color_text("Action: Skipping export (fileExistsAction=skip)", fg=RED))
        return None, 'skip'

    else:  # Default to 'rename'
        # Generate new filename with timestamp
        basePath = Path(outputFile)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        newName = f"{basePath.stem}_{timestamp}{basePath.suffix}"
        newPath = str(basePath.parent / newName)

        print(color_text(f"File exists: {outputFile}", fg=YELLOW))
        print(color_text(f"Action: Renaming to {newName}", fg=CYAN))
        return newPath, 'renamed'


def listProfiles(config):
    """List available profiles from config."""
    profiles = config.get('profiles', [])
    if not profiles:
        print(color_text("No profiles found in configuration", fg=YELLOW))
        return []

    print(color_text("\n=== Available Profiles ===", fg=CYAN))
    for i, profile in enumerate(profiles, 1):
        print(color_text(f"{i}. {profile['profileId']}", fg=GREEN))
        if 'description' in profile:
            print(color_text(f"   {profile['description']}", fg=CYAN))
    print()

    return profiles


def getProfile(config, profileId):
    """Get a specific profile by ID."""
    profiles = config.get('profiles', [])
    for profile in profiles:
        if profile['profileId'] == profileId:
            return profile
    return None


def replaceDatePlaceholders(text):
    """Replace date placeholders in text with actual date values."""
    now = datetime.now()
    replacements = {
        '{date}': now.strftime('%Y-%m-%d'),
        '{datetime}': now.strftime('%Y-%m-%d_%H%M%S'),
        '{year}': now.strftime('%Y'),
        '{month}': now.strftime('%m'),
        '{day}': now.strftime('%d'),
        '{timestamp}': now.strftime('%Y%m%d_%H%M%S')
    }

    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    return text


def exportWithProfile(profile, config, validateOnly=False, autoMode=False):
    """Export data using a profile configuration.

    Args:
        profile: Profile configuration dictionary
        config: Main configuration dictionary
        validateOnly: If True, only validate without exporting
        autoMode: If True, skip all confirmations (for cron/automated runs)
    """
    print(color_text(f"\n=== Using Profile: {profile['profileId']} ===", fg=CYAN))

    # Get profile-specific settings
    profileExport = profile.get('export', {})
    profileDb = profile.get('database', config.get('database', {}))
    profileLogging = profile.get('logging', config.get('logging', {}))

    sourceSQL = profileExport.get('sourceSQL', '')
    outputFile = profileExport.get('outputFile', '')
    deleteAfterExport = profileExport.get('deleteAfterExport', False)

    if not sourceSQL:
        print(color_text("Error: Profile has no sourceSQL defined", fg=RED))
        return False

    if not outputFile:
        print(color_text("Error: Profile has no outputFile defined", fg=RED))
        return False

    # Replace date placeholders in output filename
    outputFile = replaceDatePlaceholders(outputFile)
    outputFile = os.path.expanduser(outputFile)

    # Apply outputFilePostExt if specified (profile overrides global)
    outputFilePostExt = profileExport.get('outputFilePostExt', config.get('export', {}).get('outputFilePostExt', ''))
    outputFile = applyPostExt(outputFile, outputFilePostExt)

    # Handle existing file
    outputFile, fileAction = handleExistingFile(outputFile, config, profileExport)
    if fileAction == 'skip':
        writeLog(config, f"Profile {profile['profileId']}: Export skipped - file already exists")
        return False

    print(color_text(f"SQL: {sourceSQL}", fg=CYAN))
    print(color_text(f"Output: {outputFile}", fg=CYAN))
    print(color_text(f"Delete after export: {deleteAfterExport}", fg=CYAN))

    # Log profile settings
    if logger:
        logger.info(f"----- Profile Settings -----")
        logger.info(f"Profile ID: {profile['profileId']}")
        logger.info(f"Description: {profile.get('description', 'N/A')}")
        logger.info(f"Output file: {outputFile}")
        logger.info(f"Delete after export: {deleteAfterExport}")
        logger.info(f"Validate only: {validateOnly}")
        logger.info(f"Auto mode: {autoMode}")
        # Log truncated SQL (first 100 chars)
        sqlPreview = sourceSQL[:100] + '...' if len(sourceSQL) > 100 else sourceSQL
        logger.info(f"Source SQL: {sqlPreview}")
        logger.info(f"----------------------------")

    # Create temporary config with profile settings
    tempConfig = {
        'database': profileDb,
        'export': {
            'dateFormat': profileExport.get('dateFormat', config['export'].get('dateFormat', '%Y-%m-%d %H:%M:%S')),
            'confirmBeforeDelete': config['export'].get('confirmBeforeDelete', True)
        },
        'logging': profileLogging
    }

    # Connect to database
    print(color_text("\nConnecting to database...", fg=CYAN))
    conn, dbType = getDatabaseConnection(tempConfig)
    if not conn:
        return False

    print(color_text("Database connected successfully", fg=GREEN))

    try:
        # Log start timestamp
        startTime = datetime.now()
        startTimestamp = startTime.strftime("%Y-%m-%d %H:%M:%S")
        writeLog(tempConfig, f"=== EXPORT START: {profile['profileId']} at {startTimestamp} ===")

        # Extract table name from sourceSQL for full table count
        # Supports: tableName, [tableName], schema.table, [db].[schema].[table]
        import re
        tableMatch = re.search(r'FROM\s+([\[\]\w.]+)', sourceSQL, re.IGNORECASE)
        tableName = tableMatch.group(1) if tableMatch else "unknown"

        # Get FULL table count at START (before any operations)
        initialFullCount = getRowCount(conn, tableName)
        print(color_text(f"\n=== Initial Table Count ===", fg=CYAN))
        print(color_text(f"Total rows in table '{tableName}' at start: {initialFullCount}", fg=GREEN))
        writeLog(tempConfig, f"Full table count at START: {initialFullCount} rows in '{tableName}'")

        # MySQL supports dictionary=True, pymssql does not
        if dbType == 'MYSQL':
            cursor = conn.cursor(dictionary=True)
        else:
            cursor = conn.cursor()

        # Execute sourceSQL to get records matching criteria
        print(color_text(f"\nExecuting export query...", fg=CYAN))
        cursor.execute(sourceSQL)
        rows = fetchAllAsDict(cursor, dbType)

        if not rows:
            print(color_text("No records found matching criteria", fg=YELLOW))
            cursor.close()

            # Get final full count even if no records to export
            finalFullCount = getRowCount(conn, tableName)
            writeLog(tempConfig, f"Full table count at END: {finalFullCount} rows in '{tableName}'")

            endTime = datetime.now()
            endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
            writeLog(tempConfig, f"=== EXPORT END: {profile['profileId']} at {endTimestamp} (No records) ===")
            return False

        totalRows = len(rows)
        print(color_text(f"Rows matching export criteria: {totalRows}", fg=GREEN))
        writeLog(tempConfig, f"Rows matching export criteria: {totalRows}")

        # VALIDATE MODE
        if validateOnly:
            print(color_text("\n=== VALIDATION MODE ===", fg=YELLOW))
            print(color_text(f"Records found: {totalRows}", fg=CYAN))

            # Test export with 1 row
            print(color_text("\nExporting 1 test row...", fg=CYAN))
            testRow = rows[0]

            # Convert datetime objects for test row
            for key, value in testRow.items():
                if isinstance(value, datetime):
                    testRow[key] = value.strftime(tempConfig['export']['dateFormat'])

            # Create test export data
            testExportData = {
                "_metadata": {
                    "exportDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "profileId": profile['profileId'],
                    "sourceSQL": sourceSQL,
                    "recordCount": 1,
                    "deleteAfterExport": deleteAfterExport,
                    "validationTest": True
                },
                "records": [testRow]
            }

            # Create test filename
            testOutputFile = outputFile.replace('.json', '_TEST.json')

            # Ensure output directory exists
            outputPath = Path(testOutputFile)
            outputPath.parent.mkdir(parents=True, exist_ok=True)

            # Write test file
            with open(testOutputFile, 'w') as f:
                json.dump(testExportData, f, indent=2, default=str)

            # Get file size
            fileSize = os.path.getsize(testOutputFile)
            fileSizeKB = fileSize / 1024

            print(color_text(f"Test file created: {testOutputFile}", fg=GREEN))
            print(color_text(f"Test file size: {fileSize} bytes ({fileSizeKB:.2f} KB)", fg=CYAN))

            # Calculate estimated full export size
            estimatedSize = fileSize * totalRows
            estimatedSizeKB = estimatedSize / 1024
            estimatedSizeMB = estimatedSizeKB / 1024

            print(color_text(f"\nEstimated full export size:", fg=YELLOW))
            if estimatedSizeMB > 1:
                print(color_text(f"  {estimatedSizeMB:.2f} MB", fg=YELLOW))
            else:
                print(color_text(f"  {estimatedSizeKB:.2f} KB", fg=YELLOW))

            # Delete test file
            os.remove(testOutputFile)
            print(color_text(f"\nTest file deleted", fg=GREEN))

            print(color_text("\n=== Validation Summary ===", fg=CYAN))
            print(color_text(f"Total rows: {totalRows}", fg=CYAN))
            print(color_text(f"Estimated size: {estimatedSizeMB:.2f} MB" if estimatedSizeMB > 1 else f"Estimated size: {estimatedSizeKB:.2f} KB", fg=CYAN))
            print(color_text(f"Output file: {outputFile}", fg=CYAN))
            print(color_text("\nValidation completed successfully!", fg=GREEN))

            cursor.close()

            # Get FULL table count at END (validation mode - no changes made)
            finalFullCount = getRowCount(conn, tableName)
            writeLog(tempConfig, f"Full table count at END: {finalFullCount} rows in '{tableName}' (no changes - validation only)")

            # Log end timestamp
            endTime = datetime.now()
            endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
            writeLog(tempConfig, f"=== EXPORT END: {profile['profileId']} at {endTimestamp} (Validation mode) ===")

            return True

        # NORMAL EXPORT MODE
        print(color_text(f"\n=== Starting Export ===", fg=CYAN))
        print(color_text(f"Total rows: {totalRows}", fg=GREEN))

        # Convert datetime objects to strings for JSON serialization
        print(color_text("Converting data...", fg=CYAN))
        for i, row in enumerate(rows, 1):
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.strftime(tempConfig['export']['dateFormat'])

            # Show progress every 100 rows
            if i % 100 == 0:
                progress = (i / totalRows) * 100
                print(color_text(f"  Processed {i}/{totalRows} rows ({progress:.1f}%)", fg=CYAN))

        # Create export data structure
        exportData = {
            "_metadata": {
                "exportDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tableName": tableName,
                "profileId": profile['profileId'],
                "sourceSQL": sourceSQL,
                "recordCount": len(rows),
                "deleteAfterExport": deleteAfterExport
            },
            "records": rows
        }

        # Ensure output directory exists
        outputPath = Path(outputFile)
        outputPath.parent.mkdir(parents=True, exist_ok=True)

        # Write to JSON file
        print(color_text("\nWriting to file...", fg=CYAN))
        with open(outputFile, 'w') as f:
            json.dump(exportData, f, indent=2, default=str)

        # Get final file size
        fileSize = os.path.getsize(outputFile)
        fileSizeKB = fileSize / 1024
        fileSizeMB = fileSizeKB / 1024

        print(color_text(f"\nData exported to: {outputFile}", fg=GREEN))
        if fileSizeMB > 1:
            print(color_text(f"File size: {fileSizeMB:.2f} MB", fg=CYAN))
        else:
            print(color_text(f"File size: {fileSizeKB:.2f} KB", fg=CYAN))

        cursor.close()

        # Handle deletion if enabled
        if deleteAfterExport:
            deleteSQL = None

            # Check if explicit DELETE SQL is provided
            if 'delete' in profileExport:
                deleteSQL = profileExport['delete']
                print(color_text(f"\nUsing explicit DELETE SQL from profile", fg=CYAN))
            else:
                # Auto-generate DELETE from SELECT statement
                # Parse: SELECT * FROM tableName WHERE conditions
                import re

                # Extract table name and WHERE clause
                # Supports: tableName, [tableName], schema.table, [db].[schema].[table]
                match = re.search(r'FROM\s+([\[\]\w.]+)\s*(WHERE\s+.+)?', sourceSQL, re.IGNORECASE)

                if match:
                    tableName = match.group(1)
                    whereClause = match.group(2) if match.group(2) else ""

                    deleteSQL = f"DELETE FROM {tableName} {whereClause}".strip()

                    print(color_text("\n=== Auto-generated DELETE Statement ===", fg=YELLOW))
                    print(color_text(f"DELETE SQL: {deleteSQL}", fg=CYAN))
                    print(color_text("This will delete the exported records from the table.", fg=YELLOW))
                else:
                    print(color_text("\nError: Could not parse SELECT statement to generate DELETE", fg=RED))
                    print(color_text("Consider adding explicit 'delete' SQL to profile", fg=YELLOW))
                    writeLog(tempConfig, f"Profile {profile['profileId']}: Exported {len(rows)} records (delete failed - parse error)")
                    deleteSQL = None

            # Execute deletion if we have a valid DELETE statement
            if deleteSQL:
                # Skip confirmation in autoMode, otherwise check config
                if not autoMode and tempConfig['export'].get('confirmBeforeDelete', True):
                    print()
                    confirm = input(color_text(f"Delete {len(rows)} exported records? (yes/no): ", fg=YELLOW)).strip().lower()
                    if confirm != 'yes':
                        print(color_text("Deletion cancelled. Data exported but not deleted.", fg=YELLOW))
                        writeLog(tempConfig, f"Profile {profile['profileId']}: Exported {len(rows)} records (deletion cancelled)")

                        # Log end timestamp
                        endTime = datetime.now()
                        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
                        duration = (endTime - startTime).total_seconds()
                        writeLog(tempConfig, f"=== EXPORT END: {profile['profileId']} at {endTimestamp} (Duration: {duration:.2f}s, no delete) ===")
                        return True
                elif autoMode:
                    print(color_text(f"\nAuto mode: Proceeding with deletion of {len(rows)} records...", fg=CYAN))

                # Execute the DELETE statement in batches
                try:
                    deleteCursor = conn.cursor()

                    # Count records to delete
                    print(color_text(f"\n=== Batch Deletion ===", fg=CYAN))
                    print(color_text(f"Total records to delete: {len(rows)}", fg=CYAN))

                    # Calculate batch size (20% of total, but max 100,000)
                    totalToDelete = len(rows)
                    calculatedBatchSize = int(totalToDelete * 0.20)
                    batchSize = max(1, min(calculatedBatchSize, 100000))
                    print(color_text(f"Batch size (20%, max 100K): {batchSize} records per batch", fg=CYAN))

                    totalDeleted = 0
                    batchNum = 0

                    # Parse DELETE to add batch limit
                    baseDeleteSQL = deleteSQL

                    # Delete in batches until all records are gone
                    while True:
                        batchNum += 1

                        # Build batch DELETE (syntax differs by database)
                        if dbType == 'SQLSERVER':
                            # SQL Server: DELETE TOP (n) FROM table WHERE ...
                            # Need to reconstruct for TOP syntax
                            match = re.search(r'DELETE\s+FROM\s+([\[\]\w.]+)\s*(WHERE\s+.+)?', baseDeleteSQL, re.IGNORECASE)
                            if match:
                                delTable = match.group(1)
                                delWhere = match.group(2) if match.group(2) else ""
                                batchDeleteSQL = f"DELETE TOP ({batchSize}) FROM {delTable} {delWhere}".strip()
                            else:
                                batchDeleteSQL = f"{baseDeleteSQL}"  # Fallback
                        else:
                            # MySQL: DELETE FROM table WHERE ... LIMIT n
                            batchDeleteSQL = f"{baseDeleteSQL} LIMIT {batchSize}"

                        print(color_text(f"\nBatch {batchNum}: Deleting up to {batchSize} records...", fg=CYAN))

                        deleteCursor.execute(batchDeleteSQL)
                        deletedInBatch = deleteCursor.rowcount
                        conn.commit()

                        totalDeleted += deletedInBatch
                        print(color_text(f"  Deleted {deletedInBatch} records (Total: {totalDeleted}/{totalToDelete})", fg=GREEN))
                        writeLog(tempConfig, f"Batch {batchNum}: Deleted {deletedInBatch} records (Total: {totalDeleted}/{totalToDelete})")

                        # If we deleted fewer records than batch size, we're done
                        if deletedInBatch < batchSize or deletedInBatch == 0:
                            break

                        # Small delay between batches to reduce load
                        import time
                        time.sleep(0.5)

                    deleteCursor.close()

                    print(color_text(f"\nTotal deleted: {totalDeleted} records in {batchNum} batch(es)", fg=GREEN))
                    writeLog(tempConfig, f"Deleted {totalDeleted} records from table in {batchNum} batch(es)")

                    # Get remaining row count
                    match = re.search(r'FROM\s+([\[\]\w.]+)', sourceSQL, re.IGNORECASE)
                    if match:
                        tableName = match.group(1)
                        remainingCount = getRowCount(conn, tableName)
                        print(color_text(f"Rows remaining in table: {remainingCount}", fg=CYAN))
                        writeLog(tempConfig, f"Rows remaining in table after delete: {remainingCount}")

                except (mysql.connector.Error, pymssql.Error) as err:
                    conn.rollback()
                    print(color_text(f"Error deleting records: {err}", fg=RED))
                    writeLog(tempConfig, f"Profile {profile['profileId']}: DELETE ERROR: {err}")
                    print(color_text("Data was exported but deletion failed", fg=YELLOW))

        # Display final summary with row counts
        print(color_text(f"\n=== Export Summary ===", fg=GREEN))
        print(color_text(f"Rows exported: {len(rows)}", fg=GREEN))
        print(color_text(f"Export file: {outputFile}", fg=CYAN))

        # Get FULL table count at END (after all operations including deletion)
        finalFullCount = getRowCount(conn, tableName)
        print(color_text(f"\n=== Final Table Count ===", fg=CYAN))
        print(color_text(f"Total rows in table '{tableName}' at end: {finalFullCount}", fg=GREEN))
        writeLog(tempConfig, f"Full table count at END: {finalFullCount} rows in '{tableName}'")

        # Log completion
        writeLog(tempConfig, f"Profile {profile['profileId']}: Exported {len(rows)} records to {outputFile}")

        # Log end timestamp
        endTime = datetime.now()
        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
        duration = (endTime - startTime).total_seconds()
        writeLog(tempConfig, f"=== EXPORT END: {profile['profileId']} at {endTimestamp} (Duration: {duration:.2f}s) ===")

        print(color_text("\nExport completed successfully!", fg=GREEN))
        return True

    except (mysql.connector.Error, pymssql.Error) as err:
        print(color_text(f"Error executing query: {err}", fg=RED))
        writeLog(tempConfig, f"Profile {profile['profileId']} ERROR: {err}")

        # Try to get final count even on error
        try:
            if 'tableName' in locals():
                finalFullCount = getRowCount(conn, tableName)
                writeLog(tempConfig, f"Full table count at END: {finalFullCount} rows in '{tableName}' (after error)")
        except:
            pass

        endTime = datetime.now()
        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
        writeLog(tempConfig, f"=== EXPORT END: {profile['profileId']} at {endTimestamp} (FAILED) ===")
        return False
    except Exception as e:
        print(color_text(f"Unexpected error: {e}", fg=RED))
        writeLog(tempConfig, f"Profile {profile['profileId']} ERROR: {e}")

        # Try to get final count even on error
        try:
            if 'tableName' in locals():
                finalFullCount = getRowCount(conn, tableName)
                writeLog(tempConfig, f"Full table count at END: {finalFullCount} rows in '{tableName}' (after error)")
        except:
            pass

        endTime = datetime.now()
        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
        writeLog(tempConfig, f"=== EXPORT END: {profile['profileId']} at {endTimestamp} (FAILED) ===")
        return False
    finally:
        conn.close()


def manualExport(config):
    """Perform manual export with interactive prompts."""
    # Get table name
    tableName = input(color_text("\nEnter table name: ", fg=CYAN)).strip()
    if not tableName:
        print(color_text("Table name is required", fg=RED))
        pause()
        return

    # Get output filename
    defaultPath = os.path.expanduser(config['export']['defaultOutputPath'])
    defaultFile = f"{tableName}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    print(color_text(f"\nDefault output: {defaultPath}{defaultFile}", fg=CYAN))
    outputFile = input(color_text("Enter output filename (or press Enter for default): ", fg=CYAN)).strip()

    if not outputFile:
        outputFile = os.path.join(defaultPath, defaultFile)
    elif not outputFile.startswith('/') and not outputFile.startswith('~'):
        outputFile = os.path.join(defaultPath, outputFile)

    outputFile = os.path.expanduser(outputFile)

    # Apply outputFilePostExt if specified
    outputFilePostExt = config.get('export', {}).get('outputFilePostExt', '')
    outputFile = applyPostExt(outputFile, outputFilePostExt)

    # Handle existing file
    outputFile, fileAction = handleExistingFile(outputFile, config)
    if fileAction == 'skip':
        writeLog(config, f"Manual export skipped - file already exists: {outputFile}")
        pause("Press Enter to continue...")
        return

    # Get export mode
    print(color_text("\nExport Mode:", fg=CYAN))
    print("1. By Date (records before cutoff date)")
    print("2. By ID (records with ID less than value)")
    print("3. Custom WHERE clause")
    print("4. All records")

    mode = input(color_text("\nSelect mode (1-4): ", fg=CYAN)).strip()

    whereClause = ""
    params = []

    if mode == "1":
        cutoffDate = input(color_text("Enter cutoff date (YYYY-MM-DD): ", fg=CYAN)).strip()
        whereClause, params = buildWhereClause("date", cutoffDate)
    elif mode == "2":
        cutoffId = input(color_text("Enter cutoff ID: ", fg=CYAN)).strip()
        whereClause, params = buildWhereClause("id", cutoffId)
    elif mode == "3":
        whereClause = input(color_text("Enter WHERE clause (without WHERE keyword): ", fg=CYAN)).strip()
        params = []

    # Log manual export settings
    if logger:
        logger.info(f"----- Manual Export Settings -----")
        logger.info(f"Mode: Manual Export (Interactive)")
        logger.info(f"Table: {tableName}")
        logger.info(f"Output file: {outputFile}")
        if whereClause:
            logger.info(f"WHERE clause: {whereClause}")
        else:
            logger.info(f"WHERE clause: (none - all records)")
        logger.info(f"----------------------------------")

    # Connect to database
    print(color_text("\nConnecting to database...", fg=CYAN))
    conn, dbType = getDatabaseConnection(config)
    if not conn:
        pause("Press Enter to exit...")
        return

    print(color_text("Database connected successfully", fg=GREEN))

    try:
        # Log start timestamp
        startTime = datetime.now()
        startTimestamp = startTime.strftime("%Y-%m-%d %H:%M:%S")
        writeLog(config, f"=== EXPORT START: {tableName} at {startTimestamp} ===")

        # Get FULL table count at START (before any operations)
        initialFullCount = getRowCount(conn, tableName)
        print(color_text(f"\n=== Initial Table Count ===", fg=CYAN))
        print(color_text(f"Total rows in table '{tableName}' at start: {initialFullCount}", fg=GREEN))
        writeLog(config, f"Full table count at START: {initialFullCount} rows in '{tableName}'")

        # Get count of rows matching criteria
        if whereClause:
            matchingCount = getRowCount(conn, tableName, whereClause, params)
            print(color_text(f"Rows matching export criteria: {matchingCount}", fg=GREEN))
            writeLog(config, f"Rows matching export criteria: {matchingCount}")

        # Export data
        recordCount = exportTableData(conn, tableName, whereClause, params, outputFile, config, dbType)

        if recordCount == 0:
            print(color_text("\nNo records exported", fg=YELLOW))

            # Get FULL table count at END (no changes made)
            finalFullCount = getRowCount(conn, tableName)
            writeLog(config, f"Full table count at END: {finalFullCount} rows in '{tableName}' (no changes)")

            endTime = datetime.now()
            endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
            writeLog(config, f"=== EXPORT END: {tableName} at {endTimestamp} (No records) ===")
            return

        # Confirm deletion
        if config['export'].get('confirmBeforeDelete', True):
            print()
            confirm = input(color_text(f"Delete {recordCount} exported records from table? (yes/no): ", fg=YELLOW)).strip().lower()
            if confirm != 'yes':
                print(color_text("Deletion cancelled. Data exported but not deleted from table.", fg=YELLOW))
                writeLog(config, f"Table2JSON: Exported {recordCount} records from {tableName} (deletion cancelled)")

                # Get FULL table count at END (no deletion occurred)
                finalFullCount = getRowCount(conn, tableName)
                writeLog(config, f"Full table count at END: {finalFullCount} rows in '{tableName}' (deletion cancelled)")

                # Log end timestamp
                endTime = datetime.now()
                endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
                duration = (endTime - startTime).total_seconds()
                writeLog(config, f"=== EXPORT END: {tableName} at {endTimestamp} (Duration: {duration:.2f}s) ===")
                return

        # Delete exported records
        deletedCount = deleteExportedRecords(conn, tableName, whereClause, params, dbType)

        # Get FULL table count at END (after deletion)
        finalFullCount = getRowCount(conn, tableName)
        print(color_text(f"\n=== Export Summary ===", fg=GREEN))
        print(color_text(f"Rows exported and deleted: {deletedCount}", fg=GREEN))
        print(color_text(f"\n=== Final Table Count ===", fg=CYAN))
        print(color_text(f"Total rows in table '{tableName}' at end: {finalFullCount}", fg=GREEN))
        writeLog(config, f"Full table count at END: {finalFullCount} rows in '{tableName}'")

        # Log operation
        writeLog(config, f"Table2JSON: Exported and deleted {deletedCount} records from {tableName}")

        # Log end timestamp
        endTime = datetime.now()
        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
        duration = (endTime - startTime).total_seconds()
        writeLog(config, f"=== EXPORT END: {tableName} at {endTimestamp} (Duration: {duration:.2f}s) ===")

        print()
        print(color_text("Export and deletion completed successfully!", fg=GREEN))

    except Exception as e:
        print(color_text(f"\nUnexpected error: {e}", fg=RED))
        writeLog(config, f"Table2JSON ERROR: {e}")

        # Try to get final count even on error
        try:
            finalFullCount = getRowCount(conn, tableName)
            writeLog(config, f"Full table count at END: {finalFullCount} rows in '{tableName}' (after error)")
        except:
            pass

        endTime = datetime.now()
        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
        writeLog(config, f"=== EXPORT END: {tableName} at {endTimestamp} (FAILED) ===")
    finally:
        conn.close()
        print()
        pause("Press Enter to continue...")


def parseArgs():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export MySQL table data to JSON file',
        epilog='Example: python3 table2JsonConvert.py --profile docInfo-activityLog --auto'
    )
    parser.add_argument('--profile', '-p',
                        help='Profile ID to use for export (from config file)')
    parser.add_argument('--auto', '-a', action='store_true',
                        help='Run in auto mode (no confirmations, for cron jobs)')
    parser.add_argument('--validate', '-v', action='store_true',
                        help='Validate only (test with 1 row, no export)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available profiles and exit')
    return parser.parse_args()


def main():
    """Main application function."""
    global logger
    args = parseArgs()

    # Check if running in auto mode (non-interactive)
    autoMode = args.auto or args.profile is not None

    # Don't clear screen in auto mode (for cron log readability)
    if not autoMode:
        clear_screen()

    header("Table to JSON Export", VERSION)

    # Load configuration
    config = loadConfig()
    if not config:
        if not autoMode:
            pause("Press Enter to exit...")
        return False

    # Initialize logger from config
    initLogger(config)

    # Log script start
    if logger:
        logger.info(f"{'='*60}")
        logger.info(f"SCRIPT START: {SCRIPT_NAME} v{VERSION}")
        logger.info(f"{'='*60}")
        logger.info(f"Run mode: {'Auto (--profile)' if args.profile else 'Interactive'}")
        if args.profile:
            logger.info(f"Profile argument: {args.profile}")
        if args.auto:
            logger.info(f"Auto mode: Yes (skip confirmations)")
        if args.validate:
            logger.info(f"Validate only: Yes")

    print(color_text("Configuration loaded successfully", fg=GREEN))
    print()

    # Check for profiles
    profiles = config.get('profiles', [])

    # Handle --list option
    if args.list:
        if profiles:
            listProfiles(config)
        else:
            print(color_text("No profiles found in configuration", fg=YELLOW))
        return True

    # Auto mode with --profile argument
    if args.profile:
        # Find the profile
        selectedProfile = getProfile(config, args.profile)
        if not selectedProfile:
            print(color_text(f"Error: Profile '{args.profile}' not found", fg=RED))
            print(color_text("\nAvailable profiles:", fg=CYAN))
            for p in profiles:
                print(color_text(f"  - {p['profileId']}", fg=CYAN))
            return False

        print(color_text(f"Running with profile: {args.profile}", fg=GREEN))
        if args.auto:
            print(color_text("Auto mode: All confirmations will be skipped", fg=YELLOW))

        result = exportWithProfile(selectedProfile, config, validateOnly=args.validate, autoMode=args.auto)
        return result

    # Interactive mode
    print(color_text("Export Mode:", fg=CYAN))
    print("1. Manual Export (interactive)")
    if profiles:
        print("2. Profile Export (use saved configuration)")

    choice = input(color_text("\nSelect mode (1-2): ", fg=CYAN)).strip()

    if choice == "1":
        manualExport(config)
    elif choice == "2" and profiles:
        # List profiles
        availableProfiles = listProfiles(config)

        if not availableProfiles:
            pause("Press Enter to exit...")
            return False

        # Select profile
        profileChoice = input(color_text("Select profile number: ", fg=CYAN)).strip()

        try:
            profileIndex = int(profileChoice) - 1
            if 0 <= profileIndex < len(availableProfiles):
                selectedProfile = availableProfiles[profileIndex]

                # Ask for validate or normal mode
                print()
                print(color_text("Run Mode:", fg=CYAN))
                print("1. Normal Export (default)")
                print("2. Validate Only (test with 1 row)")

                runMode = input(color_text("\nSelect mode (1-2, or press Enter for normal): ", fg=CYAN)).strip()

                validateOnly = (runMode == "2")

                exportWithProfile(selectedProfile, config, validateOnly=validateOnly, autoMode=False)
            else:
                print(color_text("Invalid profile selection", fg=RED))
        except ValueError:
            print(color_text("Invalid input", fg=RED))
    else:
        print(color_text("Invalid choice", fg=RED))

    return True


if __name__ == "__main__":
    # Check if running in non-interactive mode
    autoMode = any(arg in sys.argv for arg in ['--auto', '-a', '--profile', '-p', '--help', '-h', '--list', '-l'])

    try:
        main()
    except KeyboardInterrupt:
        print(color_text("\n\nOperation cancelled by user", fg=YELLOW))
        if logger:
            logger.warning("Script cancelled by user (KeyboardInterrupt)")
    except SystemExit:
        # Handle argparse --help exit gracefully
        pass
    except Exception as e:
        if logger:
            logger.error(f"Unhandled exception: {e}")
        raise
    finally:
        # Log script end
        if logger:
            logger.info(f"{'='*60}")
            logger.info(f"SCRIPT END: {SCRIPT_NAME} v{VERSION}")
            logger.info(f"{'='*60}")

        # Only show exit screen and pause in interactive mode
        if not autoMode:
            print()
            pause("Press Enter to continue...")
            clear_screen()
            header("Table to JSON Export", VERSION)
            print(color_text("Table to JSON Export exiting...\n", fg=CYAN))
            print(color_text("Copyright © 2026 Cloud Box 9 Inc. All rights reserved.\n", fg=GREEN))
