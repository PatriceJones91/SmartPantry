import sqlite3
import pandas as pd

DATABASE_NAME = "smartpantry.db"

def create_tables():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pantry (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            Ingredient TEXT,

            Quantity TEXT,

            Expiration TEXT,

            Category TEXT
        )
        """
    )

    conn.commit()

    conn.close()

def add_pantry_item(

    ingredient,
    quantity,
    expiration,
    category

):

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    existing = cursor.execute(

        """
        SELECT * FROM pantry
        WHERE LOWER(Ingredient) = LOWER(?)
        """,

        (ingredient,)
    ).fetchone()

    if existing:

        conn.close()

        return False

    cursor.execute(

        """
        INSERT INTO pantry (

            Ingredient,
            Quantity,
            Expiration,
            Category

        )

        VALUES (?, ?, ?, ?)
        """,

        (
            ingredient,
            quantity,
            expiration,
            category
        )
    )

    conn.commit()

    conn.close()

    return True

def get_pantry_items():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    df = pd.read_sql_query(
        "SELECT * FROM pantry",
        conn
    )

    conn.close()

    return df

def delete_pantry_items(ids):

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    for item_id in ids:

        cursor.execute(
            "DELETE FROM pantry WHERE id = ?",
            (int(item_id),)
        )

    conn.commit()

    conn.close()

def update_pantry_item(

    item_id,
    ingredient,
    quantity,
    expiration,
    category

):

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    cursor.execute(

        """
        UPDATE pantry

        SET

            Ingredient = ?,
            Quantity = ?,
            Expiration = ?,
            Category = ?

        WHERE id = ?
        """,

        (
            ingredient,
            quantity,
            expiration,
            category,
            item_id
        )
    )

    conn.commit()

    conn.close()