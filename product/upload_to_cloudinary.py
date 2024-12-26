import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Read values from the environment variables
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


# Function to upload an image to Cloudinary with a specified public ID (original filename)


def upload_image(image_path, category_name, original_filename):
    try:
        # Remove the extension from the original filename (avoid double extensions)
        filename_without_extension = os.path.splitext(original_filename)[0]

        # Specify the folder in Cloudinary to organize images by category
        folder_name = f"ecommerce/{category_name}"

        # Custom public ID based on category and filename (without the full folder structure)
        # Just use the filename without folder in public_id
        public_id = f"{filename_without_extension}"

        # Upload the image to Cloudinary with the specified public_id
        response = cloudinary.uploader.upload(
            image_path, folder=folder_name, public_id=public_id, transformation=[])

        # Return the URL of the uploaded image
        return response['secure_url']
    except Exception as e:
        print(f"Error uploading {image_path}: {e}")
        return None

# Recursive function to traverse all directories and upload images


def upload_images_from_category(root_directory):
    uploaded_image_urls = []

    # Loop through all folders (categories) in the root directory
    for category_name in os.listdir(root_directory):
        category_path = os.path.join(root_directory, category_name)

        # Check if it's a directory (i.e., a category folder)
        if os.path.isdir(category_path):
            print(f"Processing category: {category_name}")

            # Loop through all files in the category folder
            for image_filename in os.listdir(category_path):
                image_path = os.path.join(category_path, image_filename)

                # Check if the file is an image (you can extend this list as needed)
                if image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    print(
                        f"Uploading {image_filename} from {category_name}...")

                    # Upload the image with the original filename
                    image_url = upload_image(
                        image_path, category_name, image_filename)

                    if image_url:
                        uploaded_image_urls.append({
                            'category': category_name,
                            'image': image_filename,
                            'url': image_url
                        })

    return uploaded_image_urls


# Set the root directory that contains category folders (use '.' for current directory)
root_directory = '.'  # Refers to the current directory where app.py is located

# Start the upload process
uploaded_image_urls = upload_images_from_category(root_directory)

# Print the URLs of the uploaded images
if uploaded_image_urls:
    print("\nUploaded Image URLs:")
    for item in uploaded_image_urls:
        print(
            f"Category: {item['category']}, Image: {item['image']}, URL: {item['url']}")
else:
    print("No images were uploaded.")
