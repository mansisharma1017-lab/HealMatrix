from dotenv import load_dotenv
load_dotenv()

import json
import sqlite3
import os
import razorpay
from flask import send_from_directory
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_file, flash
) 
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- EMERGENCY CHECK SYSTEM ----------------

# ---------------- ADVANCED AI EMERGENCY ENGINE ----------------

from fuzzywuzzy import fuzz
from rapidfuzz import fuzz as rapid_fuzz

EMERGENCY_SYMPTOMS = {
    "chest pain": {
        "msg": "Chest pain may indicate heart or lung emergency.",
        "risk": 90
    },
    "severe chest pain": {
        "msg": "Possible heart attack or severe cardiac issue.",
        "risk": 100
    },
    "breathing problem": {
        "msg": "Breathing difficulty can be a respiratory emergency.",
        "risk": 85
    },
    "shortness of breath": {
        "msg": "Possible respiratory distress.",
        "risk": 90
    },
    "blood vomiting": {
        "msg": "Vomiting blood is a sign of internal bleeding.",
        "risk": 100
    },
    "unconscious": {
        "msg": "Loss of consciousness—very serious emergency!",
        "risk": 100
    },
    "high fever": {
        "msg": "High fever may signal infection or dengue.",
        "risk": 70
    },
    "severe headache": {
        "msg": "Could indicate migraine or meningitis.",
        "risk": 65
    },
    "stiff neck": {
        "msg": "Stiff neck with fever may indicate meningitis.",
        "risk": 85
    },
    "blue lips": {
        "msg": "Blue lips indicate dangerously low oxygen.",
        "risk": 95
    },
    "continuous vomiting": {
        "msg": "May cause dehydration and electrolyte imbalance.",
        "risk": 60
    }
}

def ai_emergency_check(text):
    text = text.lower()
    risk_level = 0
    triggered = []

    for symptom, info in EMERGENCY_SYMPTOMS.items():
        similarity = rapid_fuzz.partial_ratio(symptom, text)

        if similarity > 70:  # fuzzy matching threshold
            triggered.append(info["msg"])
            risk_level = max(risk_level, info["risk"])

    # CLASSIFY RISK LEVEL
    if risk_level >= 90:
        level = "HIGH"
    elif risk_level >= 60:
        level = "MEDIUM"
    else:
        level = "LOW"

    return triggered, level


# ---------------- DAILY HEALTH TIPS ----------------
HEALTH_TIPS = [
    "Drink at least 2–3 liters of water every day.",
    "Get 7–8 hours of sleep for better immunity.",
    "Wash your hands frequently to prevent infections.",
    "Avoid junk food and increase fruits in diet.",
    "Do 20 minutes of walking or exercise daily.",
    "Never ignore chest pain—visit a doctor immediately.",
    "If fever lasts more than 3 days, seek medical help.",
    "Eat more fiber-rich food to improve digestion.",
    "Limit sugar intake to protect your heart.",
    "Include more green vegetables in daily meals."
]

def get_daily_tip():
    """Return health tip based on today's date."""
    today = datetime.utcnow().day
    return HEALTH_TIPS[today % len(HEALTH_TIPS)]

# ------------------ OFFLINE AI ENGINE (UNLIMITED SYMPTOMS) ------------------

import nltk
from fuzzywuzzy import fuzz

# Download nltk data (only first time)
nltk.download('punkt')
nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

stop_words = set(stopwords.words("english"))

def clean_text(text):
    text = text.lower()
    words = word_tokenize(text)
    words = [w for w in words if w.isalpha() and w not in stop_words]
    return words


def match_symptoms(user_symptoms, disease_sym_list):
    score = 0
    for u in user_symptoms:
        for d in disease_sym_list:
            similarity = fuzz.partial_ratio(u, d)
            score = max(score, similarity)
    return score


