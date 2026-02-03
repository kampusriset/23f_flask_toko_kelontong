import pymysql

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='toko_kelontong',
        cursorclass=pymysql.cursors.DictCursor
    )

def test_transaction_reset():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear transaction and transaction_item tables
    cursor.execute("DELETE FROM transaction_item")
    cursor.execute("DELETE FROM transaction")
    cursor.execute("ALTER TABLE transaction AUTO_INCREMENT = 1")
    conn.commit()

    # Insert a transaction (simulate)
    cursor.execute("INSERT INTO transaction (customer_name, total) VALUES ('TestCustomer', 1000)")
    tr_id = cursor.lastrowid
    cursor.execute("INSERT INTO transaction_item (transaction_id, product_name, harga, qty, subtotal) VALUES (%s, 'TestProduct', 1000, 1, 1000)", (tr_id,))
    conn.commit()

    # Check AUTO_INCREMENT
    cursor.execute("SHOW TABLE STATUS LIKE 'transaction'")
    status = cursor.fetchone()
    print(f"After inserting 1 transaction, AUTO_INCREMENT: {status['Auto_increment']}")

    # Delete the transaction (simulate delete_transaction logic)
    cursor.execute("DELETE FROM transaction_item WHERE transaction_id = %s", (tr_id,))
    cursor.execute("DELETE FROM transaction WHERE id = %s", (tr_id,))
    cursor.execute("SELECT COUNT(*) as count FROM transaction")
    count = cursor.fetchone()['count']
    if count == 0:
        cursor.execute("ALTER TABLE transaction AUTO_INCREMENT = 1")
    conn.commit()

    # Check AUTO_INCREMENT
    cursor.execute("SHOW TABLE STATUS LIKE 'transaction'")
    status = cursor.fetchone()
    print(f"After deleting the transaction, AUTO_INCREMENT: {status['Auto_increment']}")

    # Insert new transaction
    cursor.execute("INSERT INTO transaction (customer_name, total) VALUES ('NewCustomer', 2000)")
    new_tr_id = cursor.lastrowid
    print(f"New transaction ID: {new_tr_id}")

    conn.close()

if __name__ == '__main__':
    test_transaction_reset()
