import sqlite3, os, uuid, json, hashlib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session as flask_session, send_from_directory, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'lost.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_ar TEXT NOT NULL,
                description TEXT NOT NULL,
                desc_ar TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                file_url TEXT DEFAULT '',
                image TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT DEFAULT 'iban',
                transaction_id TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                rating INTEGER CHECK(rating>=1 AND rating<=5),
                comment TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        ''')

class User(UserMixin):
    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.email = row['email']
        self.created_at = row['created_at']

@login_manager.user_loader
def load_user(user_id):
    with get_db() as db:
        row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return User(row) if row else None

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.username != 'root':
            flash('Admin only!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    with get_db() as db:
        reviews = db.execute('''
            SELECT r.rating, r.comment, r.created_at, u.username, p.name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN products p ON r.product_id = p.id
            WHERE r.comment != ''
            ORDER BY r.created_at DESC LIMIT 20
        ''').fetchall()
    return render_template('index.html', reviews=reviews)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not email or not password:
            flash('Fill all fields / املأ جميع الحقول', 'error')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords mismatch / كلمة المرور غير متطابقة', 'error')
            return render_template('register.html')
        if len(username) < 3:
            flash('Username too short / اسم المستخدم قصير', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password too short / كلمة المرور قصيرة', 'error')
            return render_template('register.html')

        try:
            with get_db() as db:
                db.execute('INSERT INTO users (username, email, password) VALUES (?,?,?)',
                          (username, email, generate_password_hash(password)))
            flash('Registered! You can login now / تم التسجيل! سجل الدخول الآن', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email exists / الاسم أو البريد موجود', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        with get_db() as db:
            row = db.execute('SELECT * FROM users WHERE username = ? OR email = ?',
                           (username, username)).fetchone()
        if row and check_password_hash(row['password'], password):
            login_user(User(row))
            flask_session.permanent = True
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid credentials / معلومات غير صحيحة', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/shop')
def shop():
    category = request.args.get('category', '')
    with get_db() as db:
        if category:
            products = db.execute('SELECT * FROM products WHERE category = ?', (category,)).fetchall()
        else:
            products = db.execute('SELECT * FROM products').fetchall()
        categories = db.execute('SELECT DISTINCT category FROM products').fetchall()
    return render_template('shop.html', products=products, categories=[c['category'] for c in categories])

@app.route('/product/<int:pid>')
def product(pid):
    with get_db() as db:
        product = db.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('shop'))
        reviews = db.execute('''
            SELECT r.*, u.username FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = ? ORDER BY r.created_at DESC
        ''', (pid,)).fetchall()
    return render_template('product.html', product=product, reviews=reviews)

@app.route('/cart')
@login_required
def cart():
    with get_db() as db:
        items = db.execute('''
            SELECT c.id as cart_id, c.quantity, p.* FROM carts c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (current_user.id,)).fetchall()
        total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/add/<int:pid>')
@login_required
def cart_add(pid):
    with get_db() as db:
        existing = db.execute('SELECT * FROM carts WHERE user_id = ? AND product_id = ?',
                            (current_user.id, pid)).fetchone()
        if existing:
            db.execute('UPDATE carts SET quantity = quantity + 1 WHERE id = ?', (existing['id'],))
        else:
            db.execute('INSERT INTO carts (user_id, product_id) VALUES (?,?)', (current_user.id, pid))
    flash('Added to cart / أضيف للسلة', 'success')
    return redirect(request.referrer or url_for('shop'))

@app.route('/cart/remove/<int:cid>')
@login_required
def cart_remove(cid):
    with get_db() as db:
        db.execute('DELETE FROM carts WHERE id = ? AND user_id = ?', (cid, current_user.id))
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    with get_db() as db:
        items = db.execute('''
            SELECT c.id as cart_id, c.quantity, c.product_id, p.id as prod_id, p.* FROM carts c
            JOIN products p ON c.product_id = p.id WHERE c.user_id = ?
        ''', (current_user.id,)).fetchall()
        if not items:
            flash('Cart is empty / السلة فارغة', 'error')
            return redirect(url_for('shop'))
        total = sum(item['price'] * item['quantity'] for item in items)

    if request.method == 'POST':
        method = request.form.get('method', 'iban')
        with get_db() as db:
            status = 'paid' if (total == 0 or method in ('paypal', 'applepay')) else 'pending'
            db.execute(
                'INSERT INTO orders (user_id, total, payment_method, status) VALUES (?,?,?,?)',
                (current_user.id, total, method, status)
            )
            order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            for item in items:
                db.execute(
                    'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
                    (order_id, item['product_id'], item['quantity'], item['price'])
                )
            db.execute('DELETE FROM carts WHERE user_id = ?', (current_user.id,))
        flash('Order placed! / تم الطلب!', 'success')
        return redirect(url_for('orders'))

    return render_template('checkout.html', items=items, total=total)

