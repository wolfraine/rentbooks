from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    return conn


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(id=user['id'], username=user['username'], password=user['password'])
    return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Username already exists.')
            return redirect(url_for('register'))
        conn.close()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            login_user(User(id=user['id'], username=user['username'], password=user['password']))
            return redirect(url_for('index'))
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('index.html', books=books)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        image = request.form['image']
        publish_date = request.form['publish_date']
        isbn = request.form['isbn']
        language = request.form['language']
        publisher = request.form['publisher']
        copies = request.form['copies']
        tags = request.form['tags']

        conn = get_db_connection()
        conn.execute('''INSERT INTO books (title, author, image, publish_date, isbn, language, publisher, copies, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (title, author, image, publish_date, isbn, language, publisher, copies, tags))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_book.html')


@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        image = request.form['image']
        publish_date = request.form['publish_date']
        isbn = request.form['isbn']
        language = request.form['language']
        publisher = request.form['publisher']
        copies = request.form['copies']
        tags = request.form['tags']

        conn.execute(
            '''UPDATE books SET title = ?, author = ?, image = ?, publish_date = ?, isbn = ?, language = ?, publisher = ?, copies = ?, tags = ? WHERE id = ?''',
            (title, author, image, publish_date, isbn, language, publisher, copies, tags, book_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template('edit_book.html', book=book)


@app.route('/book/<int:book_id>', methods=['GET'])
@login_required
def book_details(book_id):
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    return render_template('book_details.html', book=book)


@app.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
@login_required
def borrow_book(book_id):
    if request.method == 'POST':
        borrower_id = request.form['reader_id']
        rental_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute('INSERT INTO rentals (book_id, borrower_id, rental_date) VALUES (?, ?, ?)',
                     (book_id, borrower_id, rental_date))
        conn.execute('UPDATE books SET copies = copies - 1 WHERE id = ?', (book_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    readers = conn.execute('SELECT * FROM readers').fetchall()
    conn.close()
    return render_template('borrow_book.html', book=book, readers=readers)


@app.route('/return/<int:book_id>', methods=['GET', 'POST'])
@login_required
def return_book(book_id):
    if request.method == 'POST':
        reader_id = request.form['reader_id']
        return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute('UPDATE rentals SET return_date = ? WHERE book_id = ? AND borrower_id = ? AND return_date IS NULL',
                     (return_date, book_id, reader_id))
        conn.execute('UPDATE books SET copies = copies + 1 WHERE id = ?', (book_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    readers = conn.execute('SELECT * FROM readers').fetchall()
    conn.close()
    return render_template('return_book.html', book=book, readers=readers)


@app.route('/readers', methods=['GET', 'POST'])
@login_required
def readers():
    conn = get_db_connection()
    readers = conn.execute('SELECT * FROM readers').fetchall()
    conn.close()
    return render_template('readers.html', readers=readers)


@app.route('/add_reader', methods=['GET', 'POST'])
@login_required
def add_reader():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        id_card = request.form['id_card']

        conn = get_db_connection()
        conn.execute('INSERT INTO readers (name, surname, address, phone, email, id_card) VALUES (?, ?, ?, ?, ?, ?)',
                     (name, surname, address, phone, email, id_card))
        conn.commit()
        conn.close()
        return redirect(url_for('readers'))
    return render_template('add_reader.html')


@app.route('/edit_reader/<int:reader_id>', methods=['GET', 'POST'])
@login_required
def edit_reader(reader_id):
    conn = get_db_connection()
    reader = conn.execute('SELECT * FROM readers WHERE id = ?', (reader_id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        id_card = request.form['id_card']

        conn.execute(
            '''UPDATE readers SET name = ?, surname = ?, address = ?, phone = ?, email = ?, id_card = ? WHERE id = ?''',
            (name, surname, address, phone, email, id_card, reader_id))
        conn.commit()
        conn.close()
        return redirect(url_for('readers'))
    conn.close()
    return render_template('edit_reader.html', reader=reader)


@app.route('/reader/<int:reader_id>', methods=['GET'])
@login_required
def reader_details(reader_id):
    conn = get_db_connection()
    reader = conn.execute('SELECT * FROM readers WHERE id = ?', (reader_id,)).fetchone()
    rentals = conn.execute('''SELECT books.id AS book_id, books.title, books.author, rentals.rental_date 
                              FROM rentals
                              JOIN books ON rentals.book_id = books.id
                              WHERE rentals.borrower_id = ? AND rentals.return_date IS NULL''',
                           (reader_id,)).fetchall()
    returns = conn.execute('''SELECT books.title, books.author, rentals.rental_date, rentals.return_date 
                              FROM rentals
                              JOIN books ON rentals.book_id = books.id
                              WHERE rentals.borrower_id = ? AND rentals.return_date IS NOT NULL''',
                           (reader_id,)).fetchall()
    conn.close()
    return render_template('reader_details.html', reader=reader, rentals=rentals, returns=returns)



@app.route('/delete_reader/<int:reader_id>', methods=['GET', 'POST'])
@login_required
def delete_reader(reader_id):
    conn = get_db_connection()
    rental = conn.execute('SELECT * FROM rentals WHERE borrower_id = ? AND return_date IS NULL',
                          (reader_id,)).fetchone()
    if rental:
        flash('Cannot delete reader with borrowed books.')
        conn.close()
        return redirect(url_for('readers'))
    conn.execute('DELETE FROM readers WHERE id = ?', (reader_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('readers'))


@app.route('/borrowed_books', methods=['GET'])
@login_required
def borrowed_books():
    conn = get_db_connection()
    borrowed_books = conn.execute('''SELECT books.title, books.author, readers.name, readers.surname, rentals.rental_date, rentals.return_date 
                                     FROM rentals
                                     JOIN books ON rentals.book_id = books.id
                                     JOIN readers ON rentals.borrower_id = readers.id
                                     WHERE rentals.return_date IS NULL''').fetchall()
    conn.close()
    return render_template('borrowed_books.html', borrowed_books=borrowed_books)


@app.route('/overdue_books', methods=['GET'])
@login_required
def overdue_books():
    conn = get_db_connection()
    overdue_books = conn.execute('''SELECT books.title, books.author, readers.name, readers.surname, rentals.rental_date, rentals.return_date 
                                    FROM rentals
                                    JOIN books ON rentals.book_id = books.id
                                    JOIN readers ON rentals.borrower_id = readers.id
                                    WHERE rentals.return_date IS NULL AND rentals.rental_date < DATE('now', '-30 days')''').fetchall()
    conn.close()
    return render_template('overdue_books.html', overdue_books=overdue_books)


@app.route('/search_books', methods=['GET', 'POST'])
@login_required
def search_books():
    if request.method == 'POST':
        search = request.form['search']
        conn = get_db_connection()
        books = conn.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR tags LIKE ?',
                             ('%' + search + '%', '%' + search + '%', '%' + search + '%')).fetchall()
        conn.close()
        return render_template('search_books.html', books=books)
    return render_template('search_books.html', books=[])


if __name__ == '__main__':
    app.run(debug=True)
