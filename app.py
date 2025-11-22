from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import datetime


app = Flask(__name__)
app.secret_key = 'supersecretkey'

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Najmi@123",
    database="book_reselling_db"
)
cursor = db.cursor(dictionary=True)

# Create default admin
def create_admin():
    email = 'admin@gmail.com'
    password = generate_password_hash('admin123')
    name = 'Super Admin'
    phone = '9999999999'
    role = 'admin'

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (name, email, password, phone, role) VALUES (%s, %s, %s, %s, %s)",
                       (name, email, password, phone, role))
        db.commit()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']
        role = request.form['role'].lower()

        cursor.execute("INSERT INTO users (name, email, password, phone, role) VALUES (%s, %s, %s, %s, %s)",
                       (name, email, password, phone, role))
        db.commit()
        flash("Registered successfully!", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password_input):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'seller':
                return redirect(url_for('seller_dashboard'))
            elif user['role'] == 'buyer':
                return redirect(url_for('buyer_dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')



# Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') == 'admin':
        return render_template('admin_dashboard.html', name=session.get('name'))
    return redirect(url_for('login'))

@app.route('/admin/buyers')
def manage_buyers():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM users WHERE role='buyer'")
    buyers = cursor.fetchall()
    return render_template('manage_buyers.html', buyers=buyers)
@app.route('/admin/delete_seller/<int:seller_id>', methods=['GET', 'POST'])
def delete_seller(seller_id):
    if session.get('role') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    # Check if seller exists
    cursor.execute("SELECT * FROM users WHERE id=%s AND role='seller'", (seller_id,))
    seller = cursor.fetchone()

    if not seller:
        flash("Seller not found", "warning")
        return redirect(url_for('manage_sellers'))

    # Optional: Delete related books/orders if necessary

    cursor.execute("DELETE FROM users WHERE id=%s AND role='seller'", (seller_id,))
    db.commit()
    flash("Seller deleted successfully", "success")
    return redirect(url_for('manage_sellers'))


    # Handle form submission
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        cursor.execute("UPDATE users SET name=%s, email=%s, phone=%s WHERE id=%s AND role='buyer'",
                       (name, email, phone, buyer_id))
        db.commit()
        flash("Buyer updated successfully", "success")
        return redirect(url_for('manage_buyers'))

@app.route('/admin/delete_buyer/<int:buyer_id>')
def delete_buyer(buyer_id):
    if session.get('role') == 'admin':
        cursor.execute("DELETE FROM users WHERE id=%s AND role='buyer'", (buyer_id,))
        db.commit()
        flash("Buyer deleted", "info")
    return redirect(url_for('manage_buyers'))


@app.route('/admin/sellers')
def manage_sellers():
    cursor.execute("SELECT * FROM users WHERE role='seller'")
    sellers = cursor.fetchall()
    return render_template('manage_sellers.html', sellers=sellers)
@app.route('/admin/edit_seller/<int:seller_id>', methods=['GET', 'POST'])
def edit_seller(seller_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'GET':
        cursor.execute("SELECT * FROM users WHERE id=%s AND role='seller'", (seller_id,))
        seller = cursor.fetchone()
        if seller:
            return render_template('edit_seller.html', seller=seller)
        else:
            flash("Seller not found", "danger")
            return redirect(url_for('manage_sellers'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        cursor.execute("UPDATE users SET name=%s, email=%s WHERE id=%s AND role='seller'", (name, email, seller_id))
        db.commit()
        flash("Seller updated successfully", "success")
        return redirect(url_for('manage_sellers'))


@app.route('/admin/books')
def manage_book():
    cursor.execute("SELECT books.*, users.name AS seller_name FROM books JOIN users ON books.seller_id = users.id")
    books = cursor.fetchall()
    return render_template('manage_books.html', books=books)

@app.route('/admin/orders')
def manage_orders():
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    return render_template('manage_orders.html', orders=orders)

# View all shipping details (admin)
@app.route('/admin/shipping')
def manage_shipping():
    if session.get('role') == 'admin':
        cursor.execute("SELECT * FROM shipping")
        shipping = cursor.fetchall()
        return render_template('manage_shipping.html', shipping=shipping)
    return redirect(url_for('login'))


# Delete shipping detail (admin)
@app.route('/admin/shipping/delete/<int:shipping_id>', methods=['POST'])
def delete_shipping(shipping_id):
    if session.get('role') == 'admin':
        cursor.execute("DELETE FROM shipping WHERE id = %s", (shipping_id,))
        db.commit()
        flash("Shipping detail deleted successfully!", "success")
    return redirect(url_for('manage_shipping'))


# Edit shipping detail (admin)
@app.route('/admin/shipping/edit/<int:shipping_id>', methods=['GET', 'POST'])
def edit_shipping(shipping_id):
    if session.get('role') == 'admin':
        if request.method == 'POST':
            address = request.form['address']
            city = request.form['city']
            postal_code = request.form['postal_code']
            country = request.form['country']

            cursor.execute("""
                UPDATE shipping_details
                SET address=%s, city=%s, postal_code=%s, country=%s
                WHERE id=%s
            """, (address, city, postal_code, country, shipping_id))
            db.commit()
            flash("Shipping detail updated!", "success")
            return redirect(url_for('manage_shipping'))

        cursor.execute("SELECT * FROM shipping WHERE id = %s", (shipping_id,))
        shipping = cursor.fetchone()
        return render_template("edit_shipping.html", shipping=shipping)
    return redirect(url_for('login'))


# Buyer
@app.route('/buyer/dashboard')
def buyer_dashboard():
    if session.get('role') == 'buyer':
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        return render_template('buyer_dashboard.html', books=books, name=session.get('name'))
    return redirect(url_for('login'))
# ------------------ View Books ------------------
@app.route('/buyer/view_books')
def view_books():
    if session.get('role') != 'buyer':
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return render_template('view_books.html', books=books)

# ------------------ Search Book ------------------
@app.route('/buyer/search_book', methods=['GET'])
def search_book():
    if session.get('role') != 'buyer':
        return redirect(url_for('login'))

    query = request.args.get('query')
    results = []
    if query:
        cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s", (f'%{query}%', f'%{query}%'))
        results = cursor.fetchall()

    return render_template('search_book.html', results=results)

# ------------------ Place Order ------------------
@app.route('/buyer/place_order', methods=['GET', 'POST'])
def place_order():
    if session.get('role') != 'buyer':
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        book_id = request.form['book_id']
        quantity = request.form['quantity']
        buyer_id = session.get('user_id')

        # Insert the order
        cursor.execute(
            "INSERT INTO orders (book_id, buyer_id, quantity) VALUES (%s, %s, %s)",
            (book_id, buyer_id, quantity)
        )
        db.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('buyer_dashboard'))

    # Show available books to choose from
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.close()

    return render_template('place_order.html', books=books)

@app.route('/buyer/cancel_order', methods=['GET', 'POST'])
def cancel_order():
    if session.get('role') != 'buyer':
        return redirect(url_for('login'))

    if request.method == 'POST':
        order_id = request.form['order_id']
        cursor.execute("DELETE FROM orders WHERE id = %s AND buyer_id = %s", (order_id, session.get('user_id')))
        db.commit()
        flash('Order cancelled successfully.', 'info')
        return redirect(url_for('buyer_dashboard'))

    cursor.execute("SELECT * FROM orders WHERE buyer_id = %s", (session.get('user_id'),))
    orders = cursor.fetchall()
    return render_template('cancel_order.html', orders=orders)

# ------------------ Make Payment ------------------
@app.route('/buyer/make_payment', methods=['GET', 'POST'])
def make_payment():
    if session.get('role') != 'buyer':
        return redirect(url_for('login'))

    if request.method == 'POST':
        order_id = request.form.get('order_id')
        amount = request.form.get('amount')

        if order_id and amount:
            try:
                order_id = int(order_id)
                amount = float(amount)
                cursor.execute("INSERT INTO payments (order_id, amount) VALUES (%s, %s)", (order_id, amount))
                db.commit()
                flash('Payment successful!', 'success')
            except Exception as e:
                db.rollback()
                flash(f"Payment failed: {e}", 'danger')
        else:
            flash("Order ID and amount are required.", 'danger')

        return redirect(url_for('buyer_dashboard'))

    cursor.execute("""
        SELECT o.id AS order_id, b.title, b.price 
        FROM orders o 
        JOIN books b ON o.book_id = b.id 
        WHERE o.buyer_id = %s
    """, (session.get('user_id'),))
    orders = cursor.fetchall()
    return render_template('make_payment.html', orders=orders)

# Seller
@app.route('/seller/dashboard')
def seller_dashboard():
    if session.get('role') == 'seller':
        cursor.execute("SELECT * FROM books WHERE seller_id=%s", (session['user_id'],))
        books = cursor.fetchall()
        return render_template('seller_dashboard.html', books=books, name=session.get('name'))
    return redirect(url_for('login'))

@app.route('/seller/add_book', methods=['GET', 'POST'])
def add_book():
    if session.get('role') != 'seller':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        description = request.form['description']
        price = request.form['price']
        image_url = request.form['image_url']
        seller_id = session['user_id']
        cursor = db.cursor()
        cursor.execute(
    "INSERT INTO books (title, author, description, price, image_url, seller_id, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    (title, author, description, price, image_url, seller_id, seller_id)  # or another user_id if different
)

        db.commit()
        flash("Book added successfully", "success")
        return redirect(url_for('seller_dashboard'))

    return render_template('add_book.html')

@app.route('/buyer/give_feedback', methods=['GET', 'POST'])
def give_feedback():
    if session.get('role') != 'buyer':
        return redirect(url_for('login'))

    if request.method == 'POST':
        seller_id = request.form['seller_id']
        feedback = request.form['feedback']
        rating = request.form['rating']
        buyer_id = session['user_id']

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO feedback (user_id, seller_id, feedback, rating) VALUES (%s, %s, %s, %s)",
            (buyer_id, seller_id, feedback, rating)
        )

        db.commit()
        cursor.close()

        flash("Feedback submitted successfully", "success")
        return redirect(url_for('buyer_dashboard'))

    # Fetch sellers from users table (with role='seller')
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM users WHERE role = 'seller'")
    sellers = cursor.fetchall()
    cursor.close()

    return render_template('give_feedback.html', sellers=sellers)


@app.route('/seller/manage_books')
def manage_books():
    if session.get('role') == 'seller':
        cursor.execute("SELECT * FROM books WHERE seller_id=%s", (session['user_id'],))
        books = cursor.fetchall()
        return render_template('manage_books.html', books=books)
    return redirect(url_for('login'))

@app.route('/seller/orders')
def view_orders():
    if session.get('role') == 'seller':
        cursor.execute("""
            SELECT o.*, b.title AS book_title, u.name AS customer_name
            FROM orders o
            JOIN books b ON o.book_id = b.id
            JOIN users u ON o.buyer_id = u.id
            WHERE b.seller_id = %s
        """, (session['user_id'],))
        orders = cursor.fetchall()
        return render_template('view_orders.html', orders=orders)
@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        price = request.form['price']
        description = request.form['description']

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            UPDATE books 
            SET title = %s, author = %s, price = %s, description = %s 
            WHERE id = %s
        """, (title, author, price, description, book_id))
        db.commit()
        cursor.close()
        return redirect(url_for('manage_book'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    return render_template('edit_book.html', book=book)

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    return render_template('edit_book.html', book=book)


    # Fetch book for pre-fill
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    return render_template('edit_book.html', book=book)

    return redirect(url_for('login'))

@app.route('/delete_book/<int:book_id>', methods=['POST', 'GET'])
def delete_book(book_id):
    try:
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        db.commit()
        return redirect(url_for('manage_book'))
    except Exception as e:
        db.rollback()
        return f"An error occurred while deleting the book: {str(e)}"

@app.route('/seller/update_order/<int:order_id>', methods=['GET', 'POST'])
def update_order(order_id):
    if session.get('role') == 'seller':
        if request.method == 'POST':
            new_status = request.form['status']
            cursor.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
            db.commit()
            flash("Order status updated", "success")
            return redirect(url_for('view_orders'))

        cursor.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
        order = cursor.fetchone()
        return render_template('update_order.html', order=order)
    return redirect(url_for('login'))

@app.route('/seller/feedback')
def view_feedback():
    if session.get('role') == 'seller':
        cursor.execute("""
            SELECT f.feedback, f.rating, f.created_at, u.name AS buyer_username
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            WHERE f.seller_id = %s
            ORDER BY f.created_at DESC
        """, (session['user_id'],))
        feedback_list = cursor.fetchall()
        return render_template('view_feedback.html', feedback_list=feedback_list)

    return redirect(url_for('login'))
@app.route('/seller/add_shipping', methods=['GET', 'POST'])
def add_shipping():
    if session.get('role') != 'seller':
        return redirect(url_for('login'))

    seller_id = session.get('user_id')

    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        address = request.form['address']
        city = request.form['city']
        postal_code = request.form['postal_code']
        country = request.form['country']

        # Check if shipping details already exist for this seller
        cursor.execute("SELECT * FROM shipping WHERE seller_id = %s", (seller_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE shipping SET address=%s, city=%s, postal_code=%s, country=%s 
                WHERE seller_id=%s
            """, (address, city, postal_code, country, seller_id))
            flash("Shipping details updated successfully", "success")
        else:
            cursor.execute("""
                INSERT INTO shipping (seller_id, address, city, postal_code, country)
                VALUES (%s, %s, %s, %s, %s)
            """, (seller_id, address, city, postal_code, country))
            flash("Shipping details added successfully", "success")

        db.commit()
        cursor.close()
        return redirect(url_for('seller_dashboard'))

    cursor.execute("SELECT * FROM shipping WHERE seller_id = %s", (seller_id,))
    shipping = cursor.fetchone()
    cursor.close()

    return render_template('add_shipping.html', seller_id=seller_id, shipping=shipping)
@app.route('/seller/orders/edit/<int:order_id>')
def edit_order(order_id):
    if session.get('role') == 'seller':
        cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        if not order:
            return "Order not found", 404
        return render_template('update_order.html', order=order)
    return redirect(url_for('login'))
@app.route('/seller/orders/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if session.get('role') == 'seller':
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        db.commit()
        flash("Order deleted successfully!", "success")
        return redirect(url_for('view_orders'))
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for('home'))


# Run
if __name__ == '__main__':
    create_admin()
    app.run(debug=True)
