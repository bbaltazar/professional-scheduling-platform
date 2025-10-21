#!/usr/bin/env python3
"""
Verify workplace associations for all professionals.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from calendar_app.database import (
    Specialist,
    Workplace,
    specialist_workplace_association,
)

DATABASE_URL = "sqlite:///./calendar_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def verify_associations():
    """Verify all professional-workplace associations."""
    db = SessionLocal()

    try:
        print("=" * 80)
        print("PROFESSIONAL-WORKPLACE ASSOCIATIONS")
        print("=" * 80)
        print()

        specialists = db.query(Specialist).all()

        for specialist in specialists:
            print(f"👤 {specialist.name} (ID: {specialist.id})")
            print(f"   Email: {specialist.email}")

            # Get workplaces for this specialist
            associations = (
                db.query(specialist_workplace_association)
                .filter(
                    specialist_workplace_association.c.specialist_id == specialist.id
                )
                .all()
            )

            if associations:
                print(f"   🏢 Workplaces ({len(associations)}):")
                for assoc in associations:
                    workplace = (
                        db.query(Workplace)
                        .filter(Workplace.id == assoc.workplace_id)
                        .first()
                    )
                    if workplace:
                        verified = "✓" if workplace.is_verified else " "
                        role = assoc.role or "professional"
                        active = "✓" if assoc.is_active else "✗"
                        print(f"      [{verified}] {workplace.name}")
                        print(f"          📍 {workplace.city}, {workplace.state}")
                        print(f"          Role: {role.upper()} | Active: {active}")
            else:
                print(f"   ⚠️  No workplace associations")

            # Get services
            from calendar_app.database import ServiceDB

            services = (
                db.query(ServiceDB)
                .filter(ServiceDB.specialist_id == specialist.id)
                .all()
            )

            if services:
                print(f"   💼 Services ({len(services)}):")
                for svc in services:
                    print(f"      • {svc.name} - ${svc.price} ({svc.duration} min)")

            print()

        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        total_specialists = len(specialists)
        total_workplaces = db.query(Workplace).count()
        total_associations = db.query(specialist_workplace_association).count()

        specialists_with_workplaces = (
            db.query(Specialist)
            .join(
                specialist_workplace_association,
                Specialist.id == specialist_workplace_association.c.specialist_id,
            )
            .distinct()
            .count()
        )

        print(f"Total Professionals: {total_specialists}")
        print(f"Professionals with Workplaces: {specialists_with_workplaces}")
        print(f"Total Workplaces: {total_workplaces}")
        print(f"Total Associations: {total_associations}")
        print()

        # Show all workplaces
        print("=" * 80)
        print("WORKPLACES")
        print("=" * 80)
        print()

        workplaces = db.query(Workplace).all()
        for workplace in workplaces:
            verified = "✓ VERIFIED" if workplace.is_verified else ""
            print(f"🏢 {workplace.name} {verified}")
            print(
                f"   📍 {workplace.address}, {workplace.city}, {workplace.state} {workplace.zip_code}"
            )
            if workplace.phone:
                print(f"   📞 {workplace.phone}")
            if workplace.website:
                print(f"   🌐 {workplace.website}")

            # Count specialists
            specialist_count = (
                db.query(specialist_workplace_association)
                .filter(
                    specialist_workplace_association.c.workplace_id == workplace.id,
                    specialist_workplace_association.c.is_active == True,
                )
                .count()
            )

            print(
                f"   👥 {specialist_count} professional{'s' if specialist_count != 1 else ''}"
            )
            print()

    finally:
        db.close()


if __name__ == "__main__":
    verify_associations()
