from datetime import date
from hashlib import md5
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey
from functools import wraps
import os
from dotenv import load_dotenv
from smtplib import SMTP
# importing forms from forms.py
from forms import RegisterForm, LoginForm, AddProductForm, UpdateProductForm, QuantityForm, ContactForm, ProductEnquiryForm


# Load environment variables
load_dotenv()

# Email and password for the email
MY_EMAIL = os.getenv("EMAIL")
MY_PASSWORD = os.getenv("EMAIL_PASSWORD")


# create a new flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "this-is-a-secret-key")


# create a new bootstrap object
Bootstrap5(app)
# initializing the flask ckeck editor
CKEditor(app)

# # Configure Flask Login
login_manager = LoginManager()
login_manager.init_app(app)

# # Load users


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

# # Create a decorator to check if a users is an admin


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated and not current_user.id == 1:
            abort(403)  # Forbidden access
        return f(*args, **kwargs)
    return decorated_function

# creating a declearative base


class Base(DeclarativeBase):
    pass

# connect to the database


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL", "sqlite:///shop.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# creating the database
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# creating a users class
class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    wishLists = db.relationship(
        'Wishlists', back_populates='users')  # Add wishLists
    # Add delivery address relationship
    delivery_addresses = db.relationship(
        'DeliveryAddresses', back_populates='users')
    # Add products enquiry relationship
    product_enquiries = db.relationship(
        'ProductEnquiries', back_populates='users')


# Creating a products class


class Products(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    # Add wishLists relationship
    wishLists = db.relationship('Wishlists', back_populates='products')
    # Add products enquiry relationship
    product_enquiries = db.relationship(
        'ProductEnquiries', back_populates='products')


# creating a wishLists class
class Wishlists(db.Model):
    __tablename__ = 'wishLists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey(
        'products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # Add users relationship
    users = db.relationship('Users', back_populates='wishLists')
    # Add products relationship
    products = db.relationship('Products', back_populates='wishLists')

# creating a product_enquiries class


class ProductEnquiries(db.Model):
    __tablename__ = 'product_enquiries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey(
        'products.id'), nullable=False)
    # Add users relationship
    users = db.relationship('Users', back_populates='product_enquiries')
    products = db.relationship(
        'Products', back_populates='product_enquiries')  # Add products

# creating a delivery address class


class DeliveryAddresses(db.Model):
    __tablename__ = 'delivery_addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    # Add users relationship
    users = db.relationship('Users', back_populates='delivery_addresses')


# Initializing the database
with app.app_context():
    db.create_all()


# creating homepage route
@app.route('/')
def home():
    return render_template('homepage.html')


# creating a route for users registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.name.data
        address = form.address.data
        phone_number = form.phone_number.data

        new_user = Users(
            email=email,
            password=generate_password_hash(
                form.password.data, method='pbkdf2:sha256', salt_length=8),
            name=name,
            address=address,
            phone_number=phone_number
        )
        # check if the users already exists
        users = db.session.query(Users).filter_by(email=email).first()
        if users:
            flash("Users already exists! Try login", "danger")
            return redirect(url_for('login'))

        # add the users to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f"{new_user.name} registered successfully!", "success")
            return redirect(url_for('login'))
        except Exception as e:

            flash(f"Error occurred While Registering New Users:{e}", "danger")
            db.session.rollback()
            return redirect(url_for('register'))

    return render_template('register.html', form=form)


# creating a route for users login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        users = Users.query.filter_by(email=email).first()
        if users:
            if check_password_hash(users.password, password):
                login_user(users)
                flash(f"{current_user.name} Logged in successfully.", 'success')
                return redirect(url_for('home'))
            else:
                flash("Password incorrect, please try again.", 'danger')
        else:
            flash("Email does not exist, please try again.", "danger")

    return render_template('login.html', form=form)


# creating a route for users logout
@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out.", 'success')
    return redirect(url_for('home'))

# creating a route for adding a new products


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        name = form.name.data
        category = (form.category.data).title()
        price = float(form.price.data)
        description = form.description.data

        # Save uploaded file
        file = form.image_url.data
        uploaded_image = file  # img url
        brand = (form.brand.data).lower()

        # Create and add the new products to the database
        new_product = Products(name=name, category=category, price=price,
                              description=description, image_url=uploaded_image, brand=brand)
        db.session.add(new_product)
        db.session.commit()

        flash("Products added successfully.", 'success')
        return redirect(url_for('home'))
    return render_template('addnewproduct.html', form=form)

