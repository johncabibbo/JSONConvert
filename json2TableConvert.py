#!/opt/homebrew/opt/python@3.12/libexec/bin/python3
# =============================================================================
# Filename: json2TableConvert.py
# Project: JSONConvert
# Version: 1.25
# Last Modified Date: 2026-03-01
# Category: Database Utilities
# OS: Mac/Linux
# Maintainer: Cloud Box 9
# -----------------------------------------------------------------------------
# Description:
#   Imports data from JSON export file back into MySQL table.
#
#   Features:
#     • Configurable database connection via JSON config file
#     • Validation mode (dry run) to check data without importing
#     • Batch insert processing for performance
#     • Column mapping and validation
#     • Comprehensive error handling and logging
#     • Transaction support for data integrity
#
# Usage:
#   python3 json2TableConvert.py
#   Interactive menu prompts for all required information
#
# Configuration:
#   Edit tableJsonConvert.json for database settings and defaults
#
# Notes:
#   • Use validation mode first to verify data integrity
#   • Imports data from JSON files created by table2JsonConvert.py
#   • All operations are logged to configured log file
#   • Duplicate key errors are reported but don't stop import
# -----------------------------------------------------------------------------
# Revision History:
#   v1.25 — 2026-03-01 — Fixed pymssql compatibility: getDatabaseConnection now returns (conn, dbType) tuple
#                        instead of setting conn._db_type attribute (pymssql doesn't support custom attributes)
#   v1.24 — 2026-01-11 — Always prompt for table name (with default from metadata) to allow import to different table
#   v1.23 — 2026-01-11 — Added profile selection menu to choose different profile instead of using export profile
#   v1.22 — 2026-01-11 — Added progress reporting and commits every 1000 rows with timestamps and rate
#   v1.21 — 2026-01-11 — Fixed table name handling when missing from metadata (prompt user instead of using 'Unknown')
#   v1.2 — 2026-01-11 — Added row counts (before/after import) and timestamps to log and screen
#   v1.1 — 2026-01-10 — Added profile support for database connection
#   v1.0 — 2026-01-10 — Initial creation
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # bundled CB9Lib (self-contained)
from CB9Lib import *

import json
import mysql.connector
import pymssql
from datetime import datetime
from pathlib import Path

VERSION = "1.25"
CONFIG_FILE = "tableJsonConvert.json"


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


def loadJsonFile(filePath):
    """Load and parse JSON export file."""
    try:
        with open(filePath, 'r') as f:
            data = json.load(f)

        # Validate structure
        if '_metadata' not in data or 'records' not in data:
            print(color_text("Error: Invalid JSON structure. Missing metadata or records.", fg=RED))
            return None

        return data

    except FileNotFoundError:
        print(color_text(f"Error: File '{filePath}' not found", fg=RED))
        return None
    except json.JSONDecodeError as e:
        print(color_text(f"Error: Invalid JSON in file: {e}", fg=RED))
        return None


def getTableColumns(cursor, tableName, dbType='MYSQL'):
    """Get column information for the specified table. Supports MySQL and SQL Server."""
    try:
        if dbType == 'SQLSERVER':
            # SQL Server: use INFORMATION_SCHEMA
            cursor.execute(f"""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{tableName}'
                ORDER BY ORDINAL_POSITION
            """)
            columns = {}
            for row in cursor.fetchall():
                columns[row[0]] = {
                    'type': row[1],
                    'null': row[2],  # 'YES' or 'NO'
                    'key': '',  # SQL Server uses different method for keys
                    'default': row[3]
                }
        else:
            # MySQL: use DESCRIBE
            cursor.execute(f"DESCRIBE {tableName}")
            columns = {}
            for row in cursor.fetchall():
                columns[row[0]] = {
                    'type': row[1],
                    'null': row[2],
                    'key': row[3],
                    'default': row[4]
                }
        return columns
    except (mysql.connector.Error, pymssql.Error) as err:
        print(color_text(f"Error getting table columns: {err}", fg=RED))
        return None


