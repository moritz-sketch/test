from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
import pyotp, qrcode, io, base64, sqlite3, os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Auth API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SECRET_KEY  = os.getenv("SECRET_KEY", "change-this-in-production-use-long-random-string")
ALGORITHM   = "HS256"
TOKEN_HOURS = 24

pwd_ctx  = CryptContext(schemes=["bcrypt"])
security = HTTPBearer()

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            totp_secret TEXT,
            totp_active INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    db.close()

init_db()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: str = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class Verify2FARequest(BaseModel):
    totp_code: str

def hash_pw(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_pw(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(username: str) -> str:
    exp = datetime.utcnow() + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({"sub": username, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Ungueltiger Token")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        db.close()
        if not user:
            raise HTTPException(status_code=401, detail="User nicht gefunden")
        return dict(user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token abgelaufen oder ungueltiger")

@app.post("/register")
def register(req: RegisterRequest):
    if len(req.password) < 8:
        raise HTTPException(400, "Passwort muss mindestens 8 Zeichen haben")
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, email, password) VALUES (?,?,?)",
            (req.username.strip(), req.email.strip().lower(), hash_pw(req.password))
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Benutzername oder E-Mail bereits vergeben")
    finally:
        db.close()
    return {"message": "Registrierung erfolgreich"}

@app.post("/login")
def login(req: LoginRequest):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (req.username,)).fetchone()
    db.close()
    if not user or not verify_pw(req.password, user["password"]):
        raise HTTPException(401, "Benutzername oder Passwort falsch")
    if user["totp_active"]:
        if not req.totp_code:
            raise HTTPException(401, "2FA-Code erforderlich")
        totp = pyotp.TOTP(user["totp_secret"])
        if not totp.verify(req.totp_code, valid_window=1):
            raise HTTPException(401, "Ungueltiger 2FA-Code")
    token = create_token(user["username"])
    return {"token": token, "username": user["username"], "2fa_active": bool(user["totp_active"])}

@app.get("/me")
def me(user=Depends(get_current_user)):
    return {"username": user["username"], "email": user["email"], "2fa_active": bool(user["totp_active"])}

@app.post("/change-password")
def change_password(req: ChangePasswordRequest, user=Depends(get_current_user)):
    if not verify_pw(req.old_password, user["password"]):
        raise HTTPException(400, "Altes Passwort falsch")
    if len(req.new_password) < 8:
        raise HTTPException(400, "Neues Passwort muss mindestens 8 Zeichen haben")
    db = get_db()
    db.execute("UPDATE users SET password=? WHERE username=?",
               (hash_pw(req.new_password), user["username"]))
    db.commit()
    db.close()
    return {"message": "Passwort erfolgreich geaendert"}

@app.get("/2fa/setup")
def setup_2fa(user=Depends(get_current_user)):
    secret = pyotp.random_base32()
    totp   = pyotp.TOTP(secret)
    uri    = totp.provisioning_uri(name=user["email"], issuer_name="Moritz Portfolio")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    db = get_db()
    db.execute("UPDATE users SET totp_secret=? WHERE username=?", (secret, user["username"]))
    db.commit()
    db.close()
    return {"qr_code": f"data:image/png;base64,{qr_b64}", "secret": secret}

@app.post("/2fa/verify")
def verify_2fa(req: Verify2FARequest, user=Depends(get_current_user)):
    if not user["totp_secret"]:
        raise HTTPException(400, "Zuerst /2fa/setup aufrufen")
    totp = pyotp.TOTP(user["totp_secret"])
    if not totp.verify(req.totp_code, valid_window=1):
        raise HTTPException(400, "Ungueltiger Code - bitte nochmal versuchen")
    db = get_db()
    db.execute("UPDATE users SET totp_active=1 WHERE username=?", (user["username"],))
    db.commit()
    db.close()
    return {"message": "2FA erfolgreich aktiviert"}

@app.post("/2fa/disable")
def disable_2fa(user=Depends(get_current_user)):
    db = get_db()
    db.execute("UPDATE users SET totp_active=0, totp_secret=NULL WHERE username=?", (user["username"],))
    db.commit()
    db.close()
    return {"message": "2FA deaktiviert"}
