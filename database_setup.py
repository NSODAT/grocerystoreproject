import sqlite3

def create_tables():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        image TEXT,
        FOREIGN KEY (category_id) REFERENCES Category(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Customer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        email TEXT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Order" (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        customer_id INTEGER,
        FOREIGN KEY (customer_id) REFERENCES Customer(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OrderItem (
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES "Order"(id),
        FOREIGN KEY (product_id) REFERENCES Product(id),
        PRIMARY KEY (order_id, product_id)
    )
    ''')


    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
