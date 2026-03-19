from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import time

app = Flask(__name__)
app.secret_key = "KingHematXfCC43"

ADMIN = "0764246224"

# ---------------- DB ----------------
def db():
    return sqlite3.connect("db.db")

def init():
    conn = db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users(
        user_id TEXT,
        balance INTEGER,
        ref_code TEXT,
        referred INTEGER,
        ref_by TEXT,
        last_daily INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        link TEXT,
        reward INTEGER,
        done INTEGER DEFAULT 0
    )''')

    conn.commit()
    conn.close()

init()

# ---------------- Utils ----------------
def generate_ref():
    return str(random.randint(10000000000, 99999999999))

def get_user(user_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

# ---------------- Login ----------------
@app.route('/', methods=['GET','POST'])
def login():
    ref = request.args.get("ref")

    if request.method == "POST":
        user_id = request.form['user_id']
        ref_code = request.form.get("ref")

        user = get_user(user_id)

        if not user:
            code = generate_ref()
            conn = db()
            c = conn.cursor()

            c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                      (user_id, 50, code, 0, "", 0))  # 50 welcome

            conn.commit()
            conn.close()

        session['user'] = user_id

        # apply referral
        if ref_code:
            apply_ref(user_id, ref_code)

        return redirect("/dashboard")

    return render_template("login.html", ref=ref)

# ---------------- Referral ----------------
def apply_ref(user_id, ref_code):
    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()

    if user[3] == 1:
        return

    if user[2] == ref_code:
        return

    c.execute("SELECT * FROM users WHERE ref_code=?", (ref_code,))
    ref_user = c.fetchone()

    if not ref_user:
        return

    # reward
    c.execute("UPDATE users SET balance=balance+50 WHERE user_id=?", (user_id,))
    c.execute("UPDATE users SET balance=balance+50 WHERE ref_code=?", (ref_code,))
    c.execute("UPDATE users SET referred=1 WHERE user_id=?", (user_id,))

    conn.commit()
    conn.close()

# ---------------- Dashboard ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect("/")

    user_id = session['user']
    user = get_user(user_id)

    ref_link = f"http://localhost:5000/?ref={user[2]}"

    return render_template("dashboard.html",
                           balance=user[1],
                           ref_link=ref_link)

# ---------------- Daily Bonus ----------------
@app.route('/daily')
def daily():
    user_id = session['user']

    conn = db()
    c = conn.cursor()

    now = int(time.time())

    c.execute("SELECT last_daily FROM users WHERE user_id=?", (user_id,))
    last = c.fetchone()[0]

    if now - last > 86400:
        c.execute("UPDATE users SET balance=balance+5, last_daily=? WHERE user_id=?",
                  (now, user_id))
        conn.commit()

    conn.close()
    return redirect("/dashboard")

# ---------------- Order ----------------
@app.route('/order', methods=['POST'])
def order():
    user_id = session['user']
    link = request.form['link']
    type_ = request.form['type']

    price = 100

    conn = db()
    c = conn.cursor()

    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    bal = c.fetchone()[0]

    if bal < price:
        return "Balance not enough"

    c.execute("UPDATE users SET balance=balance-100 WHERE user_id=?", (user_id,))

    for i in range(20):
        c.execute("INSERT INTO tasks(type,link,reward) VALUES (?,?,?)",
                  (type_, link, 5))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- Run ----------------
if __name__ == '__main__':
    app.run(debug=True) 
