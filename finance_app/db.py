import sqlite3
import csv
from datetime import datetime
import shutil

DB_NAME = 'finance.db'

# --- Database initialization ---
def init_db():
    """Create tables if they do not exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category_id INTEGER,
            type TEXT CHECK(type IN ('income','expense')) NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
        """
    )
    conn.commit()
    conn.close()

# --- Category operations ---

def add_category(name: str):
    """Add a new category if it does not already exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def get_categories():
    """Return list of tuples (id, name) for all categories."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM categories ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return rows

# --- Transaction operations ---

def add_transaction(date: str, category_id: int, ttype: str, amount: float, description: str = ""):
    """Insert a new transaction."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO transactions(date, category_id, type, amount, description) VALUES (?, ?, ?, ?, ?)",
        (date, category_id, ttype, amount, description),
    )
    conn.commit()
    conn.close()


def get_transactions(month: int | None = None, year: int | None = None, category_id: int | None = None, ttype: str | None = None):
    """Retrieve transactions with optional filters."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = (
        "SELECT transactions.id, date, categories.name, type, amount, description "
        "FROM transactions LEFT JOIN categories ON transactions.category_id = categories.id WHERE 1=1"
    )
    params: list[str] = []
    if month:
        query += " AND strftime('%m', date)=?"
        params.append(f"{int(month):02d}")
    if year:
        query += " AND strftime('%Y', date)=?"
        params.append(str(year))
    if category_id:
        query += " AND category_id=?"
        params.append(str(category_id))
    if ttype:
        query += " AND type=?"
        params.append(ttype)
    query += " ORDER BY date DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def get_summary(month: int | None = None, year: int | None = None):
    """Return (total_income, total_expense, balance) for given period."""
    def _total(ttype: str):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        query = "SELECT SUM(amount) FROM transactions WHERE type=?"
        params: list[str] = [ttype]
        if month:
            query += " AND strftime('%m', date)=?"
            params.append(f"{int(month):02d}")
        if year:
            query += " AND strftime('%Y', date)=?"
            params.append(str(year))
        c.execute(query, params)
        value = c.fetchone()[0] or 0
        conn.close()
        return value

    income = _total("income")
    expense = _total("expense")
    return income, expense, income - expense

# --- Export functions ---

def export_csv(filepath: str, month: int | None = None, year: int | None = None):
    """Export filtered transactions to a CSV file."""
    rows = get_transactions(month, year)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Date", "Catégorie", "Type", "Montant", "Description"])
        for r in rows:
            writer.writerow(r)


def backup_db(target_path: str):
    """Create a backup copy of the database file."""
    shutil.copy(DB_NAME, target_path)

