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

# # Load user


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# # Create a decorator to check if a user is an admin


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


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DB_URL", "sqlite:///shop.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# creating the database
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# creating a user class
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    wishList = db.relationship(
        'Wishlist', back_populates='user')  # Add wishList
    # Add delivery address relationship
    delivery_address = db.relationship(
        'DeliveryAddress', back_populates='user')
    # Add product enquiry relationship
    product_enquiry = db.relationship(
        'ProductEnquiry', back_populates='user')


# Creating a product class


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(100), nullable=False)
    # Add wishList relationship
    wishList = db.relationship('Wishlist', back_populates='product')
    # Add product enquiry relationship
    product_enquiry = db.relationship(
        'ProductEnquiry', back_populates='product')


# creating a wishList class
class Wishlist(db.Model):
    __tablename__ = 'wishList'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey(
        'product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # Add user relationship
    user = db.relationship('User', back_populates='wishList')
    # Add product relationship
    product = db.relationship('Product', back_populates='wishList')

# creating a product_enquiry class


class ProductEnquiry(db.Model):
    __tablename__ = 'product_enquiry'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey(
        'product.id'), nullable=False)
    # Add user relationship
    user = db.relationship('User', back_populates='product_enquiry')
    product = db.relationship(
        'Product', back_populates='product_enquiry')  # Add product

# creating a delivery address class


class DeliveryAddress(db.Model):
    __tablename__ = 'delivery_address'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    # Add user relationship
    user = db.relationship('User', back_populates='delivery_address')


# Initializing the database
with app.app_context():
    db.create_all()


# creating homepage route
@app.route('/')
def home():
    return render_template('homepage.html')


# creating a route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.name.data
        address = form.address.data
        phone_number = form.phone_number.data

        new_user = User(
            email=email,
            password=generate_password_hash(
                form.password.data, method='pbkdf2:sha256', salt_length=8),
            name=name,
            address=address,
            phone_number=phone_number
        )
        # check if the user already exists
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            flash("User already exists! Try login", "danger")
            return redirect(url_for('login'))

        # add the user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f"{new_user.name} registered successfully!", "success")
            return redirect(url_for('login'))
        except Exception as e:

            flash(f"Error occurred While Registering New User:{e}", "danger")
            db.session.rollback()
            return redirect(url_for('register'))

    return render_template('register.html', form=form)


# creating a route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                flash(f"{current_user.name} Logged in successfully.", 'success')
                return redirect(url_for('home'))
            else:
                flash("Password incorrect, please try again.", 'danger')
        else:
            flash("Email does not exist, please try again.", "danger")

    return render_template('login.html', form=form)


# creating a route for user logout
@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out.", 'success')
    return redirect(url_for('home'))

# creating a route for adding a new product


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

        # Create and add the new product to the database
        new_product = Product(name=name, category=category, price=price,
                              description=description, image_url=uploaded_image)
        db.session.add(new_product)
        db.session.commit()

        flash("Product added successfully.", 'success')
        return redirect(url_for('home'))
    return render_template('addnewproduct.html', form=form)

# Creating a route to view all products category


@app.route('/products_category')
def products_category():
    products_category = db.session.query(Product.category).distinct().all()
    # Convert list of tuples to list of strings
    products_category = [product[0] for product in products_category]

    category_images = {}
    for category in products_category:
        product = Product.query.filter_by(category=category).first()
        # Add category and image_url to dictionary
        category_images[category] = product.image_url

    return render_template('products_category.html', category_images=category_images)

# Creating a route to view all products in a category


@app.route('/products')
def products():
    category = (request.args.get('category')).title()
    products = Product.query.filter_by(category=category).all()
    return render_template('products.html', products=products, category=category)

# Creating a route to view a single product


@app.route('/product_details/<int:id>', methods=['GET', 'POST'])
def product_details(id):
    # Retrieve the product by ID
    product = Product.query.get_or_404(id)
    #  render the product details page
    return render_template('product_details.html', product=product)

# creating a route to add product to wishList


@app.route('/add_to_wishlist/<int:id>')
def add_to_wishlist(id):
    is_enquire = request.args.get('is_enquire')

    # Ensure the user is authenticated
    if not current_user.is_authenticated:
        flash("You need to log in first to add items to the wishlist.", "danger")
        return redirect(url_for('login'))

    # Check if the user already has the product in their wishList
    cart_item = Wishlist.query.filter_by(
        user_id=current_user.id, product_id=id).first()
    if cart_item:
        # Update the quantity of the existing wishList item
        cart_item.quantity += 1
        db.session.commit()
        flash(f"Added '{cart_item.product.name}' to your wishlist.", "success")

    else:
        # Add a new wishList item for the user
        new_cart_item = Wishlist(
            user_id=current_user.id, product_id=id, quantity=1)
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f"Added '{new_cart_item.product.name}' to your wishlist successfully.", "success")

    if is_enquire:
        return redirect(url_for('wishList'))
    # rediricting the url to the wishlist page
    return redirect(url_for('product_details', id=id))

