from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import User, get_db_connection, Product, close_db_connection, Customer, Order
from forms import LoginForm, ProductForm
import os
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
from flask import jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'D:\\DATABASEPROJECT\\static\\images'  # Используйте двойные обратные слэши для путей в Windows
app.secret_key = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def create_admin():
    username = 'admin'
    password = "BIGSHOPBOY2003"

    # Проверка, что пользователь с таким именем уже не существует
    existing_user = User.get_by_username(username)
    if existing_user:
        return "Username already exists", 400

    # Хеширование пароля
    hashed_password = generate_password_hash(password)

    # Создание нового пользователя
    new_user_id = None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO User (username, password) VALUES (?, ?)', (username, hashed_password))
        new_user_id = cursor.lastrowid
    
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('Logged in successfully.')
                return redirect(url_for('index'))
            else:
                flash('Invalid password')
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

from flask import request

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form.get('search_query', default='', type=str)
        selected_category = request.form.get('category', default='', type=str)  
    else:
        search_query = request.args.get('search_query', default='', type=str)
        selected_category = request.args.get('category', default='', type=str)  
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search_query and selected_category:
        cursor.execute("SELECT * FROM Product WHERE name LIKE ? AND category_id = ?", ('%' + search_query + '%', selected_category))
    elif search_query:
        cursor.execute("SELECT * FROM Product WHERE name LIKE ?", ('%' + search_query + '%',))
    elif selected_category:
        cursor.execute("SELECT * FROM Product WHERE category_id = ?", (selected_category,))
    else:
        cursor.execute('SELECT * FROM Product')
    
    products = cursor.fetchall()
    
    # Получаем список категорий
    categories = Product.get_categories()

    conn.close()

    return render_template('index.html', products=products, categories=categories, selected_category=selected_category)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    customer_id = current_user.id
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    quantity = 1  # or any other value depending on how you manage quantity

    # Get the current order for the customer
    current_order = Order.get_cart(customer_id)

    # If the customer doesn't have a current order, create a new one
    if not current_order:
        new_order = Order(customer_id=customer_id)
        new_order.save_to_db()
        order_id = new_order.id
    else:
        order_id = current_order.id

    # Check if the product is already in the order
    cursor.execute('SELECT 1 FROM OrderItem WHERE order_id = ? AND product_id = ?', (order_id, product_id))
    existing_order_item = cursor.fetchone()

    if existing_order_item:
        # If the product is already in the order, update its quantity
        cursor.execute('UPDATE OrderItem SET quantity = quantity + ? WHERE order_id = ? AND product_id = ?', (quantity, order_id, product_id))
    else:
        # If the product is not in the order, insert it
        cursor.execute('''
            INSERT INTO OrderItem (order_id, product_id, quantity, price)
            SELECT ?, ?, ?, price FROM Product WHERE id = ? AND quantity >= ?
        ''', (order_id, product_id, quantity, product_id, quantity))

    if cursor.rowcount > 0:
        # Decrease the quantity of the product in the Product table
        cursor.execute('UPDATE Product SET quantity = quantity - ? WHERE id = ?', (quantity, product_id))
        conn.commit()  # Commit the transaction if everything is okay
    else:
        conn.rollback()  # Rollback the transaction if there's not enough product or other error
        # You can add an error message for the user

    conn.close()

    return redirect(url_for('index'))

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    customer_id = current_user.id

    if request.method == 'POST':
        if 'edit_customer_info' in request.form:
            name = request.form['name']
            address = request.form['address']
            phone = request.form['phone']
            email = request.form['email']

            current_customer_info = Customer.get_by_id(customer_id)
            print(current_customer_info)
            if current_customer_info is not None:
                current_customer = Customer(id=current_customer_info[0], name=current_customer_info[1], address=current_customer_info[2], phone=current_customer_info[3], email=current_customer_info[4])
                current_customer.name = name
                current_customer.address = address
                current_customer.phone = phone
                current_customer.email = email
                try:
                    current_customer.save_to_db()
                    return jsonify(status='success')
                except Exception as e:
                    return jsonify(status='error', message=str(e))
            else:
                # Создаем нового покупателя
                new_customer = Customer(name=name, address=address, phone=phone, email=email)
                try:
                    new_customer.save_to_db()
                    return jsonify(status='success')
                except Exception as e:
                    return jsonify(status='error', message=str(e))


        elif 'confirm_order' in request.form:
            current_customer_info = Customer.get_by_id(customer_id)
            print(current_customer_info)
            if current_customer_info is not None:
                current_customer = Customer(id=current_customer_info[0], name=current_customer_info[1], address=current_customer_info[2], phone=current_customer_info[3], email=current_customer_info[4])
            if not current_customer or not current_customer.name or not current_customer.address or not current_customer.phone or not current_customer.email:
                return jsonify(status='error', message='Заполните информацию о пользователе перед подтверждением заказа.')

            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE "Order" SET date=datetime('now')
                        WHERE customer_id=? AND date IS NULL
                    ''', (customer_id,))
                    conn.commit()
                return jsonify(status='success')
            except Exception as e:
                return jsonify(status='error', message=str(e))

    customer_info = Customer.get_by_id(customer_id)
    current_order = Order.get_cart(customer_id)
    order_history = Order.get_order_history(customer_id)

    for order in order_history:
        order_date_time = datetime.strptime(order['date'], "%Y-%m-%d %H:%M:%S")
        order['date'] = order_date_time.date()
        order['time'] = order_date_time.time()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.name, oi.quantity, oi.price, (oi.quantity * oi.price) as total_price, p.quantity as available_quantity, p.id
            FROM OrderItem oi
            JOIN Product p ON oi.product_id = p.id
            JOIN "Order" o ON oi.order_id = o.id
            WHERE o.customer_id = ? AND o.date IS NULL
        ''', (customer_id,))
        cart_items = cursor.fetchall()

    total_cost = sum(item[3] for item in cart_items) if cart_items else 0

    return render_template('cart.html', customer=customer_info, current_order=current_order, order_history=order_history, cart_items=cart_items, total_cost=total_cost)



