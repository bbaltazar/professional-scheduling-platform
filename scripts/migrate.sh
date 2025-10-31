#!/bin/bash
# Database migration helper script

VENV_PYTHON="/Users/brianabaltazar/SoftwareEngineering/apps/calendar_app/.venv/bin/python"
VENV_ALEMBIC="/Users/brianabaltazar/SoftwareEngineering/apps/calendar_app/.venv/bin/alembic"

case "$1" in
    "upgrade")
        echo "🚀 Applying migrations..."
        $VENV_ALEMBIC upgrade head
        ;;
    "downgrade")
        echo "⏪ Rolling back one migration..."
        $VENV_ALEMBIC downgrade -1
        ;;
    "create")
        if [ -z "$2" ]; then
            echo "❌ Error: Please provide a migration message"
            echo "Usage: ./scripts/migrate.sh create 'migration message'"
            exit 1
        fi
        echo "📝 Creating new migration: $2"
        $VENV_ALEMBIC revision --autogenerate -m "$2"
        ;;
    "history")
        echo "📜 Migration history:"
        $VENV_ALEMBIC history
        ;;
    "current")
        echo "📍 Current migration:"
        $VENV_ALEMBIC current
        ;;
    "help"|*)
        echo "Database Migration Helper"
        echo ""
        echo "Usage: ./scripts/migrate.sh [command]"
        echo ""
        echo "Commands:"
        echo "  upgrade    - Apply all pending migrations"
        echo "  downgrade  - Rollback the last migration"
        echo "  create     - Create a new migration (requires message)"
        echo "  history    - Show migration history"
        echo "  current    - Show current migration state"
        echo "  help       - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./scripts/migrate.sh upgrade"
        echo "  ./scripts/migrate.sh create 'add user email index'"
        ;;
esac
