import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "sales_crm.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_db_connection()

    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                industry TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                deal_name TEXT NOT NULL,
                deal_value REAL NOT NULL DEFAULT 0 CHECK(deal_value >= 0),
                stage TEXT NOT NULL DEFAULT 'Lead'
                    CHECK(stage IN (
                        'Lead',
                        'Qualified',
                        'Proposal',
                        'Negotiation',
                        'Won',
                        'Lost'
                    )),
                expected_close_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
                    ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_deals_customer
            ON deals(customer_id);

            CREATE INDEX IF NOT EXISTS idx_deals_stage
            ON deals(stage);
        """)

        connection.commit()
        print("Sales CRM database initialised successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
