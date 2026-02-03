import pymysql

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='toko_kelontong',
        cursorclass=pymysql.cursors.DictCursor
    )

def test_customer_reset():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear customer table
    cursor.execute("DELETE FROM customer")
    cursor.execute("ALTER TABLE customer AUTO_INCREMENT = 1")
    conn.commit()

    # Insert two customers
    cursor.execute("INSERT INTO customer (nama) VALUES ('Test1')")
    cursor.execute("INSERT INTO customer (nama) VALUES ('Test2')")
    conn.commit()

    # Check AUTO_INCREMENT
    cursor.execute("SHOW TABLE STATUS LIKE 'customer'")
    status = cursor.fetchone()
    print(f"After inserting 2 customers, AUTO_INCREMENT: {status['Auto_increment']}")

    # Delete one customer (simulate delete_customer logic)
    cursor.execute("DELETE FROM customer WHERE nama = 'Test1'")
    cursor.execute("SELECT COUNT(*) as count FROM customer")
    count = cursor.fetchone()['count']
    if count == 0:
        cursor.execute("ALTER TABLE customer AUTO_INCREMENT = 1")
    conn.commit()

    # Check AUTO_INCREMENT
    cursor.execute("SHOW TABLE STATUS LIKE 'customer'")
    status = cursor.fetchone()
    print(f"After deleting one, 1 left, AUTO_INCREMENT: {status['Auto_increment']}")

    # Delete the last customer
    cursor.execute("DELETE FROM customer WHERE nama = 'Test2'")
    cursor.execute("SELECT COUNT(*) as count FROM customer")
    count = cursor.fetchone()['count']
    if count == 0:
        cursor.execute("ALTER TABLE customer AUTO_INCREMENT = 1")
    conn.commit()

    # Check AUTO_INCREMENT
    cursor.execute("SHOW TABLE STATUS LIKE 'customer'")
    status = cursor.fetchone()
    print(f"After deleting last, 0 left, AUTO_INCREMENT: {status['Auto_increment']}")

    # Insert new customer
    cursor.execute("INSERT INTO customer (nama) VALUES ('NewCustomer')")
    cursor.execute("SELECT id FROM customer WHERE nama = 'NewCustomer'")
    new_id = cursor.fetchone()['id']
    print(f"New customer ID: {new_id}")

    conn.close()

if __name__ == '__main__':
    test_customer_reset()
