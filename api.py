from flask import Blueprint, jsonify, request
from flask_login import current_user

from models import Customer, Lead


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/customers", methods=["GET"])
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


@api_bp.route("/customers", methods=["POST"])
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


@api_bp.route("/leads", methods=["GET"])
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


@api_bp.route("/leads", methods=["POST"])
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