# creating a route to delete a product


@app.route('/delete-product/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f"Product '{product.name}' deleted successfully.", "success")

    except Exception as e:
        flash(f"An error occurred while deleting the product:{product.name}", "danger")
        db.session.rollback()
    return redirect(url_for('products_category'))


# Creating a route to modify a product

@app.route('/modify-product/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def modify_product(id):
    product = Product.query.get_or_404(id)
    form = UpdateProductForm(
        name=product.name,
        category=product.category,
        price=product.price,
        description=product.description
    )
    if form.validate_on_submit():
        product.name = form.name.data
        product.category = form.category.data
        product.price = form.price.data
        product.description = form.description.data
        # Save uploaded file
        file_name = form.image_url.data

        # uploaded_image = f"assets/uploads/{file_name}"  # Path for rendering
        product.image_url = file_name
        try:
            db.session.commit()
            flash(f"Product '{product.name}' updated successfully.", "success")

            # Redirect to the same product details page to prevent resubmission
            return redirect(url_for('product_details', id=id))

        except Exception as e:
            flash(f"An error occurred while updating the product: {product.name}", "danger")
            db.session.rollback()

    # Render the modify product page
    return render_template('modify_product.html', form=form, product=product)


# Creating a route to view all products in the wishList: wishlist
@app.route('/wishlist', methods=['GET'])
def wishList():
    # Logic for displaying the wishList if authenticated
    if not current_user.is_authenticated:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))

    # getting all the products in the wishList by user_id
    cart_items = Wishlist.query.filter_by(user_id=current_user.id).all()

    # return the wishList page
    return render_template('wishlist.html', cart_items=cart_items)


# Creating a route to update the quantity of a wishlist item
@app.route('/update_wishlist_item/<int:id>', methods=['POST'])
def update_cart_item(id):
    if not current_user.is_authenticated:
        flash("You need to log in first", "danger")
        return redirect(url_for('login'))

    try:
        # Retrieve the wishList item by ID and ensure it belongs to the current user
        cart_item = Wishlist.query.filter_by(
            id=id, user_id=current_user.id).first()

        if not cart_item:
            flash("Wishlist item not found.", "danger")
            return redirect(url_for('wishList'))

        # Get the new quantity from the form
        new_quantity = int(request.form.get('quantity', 1)
                           )  # Default to 1 if missing

        if new_quantity < 1:
            flash("Quantity must be at least 1.", "warning")
        else:
            # Update the wishList item quantity
            cart_item.quantity = new_quantity
            db.session.commit()
            flash(f"Updated quantity for {cart_item.product.name} to {new_quantity}.", "success")

    except ValueError:
        flash("Invalid quantity. Please enter a valid number.", "danger")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating the wishList.", "danger")

    # Redirect back to the wishList page
    return redirect(url_for('wishList'))


# Allow POST for better practice
@app.route('/delete_wishlist_item/<int:id>', methods=['POST', 'GET'])
def delete_cart_item(id):
    try:
        # Attempt to find the item
        cart_item = Wishlist.query.filter_by(id=id).first()
        if not cart_item:
            flash("Item not found in the wishList.", "warning")
            return redirect(url_for('wishList'))

        # Delete the item
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from wishList successfully.", "success")

    except Exception as e:
        app.logger.error(f"Error deleting wishList item: {e}")
        db.session.rollback()
        flash("An error occurred while removing the item from the wishList.", "danger")

    return redirect(url_for('wishList'))


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
                connection.login(user=MY_EMAIL, password=MY_PASSWORD)
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
    product_id = request.args.get('product_id')  # Get product ID from URL

    product = Product.query.get(product_id)  # Get product by ID

    form = ProductEnquiryForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        phone_number = form.phone_number.data
        message = form.message.data

        msg = f"Subject:Product Enquiry\n\nName: {name}\nEmail: {email}\nPhone Number: {phone_number}\nProduct Name: {product.name}\nMessage: {message}"
        # Send email
        try:
            with SMTP("smtp.gmail.com") as connection:
                connection.starttls()  # Secure the connection
                connection.login(user=MY_EMAIL, password=MY_PASSWORD)
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

    return render_template('enquiry.html', form=form, product=product)


# running the app
if __name__ == "__main__":
    app.run(debug=True, port=5500)
