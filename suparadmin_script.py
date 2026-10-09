from getpass import getpass
from sqlalchemy import func

from database import SessionLocal
from models import Admins
import bcrypt


def create_superadmin():
    db = SessionLocal()

    try:
        existing = (
            db.query(Admins)
            .filter(
                Admins.role == "superadmin",
                Admins.deleted.is_(False),
            )
            .first()
        )

        if existing:
            print("Super Admin already exists.")
            return

        name = input("Enter Super Admin name: ").strip()
        email = input("Enter email: ").strip().lower()
        password = input("Enter Password : ")
        confirm_password = input("Confirm Password : ")

        if not name or not email:
            raise ValueError("Name and email are required.")

        if len(password) < 12 or len(password) > 128:
            raise ValueError("Password must be 12–128 characters.")

        if password != confirm_password:
            raise ValueError("Passwords do not match.")

        existing_email = (
            db.query(Admins)
            .filter(func.lower(Admins.email_id) == email)
            .first()
        )

        if existing_email:
            raise ValueError("This email is already registered.")

        admin = Admins(
            name=name,
            email_id=email,
            password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            role="superadmin",
            deleted=False,
        )

        db.add(admin)
        db.commit()

        print("Super Admin created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_superadmin()