# Creating a route to view all products brand
@app.route('/products_brand')
def products_brand():
    # Get all unique products brands
    products_brand = db.session.query(Products.brand).distinct().all()
    # Convert list of tuples to list of strings
    products_brand = [products[0] for products in products_brand]

    # brand_images = {}
    # for brand in products_brand:
    #     products = Products.query.filter_by(brand=brand).first()
    #     # Add brand and image_url to dictionary
    #     brand_images[brand] = products.image_url

    return render_template('products_brand.html', brands = products_brand)

# Creating a route to view all products category
@app.route('/products_category/<string:brand>')
def products_category(brand):
    
    # getting hold of all the products category for a specific brand
    # selecting all the unique categories for a specific brand
    products_category = db.session.query(Products.category).filter_by(brand=brand).distinct().all()
    
    
    # Get all unique products categories
    # products_category = db.session.query(Products.category).distinct().all()
    # Convert list of tuples to list of strings
    products_category = [products[0] for products in products_category]

    category_images = {}
    for category in products_category:
        products = Products.query.filter_by(category=category).first()
        # Add category and image_url to dictionary
        category_images[category] = products.image_url

    return render_template('products_category.html', category_images=category_images, brand=brand.upper())



# Creating a route to view all products in a category
@app.route('/products')
def products():
    category = (request.args.get('category')).title() # Get category from URL

    # retrieving all the products in a specific category for a specific brand
    # brand = request.args.get('brand')  # Get brand from URL , brand=brand
    # Get all products in the category
    products = Products.query.filter_by(category=category).all()
    
    # render the products page
    return render_template('products.html', products=products, category=category)

# Creating a route to view a single products


@app.route('/product_details/<int:id>', methods=['GET', 'POST'])
def product_details(id):
    # Retrieve the products by ID
    products = Products.query.get_or_404(id)
    #  render the products details page
    return render_template('product_details.html', products=products)

# creating a route to add products to wishLists


@app.route('/add_to_wishlist/<int:id>')
def add_to_wishlist(id):
    is_enquire = request.args.get('is_enquire')

    # Ensure the users is authenticated
    if not current_user.is_authenticated:
        flash("You need to log in first to add items to the wishlist.", "danger")
        return redirect(url_for('login'))

    # Check if the users already has the products in their wishLists
    cart_item = Wishlists.query.filter_by(
        user_id=current_user.id, product_id=id).first()
    if cart_item:
        # Update the quantity of the existing wishLists item
        cart_item.quantity += 1
        db.session.commit()
        flash(f"Added '{cart_item.products.name}' to your wishlist.", "success")

    else:
        # Add a new wishLists item for the users
        new_cart_item = Wishlists(
            user_id=current_user.id, product_id=id, quantity=1)
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f"Added '{new_cart_item.products.name}' to your wishlist successfully.", "success")

    if is_enquire:
        return redirect(url_for('wishLists'))
    # rediricting the url to the wishlist page
    return redirect(url_for('product_details', id=id))

# creating a route to delete a products


@app.route('/delete-products/<int:id>')
@login_required
@admin_required
def delete_product(id):
    products = Products.query.get_or_404(id)
    try:
        db.session.delete(products)
        db.session.commit()
        flash(f"Products '{products.name}' deleted successfully.", "success")

    except Exception as e:
        flash(f"An error occurred while deleting the products:{products.name}", "danger")
        db.session.rollback()
    return redirect(url_for('products_category'))


# Creating a route to modify a products

@app.route('/modify-products/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def modify_product(id):
    products = Products.query.get_or_404(id)
    form = UpdateProductForm(
        name=products.name,
        category=products.category,
        price=products.price,
        description=products.description,
        brand = products.brand
    )
    if form.validate_on_submit():
        products.name = form.name.data
        products.category = form.category.data
        products.price = form.price.data
        products.description = form.description.data
        # Save uploaded file
        file_name = form.image_url.data
        
        # brand name
        products.brand = form.brand.data

        # uploaded_image = f"assets/uploads/{file_name}"  # Path for rendering
        products.image_url = file_name
        try:
            db.session.commit()
            flash(f"Products '{products.name}' updated successfully.", "success")

            # Redirect to the same products details page to prevent resubmission
            return redirect(url_for('product_details', id=id))

        except Exception as e:
            flash(f"An error occurred while updating the products: {products.name}", "danger")
            db.session.rollback()

    # Render the modify products page
    return render_template('modify_product.html', form=form, products=products)


# Creating a route to view all products in the wishLists: wishlist
@app.route('/wishlist', methods=['GET'])
def wishLists():
    # Logic for displaying the wishLists if authenticated
    if not current_user.is_authenticated:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))

    # getting all the products in the wishLists by user_id
    cart_items = Wishlists.query.filter_by(user_id=current_user.id).all()

    # return the wishLists page
    return render_template('wishlist.html', cart_items=cart_items)


