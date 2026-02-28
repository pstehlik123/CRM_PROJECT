from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_session import Session
from models import db, Customer, Lead

from auth import auth_bp, login_manager, admin_required
from api import api_bp
from database import init_db
from flasgger import Swagger

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crm.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session in Datenbank speichern (nicht im Cookie)
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = db
app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
app.config["SESSION_PERMANENT"] = True

db.init_app(app)
Session(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."

app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)

swagger = Swagger(app)

init_db(app)


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    total_customers = Customer.query.count()
    total_leads = Lead.query.count()
    return render_template('index.html', total_customers=total_customers, total_leads=total_leads)


@app.route('/customers')
@login_required
def customers():
    return render_template('customers.html', customers=Customer.get_all_customers())

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
@admin_required
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
@login_required
def customer_detail(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))
    return render_template('customer_detail.html', customer=customer)

@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        Customer.update_customer(customer_id, request.form.get('name'), request.form.get('email'), 
                                request.form.get('company'), request.form.get('phone'), request.form.get('status'))
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))

    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_customer(customer_id):
    Customer.delete_customer(customer_id)
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/leads')
@login_required
def leads():
    return render_template('leads.html', leads=Lead.get_all_leads())

@app.route('/leads/add', methods=['GET', 'POST'])
@login_required
@admin_required
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
@login_required
def lead_detail(lead_id):
    lead = Lead.get_lead_by_id(lead_id)
    if not lead:
        flash('Lead not found!', 'error')
        return redirect(url_for('leads'))
    return render_template('lead_detail.html', lead=lead)

@app.route('/leads/<int:lead_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lead(lead_id):
    Lead.delete_lead(lead_id)
    flash('Lead deleted successfully!', 'success')
    return redirect(url_for('leads'))


@app.route('/api/customers', methods=['GET'])
def api_get_customers():
    """
    Get all customers
    ---
    tags:
      - Customers
    produces:
      - application/json
    responses:
      200:
        description: List of customers
    """
    customers = Customer.get_all_customers()
    data = [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "company": c.company,
            "phone": c.phone,
            "status": c.status,
        }
        for c in customers
    ]
    return jsonify(data)


@app.route('/api/customers', methods=['POST'])
def api_create_customer():
    """
    Create a new customer
    ---
    tags:
      - Customers
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
            company:
              type: string
            phone:
              type: string
            status:
              type: string
    responses:
      201:
        description: Created customer
      400:
        description: Invalid input data
      403:
        description: Admin access required for creating customers
    """
    if not current_user.is_authenticated or not current_user.is_admin():
        return jsonify({"message": "Admin access required."}), 403

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    email = payload.get("email")
    company = payload.get("company")
    phone = payload.get("phone")
    status = payload.get("status", "prospect")

    if not all([name, email, company, phone]):
        return jsonify({"message": "name, email, company and phone are required."}), 400

    customer = Customer.add_customer(name, email, company, phone, status)
    return (
        jsonify(
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "company": customer.company,
                "phone": customer.phone,
                "status": customer.status,
            }
        ),
        201,
    )


@app.route('/api/leads', methods=['GET'])
def api_get_leads():
    """
    Get all leads
    ---
    tags:
      - Leads
    produces:
      - application/json
    responses:
      200:
        description: List of leads
    """
    leads = Lead.get_all_leads()
    data = [
        {
            "id": l.id,
            "name": l.name,
            "email": l.email,
            "company": l.company,
            "value": l.value,
            "source": l.source,
            "status": l.status,
        }
        for l in leads
    ]
    return jsonify(data)


@app.route('/api/leads', methods=['POST'])
def api_create_lead():
    """
    Create a new lead
    ---
    tags:
      - Leads
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
            company:
              type: string
            value:
              type: number
            source:
              type: string
    responses:
      201:
        description: Created lead
      400:
        description: Invalid input data
      403:
        description: Admin access required for creating leads
    """
    if not current_user.is_authenticated or not current_user.is_admin():
        return jsonify({"message": "Admin access required."}), 403

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    email = payload.get("email")
    company = payload.get("company")
    value = payload.get("value")
    source = payload.get("source")

    if not all([name, email, company, value, source]):
        return jsonify({"message": "name, email, company, value and source are required."}), 400

    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return jsonify({"message": "value must be a number."}), 400

    lead = Lead.add_lead(name, email, company, value_float, source)
    return (
        jsonify(
            {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "company": lead.company,
                "value": lead.value,
                "source": lead.source,
                "status": lead.status,
            }
        ),
        201,
    )

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