def ai_predict(text_input, diseases):
    user_symptoms = clean_text(text_input)

    best_match = None
    best_score = -1

    for disease in diseases:
        disease_sym_list = [s.lower() for s in disease["symptoms"]]
        score = match_symptoms(user_symptoms, disease_sym_list)

        if score > best_score:
            best_score = score
            best_match = disease

    return best_match, best_score


# ----- Config -----
APP_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(APP_DIR, "appdata.db")
REPORTS_DIR = os.path.join(APP_DIR, "reports")
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

app = Flask(__name__)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


app.secret_key = os.getenv("SECRET_KEY")

# ----- Load diseases -----
with open(os.path.join(APP_DIR, "diseases.json"), "r", encoding="utf-8") as f:
    DISEASES = json.load(f)

# ----- Database helpers -----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            free_uses INTEGER DEFAULT 4,
            prediction_count INTEGER DEFAULT 0,
            plan TEXT DEFAULT 'FREE',
            plan_expiry TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT,
            symptoms TEXT,
            predicted TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            plan TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_db_conn():
    return sqlite3.connect(DB_PATH)

# init DB on startup
init_db()

# ----- Utility functions -----

def save_query(user_id, symptoms_list, predicted_name):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO queries (user_id, timestamp, symptoms, predicted) VALUES (?, ?, ?, ?)",
        (user_id, datetime.utcnow().isoformat(), ",".join(symptoms_list), predicted_name or "")
    )
    conn.commit()
    conn.close()

def generate_pdf_report(username, name, age, gender, symptoms, predicted):
    from reportlab.lib.colors import lightgrey, black
    from reportlab.lib.units import inch

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"report_{username}_{timestamp}.pdf"
    path = os.path.join(REPORTS_DIR, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # ======= WATERMARK =======
    # ======= WATERMARK (FIXED - FULLY VISIBLE) =======
    c.saveState()
    c.setFont("Helvetica-Bold", 45)
    c.setFillColorRGB(0.85, 0.85, 0.85)

# Move watermark safely to center
    c.translate(width / 2, height / 2)
    c.rotate(30)

# Draw name safely
    c.drawCentredString(0, 0, "MANSI  SHARMA")

    c.restoreState()


    # ======= HEADER =======
    c.setFillColorRGB(0.12, 0.35, 0.8)
    c.rect(0, height - 90, width, 90, fill=1)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 55, "Disease Prediction Medical Report")

    c.setFont("Helvetica", 11)
    c.drawCentredString(width/2, height - 75, "Developed by: Mansi Sharma")

    y = height - 130
    c.setFillColor(black)

    # ======= PATIENT INFO BOX =======
    c.setFillColor(lightgrey)
    c.roundRect(40, y-90, width-80, 80, 12, fill=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(55, y-25, "Patient Information")

    c.setFont("Helvetica", 11)
    c.drawString(55, y-50, f"Name: {name}")
    c.drawString(230, y-50, f"Age: {age}")
    c.drawString(350, y-50, f"Gender: {gender}")
    y -= 120

    # ======= SYMPTOMS =======
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Selected Symptoms")
    y -= 12
    c.line(50, y, width-50, y)
    y -= 20

    c.setFont("Helvetica", 11)
    for s in symptoms:
        c.drawString(70, y, f"• {s.capitalize()}")
        y -= 16

    y -= 20

    # ======= DISEASE RESULT BOX =======
    c.setFillColorRGB(0.9, 0.95, 1)
    c.roundRect(40, y-130, width-80, 120, 12, fill=1)
    c.setFillColor(black)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(55, y-30, "Predicted Disease Information")

    if isinstance(predicted, dict):
        c.setFont("Helvetica", 11)
        c.drawString(55, y-55, f"Disease Name: {predicted.get('name','')}")
        c.drawString(55, y-75, f"Severity: {predicted.get('severity','')}")
        c.drawString(55, y-95, f"Medicine: {predicted.get('medicine','')}")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(55, y-120, "Precautions:")

        c.setFont("Helvetica", 11)
        py = y - 138
        for line in wrap_text(predicted.get("precautions",""), 85):
            c.drawString(70, py, line)
            py -= 14
    else:
        c.drawString(55, y-70, "No disease prediction available.")

    # ======= FOOTER =======
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, 45,
        "This report is digitally generated | Not a substitute for professional medical advice")

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width-50, 25, "© 2025 Mansi Sharma")

    c.showPage()
    c.save()
    return path