def validateData(records, tableColumns, tableName):
    """Validate JSON data against table structure."""
    print(color_text("\n=== Validation Results ===", fg=CYAN))

    if not records:
        print(color_text("No records to validate", fg=YELLOW))
        return False

    errors = []
    warnings = []

    # Check first record for column mapping
    firstRecord = records[0]
    recordColumns = set(firstRecord.keys())
    tableColumnNames = set(tableColumns.keys())

    # Find missing columns
    missingInTable = recordColumns - tableColumnNames
    if missingInTable:
        errors.append(f"Columns in JSON but not in table: {', '.join(missingInTable)}")

    missingInJson = tableColumnNames - recordColumns
    if missingInJson:
        # Check if missing columns are nullable or have defaults
        requiredMissing = []
        for col in missingInJson:
            if tableColumns[col]['null'] == 'NO' and tableColumns[col]['default'] is None:
                requiredMissing.append(col)

        if requiredMissing:
            errors.append(f"Required columns missing in JSON: {', '.join(requiredMissing)}")
        else:
            warnings.append(f"Optional columns missing in JSON: {', '.join(missingInJson)}")

    # Display results
    print(color_text(f"\nTable: {tableName}", fg=CYAN))
    print(color_text(f"Records to import: {len(records)}", fg=CYAN))
    print(color_text(f"Columns in JSON: {len(recordColumns)}", fg=CYAN))
    print(color_text(f"Columns in table: {len(tableColumnNames)}", fg=CYAN))

    if warnings:
        print(color_text(f"\nWarnings ({len(warnings)}):", fg=YELLOW))
        for warning in warnings:
            print(color_text(f"  - {warning}", fg=YELLOW))

    if errors:
        print(color_text(f"\nErrors ({len(errors)}):", fg=RED))
        for error in errors:
            print(color_text(f"  - {error}", fg=RED))
        return False

    print(color_text("\n✓ Validation passed", fg=GREEN))
    return True


def importData(conn, tableName, records, config, validateOnly=False, dbType='MYSQL'):
    """Import records into database table. Supports MySQL and SQL Server."""
    cursor = conn.cursor()

    if not records:
        print(color_text("No records to import", fg=YELLOW))
        return 0

    # Get column names from first record
    columns = list(records[0].keys())
    placeholders = ', '.join(['%s'] * len(columns))

    # Column quoting differs by database
    if dbType == 'SQLSERVER':
        columnNames = ', '.join([f"[{col}]" for col in columns])  # SQL Server uses []
    else:
        columnNames = ', '.join([f"`{col}`" for col in columns])  # MySQL uses ``

    insertSql = f"INSERT INTO {tableName} ({columnNames}) VALUES ({placeholders})"

    if validateOnly:
        print(color_text("\n=== VALIDATION MODE - No data will be imported ===", fg=YELLOW))
        print(color_text(f"\nWould execute: {insertSql}", fg=CYAN))
        print(color_text(f"Records to insert: {len(records)}", fg=CYAN))
        return 0

    print(color_text(f"\nImporting {len(records)} records...", fg=CYAN))
    startTime = datetime.now()
    startTimestamp = startTime.strftime("%Y-%m-%d %H:%M:%S")
    print(color_text(f"Import started at: {startTimestamp}", fg=CYAN))
    writeLog(config, f"Import started at: {startTimestamp}")

    successCount = 0
    errorCount = 0
    batchSize = config['import'].get('insertBatchSize', 100)

    try:
        for i, record in enumerate(records, 1):
            try:
                values = [record.get(col) for col in columns]
                cursor.execute(insertSql, values)

                successCount += 1

                # Commit every 1000 rows and show progress
                if i % 1000 == 0:
                    conn.commit()

                    currentTime = datetime.now()
                    currentTimestamp = currentTime.strftime("%Y-%m-%d %H:%M:%S")
                    elapsed = (currentTime - startTime).total_seconds()
                    rate = i / elapsed if elapsed > 0 else 0

                    progressMsg = f"[{currentTimestamp}] Processed {i:,}/{len(records):,} records ({(i/len(records)*100):.1f}%) - {rate:.0f} rec/sec"
                    print(color_text(f"  {progressMsg}", fg=GREEN))
                    writeLog(config, progressMsg)

            except (mysql.connector.IntegrityError, pymssql.IntegrityError) as err:
                errorCount += 1
                if errorCount <= 10:  # Only show first 10 errors to avoid spam
                    print(color_text(f"  Warning: Record {i} - {err}", fg=YELLOW))

                if config['import'].get('stopOnError', False):
                    conn.rollback()
                    raise

            except (mysql.connector.Error, pymssql.Error) as err:
                errorCount += 1
                if errorCount <= 10:  # Only show first 10 errors to avoid spam
                    print(color_text(f"  Error: Record {i} - {err}", fg=RED))

                if config['import'].get('stopOnError', False):
                    conn.rollback()
                    raise

        # Final commit
        conn.commit()

        endTime = datetime.now()
        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
        totalElapsed = (endTime - startTime).total_seconds()
        avgRate = successCount / totalElapsed if totalElapsed > 0 else 0

        print()
        print(color_text(f"Import completed at: {endTimestamp}", fg=GREEN))
        print(color_text(f"  Successfully imported: {successCount:,}", fg=GREEN))
        if errorCount > 0:
            print(color_text(f"  Errors/Skipped: {errorCount:,}", fg=YELLOW))
        print(color_text(f"  Total time: {totalElapsed:.2f} seconds", fg=CYAN))
        print(color_text(f"  Average rate: {avgRate:.0f} records/second", fg=CYAN))

        writeLog(config, f"Import completed at: {endTimestamp}")
        writeLog(config, f"Successfully imported: {successCount:,} records")
        if errorCount > 0:
            writeLog(config, f"Errors/Skipped: {errorCount:,} records")
        writeLog(config, f"Total time: {totalElapsed:.2f} seconds, Average rate: {avgRate:.0f} rec/sec")

        return successCount

    except (mysql.connector.Error, pymssql.Error) as err:
        conn.rollback()
        print(color_text(f"\nImport failed: {err}", fg=RED))
        writeLog(config, f"Import failed: {err}")
        return 0
    finally:
        cursor.close()


