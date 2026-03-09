from models import db, Customer, Lead, User, ROLE_ADMIN, ROLE_USER


def init_db(app):
    """
    Initialisiert die Datenbank:
    - erstellt alle Tabellen über SQLAlchemy (db.create_all)
    - legt Demo-User und Demodaten an, falls die Tabellen leer sind
    """
    # app.app_context() stellt sicher, dass SQLAlchemy die aktuelle Flask-App kennt
    with app.app_context():
        # Erzeugt alle Tabellen, die in 'models.py' definiert sind
        db.create_all()

        # Falls noch kein User existiert: Admin- und Standard-User anlegen
        if User.query.count() == 0:
            admin = User(username="admin", email="admin@crm.local", role=ROLE_ADMIN)
            admin.set_password("admin")
            db.session.add(admin)

            user = User(username="user", email="user@crm.local", role=ROLE_USER)
            user.set_password("user")
            db.session.add(user)

            # Commit schreibt beide neuen Benutzer in die Datenbank
            db.session.commit()

        # Falls noch keine Kunden/Leads existieren: Beispiel-Datensätze anlegen
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

