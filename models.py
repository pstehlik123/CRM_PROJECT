from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Zentrale SQLAlchemy-Instanz für die ganze Flask‑App
db = SQLAlchemy()

# Rollen-Konstanten für einfache Rollenprüfung (z.B. is_admin)
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'


class User(UserMixin, db.Model):
    """
    User-Modell:
    - erbt von SQLAlchemy 'db.Model' (ORM-Mapping auf Tabelle 'users')
    - erbt von 'UserMixin' (Flask-Login stellt damit is_authenticated, get_id, etc. bereit)
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Rolle steuert Berechtigungen (z.B. admin vs. normaler User)
    role = db.Column(db.String(20), default=ROLE_USER)

    def set_password(self, password):
        """Passwort sicher mit Werkzeug hashen und speichern."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Plain-Text-Passwort mit gespeichertem Hash vergleichen."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Hilfsmethode für Admin-Checks (wird von Decorators benutzt)."""
        return self.role == ROLE_ADMIN

    @classmethod
    def get_by_username(cls, username):
        """User anhand des eindeutigen Usernamens aus der DB laden."""
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_email(cls, email):
        """User anhand der eindeutigen E-Mail-Adresse aus der DB laden."""
        return cls.query.filter_by(email=email).first()


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), default='prospect')

    @classmethod
    def add_customer(cls, name, email, company, phone, status='prospect'):
        """Neuen Kunden anlegen und direkt in der Datenbank speichern."""
        customer = cls(name=name, email=email, company=company, phone=phone, status=status)
        db.session.add(customer)  # Objekt der aktuellen Session hinzufügen
        db.session.commit()       # Änderungen per SQL-Transaktion schreiben
        return customer

    @classmethod
    def get_all_customers(cls):
        """Alle Kunden nach ID sortiert zurückgeben."""
        return cls.query.order_by(cls.id).all()

    @classmethod
    def get_customer_by_id(cls, customer_id):
        """Einzelnen Kunden per Primärschlüssel-ID laden."""
        return cls.query.get(customer_id)

    @classmethod
    def update_customer(cls, customer_id, name, email, company, phone, status):
        customer = cls.get_customer_by_id(customer_id)
        if customer:
            customer.name = name
            customer.email = email
            customer.company = company
            customer.phone = phone
            customer.status = status
            # Änderungen am bestehenden Objekt werden durch Commit gespeichert
            db.session.commit()

    @classmethod
    def delete_customer(cls, customer_id):
        customer = cls.get_customer_by_id(customer_id)
        if customer:
            db.session.delete(customer)  # Objekt zum Löschen markieren
            db.session.commit()          # Löschung in der DB ausführen


class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(30), default='new')

    @classmethod
    def add_lead(cls, name, email, company, value, source):
        """Neuen Lead anlegen und sofort speichern."""
        lead = cls(name=name, email=email, company=company, value=value, source=source)
        db.session.add(lead)
        db.session.commit()
        return lead

    @classmethod
    def get_all_leads(cls):
        """Alle Leads nach ID sortiert zurückgeben."""
        return cls.query.order_by(cls.id).all()

    @classmethod
    def get_lead_by_id(cls, lead_id):
        """Einzelnen Lead per Primärschlüssel-ID laden."""
        return cls.query.get(lead_id)

    @classmethod
    def delete_lead(cls, lead_id):
        lead = cls.get_lead_by_id(lead_id)
        if lead:
            db.session.delete(lead)
            db.session.commit()
