#!/usr/bin/env python3
"""
Add workplaces to the database and associate them with existing professionals.
This script creates realistic businesses and links professionals to them.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import sys
import os

# Add parent directory to path to import database modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from calendar_app.database import (
    Base,
    Specialist,
    Workplace,
    specialist_workplace_association,
)

DATABASE_URL = "sqlite:///./calendar_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Workplace data
WORKPLACES = [
    {
        "name": "HealthFirst Medical Center",
        "address": "123 Medical Plaza Drive",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94102",
        "phone": "+1-555-1000",
        "website": "https://healthfirst-medical.com",
        "description": "Comprehensive primary care and preventive medicine. State-of-the-art facility with board-certified physicians.",
        "professionals": ["Dr. Sarah Johnson"],  # General practitioner
    },
    {
        "name": "Bright Smiles Dental",
        "address": "456 Oak Street, Suite 200",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94103",
        "phone": "+1-555-2000",
        "website": "https://brightsmilesdental.com",
        "description": "Modern dental practice offering cosmetic and family dentistry. Advanced technology and gentle care.",
        "professionals": ["Dr. Michael Chen"],  # Dentist
    },
    {
        "name": "Mindful Wellness Center",
        "address": "789 Therapy Lane",
        "city": "Oakland",
        "state": "CA",
        "zip_code": "94612",
        "phone": "+1-555-3000",
        "website": "https://mindfulwellness.com",
        "description": "Holistic mental health services including individual, couples, and family therapy. Licensed therapists.",
        "professionals": ["Lisa Rodriguez, LMFT"],  # Therapist
    },
    {
        "name": "ActiveLife Sports Medicine",
        "address": "321 Fitness Boulevard",
        "city": "Berkeley",
        "state": "CA",
        "zip_code": "94704",
        "phone": "+1-555-4000",
        "website": "https://activelifesports.com",
        "description": "Sports medicine and physical therapy clinic. Specialized in injury recovery and performance optimization.",
        "professionals": ["David Park, PT"],  # Physical therapist
    },
    {
        "name": "NutriBalance Wellness",
        "address": "555 Nutrition Way",
        "city": "Palo Alto",
        "state": "CA",
        "zip_code": "94301",
        "phone": "+1-555-5000",
        "website": "https://nutribalance.com",
        "description": "Expert nutrition counseling and meal planning. Personalized approach to health and wellness.",
        "professionals": ["Amanda Thompson, RD"],  # Dietitian
    },
    {
        "name": "Elite Wellness Hub",
        "address": "999 Premium Plaza",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105",
        "phone": "+1-555-6000",
        "website": "https://elitewellnesshub.com",
        "description": "Multi-disciplinary wellness center offering medical, dental, therapy, and nutrition services under one roof.",
        "is_verified": True,
        "professionals": [
            "Dr. Sarah Johnson",
            "Dr. Michael Chen",
            "Lisa Rodriguez, LMFT",
            "Amanda Thompson, RD",
        ],  # Multi-specialty clinic
    },
]


def add_workplaces_and_associations():
    """Add workplaces and associate them with professionals."""
    db = SessionLocal()

    try:
        print("Adding workplaces and professional associations...")
        print("=" * 70)

        # Get all existing specialists
        specialists = db.query(Specialist).all()
        specialist_map = {spec.name: spec for spec in specialists}

        print(f"\nFound {len(specialists)} existing professionals:")
        for spec in specialists:
            print(f"  • {spec.name} (ID: {spec.id})")

        if not specialists:
            print("\n⚠️  No professionals found in database!")
            print("Run 'python scripts/populate_db.py' first to create professionals.")
            return

        print(f"\n{'='*70}")
        print("Creating workplaces and associations...\n")

        created_count = 0
        association_count = 0

        for workplace_data in WORKPLACES:
            # Extract professional names
            professional_names = workplace_data.pop("professionals")
            is_verified = workplace_data.pop("is_verified", False)

            # Check if workplace already exists
            existing = (
                db.query(Workplace)
                .filter(Workplace.name == workplace_data["name"])
                .first()
            )

            if existing:
                print(
                    f"✓ Workplace already exists: {workplace_data['name']} (ID: {existing.id})"
                )
                workplace = existing
            else:
                # Create workplace
                workplace = Workplace(
                    **workplace_data,
                    is_verified=is_verified,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(workplace)
                db.flush()  # Get the ID
                created_count += 1
                print(f"✓ Created workplace: {workplace.name} (ID: {workplace.id})")

            # Associate professionals
            for prof_name in professional_names:
                if prof_name not in specialist_map:
                    print(f"  ⚠️  Professional not found: {prof_name}")
                    continue

                specialist = specialist_map[prof_name]

                # Check if association already exists
                existing_assoc = (
                    db.query(specialist_workplace_association)
                    .filter(
                        specialist_workplace_association.c.specialist_id
                        == specialist.id,
                        specialist_workplace_association.c.workplace_id == workplace.id,
                    )
                    .first()
                )

                if existing_assoc:
                    print(
                        f"  ✓ Association already exists: {prof_name} ↔ {workplace.name}"
                    )
                    continue

                # Create association
                db.execute(
                    specialist_workplace_association.insert().values(
                        specialist_id=specialist.id,
                        workplace_id=workplace.id,
                        role="professional",
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )
                association_count += 1
                print(f"  ✓ Associated: {prof_name} ↔ {workplace.name}")

        # Special handling for Brian if he exists
        brian = db.query(Specialist).filter(Specialist.name.ilike("%brian%")).first()
        if brian:
            print(f"\n{'='*70}")
            print(f"Found Brian! (ID: {brian.id}, Email: {brian.email})")

            # Get Elite Wellness Hub
            elite_hub = (
                db.query(Workplace)
                .filter(Workplace.name == "Elite Wellness Hub")
                .first()
            )

            if elite_hub:
                # Check if association exists
                existing_assoc = (
                    db.query(specialist_workplace_association)
                    .filter(
                        specialist_workplace_association.c.specialist_id == brian.id,
                        specialist_workplace_association.c.workplace_id == elite_hub.id,
                    )
                    .first()
                )

                if not existing_assoc:
                    db.execute(
                        specialist_workplace_association.insert().values(
                            specialist_id=brian.id,
                            workplace_id=elite_hub.id,
                            role="owner",
                            is_active=True,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                    )
                    association_count += 1
                    print(f"✓ Associated Brian with Elite Wellness Hub as OWNER")
                else:
                    print(f"✓ Brian already associated with Elite Wellness Hub")

        db.commit()

        print(f"\n{'='*70}")
        print("✅ Workplace setup complete!")
        print(f"\n📊 Summary:")
        print(f"  • Workplaces created: {created_count}")
        print(f"  • Associations created: {association_count}")
        print(f"  • Total workplaces: {db.query(Workplace).count()}")
        print(
            f"  • Total associations: {db.query(specialist_workplace_association).count()}"
        )

        print(f"\n🔍 Test the search:")
        print(f"  • http://localhost:8000/search?query=wellness&search_type=business")
        print(
            f"  • http://localhost:8000/search?query=dental&search_type=business&location=San%20Francisco"
        )
        print(f"  • http://localhost:8000/consumer (click 'Browse by Business')")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("WORKPLACE SETUP SCRIPT")
    print("=" * 70)
    print()
    add_workplaces_and_associations()