@app.route('/orders')
@login_required
def orders():
    with get_db() as db:
        orders = db.execute('''
            SELECT o.*, GROUP_CONCAT(p.name || " x" || oi.quantity, ", ") as items_list,
                   GROUP_CONCAT(oi.product_id, ",") as product_ids
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE o.user_id = ?
            GROUP BY o.id ORDER BY o.created_at DESC
        ''', (current_user.id,)).fetchall()
    return render_template('orders.html', orders=orders)

@app.route('/review/add/<int:pid>', methods=['POST'])
@login_required
def review_add(pid):
    rating = request.form.get('rating', 5, type=int)
    comment = request.form.get('comment', '').strip()
    if rating < 1 or rating > 5:
        rating = 5
    with get_db() as db:
        existing = db.execute('SELECT * FROM reviews WHERE user_id = ? AND product_id = ?',
                            (current_user.id, pid)).fetchone()
        if existing:
            db.execute('UPDATE reviews SET rating = ?, comment = ? WHERE id = ?',
                      (rating, comment, existing['id']))
        else:
            db.execute('INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?,?,?,?)',
                      (current_user.id, pid, rating, comment))
    flash('Review submitted! / تم إرسال التقييم', 'success')
    return redirect(url_for('product', pid=pid))

@app.route('/dashboard')
@login_required
def dashboard():
    with get_db() as db:
        order_count = db.execute('SELECT COUNT(*) FROM orders WHERE user_id = ?',
                               (current_user.id,)).fetchone()[0]
        total_spent = db.execute('SELECT COALESCE(SUM(total),0) FROM orders WHERE user_id = ?',
                               (current_user.id,)).fetchone()[0]
        recent = db.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
                          (current_user.id,)).fetchall()
    return render_template('dashboard.html', order_count=order_count,
                          total_spent=total_spent, recent=recent)

@app.route('/admin')
@login_required
@admin_required
def admin():
    with get_db() as db:
        users = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        orders = db.execute('''
            SELECT o.*, u.username FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC LIMIT 20
        ''').fetchall()
        products = db.execute('SELECT * FROM products').fetchall()
    return render_template('admin.html', users=users, orders=orders, products=products)

@app.route('/admin/product/add', methods=['POST'])
@login_required
@admin_required
def admin_product_add():
    with get_db() as db:
        db.execute('''INSERT INTO products (name, name_ar, description, desc_ar, price, category)
            VALUES (?,?,?,?,?,?)''',
            (request.form['name'], request.form['name_ar'],
             request.form['description'], request.form['desc_ar'],
             float(request.form['price']), request.form['category']))
    flash('Product added!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/order/status/<int:oid>', methods=['POST'])
@login_required
@admin_required
def admin_order_status(oid):
    status = request.form.get('status', 'pending')
    with get_db() as db:
        db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, oid))
    flash('Order updated!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/product/delete/<int:pid>')
@login_required
@admin_required
def admin_product_delete(pid):
    with get_db() as db:
        db.execute('DELETE FROM products WHERE id = ?', (pid,))
    flash('Product deleted', 'success')
    return redirect(url_for('admin'))

@app.route('/download/<int:order_id>/<int:product_id>')
@login_required
def download_product(order_id, product_id):
    with get_db() as db:
        order = db.execute('SELECT * FROM orders WHERE id = ? AND user_id = ?',
                         (order_id, current_user.id)).fetchone()
        if not order or order['status'] not in ('paid', 'completed'):
            flash('Order not paid yet / الطلب لم يدفع بعد', 'error')
            return redirect(url_for('orders'))
        product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product or not product['file_url']:
            flash('No file available / لا يوجد ملف', 'error')
            return redirect(url_for('orders'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], product['file_url'], as_attachment=True)

@app.route('/admin/product/upload', methods=['POST'])
@login_required
@admin_required
def admin_product_upload():
    pid = request.form.get('pid', type=int)
    file = request.files.get('file')
    if not pid or not file:
        flash('Missing data', 'error')
        return redirect(url_for('admin'))
    filename = f'p{pid}_{secure_filename(file.filename)}'
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    with get_db() as db:
        db.execute('UPDATE products SET file_url = ? WHERE id = ?', (filename, pid))
    flash('File uploaded!', 'success')
    return redirect(url_for('admin'))

init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
