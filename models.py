import sqlite3
from flask import g

DATABASE = 'store.db'

def get_db_connection():
    return sqlite3.connect(DATABASE)

def close_db_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def get_id(self):
        return str(self.id)
   
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
    @staticmethod
    def get_by_id(user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM User WHERE id = ?', (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(*user_data)
            else:
                return None

    @staticmethod
    def get_by_username(username):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM User WHERE username = ?', (username,))
            user_data = cursor.fetchone()
            if user_data:
                return User(*user_data)
            else:
                return None

class Product:
    def __init__(self, id=None, name=None, category_id=None, price=None, quantity=None, image=None):
        self.id = id
        self.name = name
        self.category_id = category_id
        self.price = price
        self.quantity = quantity
        self.image = image

    def save_to_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if self.id is None:
                cursor.execute('INSERT INTO Product (name, category_id, price, quantity, image) VALUES (?, ?, ?, ?, ?)',
                               (self.name, self.category_id, self.price, self.quantity, self.image))
            else:
                cursor.execute('UPDATE Product SET name = ?, category_id = ?, price = ?, quantity = ?, image = ? WHERE id = ?',
                               (self.name, self.category_id, self.price, self.quantity, self.image, self.id))
            conn.commit()

    def delete_from_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Product WHERE id = ?', (self.id,))
            conn.commit()

    def increase_stock(self, quantity):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE Product SET quantity = quantity + ? WHERE id = ?', (quantity, self.id))
            conn.commit()

    def decrease_stock(self, quantity):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE Product SET quantity = quantity - ? WHERE id = ?', (quantity, self.id))
            conn.commit()
    

    @classmethod
    def get_by_id(cls, product_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Product WHERE id = ?', (product_id,))
            product_data = cursor.fetchone()
            if product_data:
                return cls(*product_data)
            else:
                return None

    @staticmethod
    def get_all_products():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Product')
            products_data = cursor.fetchall()
            return [Product(*data) for data in products_data]
        
    @staticmethod
    def get_categories():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category_id FROM Product')
            category_ids = cursor.fetchall()
            return [category_id[0] for category_id in category_ids]
class Customer:
    def __init__(self, id=None, name=None, address=None, phone=None, email=None, username=None, password=None):
        self.id = id
        self.name = name
        self.address = address
        self.phone = phone
        self.email = email
        self.username = username
        self.password = password

    @staticmethod
    def get_by_id(id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Customer WHERE id = ?', (id,))
            return cursor.fetchone()

    @staticmethod
    def get_by_username(username):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Customer WHERE username = ?', (username,))
            return cursor.fetchone()

    def save_to_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if self.id is None:
                cursor.execute('''
                    INSERT INTO Customer (name, address, phone, email, username, password) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                               (self.name, self.address, self.phone, self.email, self.username, self.password))
                self.id = cursor.lastrowid
            else:
                cursor.execute('''
                    UPDATE Customer SET name = ?, address = ?, phone = ?, email = ?
                    WHERE id = ?''',
                               (self.name, self.address, self.phone, self.email, self.id))
            conn.commit()


class Order:
    def __init__(self, id=None, customer_id=None, date=None):
        self.id = id
        self.customer_id = customer_id
        self.date = date

    def save_to_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if self.id is None:
                cursor.execute('INSERT INTO "Order" (customer_id) VALUES (?)', (self.customer_id,))
                self.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE "Order" SET customer_id = ? WHERE id = ?', (self.customer_id, self.id))
            conn.commit()

    @staticmethod
    def update_order_date(order_id, date):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE "Order" SET date = ? WHERE id = ?', (date, order_id))
            conn.commit()

    @staticmethod
    def get_cart(customer_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "Order" WHERE customer_id = ? AND date IS NULL', (customer_id,))
            order_data = cursor.fetchone()
            if order_data:
                return Order(*order_data)
            else:
                return None

class Order:
    def __init__(self, id=None, customer_id=None, date=None):
        self.id = id
        self.customer_id = customer_id
        self.date = date

    def save_to_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if self.id is None:
                cursor.execute('INSERT INTO "Order" (customer_id) VALUES (?)', (self.customer_id,))
                self.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE "Order" SET customer_id = ? WHERE id = ?', (self.customer_id, self.id))
            conn.commit()

    @staticmethod
    def update_order_date(order_id, date):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE "Order" SET date = ? WHERE id = ?', (date, order_id))
            conn.commit()

    @staticmethod
    def get_cart(customer_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "Order" WHERE customer_id = ? AND date IS NULL', (customer_id,))
            order_data = cursor.fetchone()
            if order_data:
                return Order(*order_data)
            else:
                return None
    
    @staticmethod
    def get_order_history(customer_id):
        """Get order history for a customer."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Извлекаем заказы клиента
            cursor.execute('SELECT id, date FROM "Order" WHERE customer_id = ? AND date IS NOT NULL', (customer_id,))
            orders_data = cursor.fetchall()
            
            orders = []
            for order_data in orders_data:
                order_id, date = order_data
                # Извлекаем данные покупателя для текущего заказа
                cursor.execute('SELECT name, phone, address, email FROM Customer WHERE id = ?', (customer_id,))
                customer_data = cursor.fetchone()
                
                if customer_data:
                    name, phone, address, email = customer_data
                    # Извлекаем товары для текущего заказа
                    items = OrderItem.get_order_items(order_id)
                    total_cost = sum(item['total_price'] for item in items)
                    order = {
                        'order_id': order_id,
                        'date': date,
                        'customer_name': name,
                        'customer_phone': phone,
                        'customer_address': address,
                        'customer_email': email,
                        'items': items,
                        'total_cost': total_cost
                    }
                    orders.append(order)
            return orders

class OrderItem:
    @staticmethod
    def get_order_items(order_id):
        """Get items for a specific order."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    p.name,
                    oi.quantity,
                    oi.price,
                    (oi.quantity * oi.price) AS total_price,
                    p.image
                FROM 
                    OrderItem oi
                JOIN 
                    Product p ON oi.product_id = p.id
                WHERE 
                    oi.order_id = ?
            ''', (order_id,))
            items_data = cursor.fetchall()
            items = [
                {
                    'name': item_data[0],
                    'quantity': item_data[1],
                    'price': item_data[2],
                    'total_price': item_data[3],
                    'image': item_data[4]
                }
                for item_data in items_data
            ]
            return items