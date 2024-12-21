from datetime import date
from hashlib import md5
from flask import Flask, abort, render_template, redirect, url_for, flash, request,current_app, session
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # Secure filename
from flask_sqlalchemy import SQLAlchemy, pagination
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
import os
from dotenv import load_dotenv
from smtplib import SMTP
# importing forms from forms.py
from forms import RegisterForm, LoginForm, AddProductForm, UpdateProductForm, QuantityForm, ContactForm
import hmac
import hashlib
import uuid
import base64
import json

# Generating a unique transaction Signature
def genSha256(key, message):
    key = key.encode('utf-8')
    message = message.encode('utf-8')
    hmac_sha256 = hmac.new(key, message, hashlib.sha256)
    digest = hmac_sha256.digest()
    #Convert the digest to a Base64-encoded string
    signature = base64.b64encode(digest).decode('utf-8')
    return signature



# Load environment variables
load_dotenv()

# Email and password for the email
MY_EMAIL = os.getenv("EMAIL")
MY_PASSWORD = os.getenv("EMAIL_PASSWORD")


# create a new flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "this-is-a-secret-key")


# Configure upload folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'assets', 'uploads')  # Define upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create upload folder if it doesn't exist
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        if not current_user.is_authenticated and not current_user.id== 1:
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


# creating a user class
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    cart = db.relationship('Cart', back_populates='user') # Add cart 
    orders = db.relationship('Order', back_populates='user') # Add order relationship
    delivery_address = db.relationship('DeliveryAddress', back_populates='user') # Add delivery address relationship

# Creating a product class
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(100), nullable=False)
    orders = db.relationship('Order', back_populates='product')
    cart = db.relationship('Cart', back_populates='product') # Add cart relationship


# creating a cart class
class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', back_populates='cart') # Add user relationship
    product = db.relationship('Product', back_populates='cart') # Add product relationship

# creating a order class
class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)    
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False) # Foreign key to user
    order_uuid = db.Column(db.String(100), nullable=False, unique=True) # Unique order identifier
    product_id = db.Column(db.Integer, ForeignKey('product.id'), nullable=False) # Foreign key to product
    order_date = db.Column(db.Date, nullable=False, default=date.today()) # Default to today's date
    is_delivered = db.Column(db.Boolean, nullable=False, default=False) # Default to False
    delivery_address = db.Column(db.String(100), nullable=False) # Address for delivery
    quantity = db.Column(db.Integer, nullable=False) # Quantity of product ordered
    user = db.relationship('User', back_populates='orders') # Add user relationship
    product = db.relationship('Product', back_populates='orders') # Add product relationship

# creating a delivery address class
class DeliveryAddress(db.Model):
    __tablename__ = 'delivery_address'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    user = db.relationship('User', back_populates='delivery_address') # Add user relationship

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
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
            name=name,
            address=address,
            phone_number=phone_number
        )
        #check if the user already exists
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            flash("User already exists! Try login", "danger")
            return redirect(url_for('login'))
        
        #add the user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f"{new_user.name} registered successfully!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred while registering the user. {e}", "danger")
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
        file_name = file.filename  # Get file name
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        file.save(file_path)

        uploaded_image = f"assets/uploads/{file_name}"  # Path for rendering
        

        
        # Create and add the new product to the database
        new_product = Product(name=name, category=category, price=price, description=description, image_url=uploaded_image)
        db.session.add(new_product)
        db.session.commit()
        
        flash("Product added successfully.", 'success')
        return redirect(url_for('home'))
    return render_template('addnewproduct.html', form=form)

# Creating a route to view all products category
@app.route('/products_category')
def products_category():
    products_category = db.session.query(Product.category).distinct().all()
    products_category = [product[0] for product in products_category]  # Convert list of tuples to list of strings
    
    category_images = {}
    for category in products_category:
        product = Product.query.filter_by(category=category).first()
        category_images[category] = product.image_url  # Add category and image_url to dictionary


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

    # Render the form for adding quantity to cart
    form = QuantityForm()

    if form.validate_on_submit():
        quantity = form.quantity.data

        # Ensure the user is authenticated
        if not current_user.is_authenticated:
            flash("You need to log in first to add items to the cart.", "danger")
            return redirect(url_for('login'))

        # Check if the user already has the product in their cart
        cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=id).first()
        if cart_item:
            # Update the quantity of the existing cart item
            cart_item.quantity += quantity
            db.session.commit()
            flash(f"Added {quantity} more of '{product.name}' to your cart.", "success")

        else:
            # Add a new cart item for the user
            new_cart_item = Cart(user_id=current_user.id, product_id=id, quantity=quantity)
            db.session.add(new_cart_item)
            db.session.commit()
            flash(f"Added '{product.name}' to your cart successfully.", "success")

        # Redirect to the same product details page to prevent resubmission
        return redirect(url_for('product_details', id=id))

    return render_template('product_details.html', product=product, form=form)

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
        flash(f"An error occurred while deleting the product:  {product.name}", "danger")
        db.session.rollback()
    return redirect(url_for('products_category'))



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
        file = form.image_url.data
        file_name = file.filename  # Get file name
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        file.save(file_path)

        uploaded_image = f"assets/uploads/{file_name}"  # Path for rendering
        product.image_url = uploaded_image
        try:
            db.session.commit()
            flash(f"Product '{product.name}' updated successfully.", "success")

            # Redirect to the same product details page to prevent resubmission
            return redirect(url_for('product_details', id=id))

        except Exception as e:
            flash(f"An error occurred while updating the product: {product.name}", "danger")
            db.session.rollback()

    
    return render_template('modify_product.html', form=form, product=product)


