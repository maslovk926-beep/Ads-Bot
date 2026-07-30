import sqlite3

DB = "ads.db"


def connect():
    return sqlite3.connect(DB)


def init():

    con = connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

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
        moderator TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manager TEXT,
        action TEXT,
        ad_id INTEGER
    )
    """)

    con.commit()
    con.close()



def add_user(user_id, username):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO users(id, username) VALUES(?,?)",
        (user_id, username)
    )

    con.commit()
    con.close()



def set_role(user_id, role):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET role=? WHERE id=?",
        (role,user_id)
    )

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



def add_ad(data):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO ads
    (user_id,category,title,description,price,city,contact,photo)
    VALUES(?,?,?,?,?,?,?,?)
    """,
    (
        data["user_id"],
        data["category"],
        data["title"],
        data["description"],
        data["price"],
        data["city"],
        data["contact"],
        data["photo"]
    ))

    ad_id = cur.lastrowid

    con.commit()
    con.close()

    return ad_id



def get_ad(ad_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM ads WHERE id=?",
        (ad_id,)
    )

    ad = cur.fetchone()

    con.close()

    return ad



def approve(ad_id, moderator):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    UPDATE ads
    SET status='published', moderator=?
    WHERE id=? AND status='moderation'
    """,
    (moderator,ad_id))

    con.commit()

    changed = cur.rowcount

    con.close()

    return changed



def reject(ad_id, moderator):

    con = connect()
    cur = con.cursor()

    cur.execute("""
    UPDATE ads
    SET status='rejected', moderator=?
    WHERE id=?
    """,
    (moderator,ad_id))

    con.commit()
    con.close()



def log(manager, action, ad_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO logs(manager,action,ad_id) VALUES(?,?,?)",
        (manager,action,ad_id)
    )

    con.commit()
    con.close()
