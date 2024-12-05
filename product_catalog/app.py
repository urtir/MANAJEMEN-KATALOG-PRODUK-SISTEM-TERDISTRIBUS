###REVISED BY BAINUL


from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from mysql.connector import Error
import database as db
import logging
import secrets
from functools import wraps
from werkzeug.exceptions import BadRequest
import os
from dotenv import load_dotenv
from flask_cors import CORS
import secrets
from decimal import Decimal
import json
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Decorators
class DatabaseConnectionError(Exception):
    pass

def db_connection(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conn = None
        try:
            conn = db.get_db_connection()
            return f(conn, *args, **kwargs)
        except Error as e:
            logger.error(f"Database error: {e}")
            flash('An error occurred while accessing the database', 'error')
            return redirect(url_for('index'))
        finally:
            if conn and conn.is_connected():
                conn.close()
    return decorated_function

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key missing'}), 401
            
        conn = None
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM api_keys WHERE key_value = %s AND is_active = 1', (api_key,))
            key_data = cursor.fetchone()
            
            if not key_data:
                return jsonify({'error': 'Invalid API key'}), 401
                
            return f(*args, **kwargs)
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    return decorated_function

# Helper Functions
def generate_api_key():
    return secrets.token_hex(32)

# Web Routes
@app.route('/')
@db_connection
def index(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    cursor.close()
    return render_template('index.html', products=products)

@app.route('/add', methods=['GET', 'POST'])
@db_connection
def add_product(conn):
    if request.method == 'POST':
        try:
            name = request.form['name']
            category = request.form['category']
            price = float(request.form['price'])
            description = request.form['description']

            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO products (name, category, price, description) VALUES (%s, %s, %s, %s)',
                (name, category, price, description)
            )
            conn.commit()
            cursor.close()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('index'))
            
        except (ValueError, KeyError) as e:
            flash('Invalid input data', 'error')
            logger.error(f"Input error: {e}")
            return render_template('add.html'), 400
            
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@db_connection
def edit_product(conn, id):
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            category = request.form['category']
            price = float(request.form['price'])
            description = request.form['description']
            
            cursor.execute(
                'UPDATE products SET name = %s, category = %s, price = %s, description = %s WHERE id = %s',
                (name, category, price, description, id)
            )
            conn.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('index'))
            
        except ValueError as e:
            flash('Invalid input data', 'error')
            logger.error(f"Input error: {e}")
            return redirect(url_for('edit_product', id=id))
    
    cursor.execute('SELECT * FROM products WHERE id = %s', (id,))
    product = cursor.fetchone()
    cursor.close()
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
        
    return render_template('edit.html', product=product)

@app.route('/delete/<int:id>')
@db_connection
def delete_product(conn, id):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/search')
@db_connection
def search(conn):
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    
    cursor = conn.cursor(dictionary=True)
    
    if category:
        cursor.execute(
            'SELECT * FROM products WHERE category = %s AND name LIKE %s', 
            (category, f'%{query}%')
        )
    else:
        cursor.execute(
            'SELECT * FROM products WHERE name LIKE %s', 
            (f'%{query}%',)
        )
    
    products = cursor.fetchall()
    cursor.close()
    return render_template('index.html', products=products)

# API Routes
@app.route('/api/keys', methods=['POST'])
@db_connection
def create_api_key(conn):
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
        
    data = request.get_json()
    if 'client_name' not in data:
        return jsonify({'error': 'client_name is required'}), 400

        
    api_key = generate_api_key()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO api_keys (key_value, client_name) VALUES (%s, %s)',
        (api_key, data['client_name'])
    )
    conn.commit()
    cursor.close()
    
    return jsonify({
        'api_key': api_key,
        'message': 'API key generated successfully'
    }), 201

@app.route('/api/products', methods=['GET'])
@require_api_key
@db_connection
def get_products_api(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    cursor.close()
    return jsonify({'products': products})

@app.route('/api/products/<int:id>', methods=['GET'])
@require_api_key
@db_connection
def get_product_api(conn, id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM products WHERE id = %s', (id,))
    product = cursor.fetchone()
    cursor.close()
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'product': product})

