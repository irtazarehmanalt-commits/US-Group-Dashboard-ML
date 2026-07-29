import os
import re
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

def get_engine():
    connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    return create_engine(connection_string)

def build_database():
    df = pd.read_csv('data/US_Group_ML_Dataset_2025_2026_refined_2.csv')
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    df['Dispatch_Date'] = pd.to_datetime(df['Dispatch_Date'])
    engine = get_engine()
    df.to_sql('orders', engine, if_exists='replace', index=False)
    print(f"Loaded {len(df)} rows into PostgreSQL 'orders' table.")

def create_chat_history_table():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                user_name TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        # covers databases where the table already existed before user_name was added
        conn.execute(text("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS user_name TEXT"))
        conn.commit()
    print("chat_history table ready.")

def create_users_table():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_approved BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        # covers databases where the table already existed before is_approved was added
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_approved BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.commit()
    print("users table ready.")

def seed_admin_account():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO users (name, email, password, role, is_approved)
            VALUES ('Admin', 'admin', 'admin123', 'admin', TRUE)
            ON CONFLICT (email) DO NOTHING
        """))
        conn.commit()
    print("admin account ready (email: admin / password: admin123).")

def create_scraped_products_table():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS scraped_products (
                id SERIAL PRIMARY KEY,
                brand TEXT,
                name TEXT,
                price NUMERIC,
                category TEXT,
                url TEXT,
                image_url TEXT,
                scraped_at TIMESTAMP DEFAULT now()
            )
        """))
        conn.commit()
    print("scraped_products table ready.")

# added: turn a scraped price string into a number for the NUMERIC price column.
# Grabs the FIRST number in the string, so messy labels like
# "Temporary Price is $59.99 Original Price was $84.95" store the current price
# (59.99), and "USD 1,299" / "£50.10" work too. Returns None (NULL) if no number
# is found, so a weird price label never blocks the rest of the insert.
def _parse_price(raw):
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return raw
    match = re.search(r'\d[\d,]*\.?\d*', str(raw))
    if not match:
        return None
    try:
        return float(match.group(0).replace(',', ''))
    except ValueError:
        return None

# added: insert scraped product rows into the scraped_products table. Reuses the
# existing SQLAlchemy get_engine() helper and parameterized text() inserts - same
# DB access pattern as every other table helper in this file (no ORM, no psycopg2).
# Called by the /market-data/save endpoint and by the scheduler.
def save_products(products: list) -> int:
    if not products:
        return 0
    engine = get_engine()
    with engine.connect() as conn:
        for p in products:
            conn.execute(
                text("""
                    INSERT INTO scraped_products (brand, name, price, category, url, image_url)
                    VALUES (:brand, :name, :price, :category, :url, :image_url)
                """),
                {
                    "brand": p.get("brand"),
                    "name": p.get("name"),
                    "price": _parse_price(p.get("price")),
                    "category": p.get("category"),
                    "url": p.get("url"),
                    "image_url": p.get("image_url"),
                },
            )
        conn.commit()
    print(f"Inserted {len(products)} rows into scraped_products.")
    return len(products)

if __name__ == '__main__':
    build_database()
    create_chat_history_table()
    create_users_table()
    create_scraped_products_table()
    seed_admin_account()