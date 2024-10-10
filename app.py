from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, validate
from marshmallow import ValidationError
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%40Deblin312145@localhost/api_mp_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Schema Tables
class CustomerSchema(ma.Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)

    class Meta:
        fields = ("id", "name")

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

class CustomerAccountSchema(ma.Schema):
    account_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    name = fields.String(required=True)
    email = fields.String(required=True)
    password = fields.String(required=True)

    class Meta:
        fields = ("account_id", "customer_id", "name", "email", "password")

customer_account_schema = CustomerAccountSchema()
customer_accounts_schema = CustomerAccountSchema(many=True)

class OrdersSchema(ma.Schema):
    order_id = fields.Integer(required=True)
    account_id = fields.Integer(required=True)
    product_id = fields.Integer(required=True)
    order_date = fields.DateTime(required=True)  # Track order date
    expected_delivery = fields.DateTime(required=False)  # Track expected delivery

    class Meta:
        fields = ("order_id", "account_id", "product_id", "order_date", "expected_delivery")

order_schema = OrdersSchema()
orders_schema = OrdersSchema(many=True)

class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=True)
    product_name = fields.String(required=True)
    product_brand = fields.String(required=True)

    class Meta:
        fields = ("product_id", "product_name", "product_brand")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Table Models
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    customer = db.relationship('CustomerAccounts', backref='customers')

class CustomerAccounts(db.Model):
    __tablename__ = 'customerAccounts'
    account_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # !!! Figure out what relationships we need to add here !!!
    accounts = db.relationship('Customer', backref='customerAccounts')

order_product = db.Table('order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.order_id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.product_id'), primary_key=True)
)

class Products(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    product_brand = db.Column(db.String(50), nullable=False)
    # !!! Figure out what relationships we need to add here !!!
    product = db.relationship('Orders', secondary=order_product, backref='products')



class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_id = db.Column(db.Integer, db.ForeignKey('customerAccounts.account_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'))
    
    order_date = db.Column(db.DateTime, default=datetime)  # Tracks when the order was placed
    expected_delivery = db.Column(db.DateTime, nullable=True)  # Expected delivery date

    order = db.relationship('Product', secondary='order_product', backref='orders')

# CRUD Operations

# Customers Operations
@app.route('/customers/all', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customer_schema.jsonify(customers)

@app.route('/customers/add', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_customer = Customer(name=customer_data['name'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"Message": "New customer added succesfully."})

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    customer.name = customer_data['name']
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200

@app.route('/customers/delete/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

# Customer Accounts Operations
@app.route('/customer_accounts/all', methods=['GET'])
def get_customer_accounts():
    accounts = CustomerAccounts.query.all()
    return customer_account_schema.jsonify(accounts)

@app.route('/customer_accounts/add', methods=['POST'])
def add_customer_account():
    try:
        account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    customer = Customer.query.get_or_404(account_data['customer_id'])

    new_account = CustomerAccounts(
        customer_id=customer.id,
        name=account_data['name'],
        email=account_data['email'],
        password=account_data['password']
    )

    db.session.add(new_account)
    db.session.commit()
    return jsonify({"message": "New customer account created successfully."}), 201

@app.route('/customer_accounts/<int:id>', methods=['PUT'])
def update_customer_account(id):
    account = CustomerAccounts.query.get_or_404(id)
    try:
        account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    account.name = account_data['name']
    account.email = account_data['email']
    account.password = account_data['password']

    db.session.commit()
    return jsonify({"message": "Customer account details updated successfully"}), 200

@app.route('/customer_accounts/delete/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
    account = CustomerAccounts.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 204

# Products Operations
@app.route('/products/all', methods=['GET'])
def get_products():
    products = Products.query.all()
    return products_schema.jsonify(products)

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Products.query.get_or_404(id)
    return product_schema.jsonify(product)

@app.route('/products/add', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_product = Products(
        product_brand=product_data['product_brand'],
        product_name=product_data['product_name'],
    )

    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "New product successfully added."}), 201

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Products.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    product.product_name = product_data['product_name']
    product.product_brand = product_data['product_brand']

    db.session.commit()
    return jsonify({'message': 'Product updated successfully.'}), 200

@app.route('/products/delete/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Products.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product removed successfully"}), 204

# Orders Operations
@app.route('/orders/all', methods=['GET'])
def get_orders():
    orders = Orders.query.all()
    return orders_schema.jsonify(orders)

@app.route('/orders/add', methods=['POST'])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    account = CustomerAccounts.query.get_or_404(order_data['account_id'])
    product = Products.query.get_or_404(order_data['product_id'])

    new_order = Orders(
        account_id=account.account_id,
        product_id=product.product_id,
        order_date=datetime.utcnow(),  # Set the order date to now
        expected_delivery=order_data.get('expected_delivery')  # Optional
    )

    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "New order successfully added."}), 201


@app.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    order = Orders.query.get_or_404(id)
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    if 'account_id' in order_data:
        account = CustomerAccounts.query.get_or_404(order_data['account_id'])
        order.account_id = account.account_id

    if 'product_id' in order_data:
        product = Products.query.get_or_404(order_data['product_id'])
        order.product_id = product.product_id

    # Update the new fields if they exist
    if 'order_date' in order_data:
        order.order_date = order_data['order_date']

    if 'expected_delivery' in order_data:
        order.expected_delivery = order_data['expected_delivery']

    db.session.commit()
    return jsonify({'message': 'Order updated successfully.'}), 200


@app.route('/orders/delete/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Orders.query.get_or_404(id) 
    db.session.delete(order)  
    db.session.commit()  
    return jsonify({"message": "Order removed successfully"}), 204

with app.app_context():
    db.create_all()