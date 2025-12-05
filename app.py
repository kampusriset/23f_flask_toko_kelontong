print("=== Mulai menjalankan aplikasi Flask ===")
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev-secret-key-change-me'

db = SQLAlchemy(app)

# Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200), nullable=False)
    harga = db.Column(db.Float, nullable=False, default=0.0)
    stok = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(120), nullable=False)
    telepon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    total = db.Column(db.Float, nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)

class TransactionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    product_name = db.Column(db.String(200))
    harga = db.Column(db.Float)
    qty = db.Column(db.Integer)
    subtotal = db.Column(db.Float)

# create db and sample data
@app.before_first_request
def create_tables():
    db.create_all()
    if Product.query.count() == 0:
        p1 = Product(nama='Indomie Goreng', harga=3500, stok=50)
        p2 = Product(nama='Gula Pasir 1kg', harga=14000, stok=20)
        p3 = Product(nama='Kopi Kapal Api', harga=2000, stok=30)
        db.session.add_all([p1,p2,p3])
    if Customer.query.count() == 0:
        c1 = Customer(nama='Salvano')
        c2 = Customer(nama='Panji')
        db.session.add_all([c1,c2])
    db.session.commit()

# Simple auth
def is_logged_in():
    return session.get('logged_in')

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
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    total_transactions = Transaction.query.count()
    today = date.today()
    omzet_today = db.session.query(db.func.coalesce(db.func.sum(Transaction.total),0)).filter(db.func.date(Transaction.tanggal)==today).scalar()
    return render_template('dashboard.html', total_products=total_products,
                           total_customers=total_customers,
                           total_transactions=total_transactions,
                           omzet_today=omzet_today)

# Products CRUD
@app.route('/products')
def products():
    if not is_logged_in():
        return redirect(url_for('login'))
    q = request.args.get('q','')
    if q:
        items = Product.query.filter(Product.nama.ilike(f'%{q}%')).all()
    else:
        items = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('products.html', products=items, q=q)

@app.route('/products/add', methods=['GET','POST'])
def add_product():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        nama = request.form['nama'].strip()
        harga = float(request.form['harga'])
        stok = int(request.form['stok'])
        p = Product(nama=nama, harga=harga, stok=stok)
        db.session.add(p)
        db.session.commit()
        flash('Produk berhasil ditambahkan', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Tambah')

@app.route('/products/edit/<int:id>', methods=['GET','POST'])
def edit_product(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    p = Product.query.get_or_404(id)
    if request.method == 'POST':
        p.nama = request.form['nama'].strip()
        p.harga = float(request.form['harga'])
        p.ststok = int(request.form['stok'])
        db.session.commit()
        flash('Produk berhasil diperbarui', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Edit', product=p)

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    p = Product.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Produk dihapus', 'success')
    return redirect(url_for('products'))

# Customers CRUD
@app.route('/customers')
def customers():
    if not is_logged_in():
        return redirect(url_for('login'))
    items = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('customers.html', customers=items)

@app.route('/customers/add', methods=['GET','POST'])
def add_customer():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        nama = request.form['nama'].strip()
        telepon = request.form.get('telepon','').strip()
        c = Customer(nama=nama, telepon=telepon)
        db.session.add(c)
        db.session.commit()
        flash('Pelanggan ditambahkan', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', action='Tambah')

@app.route('/customers/edit/<int:id>', methods=['GET','POST'])
def edit_customer(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    c = Customer.query.get_or_404(id)
    if request.method == 'POST':
        c.nama = request.form['nama'].strip()
        c.telepon = request.form.get('telepon','').strip()
        db.session.commit()
        flash('Pelanggan diperbarui', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', action='Edit', customer=c)

@app.route('/customers/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    c = Customer.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash('Pelanggan dihapus', 'success')
    return redirect(url_for('customers'))

# Simple POS
@app.route('/pos')
def pos():
    if not is_logged_in():
        return redirect(url_for('login'))
    products = Product.query.order_by(Product.nama).all()
    cart = session.get('cart', {})
    return render_template('pos.html', products=products, cart=cart)

@app.route('/pos/add', methods=['POST'])
def pos_add():
    if not is_logged_in():
        return redirect(url_for('login'))
    pid = int(request.form['product_id'])
    qty = int(request.form.get('qty',1))
    product = Product.query.get_or_404(pid)
    cart = session.get('cart', {})
    if str(pid) in cart:
        cart[str(pid)]['qty'] += qty
    else:
        cart[str(pid)] = {'nama': product.nama, 'harga': product.harga, 'qty': qty}
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

    # 🔥 NAMA PELANGGAN WAJIB DIISI
    customer_name = request.form.get('customer_name', '').strip()
    if not customer_name:
        flash('Nama pelanggan wajib diisi!', 'danger')
        return redirect(url_for('pos'))

    total = 0
    for pid, item in cart.items():
        total += item['harga'] * item['qty']

    tr = Transaction(customer_name=customer_name, total=total)
    db.session.add(tr)
    db.session.commit()

    # tambah item
    for pid, item in cart.items():
        prod = Product.query.get(int(pid))
        qty = int(item['qty'])
        subtotal = item['harga'] * qty
        ti = TransactionItem(transaction_id=tr.id, product_name=prod.nama, harga=prod.harga, qty=qty, subtotal=subtotal)
        db.session.add(ti)
        prod.stok = max(0, prod.stok - qty)
    db.session.commit()

    session['cart'] = {}
    flash('Transaksi berhasil disimpan', 'success')
    return redirect(url_for('transactions'))

# transactions
@app.route('/transactions')
def transactions():
    if not is_logged_in():
        return redirect(url_for('login'))
    trans = Transaction.query.order_by(Transaction.tanggal.desc()).all()
    return render_template('transactions.html', transactions=trans)

@app.route('/transactions/<int:id>')
def transaction_detail(id):
    if not is_logged_in():
        return redirect(url_for('login'))
    tr = Transaction.query.get_or_404(id)
    items = TransactionItem.query.filter_by(transaction_id=id).all()
    return render_template('transaction_detail.html', tr=tr, items=items)

# 🔥 ROUTE DELETE TRANSAKSI
@app.route('/transactions/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    if not is_logged_in():
        return redirect(url_for('login'))

    tr = Transaction.query.get_or_404(id)
    items = TransactionItem.query.filter_by(transaction_id=id).all()
    for item in items:
        db.session.delete(item)

    db.session.delete(tr)
    db.session.commit()

    flash('Transaksi berhasil dihapus', 'success')
    return redirect(url_for('transactions'))

if __name__ == '__main__':
    app.run(debug=True)