# Creating a route to view all products in the cart
@app.route('/cart' ,methods=['GET'])
def cart():
    # Logic for displaying the cart if authenticated
    if not current_user.is_authenticated:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))
    
    # getting all the products in the cart by user_id
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
    # calculate the total quantity of the products in the cart
    total_quantity = sum([item.quantity for item in cart_items])

    # calculate the total price of the products in the cart
    total_price = sum([item.product.price * item.quantity for item in cart_items])
        # generate a unique transaction id
    uuid_val = uuid.uuid4()
    # Example usage:
    secret_key = "8gBm/:&EnhH.1/q"
    data_to_sign = f"total_amount={total_price},transaction_uuid={uuid_val},product_code=EPAYTEST"
    result = genSha256(secret_key, data_to_sign)

    # creating a context dictionary
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_quantity': total_quantity,
        'uuid': uuid_val,
        'signature': result
    }


    
    # Handling the form submission
    if request.method == 'GET':
        data = request.args.get('data')
        if data:
            decoded_data = base64.b64decode(data).decode('utf-8')
            print(decoded_data)
            map_data = json.loads(decoded_data)

            # get the transaction status
            if map_data['status'] == 'COMPLETE':
                flash("Transaction successful", "success")

                # Create an order for each cart item
                for item in cart_items:
                    new_order = Order(
                        user_id=current_user.id,
                        order_uuid=str(uuid_val),
                        product_id=item.product_id,
                        quantity=item.quantity,
                        delivery_address=current_user.address
                    )
                    db.session.add(new_order) # Add the order to the session
                    db.session.delete(item) # Remove the item from the cart
                    db.session.commit()

                    return redirect(url_for('orders'))

            else:
                flash("Transaction failed", "danger")


            print(map_data)
    

    
    # return the cart page
    return render_template('shoppingcart.html', cart_items = cart_items, total_price=total_price, total_quantity=total_quantity , context=context)


# Creating a new route for the orders
@app.route('/orders')
def orders():
    # Logic for displaying the orders if authenticated
    if not current_user.is_authenticated:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))
    
    # getting all the orders by user_id
    orders = Order.query.filter_by(user_id=current_user.id).all()
    
    
    # return the orders page
    return render_template('orders.html', orders=orders)


# Creating a route to update the quantity of a cart item
@app.route('/update_cart_item/<int:id>', methods=['POST'])
def update_cart_item(id):
    if not current_user.is_authenticated:
        flash("You need to log in first", "danger")
        return redirect(url_for('login'))

    try:
        # Retrieve the cart item by ID and ensure it belongs to the current user
        cart_item = Cart.query.filter_by(id=id, user_id=current_user.id).first()

        if not cart_item:
            flash("Cart item not found.", "danger")
            return redirect(url_for('cart'))

        # Get the new quantity from the form
        new_quantity = int(request.form.get('quantity', 1))  # Default to 1 if missing

        if new_quantity < 1:
            flash("Quantity must be at least 1.", "warning")
        else:
            # Update the cart item quantity
            cart_item.quantity = new_quantity
            db.session.commit()
            flash(f"Updated quantity for {cart_item.product.name} to {new_quantity}.", "success")

    except ValueError:
        flash("Invalid quantity. Please enter a valid number.", "danger")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating the cart.", "danger")

    # Redirect back to the cart page
    return redirect(url_for('cart'))


@app.route('/delete_cart_item/<int:id>', methods=['POST', 'GET'])  # Allow POST for better practice
def delete_cart_item(id):
    try:
        # Attempt to find the item
        cart_item = Cart.query.filter_by(id=id).first()
        if not cart_item:
            flash("Item not found in the cart.", "warning")
            return redirect(url_for('cart'))

        # Delete the item
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from cart successfully.", "success")

    except Exception as e:
        app.logger.error(f"Error deleting cart item: {e}")
        db.session.rollback()
        flash("An error occurred while removing the item from the cart.", "danger")

    return redirect(url_for('cart'))


# Creating a route to contact us
@app.route('/contact', methods=['GET', 'POST'])
def contact_us():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        subject = form.subject.data
        message = form.message.data

        # Send email
        try:
            with SMTP("smtp.gmail.com") as connection:
                connection.starttls()  # Secure the connection
                connection.login(user=MY_EMAIL, password=MY_PASSWORD)
                connection.sendmail(
                    from_addr=MY_EMAIL,
                    to_addrs='kushalbro82@gmail.com',
                    msg=f"Subject:{subject}\n\nName: {name}\nEmail: {email}\nMessage: {message}"
                )
            flash("Message sent successfully.", "success")

            return redirect(url_for('home'))
        
        except Exception as e:
            app.logger.error(f"Error sending email: {e}")
            flash("An error occurred while sending the message.", "danger")

    return render_template('contact_us.html', form=form)





# # Code to convert base64encoded string:
# decoded_data = base64.b64decode(data).decode('utf-8')
# print(decoded_data)
# map_data = json.loads(decoded_data)

# url for the checkout page
# @app.route('/checkout', methods=['GET', 'POST'])
# def checkout():
#     # Logic for displaying the cart if authenticated
#     if not current_user.is_authenticated:
#         flash("You need to login first", "danger")
#         return redirect(url_for('login'))
    
#     # getting all the products in the cart by user_id
#     cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
#     # calculate the total quantity of the products in the cart
#     total_quantity = sum([item.quantity for item in cart_items])

#     # calculate the total price of the products in the cart
#     total_price = sum([item.product.price * item.quantity for item in cart_items])


#     # return the checkout page
#     return render_template('checkout.html', context=context)

# runnning the app
if __name__ == "__main__":
    app.run(debug=True, port=5500)