@app.route('/api/products', methods=['POST'])
@require_api_key
@db_connection
def create_product_api(conn):
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
        
    data = request.get_json()
    required_fields = ['name', 'category', 'price']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO products (name, category, price, description) VALUES (%s, %s, %s, %s)',
            (data['name'], data['category'], float(data['price']), data.get('description', ''))
        )
        product_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        
        return jsonify({
            'message': 'Product created successfully',
            'product_id': product_id
        }), 201
        
    except ValueError:
        return jsonify({'error': 'Invalid price value'}), 400

@app.route('/api/products/<int:id>', methods=['PUT'])
@require_api_key
@db_connection
def update_product_api(conn, id):
    if not request.is_json:
        raise BadRequest("Content-Type must be application/json")
        
    data = request.get_json()
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM products WHERE id = %s', (id,))
    
    if not cursor.fetchone():
        cursor.close()
        return jsonify({'error': 'Product not found'}), 404
        
    update_fields = []
    update_values = []
    
    for field in ['name', 'category', 'price', 'description']:
        if field in data:
            update_fields.append(f"{field} = %s")
            update_values.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
        
    update_values.append(id)
    query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s"
    
    cursor.execute(query, update_values)
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Product updated successfully'})

@app.route('/api/products/<int:id>', methods=['DELETE'])
@require_api_key
@db_connection
def delete_product_api(conn, id):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM products WHERE id = %s', (id,))
    
    if not cursor.fetchone():
        cursor.close()
        return jsonify({'error': 'Product not found'}), 404
        
    cursor.execute('DELETE FROM products WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Product deleted successfully'})

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

from flask_restx import Api, Resource, fields, Namespace

# Initialize API
api = Api(app, 
    version='1.0', 
    title='Product Catalog API',
    description='API for managing product catalog',
    doc='/docs'
)

# Create namespace
ns = api.namespace('api', description='Product operations')

# Define models
product_model = api.model('Product', {
    'id': fields.Integer(readonly=True, description='Product identifier'),
    'name': fields.String(required=True, description='Product name'),
    'category': fields.String(required=True, description='Product category'),
    'price': fields.Float(required=True, description='Product price'),
    'description': fields.String(description='Product description')
})

api_key_model = api.model('APIKey', {
    'client_name': fields.String(required=True, description='Client name'),
})

api_key_response = api.model('APIKeyResponse', {
    'api_key': fields.String(description='Generated API key'),
    'message': fields.String(description='Response message')
})

# Document API endpoints
@ns.route('/products')
class ProductList(Resource):
    @ns.doc('list_products', security='apikey')
    @ns.marshal_list_with(product_model)
    @require_api_key
    @db_connection
    def get(self, conn):
        """List all products"""
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()
        cursor.close()
        return products

    @ns.doc('create_product', security='apikey')
    @ns.expect(product_model)
    @ns.response(201, 'Product created')
    @require_api_key
    @db_connection
    def post(self, conn):
        """Create a new product"""
        data = request.json
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO products (name, category, price, description) VALUES (%s, %s, %s, %s)',
            (data['name'], data['category'], data['price'], data.get('description', ''))
        )
        product_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return {'message': 'Product created', 'id': product_id}, 201

@ns.route('/products/<int:id>')
@ns.param('id', 'The product identifier')
class Product(Resource):
    @ns.doc('get_product', security='apikey')
    @ns.marshal_with(product_model)
    @require_api_key
    @db_connection
    def get(self, conn, id):
        """Get a product by ID"""
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM products WHERE id = %s', (id,))
        product = cursor.fetchone()
        cursor.close()
        if not product:
            api.abort(404, f"Product {id} not found")
        return product

@ns.route('/keys')
class APIKey(Resource):
    @ns.doc('create_api_key')
    @ns.expect(api_key_model)
    @ns.marshal_with(api_key_response, code=201)
    def post(self):
        """Generate new API key"""
        data = request.json
        if 'client_name' not in data:
            api.abort(400, "client_name is required")
        
        api_key = generate_api_key()
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO api_keys (key_value, client_name) VALUES (%s, %s)',
            (api_key, data['client_name'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'api_key': api_key,
            'message': 'API key generated successfully'
        }, 201

# Configure security
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-Key'
    }
}
api.authorizations = authorizations

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # Allow external access
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )