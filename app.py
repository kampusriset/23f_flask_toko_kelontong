print("=== Mulai menjalankan aplikasi Flask ===")
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
import pymysql
from datetime import datetime, date, timedelta
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-me'

# Database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='toko_kelontong',
        cursorclass=pymysql.cursors.DictCursor
    )

# Database functions
def create_db_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(200) NOT NULL,
            harga FLOAT NOT NULL DEFAULT 0.0,
            stok INT NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(120) NOT NULL,
            telepon VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(120) NOT NULL,
            total FLOAT NOT NULL,
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_item (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id INT NOT NULL,
            product_name VARCHAR(200),
            harga FLOAT,
            qty INT,
            subtotal FLOAT,
            FOREIGN KEY (transaction_id) REFERENCES transaction(id)
        )
    ''')
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM product")
    if cursor.fetchone()['COUNT(*)'] == 0:
        cursor.execute("INSERT INTO product (nama, harga, stok) VALUES (%s, %s, %s)", ('Indomie Goreng', 3500, 50))
        cursor.execute("INSERT INTO product (nama, harga, stok) VALUES (%s, %s, %s)", ('Gula Pasir 1kg', 14000, 20))
        cursor.execute("INSERT INTO product (nama, harga, stok) VALUES (%s, %s, %s)", ('Kopi Kapal Api', 2000, 30))
    cursor.execute("SELECT COUNT(*) FROM customer")
    if cursor.fetchone()['COUNT(*)'] == 0:
        cursor.execute("INSERT INTO customer (nama) VALUES (%s)", ('Salvano',))
        cursor.execute("INSERT INTO customer (nama) VALUES (%s)", ('Panji',))
    conn.commit()
    conn.close()

# create db and sample data
def create_tables():
    create_db_tables()
    insert_sample_data()

# Simple auth
def is_logged_in():
    return session.get('logged_in')

def get_chart_data(cursor, today):
    # Daily
    day_names = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
    daily_labels = []
    daily_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        label = day_names[d.weekday()]
        daily_labels.append(label)
        cursor.execute("SELECT COALESCE(SUM(total), 0) as revenue FROM transaction WHERE DATE(tanggal) = %s", (d,))
        revenue = cursor.fetchone()['revenue']
        daily_data.append(revenue)
    # Weekly
    weekly_labels = ["Minggu 1", "Minggu 2", "Minggu 3", "Minggu 4"]
    weekly_data = []
    for i in range(3, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7*i)
        week_end = week_start + timedelta(days=6)
        cursor.execute("SELECT COALESCE(SUM(total), 0) as revenue FROM transaction WHERE DATE(tanggal) >= %s AND DATE(tanggal) <= %s", (week_start, week_end))
        revenue = cursor.fetchone()['revenue']
        weekly_data.append(revenue)
    # Monthly
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_labels = []
    monthly_data = []
    for i in range(4, -1, -1):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        label = month_names[month - 1]
        monthly_labels.append(label)
        cursor.execute("SELECT COALESCE(SUM(total), 0) as revenue FROM transaction WHERE YEAR(tanggal) = %s AND MONTH(tanggal) = %s", (year, month))
        revenue = cursor.fetchone()['revenue']
        monthly_data.append(revenue)
    return daily_labels, daily_data, weekly_labels, weekly_data, monthly_labels, monthly_data

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == '123':
            session['logged_in'] = True
            session['user'] = 'admin'
            flash('Berhasil login', 'success')
            return redirect(url_for('index'))
        flash('Username / password salah', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout berhasil', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM product")
    total_products = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM customer")
    total_customers = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM transaction")
    total_transactions = cursor.fetchone()['count']
    today = date.today()
    cursor.execute("SELECT COALESCE(SUM(total), 0) as omzet FROM transaction WHERE DATE(tanggal) = %s", (today,))
    omzet_today = cursor.fetchone()['omzet']
    # Add chart data for dashboard
    daily_labels, daily_data, weekly_labels, weekly_data, monthly_labels, monthly_data = get_chart_data(cursor, today)
    conn.close()
    return render_template('dashboard.html', total_products=total_products,
                           total_customers=total_customers,
                           total_transactions=total_transactions,
                           omzet_today=omzet_today,
                           daily_labels=daily_labels,
                           daily_data=daily_data,
                           weekly_labels=weekly_labels,
                           weekly_data=weekly_data,
                           monthly_labels=monthly_labels,
                           monthly_data=monthly_data)

# Products CRUD
@app.route('/products')
def products():
    if not is_logged_in():
        return redirect(url_for('login'))
    q = request.args.get('q','')
    conn = get_db_connection()
    cursor = conn.cursor()
    if q:
        cursor.execute("SELECT * FROM product WHERE nama LIKE %s AND stok > 0 ORDER BY created_at DESC", ('%' + q + '%',))
    else:
        cursor.execute("SELECT * FROM product WHERE stok > 0 ORDER BY created_at DESC")
    items = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=items, q=q)

@app.route('/products/add', methods=['GET','POST'])
def add_product():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        nama = request.form['nama'].strip()
        harga = float(request.form['harga'])
        stok = int(request.form['stok'])
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check if product with same name already exists
        cursor.execute("SELECT id FROM product WHERE nama = %s", (nama,))
        existing_product = cursor.fetchone()
        if existing_product:
            conn.close()
            flash('Produk Sudah Tersedia di Database', 'danger')
            return redirect(url_for('add_product'))
        cursor.execute("INSERT INTO product (nama, harga, stok) VALUES (%s, %s, %s)", (nama, harga, stok))
        conn.commit()
        conn.close()
        flash('Produk berhasil ditambahkan', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Tambah')

@app.route('/products/edit/<int:id>', methods=['GET','POST'])
def edit_product(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product WHERE id = %s", (id,))
    p = cursor.fetchone()
    if not p:
        conn.close()
        return redirect(url_for('products'))
    if request.method == 'POST':
        nama = request.form['nama'].strip()
        harga = float(request.form['harga'])
        stok = int(request.form['stok'])
        if stok <= 0:
            cursor.execute("DELETE FROM product WHERE id = %s", (id,))
            conn.commit()
            conn.close()
            flash('Produk dihapus karena stok habis', 'success')
            return redirect(url_for('products'))
        else:
            cursor.execute("UPDATE product SET nama = %s, harga = %s, stok = %s WHERE id = %s", (nama, harga, stok, id))
            conn.commit()
            conn.close()
            flash('Produk berhasil diperbarui', 'success')
            return redirect(url_for('products'))
    conn.close()
    return render_template('product_form.html', action='Edit', product=p)

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    flash('Produk dihapus', 'success')
    return redirect(url_for('products'))

# Customers CRUD
@app.route('/customers')
def customers():
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer ORDER BY created_at DESC")
    items = cursor.fetchall()
    conn.close()
    return render_template('customers.html', customers=items)

@app.route('/customers/add', methods=['GET','POST'])
def add_customer():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        nama = request.form['nama'].strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customer (nama) VALUES (%s)", (nama,))
        conn.commit()
        conn.close()
        flash('Pelanggan ditambahkan', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', action='Tambah')

@app.route('/customers/edit/<int:id>', methods=['GET','POST'])
def edit_customer(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer WHERE id = %s", (id,))
    c = cursor.fetchone()
    if not c:
        conn.close()
        return redirect(url_for('customers'))
    if request.method == 'POST':
        nama = request.form['nama'].strip()
        cursor.execute("UPDATE customer SET nama = %s WHERE id = %s", (nama, id))
        conn.commit()
        conn.close()
        flash('Pelanggan diperbarui', 'success')
        return redirect(url_for('customers'))
    conn.close()
    return render_template('customer_form.html', action='Edit', customer=c)

@app.route('/customers/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customer WHERE id = %s", (id,))
    # Check if no customers left, reset AUTO_INCREMENT to 1
    cursor.execute("SELECT COUNT(*) as count FROM customer")
    if cursor.fetchone()['count'] == 0:
        cursor.execute("ALTER TABLE customer AUTO_INCREMENT = 1")
    conn.commit()
    conn.close()
    flash('Pelanggan dihapus', 'success')
    return redirect(url_for('customers'))

# Simple POS
@app.route('/pos')
def pos():
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product WHERE stok > 0 ORDER BY nama")
    products = cursor.fetchall()
    conn.close()
    cart = session.get('cart', {})
    # Ensure all harga are floats
    for pid in cart:
        cart[pid]['harga'] = float(cart[pid]['harga'])
    total = 0
    for pid, item in cart.items():
        total += item['harga'] * item['qty']
    return render_template('pos.html', products=products, cart=cart, total=total)

@app.route('/pos/add', methods=['POST'])
def pos_add():
    if not is_logged_in():
        return redirect(url_for('login'))
    pid = int(request.form['product_id'])
    qty = int(request.form.get('qty',1))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product WHERE id = %s", (pid,))
    product = cursor.fetchone()
    conn.close()
    if not product:
        flash('Produk tidak ditemukan', 'danger')
        return redirect(url_for('pos'))
    cart = session.get('cart', {})
    if str(pid) in cart:
        cart[str(pid)]['qty'] += qty
    else:
        cart[str(pid)] = {'nama': product['nama'], 'harga': float(product['harga']), 'qty': qty}
    session['cart'] = cart
    flash('Produk ditambahkan ke keranjang', 'success')
    return redirect(url_for('pos'))

@app.route('/pos/remove/<int:pid>', methods=['POST'])
def pos_remove(pid):
    if not is_logged_in():
        return redirect(url_for('login'))
    cart = session.get('cart', {})
    cart.pop(str(pid), None)
    session['cart'] = cart
    return redirect(url_for('pos'))

@app.route('/pos/checkout', methods=['POST'])
def pos_checkout():
    if not is_logged_in():
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    if not cart:
        flash('Keranjang kosong', 'danger')
        return redirect(url_for('pos'))

    customer_name = request.form.get('customer_name', '').strip()
    if not customer_name:
        customer_name = "(None)"

    total = 0
    for pid, item in cart.items():
        total += item['harga'] * item['qty']

    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if customer exists, if not, add to customer table (only if not "(None)")
    if customer_name != "(None)":
        cursor.execute("SELECT id FROM customer WHERE nama = %s", (customer_name,))
        existing_customer = cursor.fetchone()
        if not existing_customer:
            cursor.execute("INSERT INTO customer (nama) VALUES (%s)", (customer_name,))
    cursor.execute("INSERT INTO transaction (customer_name, total, tanggal) VALUES (%s, %s, %s)", (customer_name, total, datetime.now()))
    tr_id = cursor.lastrowid

    # tambah item
    for pid, item in cart.items():
        cursor.execute("SELECT * FROM product WHERE id = %s", (int(pid),))
        prod = cursor.fetchone()
        qty = int(item['qty'])
        subtotal = item['harga'] * qty
        cursor.execute("INSERT INTO transaction_item (transaction_id, product_name, harga, qty, subtotal) VALUES (%s, %s, %s, %s, %s)", (tr_id, prod['nama'], prod['harga'], qty, subtotal))
        new_stok = max(0, prod['stok'] - qty)
        if new_stok == 0:
            cursor.execute("DELETE FROM product WHERE id = %s", (int(pid),))
        else:
            cursor.execute("UPDATE product SET stok = %s WHERE id = %s", (new_stok, int(pid)))
    conn.commit()
    conn.close()

    session['cart'] = {}
    flash('Transaksi berhasil disimpan', 'success')
    return redirect(url_for('transactions'))

# transactions
@app.route('/transactions')
def transactions():
    if not is_logged_in():
        return redirect(url_for('login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM transaction WHERE 1=1"
    params = []

    if start_date:
        query += " AND DATE(tanggal) >= %s"
        params.append(start_date)

    if end_date:
        query += " AND DATE(tanggal) <= %s"
        params.append(end_date)

    query += " ORDER BY tanggal DESC"

    cursor.execute(query, params)
    trans = cursor.fetchall()
    conn.close()

    return render_template(
        'transactions.html',
        transactions=trans
    )

# 🔥 Route Cetak PDF
@app.route('/transactions/print')
def print_transactions():
    if not is_logged_in():
        return redirect(url_for('login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM transaction WHERE 1=1"
    params = []

    if start_date:
        query += " AND DATE(tanggal) >= %s"
        params.append(start_date)

    if end_date:
        query += " AND DATE(tanggal) <= %s"
        params.append(end_date)

    query += " ORDER BY tanggal DESC"
    cursor.execute(query, params)
    transactions = cursor.fetchall()

    # Fetch items for each transaction
    transaction_items = {}
    for t in transactions:
        cursor.execute("SELECT * FROM transaction_item WHERE transaction_id = %s", (t['id'],))
        transaction_items[t['id']] = cursor.fetchall()

    conn.close()

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(
        "<b>LAPORAN TRANSAKSI TOKO MANDIRI JAYA</b>",
        styles['Title']
    ))

    periode = "Semua Tanggal"
    if start_date and end_date:
        periode = f"{start_date} s/d {end_date}"

    elements.append(Paragraph(f"Periode: {periode}", styles['Normal']))
    elements.append(Paragraph(
        f"Tanggal Cetak: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        styles['Normal']
    ))
    elements.append(Paragraph("<br/>", styles['Normal']))

    data = [["ID", "Pelanggan", "Total (Rp)", "Tanggal"]]
    total_all = 0

    for t in transactions:
        data.append([
            t['id'],
            t['customer_name'],
            f"{t['total']:,.0f}",
            t['tanggal'].strftime("%d-%m-%Y %H:%M")
        ])
        total_all += t['total']

    data.append(["", "TOTAL", f"{total_all:,.0f}", ""])

    table = Table(data, colWidths=[50, 180, 120, 140])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('FONT', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONT', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
    ]))

    elements.append(table)

    # Add details for each transaction
    for t in transactions:
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        elements.append(Paragraph(f"<b>Detail Transaksi #{t['id']} - {t['customer_name']}</b>", styles['Heading2']))
        elements.append(Paragraph(f"Total: Rp {t['total']:,.0f} | Tanggal: {t['tanggal'].strftime('%d-%m-%Y %H:%M')}", styles['Normal']))
        elements.append(Paragraph("<br/>", styles['Normal']))

        items = transaction_items.get(t['id'], [])
        if items:
            item_data = [["Produk", "Harga (Rp)", "Qty", "Subtotal (Rp)"]]
            for item in items:
                item_data.append([
                    item['product_name'],
                    f"{item['harga']:,.0f}",
                    item['qty'],
                    f"{item['subtotal']:,.0f}"
                ])
            item_table = Table(item_data, colWidths=[200, 80, 50, 100])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('FONT', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,1), (3,-1), 'RIGHT'),
            ]))
            elements.append(item_table)
        else:
            elements.append(Paragraph("Tidak ada item.", styles['Normal']))

    pdf.build(elements)

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=laporan_transaksi.pdf'
    return response

@app.route('/transactions/print/<int:id>')
def print_transaction(id):
    if not is_logged_in():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the specific transaction
    cursor.execute("SELECT * FROM transaction WHERE id = %s", (id,))
    transaction = cursor.fetchone()
    if not transaction:
        conn.close()
        flash('Transaksi tidak ditemukan', 'danger')
        return redirect(url_for('transactions'))

    # Fetch items for the transaction
    cursor.execute("SELECT * FROM transaction_item WHERE transaction_id = %s", (id,))
    items = cursor.fetchall()

    conn.close()

    try:
        buffer = BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        elements.append(Paragraph(
            "<b>NOTA TRANSAKSI TOKO MANDIRI JAYA</b>",
            styles['Title']
        ))

        elements.append(Paragraph(f"ID Transaksi: {transaction['id']}", styles['Normal']))
        elements.append(Paragraph(f"Pelanggan: {transaction['customer_name']}", styles['Normal']))
        tanggal_str = transaction['tanggal'].strftime('%d-%m-%Y %H:%M') if transaction['tanggal'] else 'N/A'
        elements.append(Paragraph(f"Tanggal: {tanggal_str}", styles['Normal']))
        elements.append(Paragraph(
            f"Tanggal Cetak: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            styles['Normal']
        ))
        elements.append(Paragraph("<br/>", styles['Normal']))

        if items:
            item_data = [["Produk", "Harga (Rp)", "Qty", "Subtotal (Rp)"]]
            for item in items:
                item_data.append([
                    item['product_name'],
                    f"{item['harga']:,.0f}",
                    item['qty'],
                    f"{item['subtotal']:,.0f}"
                ])
            item_table = Table(item_data, colWidths=[200, 80, 50, 100])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('FONT', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,1), (3,-1), 'RIGHT'),
            ]))
            elements.append(item_table)

            # Add summary table for total
            elements.append(Paragraph("<br/>", styles['Normal']))
            summary_data = [["Total Pembelian", "", "", f"Rp {transaction['total']:,.0f}"]]
            summary_table = Table(summary_data, colWidths=[200, 80, 50, 100])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('FONT', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (3,0), (3,0), 'RIGHT'),
            ]))
            elements.append(summary_table)
        else:
            elements.append(Paragraph("Tidak ada item.", styles['Normal']))

        pdf.build(elements)

        buffer.seek(0)
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=nota_transaksi_{id}.pdf'
        return response
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('transactions'))

@app.route('/transactions/<int:id>')
def transaction_detail(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transaction WHERE id = %s", (id,))
    tr = cursor.fetchone()
    if not tr:
        conn.close()
        return redirect(url_for('transactions'))
    cursor.execute("SELECT * FROM transaction_item WHERE transaction_id = %s", (id,))
    items = cursor.fetchall()
    conn.close()
    return render_template('transaction_detail.html', tr=tr, items=items)

# 🔥 ROUTE DELETE TRANSAKSI
@app.route('/transactions/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    if not is_logged_in():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    # Delete transaction items first
    cursor.execute("DELETE FROM transaction_item WHERE transaction_id = %s", (id,))
    # Then delete the transaction
    cursor.execute("DELETE FROM transaction WHERE id = %s", (id,))
    # Check if no transactions left, reset AUTO_INCREMENT to 1
    cursor.execute("SELECT COUNT(*) as count FROM transaction")
    if cursor.fetchone()['count'] == 0:
        cursor.execute("ALTER TABLE transaction AUTO_INCREMENT = 1")
    conn.commit()
    conn.close()

    flash('Transaksi berhasil dihapus', 'success')
    return redirect(url_for('transactions'))

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)