@app.route('/update_quantity', methods=['POST'])
@login_required
def update_quantity():
    product_id = request.form['product_id']
    action = request.form['action']
    customer_id = current_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT oi.quantity, p.quantity as stock_quantity
        FROM OrderItem oi
        JOIN Product p ON oi.product_id = p.id
        JOIN "Order" o ON oi.order_id = o.id
        WHERE o.customer_id = ? AND o.date IS NULL AND oi.product_id = ?
    ''', (customer_id, product_id))
    order_item = cursor.fetchone()
    if not order_item:
        print("No order item found for the given criteria.")
        return jsonify(status='error')

    order_quantity = order_item[0]
    stock_quantity = order_item[1]

    if action == 'increase' and stock_quantity > 0:
        cursor.execute('''
            INSERT OR IGNORE INTO OrderItem (order_id, product_id, quantity, price)
            SELECT o.id, ?, 1, p.price 
            FROM "Order" o
            JOIN Product p ON p.id = ?
            WHERE o.customer_id = ? AND o.date IS NULL
        ''', (product_id, product_id, current_user.id))
        cursor.execute('''
            UPDATE OrderItem SET quantity = quantity + 1
            WHERE product_id = ? AND order_id IN (SELECT id FROM "Order" WHERE customer_id = ? AND date IS NULL)
        ''', (product_id, current_user.id))
        cursor.execute('UPDATE Product SET quantity = quantity - 1 WHERE id = ?', (product_id,))
    elif action == 'decrease':
        if order_quantity > 1:
            cursor.execute('''
                UPDATE OrderItem SET quantity = quantity - 1
                WHERE product_id = ? AND order_id IN (SELECT id FROM "Order" WHERE customer_id = ? AND date IS NULL)
            ''', (product_id, current_user.id))
            cursor.execute('UPDATE Product SET quantity = quantity + 1 WHERE id = ?', (product_id,))
        else:
            # Если количество товара равно 1, удаляем товар из корзины
            cursor.execute('''
                DELETE FROM OrderItem
                WHERE product_id = ? AND order_id IN (SELECT id FROM "Order" WHERE customer_id = ? AND date IS NULL)
            ''', (product_id, current_user.id))
    else:
        return jsonify(status='error')
    
    conn.commit()
    conn.close()

    return jsonify(status='success')



@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.username != 'admin':
        return redirect(url_for('index'))

    if request.method == 'POST':
        search_query = request.form.get('search_query', default='', type=str)
        selected_category = request.form.get('category', default='', type=str)  
    else:
        search_query = request.args.get('search_query', default='', type=str)
        selected_category = request.args.get('category', default='', type=str)  
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search_query and selected_category:
        cursor.execute("SELECT * FROM Product WHERE name LIKE ? AND category_id = ?", ('%' + search_query + '%', selected_category))
    elif search_query:
        cursor.execute("SELECT * FROM Product WHERE name LIKE ?", ('%' + search_query + '%',))
    elif selected_category:
        cursor.execute("SELECT * FROM Product WHERE category_id = ?", (selected_category,))
    else:
        cursor.execute('SELECT * FROM Product')
    
    products_data = cursor.fetchall()
    categories = Product.get_categories()
    conn.close()

    # Преобразуем кортежи в объекты Product
    products = [Product(*product_data) for product_data in products_data]

    return render_template('admin.html', products=products, categories=categories, selected_category=selected_category)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.username != 'admin':
        return redirect(url_for('index'))
    form = ProductForm()
    if form.validate_on_submit():
        category_id_str = str(form.category_id.data)
        image_filename = secure_filename(form.image.data.filename)  # Получение имени файла
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        new_product = Product(
            name=form.name.data,
            category_id=category_id_str,
            price=form.price.data,
            quantity=form.quantity.data,
            image=image_filename
        )
        new_product.save_to_db()  # Пусть метод save_to_db сам генерирует id при сохранении
        # Сохранение изображения на сервере
        form.image.data.save(image_path)
        return redirect(url_for('admin'))
    return render_template('add_product.html', form=form)


@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.username != 'admin':
        return redirect(url_for('index'))
    product = Product.get_by_id(product_id)
    if product is None:
        flash('Product not found', 'error')
        return redirect(url_for('admin'))
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        image_filename = secure_filename(form.image.data)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        product.name = form.name.data
        product.category_id = form.category_id.data
        product.price = form.price.data
        product.quantity = form.quantity.data
        product.image = image_filename
        product.save_to_db()
        return redirect(url_for('admin'))
    return render_template('edit_product.html', form=form, product=product)

@app.route('/admin/delete_product/<int:product_id>', methods=['POST', 'GET'])
@login_required
def delete_product(product_id):
    if current_user.username != 'admin':
        return redirect(url_for('index'))
    
    product = Product.get_by_id(product_id)
    if product is None:
        flash('Product not found', 'error')
    else:
        product.delete_from_db()
    
    return redirect(url_for('admin'))

@app.route('/cart/customer_info', methods=['GET', 'POST'])
@login_required
def customer_info():
    customer_id = current_user.id
    if request.method == 'POST':
        customer_data = request.json
        customer = Customer(
            id=customer_id,
            name=customer_data['name'],
            address=customer_data['address'],
            phone=customer_data['phone'],
            email=customer_data.get('email', None),
            username=current_user.username,
            password=current_user.password
        )
        customer.save_to_db()
        return jsonify({"message": "Customer info updated successfully"})
    else:
        customer = Customer.get_by_id(customer_id)
        if customer:
            return jsonify({
                "name": customer[1],
                "address": customer[2],
                "phone": customer[3],
                "email": customer[4]
            })
        else:
            return jsonify({"message": "Customer info not found"}), 404

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    # Проверка, что пароль совпадает с подтверждением пароля
    if password != confirm_password:
        return "Passwords do not match", 400

    # Проверка, что пользователь с таким именем уже не существует
    existing_user = User.get_by_username(username)
    if existing_user:
        return "Username already exists", 400

    # Хеширование пароля
    hashed_password = generate_password_hash(password)

    # Создание нового пользователя
    new_user_id = None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO User (username, password) VALUES (?, ?)', (username, hashed_password))
        new_user_id = cursor.lastrowid

    # Перенаправление на страницу входа после успешной регистрации
    return redirect(url_for('login'))

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)