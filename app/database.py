import sqlite3
import hashlib
from datetime import datetime
import pandas as pd

DB_NAME = "smart_pantry.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_missing(cursor, table_name, column_name, column_definition):
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'participant',
            allergies TEXT,
            disliked_ingredients TEXT,
            preferred_meal_types TEXT,
            preferred_cuisine_types TEXT,
            created_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pantry_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT,
            quantity REAL DEFAULT 1,
            unit TEXT,
            container_type TEXT DEFAULT 'item',
            expiration_date TEXT,
            status TEXT DEFAULT 'available',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_recommendation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            meal_name TEXT NOT NULL,
            meal_type TEXT,
            score INTEGER,
            matched_ingredients TEXT,
            expiring_ingredients TEXT,
            used_recommendation TEXT DEFAULT 'No',
            feedback TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ingredient_usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pantry_item_id INTEGER,
            item_name TEXT,
            usage_type TEXT,
            quantity_used REAL DEFAULT 0,
            unit TEXT,
            remaining_quantity REAL,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (pantry_item_id) REFERENCES pantry_items(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            survey_type TEXT NOT NULL,
            pantry_awareness INTEGER,
            recommendation_usefulness INTEGER,
            ingredient_utilization INTEGER,
            ease_of_use INTEGER,
            current_method TEXT,
            comments TEXT,
            survey_responses TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    add_column_if_missing(cursor, "pantry_items", "container_type", "TEXT DEFAULT 'item'")
    add_column_if_missing(cursor, "ingredient_usage_logs", "quantity_used", "REAL DEFAULT 0")
    add_column_if_missing(cursor, "ingredient_usage_logs", "unit", "TEXT")
    add_column_if_missing(cursor, "ingredient_usage_logs", "remaining_quantity", "REAL")
    add_column_if_missing(cursor, "surveys", "survey_responses", "TEXT")
    add_column_if_missing(cursor, "users", "preferred_cuisine_types", "TEXT")

    conn.commit()
    conn.close()

    create_default_admin()


def create_default_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        cursor.execute(
            """
            INSERT INTO users (
                username, password_hash, role, allergies,
                disliked_ingredients, preferred_meal_types, preferred_cuisine_types, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "admin",
                hash_password("admin123"),
                "admin",
                "",
                "",
                "",
                "",
                datetime.now().isoformat(),
            ),
        )

    conn.commit()
    conn.close()


def register_user(username, password, role="participant"):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (
                username, password_hash, role, allergies,
                disliked_ingredients, preferred_meal_types, preferred_cuisine_types, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username.strip(),
                hash_password(password),
                role,
                "",
                "",
                "",
                "",
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "That username already exists."
    finally:
        conn.close()


def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, role
        FROM users
        WHERE username = ? AND password_hash = ?
        """,
        (username.strip(), hash_password(password)),
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return {
            "id": user[0],
            "username": user[1],
            "role": user[2],
        }

    return None


def update_user_profile(user_id, allergies, disliked_ingredients, preferred_meal_types, preferred_cuisine_types=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET allergies = ?, disliked_ingredients = ?, preferred_meal_types = ?, preferred_cuisine_types = ?
        WHERE id = ?
        """,
        (allergies, disliked_ingredients, preferred_meal_types, preferred_cuisine_types, user_id),
    )

    conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT allergies, disliked_ingredients, preferred_meal_types, preferred_cuisine_types
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "allergies": row[0] or "",
            "disliked_ingredients": row[1] or "",
            "preferred_meal_types": row[2] or "",
            "preferred_cuisine_types": row[3] or "",
        }

    return {
        "allergies": "",
        "disliked_ingredients": "",
        "preferred_meal_types": "",
        "preferred_cuisine_types": "",
    }


def add_pantry_item(user_id, item_name, category, quantity, unit, expiration_date, container_type="item"):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO pantry_items (
            user_id, item_name, category, quantity, unit,
            container_type, expiration_date, status, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            item_name.lower().strip(),
            category,
            float(quantity),
            unit,
            container_type,
            expiration_date,
            "available",
            now,
            now,
        ),
    )

    conn.commit()
    conn.close()


def get_user_pantry(user_id):
    conn = get_connection()

    query = """
        SELECT id, item_name, category, quantity, unit, container_type,
               expiration_date, status, created_at, updated_at
        FROM pantry_items
        WHERE user_id = ? AND status = 'available'
        ORDER BY expiration_date ASC
    """

    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()

    return df


def update_pantry_item_quantity(user_id, pantry_item_id, new_quantity):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE pantry_items
        SET quantity = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            float(new_quantity),
            datetime.now().isoformat(),
            pantry_item_id,
            user_id,
        ),
    )

    conn.commit()
    conn.close()


def update_pantry_item(
    user_id,
    pantry_item_id,
    item_name,
    category,
    quantity,
    unit,
    expiration_date,
    container_type="item",
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE pantry_items
        SET item_name = ?,
            category = ?,
            quantity = ?,
            unit = ?,
            container_type = ?,
            expiration_date = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ? AND status = 'available'
        """,
        (
            item_name.lower().strip(),
            category,
            float(quantity),
            unit,
            container_type,
            expiration_date,
            datetime.now().isoformat(),
            pantry_item_id,
            user_id,
        ),
    )

    conn.commit()
    conn.close()


def reduce_pantry_item_quantity(user_id, pantry_item_id, amount_used, usage_type, notes=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT item_name, quantity, unit
        FROM pantry_items
        WHERE id = ? AND user_id = ? AND status = 'available'
        """,
        (pantry_item_id, user_id),
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, "Pantry item was not found."

    item_name, current_quantity, unit = row
    current_quantity = float(current_quantity or 0)
    amount_used = float(amount_used or 0)

    if amount_used <= 0:
        conn.close()
        return False, "Amount used must be greater than zero."

    if amount_used > current_quantity:
        conn.close()
        return False, f"Not enough {item_name}. You only have {current_quantity:g} {unit} left."

    remaining_quantity = current_quantity - amount_used
    now = datetime.now().isoformat()

    if remaining_quantity <= 0:
        cursor.execute(
            """
            UPDATE pantry_items
            SET quantity = 0, status = 'used', updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (now, pantry_item_id, user_id),
        )
        message = (
            f"{amount_used:g} {unit} used from {item_name}. "
            f"The item is now empty and was removed from the active pantry."
        )
    else:
        cursor.execute(
            """
            UPDATE pantry_items
            SET quantity = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (remaining_quantity, now, pantry_item_id, user_id),
        )
        message = f"{amount_used:g} {unit} used from {item_name}. {remaining_quantity:g} {unit} remaining."

    cursor.execute(
        """
        INSERT INTO ingredient_usage_logs (
            user_id, pantry_item_id, item_name, usage_type,
            quantity_used, unit, remaining_quantity, notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            pantry_item_id,
            item_name,
            usage_type,
            amount_used,
            unit,
            max(remaining_quantity, 0),
            notes,
            now,
        ),
    )

    conn.commit()
    conn.close()

    return True, message


def mark_item_used(user_id, pantry_item_id, usage_type, notes=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT item_name, quantity, unit
        FROM pantry_items
        WHERE id = ? AND user_id = ?
        """,
        (pantry_item_id, user_id),
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    item_name, quantity, unit = row
    now = datetime.now().isoformat()

    cursor.execute(
        """
        UPDATE pantry_items
        SET status = 'used', quantity = 0, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (now, pantry_item_id, user_id),
    )

    cursor.execute(
        """
        INSERT INTO ingredient_usage_logs (
            user_id, pantry_item_id, item_name, usage_type,
            quantity_used, unit, remaining_quantity, notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            pantry_item_id,
            item_name,
            usage_type,
            float(quantity or 0),
            unit,
            0,
            notes,
            now,
        ),
    )

    conn.commit()
    conn.close()

    return True


def delete_pantry_item(user_id, pantry_item_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM pantry_items
        WHERE id = ? AND user_id = ?
        """,
        (pantry_item_id, user_id),
    )

    conn.commit()
    conn.close()


def save_recommendation_log(
    user_id,
    meal_name,
    meal_type,
    score,
    matched_ingredients,
    expiring_ingredients,
    feedback="",
    used_recommendation="No",
):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO meal_recommendation_logs (
            user_id, meal_name, meal_type, score,
            matched_ingredients, expiring_ingredients,
            used_recommendation, feedback, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            meal_name,
            meal_type,
            score,
            ", ".join(matched_ingredients),
            ", ".join(expiring_ingredients),
            used_recommendation,
            feedback,
            now,
            now,
        ),
    )

    conn.commit()
    conn.close()


def get_user_recommendation_logs(user_id):
    conn = get_connection()

    query = """
        SELECT id, meal_name, meal_type, score, matched_ingredients,
               expiring_ingredients, used_recommendation, feedback, created_at
        FROM meal_recommendation_logs
        WHERE user_id = ?
        ORDER BY created_at DESC
    """

    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()

    return df


def mark_recommendation_used(user_id, recommendation_id, feedback):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE meal_recommendation_logs
        SET used_recommendation = 'Yes', feedback = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            feedback,
            datetime.now().isoformat(),
            recommendation_id,
            user_id,
        ),
    )

    conn.commit()
    conn.close()


