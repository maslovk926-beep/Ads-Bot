import sqlite3
import datetime

DB = "ads.db"


def connect():
    return sqlite3.connect(DB)


def init():

    con = connect()
    cur = con.cursor()

    # Пользователи
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT DEFAULT 'user',
        rating INTEGER DEFAULT 0,
        successful_ads INTEGER DEFAULT 0,
        created TEXT
    )
    """)

    # Объявления
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        title TEXT,
        description TEXT,
        price TEXT,
        city TEXT,
        contact TEXT,
        photo TEXT,
        status TEXT DEFAULT 'moderation',
        moderator TEXT,
        created TEXT
    )
    """)

    # Менеджеры
    cur.execute("""
    CREATE TABLE IF NOT EXISTS managers(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        added_by INTEGER,
        created TEXT
    )
    """)

    # Избранное
    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorites(
        user_id INTEGER,
        ad_id INTEGER,
        UNIQUE(user_id, ad_id)
    )
    """)

    # Лайки
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes(
        user_id INTEGER,
        ad_id INTEGER,
        UNIQUE(user_id, ad_id)
    )
    """)

    # Просмотры
    cur.execute("""
    CREATE TABLE IF NOT EXISTS views(
        user_id INTEGER,
        ad_id INTEGER,
        created TEXT
    )
    """)

    # Чёрный список
    cur.execute("""
    CREATE TABLE IF NOT EXISTS blacklist(
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        added_by INTEGER,
        created TEXT
    )
    """)

    # Предупреждения
    cur.execute("""
    CREATE TABLE IF NOT EXISTS warnings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        reason TEXT,
        manager TEXT,
        created TEXT
    )
    """)

    con.commit()
    con.close()# =========================
# USERS
# =========================

def add_user(user_id, username):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (id, username, created)
    VALUES(?,?,?)
    """,
    (
        user_id,
        username,
        str(datetime.datetime.now())
    ))

    con.commit()
    con.close()



def get_role(user_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT role FROM users WHERE id=?",
        (user_id,)
    )

    result = cur.fetchone()

    con.close()

    if result:
        return result[0]

    return "user"



def set_role(user_id, role):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET role=? WHERE id=?",
        (role, user_id)
    )

    con.commit()
    con.close()



# =========================
# MANAGERS
# =========================

def add_manager(user_id, username, owner_id):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO managers
    (user_id, username, added_by, created)
    VALUES(?,?,?,?)
    """,
    (
        user_id,
        username,
        owner_id,
        str(datetime.datetime.now())
    ))

    cur.execute(
        "UPDATE users SET role='manager' WHERE id=?",
        (user_id,)
    )

    con.commit()
    con.close()



def remove_manager(user_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "DELETE FROM managers WHERE user_id=?",
        (user_id,)
    )

    cur.execute(
        "UPDATE users SET role='user' WHERE id=?",
        (user_id,)
    )

    con.commit()
    con.close()



def get_managers():

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT user_id, username FROM managers"
    )

    data = cur.fetchall()

    con.close()

    return data



# =========================
# FAVORITES
# =========================

def add_favorite(user_id, ad_id):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO favorites
    VALUES(?,?)
    """,
    (
        user_id,
        ad_id
    ))

    con.commit()
    con.close()



def get_favorites(user_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT ad_id FROM favorites WHERE user_id=?",
        (user_id,)
    )

    result = cur.fetchall()

    con.close()

    return result



# =========================
# LIKES
# =========================

def add_like(user_id, ad_id):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO likes
    VALUES(?,?)
    """,
    (
        user_id,
        ad_id
    ))

    con.commit()
    con.close()



def count_likes(ad_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM likes WHERE ad_id=?",
        (ad_id,)
    )

    result = cur.fetchone()[0]

    con.close()

    return result# =========================
# VIEWS
# =========================

def add_view(user_id, ad_id):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO views
    VALUES(?,?,?)
    """,
    (
        user_id,
        ad_id,
        str(datetime.datetime.now())
    ))

    con.commit()
    con.close()



def count_views(ad_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM views WHERE ad_id=?",
        (ad_id,)
    )

    result = cur.fetchone()[0]

    con.close()

    return result



# =========================
# BLACKLIST
# =========================

def add_blacklist(user_id, reason, manager):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO blacklist
    VALUES(?,?,?,?)
    """,
    (
        user_id,
        reason,
        manager,
        str(datetime.datetime.now())
    ))

    con.commit()
    con.close()



def is_blacklisted(user_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT user_id FROM blacklist WHERE user_id=?",
        (user_id,)
    )

    result = cur.fetchone()

    con.close()

    return result is not None



# =========================
# WARNINGS
# =========================

def add_warning(user_id, reason, manager):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO warnings
    (user_id,reason,manager,created)
    VALUES(?,?,?,?)
    """,
    (
        user_id,
        reason,
        manager,
        str(datetime.datetime.now())
    ))

    con.commit()
    con.close()



def get_warnings(user_id):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    SELECT reason,manager,created
    FROM warnings
    WHERE user_id=?
    """,
    (user_id,))

    result = cur.fetchall()

    con.close()

    return result



# =========================
# REPORTS
# =========================

def create_report(user_id, ad_id, reason):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ad_id INTEGER,
        reason TEXT,
        status TEXT DEFAULT 'new',
        created TEXT
    )
    """)

    cur.execute("""
    INSERT INTO reports
    (user_id,ad_id,reason,created)
    VALUES(?,?,?,?)
    """,
    (
        user_id,
        ad_id,
        reason,
        str(datetime.datetime.now())
    ))

    con.commit()
    con.close()



# =========================
# LOGS
# =========================

def log(manager, action, ad_id=None):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manager TEXT,
        action TEXT,
        ad_id INTEGER,
        created TEXT
    )
    """)

    cur.execute("""
    INSERT INTO logs
    (manager,action,ad_id,created)
    VALUES(?,?,?,?)
    """,
    (
        manager,
        action,
        ad_id,
        str(datetime.datetime.now())
    ))

    con.commit()
    con.close()



# =========================
# STATISTICS
# =========================

def get_stats():

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )
    users = cur.fetchone()[0]


    cur.execute(
        "SELECT COUNT(*) FROM ads"
    )
    ads = cur.fetchone()[0]


    cur.execute(
        "SELECT COUNT(*) FROM ads WHERE status='published'"
    )
    published = cur.fetchone()[0]


    con.close()

    return {
        "users": users,
        "ads": ads,
        "published": published
    }
