from flask import (
    Blueprint,
    request,
    redirect,
    render_template,
    session,
    url_for,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

from extensions import db, mail
from models.user import User

from datetime import datetime


# ==========================================================
# BLUEPRINT
# ==========================================================

auth_bp = Blueprint("auth", __name__)


# ==========================================================
# EMAIL VALIDATION
# ==========================================================

def is_valid_email(email):

    allowed_domains = [
        "apvtechnologies.com",
        "gmail.com"
    ]

    specific_allowed_emails = [
        "vishnuapv89@gmail.com"
    ]

    email = email.lower().strip()

    if email in specific_allowed_emails:
        return True

    try:
        domain = email.split("@")[1]
        return domain in allowed_domains
    except IndexError:
        return False


# ==========================================================
# SEND VERIFICATION EMAIL
# ==========================================================

def send_verification_email(email):

    msg = Message(
        subject="Welcome to APV Monitor Pro",
        recipients=[email]
    )

    msg.body = f"""
Welcome to APV Monitor Pro 🚀

Your account has been created successfully.

You can now login to your dashboard.

Login URL:
http://localhost:5004/auth/login

Thanks,
APV Monitor Pro
"""

    mail.send(msg)


# ==========================================================
# SIGNUP
# ==========================================================

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "GET":
        return render_template("auth/signup.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    # ================= VALIDATIONS =================

    if not email or not password or not confirm_password:
        return render_template(
            "auth/signup.html",
            error="All fields are required"
        )

    if not is_valid_email(email):
        return render_template(
            "auth/signup.html",
            error="Only @apvtechnologies.com and @gmail.com emails allowed"
        )

    if len(password) < 8:
        return render_template(
            "auth/signup.html",
            error="Password must be at least 8 characters"
        )

    if password != confirm_password:
        return render_template(
            "auth/signup.html",
            error="Passwords do not match"
        )

    if User.query.filter_by(email=email).first():
        return render_template(
            "auth/signup.html",
            error="User already exists"
        )

    # ================= CREATE USER =================

    hashed_password = generate_password_hash(password)

    new_user = User(
        email=email,
        password=hashed_password,
        role="viewer",
        is_verified=True
    )

    db.session.add(new_user)
    db.session.commit()

    # ================= SEND EMAIL =================

    try:
        send_verification_email(email)
    except Exception as e:
        print("Email sending failed:", str(e))

    # ================= SHOW CHECK EMAIL PAGE =================

    return render_template(
        "auth/check_email.html",
        email=email
    )


# ==========================================================
# LOGIN
# ==========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("auth/login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template(
            "auth/login.html",
            error="Please enter email and password"
        )

    user = User.query.filter_by(email=email).first()

    if not user:
        return render_template(
            "auth/login.html",
            error="User not found"
        )

    if not check_password_hash(user.password, password):
        return render_template(
            "auth/login.html",
            error="Invalid credentials"
        )

    if not user.is_verified:
        return render_template(
            "auth/login.html",
            error="Email not verified"
        )

    session.clear()

    session["user_id"] = user.id
    session["email"] = user.email
    session["role"] = user.role
    session["logged_in"] = True
    session["login_at"] = datetime.utcnow().isoformat()

    session.permanent = True

    return redirect(url_for("dashboard"))


# ==========================================================
# LOGOUT
# ==========================================================

@auth_bp.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "info")

    return redirect(url_for("home"))