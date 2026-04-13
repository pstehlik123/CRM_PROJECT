import csv
from io import StringIO, TextIOWrapper

from models import db, Customer, Lead


class CSVService:
    CUSTOMER_FIELDS = ["name", "email", "company", "phone", "status"]
    LEAD_FIELDS = ["name", "email", "company", "value", "source"]

    @staticmethod
    def export_customers():
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=CSVService.CUSTOMER_FIELDS)
        writer.writeheader()
        for customer in Customer.get_all_customers():
            writer.writerow(
                {
                    "name": customer.name,
                    "email": customer.email,
                    "company": customer.company,
                    "phone": customer.phone,
                    "status": customer.status,
                }
            )
        return output.getvalue()

    @staticmethod
    def export_leads():
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=CSVService.LEAD_FIELDS)
        writer.writeheader()
        for lead in Lead.get_all_leads():
            writer.writerow(
                {
                    "name": lead.name,
                    "email": lead.email,
                    "company": lead.company,
                    "value": lead.value,
                    "source": lead.source,
                }
            )
        return output.getvalue()

    @staticmethod
    def import_customers(file_storage):
        reader = CSVService._create_reader(file_storage)
        CSVService._validate_required_columns(reader.fieldnames, CSVService.CUSTOMER_FIELDS)

        imported_count = 0
        skipped_count = 0

        for row in reader:
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            company = (row.get("company") or "").strip()
            phone = (row.get("phone") or "").strip()
            status = (row.get("status") or "prospect").strip() or "prospect"

            if not all([name, email, company, phone]):
                skipped_count += 1
                continue

            db.session.add(
                Customer(
                    name=name,
                    email=email,
                    company=company,
                    phone=phone,
                    status=status,
                )
            )
            imported_count += 1

        db.session.commit()
        return imported_count, skipped_count

    @staticmethod
    def import_leads(file_storage):
        reader = CSVService._create_reader(file_storage)
        CSVService._validate_required_columns(reader.fieldnames, CSVService.LEAD_FIELDS)

        imported_count = 0
        skipped_count = 0

        for row in reader:
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            company = (row.get("company") or "").strip()
            source = (row.get("source") or "").strip()
            value_raw = (row.get("value") or "").strip()

            if not all([name, email, company, source, value_raw]):
                skipped_count += 1
                continue

            try:
                value = float(value_raw)
            except ValueError:
                skipped_count += 1
                continue

            db.session.add(
                Lead(
                    name=name,
                    email=email,
                    company=company,
                    value=value,
                    source=source,
                )
            )
            imported_count += 1

        db.session.commit()
        return imported_count, skipped_count

    @staticmethod
    def _create_reader(file_storage):
        text_stream = TextIOWrapper(file_storage.stream, encoding="utf-8-sig")
        return csv.DictReader(text_stream)

    @staticmethod
    def _validate_required_columns(fieldnames, required_columns):
        if not fieldnames:
            raise ValueError("CSV file has no header.")

        normalized = {name.strip() for name in fieldnames if name}
        missing = [column for column in required_columns if column not in normalized]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
