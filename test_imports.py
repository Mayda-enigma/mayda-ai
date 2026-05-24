import sys
sys.path.insert(0, r'c:\Users\pc\Desktop\mayda_hack\mayda-ai')

print("1. Testing imports...")
try:
    print("  - Importing FastAPI...")
    from fastapi import FastAPI
    print("    ✓ FastAPI imported")
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

try:
    print("  - Importing src modules...")
    from src.core.config import settings
    print("    ✓ Config imported")
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

try:
    print("  - Importing routes...")
    from src.api.routes import router
    print("    ✓ Routes imported")
except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll imports successful!")
print(f"Config PORT: {settings.PORT}")
