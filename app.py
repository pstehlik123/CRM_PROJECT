from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_session import Session
from models import db, Customer, Lead

from auth import auth_bp, login_manager, admin_required
from api import api_bp
from database import init_db
from flasgger import Swagger

# Haupt-Flask-App erstellen
app = Flask(__name__)
# Secret-Key für Sessions und CSRF-Schutz
app.secret_key = "your-secret-key-change-this"

# -----------------------
# SQLAlchemy-Konfiguration
# -----------------------
# Verbindung zur SQLite-Datenbank, die von SQLAlchemy verwendet wird
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crm.db"
# Optionales Event-System von SQLAlchemy deaktivieren (etwas effizienter)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -----------------------
# Session-Konfiguration
# -----------------------
# Sessiondaten in der Datenbank speichern (nicht im Browser-Cookie)
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = db
app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
app.config["SESSION_PERMANENT"] = True

# SQLAlchemy mit dieser Flask-App verbinden
db.init_app(app)
# Flask-Session mit SQLAlchemy-Backend initialisieren
Session(app)

# LoginManager mit der App verbinden, damit current_user & Login funktioniert
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."

# -----------------------
# Blueprints & Swagger
# -----------------------
# Authentifizierungs-Blueprint und API-Blueprint registrieren
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)

# Flasgger initialisieren → generiert OpenAPI/Swagger-Doku und /apidocs UI
swagger = Swagger(app)

# Datenbanktabellen erzeugen und Beispieldaten einfügen (falls noch leer)
init_db(app)


# -----------------------
# Dashboard
# -----------------------
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    total_customers = Customer.query.count()
    total_leads = Lead.query.count()
    return render_template(
        'index.html',
        total_customers=total_customers,
        total_leads=total_leads
    )


# -----------------------
# Customers (HTML Views)
# -----------------------
@app.route('/customers')
@login_required  # nur eingeloggte Nutzer dürfen die Kundenliste sehen
def customers():
    return render_template(
        'customers.html',
        customers=Customer.get_all_customers()
    )


@app.route('/customers/add', methods=['GET', 'POST'])
@login_required  # Login erforderlich
@admin_required  # zusätzlich Admin-Rolle erforderlich
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        phone = request.form.get('phone')
        status = request.form.get('status', 'prospect')

        if not all([name, email, company, phone]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_customer'))

        Customer.add_customer(name, email, company, phone, status)
        flash(f'Customer {name} added successfully!', 'success')
        return redirect(url_for('customers'))

    return render_template('add_customer.html')


@app.route('/customers/<int:customer_id>')
@login_required  # Detailseite nur für eingeloggte Nutzer
def customer_detail(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    return render_template('customer_detail.html', customer=customer)


@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required  # Login erforderlich
@admin_required  # nur Admins dürfen Kundendaten ändern
def edit_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        Customer.update_customer(
            customer_id,
            request.form.get('name'),
            request.form.get('email'),
            request.form.get('company'),
            request.form.get('phone'),
            request.form.get('status')
        )
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))

    return render_template('edit_customer.html', customer=customer)


@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
@login_required  # Login erforderlich
@admin_required  # nur Admins dürfen Kunden löschen
def delete_customer(customer_id):
    Customer.delete_customer(customer_id)
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))


# -----------------------
# Leads (HTML Views)
# -----------------------
@app.route('/leads')
@login_required  # Lead-Liste nur für eingeloggte Nutzer
def leads():
    return render_template(
        'leads.html',
        leads=Lead.get_all_leads()
    )


@app.route('/leads/add', methods=['GET', 'POST'])
@login_required  # Login erforderlich
@admin_required  # nur Admins dürfen neue Leads anlegen
def add_lead():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        value = request.form.get('value')
        source = request.form.get('source')

        if not all([name, email, company, value, source]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_lead'))

        try:
            Lead.add_lead(name, email, company, float(value), source)
            flash(f'Lead {name} added successfully!', 'success')
        except ValueError:
            flash('Deal value must be a number!', 'error')

        return redirect(url_for('leads'))

    return render_template('add_lead.html')


@app.route('/leads/<int:lead_id>')
@login_required  # Detailansicht nur mit Login
def lead_detail(lead_id):
    lead = Lead.get_lead_by_id(lead_id)
    if not lead:
        flash('Lead not found!', 'error')
        return redirect(url_for('leads'))

    return render_template('lead_detail.html', lead=lead)


@app.route('/leads/<int:lead_id>/delete', methods=['POST'])
@login_required  # Login erforderlich
@admin_required  # nur Admins dürfen Leads löschen
def delete_lead(lead_id):
    Lead.delete_lead(lead_id)
    flash('Lead deleted successfully!', 'success')
    return redirect(url_for('leads'))


# -----------------------
# Error Handlers
# -----------------------
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)