def wrap_text(text, max_len):
    # simple wrapper
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_len:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def has_active_plan(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT plan, plan_expiry FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    plan, expiry = row

    if plan == "FREE":
        return False

    if expiry:
        expiry_date = datetime.fromisoformat(expiry)
        return datetime.utcnow() <= expiry_date

    return False



# ----- Auth routes -----
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        security_question = request.form.get("security_question", "").strip()
        security_answer = request.form.get("security_answer", "").lower().strip()

        if not username or not password or not security_question or not security_answer:
            flash("All fields are required", "error")
            return redirect(url_for("register"))

        pw_hash = generate_password_hash(password)
        sec_ans_hash = generate_password_hash(security_answer)

        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (username, password_hash, security_question, security_answer)
                VALUES (?, ?, ?, ?)
            """, (username, pw_hash, security_question, sec_ans_hash))
            conn.commit()
            conn.close()

            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, plan FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
            session["username"] = username
            session["plan"] = row[2]   # monthly / yearly / FREE

            flash("Logged in", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("index"))

# ----- Main app -----
@app.route("/", methods=["GET", "POST"])
def index():

    # FREE USE LIMIT LOGIC
    user_id = session.get("user_id")
    free_uses = 0

    if user_id:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT free_uses FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        conn.close()

        free_uses = row[0] if row else 0

    daily_tip = get_daily_tip()

    return render_template(
      "index.html",
      free_uses=free_uses,
      daily_tip=daily_tip
    )



# ----- Download PDF route -----
@app.route("/download_report")
def download_report():
    if "user_id" not in session:
        flash("You must be logged in to download reports", "error")
        return redirect(url_for("login"))
    # create a report for last saved query by this user
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT symptoms, predicted, timestamp FROM queries WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],))
    row = cur.fetchone()
    conn.close()
    if not row:
        flash("No history found to generate report", "error")
        return redirect(url_for("index"))
    symptoms_csv, predicted_name, timestamp = row
    symptoms = symptoms_csv.split(",") if symptoms_csv else []
    # find predicted object if exists
    predicted_obj = None
    for d in DISEASES:
        if d.get("name") == predicted_name:
            predicted_obj = d
            break
    # create PDF
    pdf_path = generate_pdf_report(
    session.get("username"),
    session.get("username"),
    "N/A",
    "N/A",
    symptoms,
    predicted_obj or predicted_name
)
    return send_file(pdf_path, as_attachment=True)



# ----- User history page -----
@app.route("/history")
def history():
    if "user_id" not in session:
        flash("Please login to see history", "error")
        return redirect(url_for("login"))

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT timestamp, symptoms, predicted, health_score 
        FROM queries 
        WHERE user_id = ? 
        ORDER BY timestamp ASC
    """, (session["user_id"],))

    rows = cur.fetchall()
    conn.close()

    history = []
    dates = []
    scores = []

    for r in rows:
        history.append({
            "timestamp": r[0],
            "symptoms": r[1].split(","),
            "predicted": r[2],
            "health_score": r[3]
        })

        dates.append(r[0][:10])  
        scores.append(r[3])

    return render_template(
        "history.html",
        history=history,
        dates=dates,
        scores=scores
    )

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Admin login successful", "success")
            return redirect("/admin")
        else:
            flash("Invalid Admin Credentials", "error")

    return render_template("admin_login.html")



