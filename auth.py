"""Login, logout, registration and role-based access."""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from models import db, User, ROLE_ADMIN, ROLE_USER

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    """Decorator: only admin can access the route."""
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for(login_manager.login_view))
        if not current_user.is_admin():
            flash("Admin access required.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_view


@auth_bp.route("/guest-login", methods=["GET"])
def guest_login():
    """Log in as a non-admin guest user without entering credentials."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    guest = User.get_by_username("guest")
    if guest is None:
        guest = User(username="guest", email="guest@crm.local", role=ROLE_USER)
        guest.set_password("guest")
        db.session.add(guest)
        db.session.commit()

    login_user(guest)
    flash("You are now logged in as Guest.", "success")
    return redirect(url_for("index"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not all([username, email, password]):
            flash("All fields are required.", "error")
            return render_template("register.html")
        if password != password2:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
            return render_template("register.html")
        if User.get_by_username(username):
            flash("Username already taken.", "error")
            return render_template("register.html")
        if User.get_by_email(email):
            flash("Email already registered.", "error")
            return render_template("register.html")

        role = ROLE_ADMIN if request.form.get("register_as_admin") else ROLE_USER
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Registration successful. You are logged in.", "success")
        return redirect(url_for("index"))
    return render_template("register.html")
