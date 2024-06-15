import sqlite3
from werkzeug.security import generate_password_hash


def init_db():
    with sqlite3.connect('books.db') as conn:
        cursor = conn.cursor()
        # Tabela książek
        cursor.execute('''CREATE TABLE IF NOT EXISTS books (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            author TEXT NOT NULL,
                            image TEXT,
                            publish_date TEXT,
                            isbn TEXT,
                            language TEXT,
                            publisher TEXT,
                            copies INTEGER NOT NULL,
                            tags TEXT)''')
        # Tabela wypożyczeń
        cursor.execute('''CREATE TABLE IF NOT EXISTS rentals (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            book_id INTEGER,
                            borrower_id INTEGER,
                            rental_date TEXT NOT NULL,
                            return_date TEXT)''')
        # Tabela użytkowników
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL,
                            password TEXT NOT NULL,
                            name TEXT,
                            email TEXT,
                            address TEXT,
                            phone TEXT,
                            id_card TEXT,
                            UNIQUE(username))''')
        # Tabela czytelników
        cursor.execute('''CREATE TABLE IF NOT EXISTS readers (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            surname TEXT NOT NULL,
                            address TEXT NOT NULL,
                            phone TEXT NOT NULL,
                            email TEXT NOT NULL,
                            id_card TEXT NOT NULL,
                            UNIQUE(id_card))''')

        # Dodanie domyślnego użytkownika
        hashed_password = generate_password_hash('admin')
        cursor.execute('INSERT OR IGNORE INTO users (username, password, name) VALUES (?, ?, ?)',
                       ('admin', hashed_password, 'Default Admin'))

        conn.commit()


if __name__ == "__main__":
    init_db()
