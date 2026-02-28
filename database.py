from models import db, Customer, Lead, User, ROLE_ADMIN, ROLE_USER


def init_db(app):
    """Create tables and insert initial sample data if the database is empty."""
    with app.app_context():
        db.create_all()

        if User.query.count() == 0:
            admin = User(username="admin", email="admin@crm.local", role=ROLE_ADMIN)
            admin.set_password("admin")
            db.session.add(admin)

            user = User(username="user", email="user@crm.local", role=ROLE_USER)
            user.set_password("user")
            db.session.add(user)

            db.session.commit()

        if Customer.query.count() == 0 and Lead.query.count() == 0:
            Customer.add_customer(
                "John Doe", "john@example.com", "Acme Corp", "555-0001", "active"
            )
            Customer.add_customer(
                "Jane Smith",
                "jane@example.com",
                "Tech Solutions",
                "555-0002",
                "prospect",
            )
            Customer.add_customer(
                "Bob Wilson",
                "bob@example.com",
                "Global Industries",
                "555-0003",
                "inactive",
            )
            Lead.add_lead(
                "Alice Brown", "alice@example.com", "StartUp Inc", 50000, "Website"
            )
            Lead.add_lead(
                "Charlie Davis",
                "charlie@example.com",
                "Enterprise Ltd",
                100000,
                "Referral",
            )

