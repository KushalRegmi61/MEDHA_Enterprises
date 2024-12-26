import sqlite3
import csv

# SQLite database setup
DB_PATH = 'instance/shop.db'  # Path to your SQLite database (adjust as needed)

# Function to export all product data to a CSV file


def export_products_to_csv(csv_filename):
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all data from the 'product' table
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()

    # Get column names (headers)
    column_names = [description[0] for description in cursor.description]

    # Open the CSV file for writing
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header row (column names)
        writer.writerow(column_names)

        # Write all the rows (product data)
        writer.writerows(products)

    # Close the database connection
    conn.close()

    print(f"Data successfully exported to {csv_filename}")


# Main function to call the export function
if __name__ == '__main__':
    # Specify the output CSV file name
    csv_filename = 'products_data.csv'

    # Export the data to CSV
    export_products_to_csv(csv_filename)