@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users")
    user_rows = cur.fetchall()
    conn.close()

    users = [{"username": u[0], "email": "Hidden"} for u in user_rows]

    # Load diseases
    with open("diseases.json") as f:
        diseases = json.load(f)

    # Load total revenue
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM payments")
    total_revenue = cur.fetchone()[0] or 0
    conn.close()

    # RETURN (correct indent)
    return render_template(
        "admin.html",
        users=users,
        diseases=diseases,
        total_revenue=total_revenue
    )


@app.route("/add_disease", methods=["POST"])
def add_disease():
    if not session.get("admin_logged_in"):
        return "Unauthorized"

    new_disease = {
        "name": request.form["name"],
        "symptoms": request.form["symptoms"].split(","),
        "severity": request.form["severity"],
        "medicine": request.form["medicine"],
        "precautions": request.form["precautions"]
    }

    with open("diseases.json") as f:
        diseases = json.load(f)

    diseases.append(new_disease)

    with open("diseases.json", "w") as f:
        json.dump(diseases, f, indent=4)

    return redirect("/admin")

@app.route("/delete_disease/<name>")
def delete_disease(name):
    if not session.get("admin_logged_in"):
        return "Unauthorized"

    with open("diseases.json") as f:
        diseases = json.load(f)

    diseases = [d for d in diseases if d["name"] != name]

    with open("diseases.json", "w") as f:
        json.dump(diseases, f, indent=4)

    return redirect("/admin")

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin_login")

@app.route("/upgrade")
def upgrade():
    return render_template("upgrade.html")

client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY"), os.getenv("RAZORPAY_SECRET"))
)

@app.route("/create_order/<int:amount>")
def create_order(amount):
    order = client.order.create({
        'amount': amount,
        'currency': 'INR'
    })
    return order

@app.route("/payment_success")
def payment_success():
    user_id = session.get("user_id")
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
    UPDATE users 
    SET plan='PREMIUM', plan_expiry=NULL
    WHERE id=?