def save_survey(
    user_id,
    survey_type,
    pantry_awareness,
    recommendation_usefulness,
    ingredient_utilization,
    ease_of_use,
    current_method,
    comments,
    survey_responses="",
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO surveys (
            user_id, survey_type, pantry_awareness,
            recommendation_usefulness, ingredient_utilization,
            ease_of_use, current_method, comments, survey_responses, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            survey_type,
            pantry_awareness,
            recommendation_usefulness,
            ingredient_utilization,
            ease_of_use,
            current_method,
            comments,
            survey_responses,
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def has_completed_survey(user_id, survey_type):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM surveys
        WHERE user_id = ? AND survey_type = ?
        """,
        (user_id, survey_type),
    )

    row = cursor.fetchone()
    conn.close()

    return row is not None


def get_all_users():
    conn = get_connection()

    query = """
        SELECT id, username, role, created_at
        FROM users
        ORDER BY created_at DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def get_all_pantry_items():
    conn = get_connection()

    query = """
        SELECT u.username, p.item_name, p.category, p.quantity, p.unit,
               p.container_type, p.expiration_date, p.status,
               p.created_at, p.updated_at
        FROM pantry_items p
        JOIN users u ON p.user_id = u.id
        ORDER BY u.username, p.expiration_date
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def get_all_recommendation_logs():
    conn = get_connection()

    query = """
        SELECT u.username, r.meal_name, r.meal_type, r.score,
               r.matched_ingredients, r.expiring_ingredients,
               r.used_recommendation, r.feedback, r.created_at
        FROM meal_recommendation_logs r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def get_all_ingredient_usage():
    conn = get_connection()

    query = """
        SELECT u.username, i.item_name, i.usage_type, i.quantity_used,
               i.unit, i.remaining_quantity, i.notes, i.created_at
        FROM ingredient_usage_logs i
        JOIN users u ON i.user_id = u.id
        ORDER BY i.created_at DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def get_all_surveys():
    conn = get_connection()

    query = """
        SELECT u.username, s.survey_type, s.pantry_awareness,
               s.recommendation_usefulness, s.ingredient_utilization,
               s.ease_of_use, s.current_method, s.comments,
               s.survey_responses, s.created_at
        FROM surveys s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df