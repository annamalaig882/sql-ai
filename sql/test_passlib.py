try:
    from passlib.context import CryptContext
    print("Imported CryptContext")
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print("Created CryptContext")
    h = pwd_context.hash("test")
    print(f"Hash: {h}")
    v = pwd_context.verify("test", h)
    print(f"Verify: {v}")
except Exception as e:
    import traceback
    traceback.print_exc()
