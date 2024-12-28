import sqlite3
import psycopg2
from datetime import date
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# SQLite database path
sqlite_db_path = 'shop.db'  # Path to your SQLite database


# Connect to SQLite database
sqlite_conn = sqlite3.connect(sqlite_db_path)
sqlite_cursor = sqlite_conn.cursor()


# Render PostgreSQL external connection URI
postgresql_uri = os.getenv('DB_RENDER_URI')

# Connect to PostgreSQL database using psycopg2
postgresql_conn = psycopg2.connect(postgresql_uri)
postgresql_cursor = postgresql_conn.cursor()

# Function to truncate strings if they exceed the max length


def truncate_string(value, max_length=100):
    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length]  # Truncate the string to max_length
    return value

# Function to truncate all tables in PostgreSQL


def truncate_tables():
    # List the tables you want to truncate in the same order as foreign keys
    tables = ['user', 'product', 'cart', 'order', 'delivery_address']
    for table in tables:
        try:
            truncate_sql = f"TRUNCATE TABLE \"{table}\" RESTART IDENTITY CASCADE;"
            postgresql_cursor.execute(truncate_sql)
            print(f"Successfully truncated table: {table}")
        except Exception as e:
            print(f"Error truncating table {table}: {e}")

# Function to migrate data


def migrate_data():
    try:
        # Step 1: Get the table names from SQLite
        sqlite_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';")
        tables = sqlite_cursor.fetchall()

        # Step 2: Migrate each table
        for table in tables:
            table_name = table[0]

            # Quote the table name if it's a reserved keyword like 'user'
            table_name_quoted = f'"{table_name}"' if table_name in [
                'user', 'select', 'insert', 'update', 'order'] else table_name

            # Step 2.1: Get column information from SQLite
            sqlite_cursor.execute(f"PRAGMA table_info({table_name_quoted});")
            columns = sqlite_cursor.fetchall()

            # Step 2.2: Create the table in PostgreSQL if it doesn't exist
            column_definitions = []
            for column in columns:
                column_name = column[1]
                # Convert SQLite types to PostgreSQL compatible types
                column_type = column[2].upper()
                if column_type == 'INTEGER':
                    column_type = 'INTEGER'
                elif column_type == 'TEXT':
                    column_type = 'TEXT'
                elif column_type == 'REAL':
                    column_type = 'FLOAT'

                # Quote the column name if it's a reserved keyword
                column_name_quoted = f'"{column_name}"' if column_name in [
                    'user', 'select', 'insert', 'update', 'order'] else column_name
                column_definitions.append(
                    f"{column_name_quoted} {column_type}")

            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name_quoted} ({', '.join(column_definitions)});"
            postgresql_cursor.execute(create_table_sql)

            # Step 2.3: Insert the data into PostgreSQL
            sqlite_cursor.execute(f"SELECT * FROM {table_name_quoted};")
            rows = sqlite_cursor.fetchall()

            for row in rows:
                # Truncate strings that are too long for their columns
                # Adjust the length for all columns as needed
                row = [truncate_string(value, 100) for value in row]
                # PostgreSQL placeholders for data
                placeholders = ', '.join(['%s'] * len(row))
                insert_sql = f"INSERT INTO {table_name_quoted} VALUES ({placeholders});"
                postgresql_cursor.execute(insert_sql, row)

            # Commit after each table is migrated
            postgresql_conn.commit()
            print(f"Successfully migrated table: {table_name_quoted}")

    except Exception as e:
        print(f"Error migrating data: {e}")
    finally:
        # Step 3: Close the connections
        sqlite_conn.close()
        postgresql_conn.close()
        print("Migration completed.")


# Clear existing data in PostgreSQL before migration
# --> If you do not want just comment this function
truncate_tables()

# Run migration after truncating
migrate_data()