def getRowCount(conn, tableName):
    """Get total count of rows in table. Supports MySQL and SQL Server."""
    cursor = conn.cursor()
    try:
        sql = f"SELECT COUNT(*) FROM {tableName}"
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        return count
    except (mysql.connector.Error, pymssql.Error) as err:
        print(color_text(f"Error counting rows: {err}", fg=RED))
        return 0
    finally:
        cursor.close()


def writeLog(config, message):
    """Write message to log file."""
    if not config.get('logging', {}).get('enabled', False):
        return

    logPath = os.path.expanduser(config['logging']['logPath'])
    logDir = os.path.dirname(logPath)

    if logDir and not os.path.exists(logDir):
        os.makedirs(logDir)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(logPath, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")


def listProfiles(config):
    """List available profiles from config."""
    profiles = config.get('profiles', [])
    if not profiles:
        return []

    print(color_text("\n=== Available Profiles ===", fg=CYAN))
    for i, profile in enumerate(profiles, 1):
        print(color_text(f"{i}. {profile['profileId']}", fg=GREEN))
        if 'description' in profile:
            print(color_text(f"   {profile['description']}", fg=CYAN))
        if 'database' in profile:
            print(color_text(f"   Database: {profile['database'].get('database', 'N/A')}", fg=CYAN))
    print()

    return profiles


def getProfileById(config, profileId):
    """Get a specific profile by ID."""
    profiles = config.get('profiles', [])
    for profile in profiles:
        if profile['profileId'] == profileId:
            return profile
    return None


def applyProfileSettings(config, profileId):
    """Apply profile settings by profile ID."""
    if not profileId:
        return config  # No profile, use default config

    # Find matching profile
    profile = getProfileById(config, profileId)
    if not profile:
        print(color_text(f"\nWarning: Profile '{profileId}' not found in config", fg=YELLOW))
        print(color_text("Using default database settings", fg=YELLOW))
        return config

    print(color_text(f"\nUsing profile: {profileId}", fg=GREEN))

    # Merge profile settings into config
    profileConfig = config.copy()

    # Override database settings if profile has them
    if 'database' in profile:
        profileConfig['database'] = profile['database']
        print(color_text(f"  Database: {profile['database'].get('database', 'N/A')}", fg=CYAN))

    # Override import settings if profile has them
    if 'import' in profile:
        profileConfig['import'] = {**config.get('import', {}), **profile.get('import', {})}

    # Override logging settings if profile has them
    if 'logging' in profile:
        profileConfig['logging'] = profile['logging']

    return profileConfig


def main():
    """Main application function."""
    clear_screen()
    header("JSON to Table Import", VERSION)

    # Load configuration
    config = loadConfig()
    if not config:
        pause("Press Enter to exit...")
        return

    print(color_text("Configuration loaded successfully", fg=GREEN))
    print()

    # Get JSON file path
    defaultPath = os.path.expanduser(config['export']['defaultOutputPath'])
    print(color_text(f"Default export path: {defaultPath}", fg=CYAN))

    filePath = input(color_text("Enter JSON file path: ", fg=CYAN)).strip()
    if not filePath:
        print(color_text("File path is required", fg=RED))
        pause()
        return

    filePath = os.path.expanduser(filePath)

    # Load JSON file
    print(color_text("\nLoading JSON file...", fg=CYAN))
    jsonData = loadJsonFile(filePath)
    if not jsonData:
        pause("Press Enter to exit...")
        return

    # Display metadata
    metadata = jsonData['_metadata']
    records = jsonData['records']

    print(color_text("\n=== Export Metadata ===", fg=CYAN))
    print(color_text(f"Table: {metadata.get('tableName', 'N/A')}", fg=CYAN))
    print(color_text(f"Export Date: {metadata['exportDate']}", fg=CYAN))
    print(color_text(f"Record Count: {metadata['recordCount']}", fg=CYAN))
    if 'whereClause' in metadata:
        print(color_text(f"WHERE Clause: {metadata.get('whereClause', 'None')}", fg=CYAN))

    exportProfileId = metadata.get('profileId', '')
    if exportProfileId:
        print(color_text(f"Export Profile: {exportProfileId}", fg=GREEN))

    # Get table name from metadata (as default) but allow user to override
    defaultTableName = metadata.get('tableName', '').strip()

    print()
    print(color_text("=== Table Name Selection ===", fg=CYAN))

    if defaultTableName and defaultTableName != 'N/A':
        print(color_text(f"Export table name: {defaultTableName}", fg=CYAN))
        tableName = input(color_text(f"Enter destination table name (or press Enter for '{defaultTableName}'): ", fg=CYAN)).strip()

        if not tableName:
            tableName = defaultTableName
    else:
        print(color_text("Warning: Table name not found in metadata", fg=YELLOW))
        tableName = input(color_text("Enter destination table name: ", fg=CYAN)).strip()

    if not tableName:
        print(color_text("Table name is required", fg=RED))
        pause("Press Enter to exit...")
        return

    print(color_text(f"Using table: {tableName}", fg=GREEN))

    # Profile selection and database configuration
    selectedProfileId = None
    manualDatabase = False
    profiles = config.get('profiles', [])

    print()
    print(color_text("=== Database Selection ===", fg=CYAN))

    if exportProfileId:
        print(color_text(f"Export was created with profile: {exportProfileId}", fg=CYAN))

    print()
    print("1. Use default database settings" + (" (export profile)" if exportProfileId else ""))
    if profiles:
        print("2. Choose a profile")
    print("3. Manually enter database connection")

    maxOption = "3"
    choice = input(color_text(f"\nSelect option (1-{maxOption}, or press Enter for option 1): ", fg=CYAN)).strip()

    if choice == "" or choice == "1":
        if exportProfileId:
            selectedProfileId = exportProfileId
        # else use default config
    elif choice == "2" and profiles:
        # List available profiles
        availableProfiles = listProfiles(config)
        if availableProfiles:
            profileChoice = input(color_text("Select profile number: ", fg=CYAN)).strip()
            try:
                profileIndex = int(profileChoice) - 1
                if 0 <= profileIndex < len(availableProfiles):
                    selectedProfileId = availableProfiles[profileIndex]['profileId']
                else:
                    print(color_text("Invalid profile selection, using default", fg=YELLOW))
            except ValueError:
                print(color_text("Invalid input, using default", fg=YELLOW))
    elif choice == "3":
        # Manual database entry
        print()
        print(color_text("=== Manual Database Configuration ===", fg=CYAN))
        print(color_text(f"Current default: {config['database'].get('database', 'N/A')} on {config['database'].get('host', 'N/A')}", fg=CYAN))
        print()

        dbHost = input(color_text("Database Host (or press Enter for current): ", fg=CYAN)).strip()
        dbUser = input(color_text("Database User (or press Enter for current): ", fg=CYAN)).strip()
        dbPass = input(color_text("Database Password (or press Enter for current): ", fg=CYAN)).strip()
        dbName = input(color_text("Database Name (or press Enter for current): ", fg=CYAN)).strip()
        dbPort = input(color_text("Database Port (or press Enter for current): ", fg=CYAN)).strip()

        # Create manual database config
        manualDbConfig = config['database'].copy()

        if dbHost:
            manualDbConfig['host'] = dbHost
        if dbUser:
            manualDbConfig['user'] = dbUser
        if dbPass:
            manualDbConfig['password'] = dbPass
        if dbName:
            manualDbConfig['database'] = dbName
        if dbPort:
            try:
                manualDbConfig['port'] = int(dbPort)
            except ValueError:
                print(color_text("Invalid port, using default", fg=YELLOW))

        config['database'] = manualDbConfig
        manualDatabase = True

        print()
        print(color_text("Using manual database configuration:", fg=GREEN))
        print(color_text(f"  Host: {manualDbConfig['host']}", fg=CYAN))
        print(color_text(f"  User: {manualDbConfig['user']}", fg=CYAN))
        print(color_text(f"  Database: {manualDbConfig['database']}", fg=CYAN))
        print(color_text(f"  Port: {manualDbConfig.get('port', 3306)}", fg=CYAN))

    # Apply profile settings if profile was selected (not for manual config)
    if not manualDatabase:
        config = applyProfileSettings(config, selectedProfileId)

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
        writeLog(config, f"=== IMPORT START: {tableName} at {startTimestamp} ===")

        # Get initial row count (before import)
        initialCount = getRowCount(conn, tableName)
        print(color_text(f"\n=== Row Count ===", fg=CYAN))
        print(color_text(f"Rows in table before import: {initialCount}", fg=GREEN))
        writeLog(config, f"Rows before import: {initialCount}")

        # Get table structure
        cursor = conn.cursor()
        tableColumns = getTableColumns(cursor, tableName, dbType)
        cursor.close()

        if not tableColumns:
            print(color_text(f"Error: Table '{tableName}' not found", fg=RED))
            endTime = datetime.now()
            endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
            writeLog(config, f"=== IMPORT END: {tableName} at {endTimestamp} (FAILED - table not found) ===")
            return

        # Validate data
        isValid = validateData(records, tableColumns, tableName)

        if not isValid:
            print(color_text("\nValidation failed. Cannot import data.", fg=RED))
            pause("Press Enter to exit...")
            endTime = datetime.now()
            endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
            writeLog(config, f"=== IMPORT END: {tableName} at {endTimestamp} (FAILED - validation failed) ===")
            return

        # Ask for import mode
        print()
        print(color_text("Import Mode:", fg=CYAN))
        print("1. Validate Only (dry run)")
        print("2. Import Data")

        mode = input(color_text("\nSelect mode (1-2): ", fg=CYAN)).strip()

        validateOnly = (mode == "1")

        if validateOnly:
            importData(conn, tableName, records, config, validateOnly=True, dbType=dbType)
            writeLog(config, f"JSON2Table: Validated {len(records)} records for {tableName} (no import)")

            # Log end timestamp
            endTime = datetime.now()
            endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
            duration = (endTime - startTime).total_seconds()
            writeLog(config, f"=== IMPORT END: {tableName} at {endTimestamp} (Validation only, Duration: {duration:.2f}s) ===")
        else:
            # Confirm import
            print()
            confirm = input(color_text(f"Import {len(records)} records into {tableName}? (yes/no): ", fg=YELLOW)).strip().lower()

            if confirm != 'yes':
                print(color_text("Import cancelled", fg=YELLOW))
                endTime = datetime.now()
                endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
                writeLog(config, f"=== IMPORT END: {tableName} at {endTimestamp} (Cancelled by user) ===")
                return

            # Import data
            importedCount = importData(conn, tableName, records, config, validateOnly=False, dbType=dbType)

            if importedCount > 0:
                # Get final row count (after import)
                finalCount = getRowCount(conn, tableName)
                print(color_text(f"\n=== Import Summary ===", fg=GREEN))
                print(color_text(f"Rows imported: {importedCount}", fg=GREEN))
                print(color_text(f"Rows in table after import: {finalCount}", fg=CYAN))
                writeLog(config, f"Rows after import: {finalCount}")
                writeLog(config, f"JSON2Table: Imported {importedCount} records into {tableName}")

                # Log end timestamp
                endTime = datetime.now()
                endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
                duration = (endTime - startTime).total_seconds()
                writeLog(config, f"=== IMPORT END: {tableName} at {endTimestamp} (Duration: {duration:.2f}s) ===")

                print()
                print(color_text("Import completed successfully!", fg=GREEN))
            else:
                # Import failed
                endTime = datetime.now()
                endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
                writeLog(config, f"=== IMPORT END: {tableName} at {endTimestamp} (FAILED - no records imported) ===")

    except Exception as e:
        print(color_text(f"\nUnexpected error: {e}", fg=RED))
        writeLog(config, f"JSON2Table ERROR: {e}")
        endTime = datetime.now()
        endTimestamp = endTime.strftime("%Y-%m-%d %H:%M:%S")
        writeLog(config, f"=== IMPORT END: {tableName} at {endTimestamp} (FAILED - exception) ===")
    finally:
        conn.close()
        print()
        pause("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(color_text("\n\nOperation cancelled by user", fg=YELLOW))
    finally:
        clear_screen()
        header("JSON to Table Import", VERSION)
        print(color_text("JSON to Table Import exiting...\n", fg=CYAN))
        print(color_text("Copyright © 2026 Cloud Box 9 Inc. All rights reserved.\n", fg=GREEN))
