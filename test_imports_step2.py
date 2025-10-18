try:
    from app.database.models import log_audit_event
    print("✅ log_audit_event import successful!")
except ImportError as e:
    print(f"❌ log_audit_event import failed: {e}")

try:
    from app.security.engine.security_engine import SecurityEngine
    print("✅ SecurityEngine import successful!")
except ImportError as e:
    print(f"❌ SecurityEngine import failed: {e}")

try:
    from app.main import app
    print("✅ Main app import successful!")
    print("🎉 All imports are working!")
except ImportError as e:
    print(f"❌ Main app import failed: {e}")