""", (user_id,))

    conn.commit()
    conn.close()

    flash("Payment successful! You are now Premium.", "success")
    return redirect(url_for("index"))

@app.route("/activate/<plan>")
def activate_plan(plan):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if plan == "monthly":
        amount = 99
        plan_name = "MONTHLY"
    elif plan == "yearly":
        amount = 299
        plan_name = "YEARLY"
    else:
        flash("Invalid plan", "error")
        return redirect("/upgrade")

    return render_template("manual_payment.html", amount=amount, plan=plan_name)

@app.route("/upload_payment", methods=["POST"])
def upload_payment():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    plan = request.form.get("plan")
    amount = request.form.get("amount")

    screenshot = request.files.get("screenshot")

    if not screenshot:
        flash("Please upload a payment screenshot!", "error")
        return redirect("/upgrade")

    # Save screenshot
    folder = "payment_screenshots"
    os.makedirs(folder, exist_ok=True)

    filename = f"{user_id}_{datetime.utcnow().timestamp()}.png"
    filepath = os.path.join(folder, filename)
    screenshot.save(filepath)

    # Create pending payment entry
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO payments (user_id, amount, plan, timestamp, status)
        VALUES (?, ?, ?, ?, 'PENDING')
    """, (user_id, amount, plan, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    # Notify admin via email (optional)
    flash("Your payment screenshot was submitted. Admin will verify within 24 hours.", "success")
    return redirect("/")


@app.route("/admin_payments")
def admin_payments():
    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT payments.id, users.username, payments.plan, payments.amount, payments.timestamp, payments.status
        FROM payments
        JOIN users ON payments.user_id = users.id
        ORDER BY payments.id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    payments = []
    for r in rows:
        payments.append({
            "id": r[0],
            "username": r[1],
            "plan": r[2],
            "amount": r[3],
            "timestamp": r[4],
            "status": r[5]
        })

    return render_template("admin_payments.html", payments=payments)

@app.route("/admin/approve_payment/<int:payment_id>")
def approve_payment(payment_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db_conn()
    cur = conn.cursor()

    # Get payment details
    cur.execute("SELECT user_id, plan FROM payments WHERE id=?", (payment_id,))
    row = cur.fetchone()

    if not row:
        flash("Payment not found", "error")
        return redirect("/admin_payments")

    user_id, plan = row

    # Determine plan expiry
    if plan == "MONTHLY":
        expiry = datetime.utcnow() + timedelta(days=30)
    else:
        expiry = datetime.utcnow() + timedelta(days=365)

    # Upgrade user
    cur.execute("UPDATE users SET plan=?, plan_expiry=? WHERE id=?", (plan, expiry.isoformat(), user_id))

    # Update payment status
    cur.execute("UPDATE payments SET status='APPROVED' WHERE id=?", (payment_id,))

    conn.commit()
    conn.close()

    flash("Payment approved. User upgraded!", "success")
    return redirect("/admin_payments")

@app.route("/admin/reject_payment/<int:payment_id>")
def reject_payment(payment_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE payments SET status='REJECTED' WHERE id=?", (payment_id,))
    conn.commit()
    conn.close()

    flash("Payment rejected.", "info")
    return redirect("/admin_payments")


@app.get("/privacy")
def privacy():
    return render_template("privacy.html")

@app.get("/terms")
def terms():
    return render_template("terms.html")

@app.get("/contact")
def contact():
    return render_template("contact.html")

@app.route("/predict", methods=["POST"])
def predict():
    if "user_id" not in session:
        flash("Please login to continue", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_conn()
    cur = conn.cursor()

    # Get free uses
    cur.execute("SELECT free_uses FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    free_left = row[0] if row else 0

    # Check premium
    is_paid = has_active_plan(user_id)

    # If user has no free predictions and no premium plan
    if free_left <= 0 and not is_paid:
        flash("Your free predictions are over. Please upgrade your plan.", "error")
        return redirect(url_for("upgrade"))

    text_input = request.form["symptoms"]
    warnings, emergency_level = ai_emergency_check(text_input)

    # LOAD diseases
    with open("diseases.json", "r") as f:
        diseases = json.load(f)

    disease, score = ai_predict(text_input, diseases)

    probability = round(score / 100 * 80 + 20)
    health_score = 100 - probability

    # Save query
    cur.execute("""
        INSERT INTO queries (user_id, timestamp, symptoms, predicted, health_score)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, datetime.utcnow().isoformat(), text_input, disease["name"], health_score))

    # Decrease free uses if not premium
    if not is_paid:
        cur.execute("UPDATE users SET free_uses = free_uses - 1 WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    result = {
        "name": disease["name"],
        "probability": probability,
        "severity": disease["severity"],
        "medicine": disease["medicine"],
        "precautions": disease["precautions"],
        "health_score": health_score
    }

    return render_template(
        "result.html",
        result=result,
        user_text=text_input,
        warnings=warnings,
        emergency_level=emergency_level
    )

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username")

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT security_question FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()

        if not row:
            flash("Username not found", "error")
            return redirect("/forgot_password")

        # store username temporarily
        session["reset_username"] = username
        return render_template("forgot_question.html", question=row[0])

    return render_template("forgot_username.html")

@app.route("/verify_answer", methods=["POST"])
def verify_answer():
    answer = request.form.get("answer").lower().strip()

    username = session.get("reset_username")

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT security_answer FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if row and row[0] == answer:
        return render_template("reset_password.html")

    flash("Incorrect answer!", "error")
    return redirect("/forgot_password")

@app.route("/reset_password", methods=["POST"])
def reset_password():
    new_pass = request.form.get("password")
    username = session.get("reset_username")

    pw_hash = generate_password_hash(new_pass)

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash=? WHERE username=?", (pw_hash, username))
    conn.commit()
    conn.close()

    session.pop("reset_username", None)

    flash("Password reset successful! Please login.", "success")
    return redirect("/login")

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service_worker.js')
def service_worker():
    return send_from_directory('static', 'service_worker.js')


if __name__ == "__main__":
    app.run()
