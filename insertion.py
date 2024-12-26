import sqlite3
import os
import re

# SQLite database setup
DB_PATH = 'instance/shop.db'  # Path to your SQLite database (adjust as needed)

# Function to insert product into the SQLite database


def insert_product(name, category, price, description, image_url):
    # Modify the name and description to add inch symbol where necessary
    name = add_inch_to_number_after_shower_arm(name)
    description = add_inch_to_number_after_shower_arm_in_description(
        description)

    # Now, insert the modified name and description into the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO product (name, category, price, description, image_url)
        VALUES (?, ?, ?, ?, ?)
    """, (name, category, price, description, image_url))
    conn.commit()
    conn.close()
    print(f"Inserted {name} from category '{category}' into database.")

# Helper function to sanitize product name (replace underscores with spaces, keep hyphens)


def sanitize_product_name(product_name):
    return product_name.replace('_', ' ')

# Helper function to sanitize category name (replace hyphens with spaces, capitalize words)


def sanitize_category(category):
    return category.replace('-', ' ').title()

# Function to add inch symbol after the number that appears after 'Shower Arm' in the product name


def add_inch_to_number_after_shower_arm(product_name):
    # Regular expression to find the number after 'Shower Arm' and add the inch symbol to it
    updated_name = re.sub(r'(Shower Arm\s+)(\d+)(?=\s)',
                          r'\1\2" ', product_name)
    return updated_name

# Function to add inch symbol after the number that appears after 'Shower Arm' in the product description


def add_inch_to_number_after_shower_arm_in_description(product_description):
    # Regular expression to find the number after 'Shower Arm' and add the inch symbol to it inside <p> tags
    updated_description = re.sub(
        r'(Shower Arm\s+)(\d+)(?=\s)', r'\1\2" ', product_description)
    return updated_description

# Function to process all products in the directory and insert data into the database


def process_all_products(base_directory, cloudinary_base_url):
    # Loop through all the categories in the base directory
    for category in os.listdir(base_directory):
        category_path = os.path.join(base_directory, category)

        # If it's a directory, process the products inside it
        if os.path.isdir(category_path):
            print(f"Processing category: {category}")

            # Loop through all the product images in the category
            for product_image in os.listdir(category_path):
                if product_image.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Extract product name and file extension
                    product_name, ext = os.path.splitext(product_image)

                    # Sanitize product name and category
                    sanitized_product_name = sanitize_product_name(
                        product_name)
                    sanitized_category = sanitize_category(category)

                    # For simplicity, use sanitized product name as description in a <p> tag
                    description = f"<p>{sanitized_product_name}</p>"

                    # Placeholder price for testing (can be fetched from elsewhere if needed)
                    price = 29.99

                    # Construct the image URL based on Cloudinary URL pattern (use original category and product name)
                    image_url = f"{cloudinary_base_url}/{category}/{product_name}{ext}"

                    # Insert the product data into the SQLite database
                    insert_product(
                        sanitized_product_name, sanitized_category, price, description, image_url)


# Main function to process all products
if __name__ == '__main__':
    # Path to the 'products' directory (adjust as needed)
    base_directory = '.'
    # Your Cloudinary base URL
    cloudinary_base_url = os.getenv('CLOUDINARY_BASE_URL')
    # Process all products in the directory
    process_all_products(base_directory, cloudinary_base_url)