# Creating a route to update the quantity of a wishlist item
@app.route('/update_wishlist_item/<int:id>', methods=['POST'])
def update_cart_item(id):
    if not current_user.is_authenticated:
        flash("You need to log in first", "danger")
        return redirect(url_for('login'))

    try:
        # Retrieve the wishLists item by ID and ensure it belongs to the current users
        cart_item = Wishlists.query.filter_by(
            id=id, user_id=current_user.id).first()

        if not cart_item:
            flash("Wishlists item not found.", "danger")
            return redirect(url_for('wishLists'))

        # Get the new quantity from the form
        new_quantity = int(request.form.get('quantity', 1)
                           )  # Default to 1 if missing

        if new_quantity < 1:
            flash("Quantity must be at least 1.", "warning")
        else:
            # Update the wishLists item quantity
            cart_item.quantity = new_quantity
            db.session.commit()
            flash(f"Updated quantity for {cart_item.products.name} to {new_quantity}.", "success")

    except ValueError:
        flash("Invalid quantity. Please enter a valid number.", "danger")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating the wishLists.", "danger")

    # Redirect back to the wishLists page
    return redirect(url_for('wishLists'))


# Allow POST for better practice
@app.route('/delete_wishlist_item/<int:id>', methods=['POST', 'GET'])
def delete_cart_item(id):
    try:
        # Attempt to find the item
        cart_item = Wishlists.query.filter_by(id=id).first()
        if not cart_item:
            flash("Item not found in the wishLists.", "warning")
            return redirect(url_for('wishLists'))

        # Delete the item
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from wishLists successfully.", "success")

    except Exception as e:
        app.logger.error(f"Error deleting wishLists item: {e}")
        db.session.rollback()
        flash("An error occurred while removing the item from the wishLists.", "danger")

    return redirect(url_for('wishLists'))


# Creating a route to contact us
@app.route('/contact', methods=['GET', 'POST'])
def contact_us():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        subject = form.subject.data
        message = form.message.data

        msg = f"Name: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}"
        # Send email
        try:
            with SMTP("smtp.gmail.com") as connection:
                connection.starttls()  # Secure the connection
                connection.login(users=MY_EMAIL, password=MY_PASSWORD)
                connection.sendmail(
                    from_addr=MY_EMAIL,
                    to_addrs='kushalbro82@gmail.com',
                    msg=msg
                )
            flash("Message sent successfully.", "success")

            return redirect(url_for('home'))

        except Exception as e:
            app.logger.error(f"Error sending email: {e}")
            flash("An error occurred while sending the message.", "danger")

    return render_template('contact_us.html', form=form)

# about us route


@app.route('/about')
def about():
    return render_template('about_us.html')

# route for enquiry form


@app.route('/enquiry', methods=['GET', 'POST'])
def enquiry():
    product_id = request.args.get('product_id')  # Get products ID from URL

    products = Products.query.get(product_id)  # Get products by ID

    form = ProductEnquiryForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        phone_number = form.phone_number.data
        message = form.message.data

        msg = f"Subject:Products Enquiry\n\nName: {name}\nEmail: {email}\nPhone Number: {phone_number}\nProduct Name: {products.name}\nMessage: {message}"
        # Send email
        try:
            with SMTP("smtp.gmail.com") as connection:
                connection.starttls()  # Secure the connection
                connection.login(users=MY_EMAIL, password=MY_PASSWORD)
                connection.sendmail(
                    from_addr=MY_EMAIL,
                    to_addrs='kushalbro82@gmail.com',
                    msg=msg
                )
            flash("Enquiry sent successfully.", "success")
            return redirect(url_for('product_details', id=product_id))

        except Exception as e:
            app.logger.error(f"Error sending enquiry email: {e}")
            flash("An error occurred while sending the enquiry.", "danger")

    return render_template('enquiry.html', form=form, products=products)


# running the app
if __name__ == "__main__":
    app.run(debug=True, port=5500)
