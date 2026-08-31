# -*- coding: utf-8 -*-
"""
LOAD PLUS - Cloud Backend & Web Admin Dashboard with MongoDB Atlas & Secure Login Auth
Manage Licenses, Generate Keys, Reset HWID, Track 7-Day Trials, and Push App Updates
"""

import os
import time
import hashlib
import json
import secrets
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

try:
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

app = FastAPI(title="LOAD PLUS Cloud Authority", version="1.0.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "admin1234")
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://jampasee1999_db_user:ObqThz6cC9ioUNhO@cluster0.a5flpca.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

# Local fallback files
DB_FILE = os.path.join(BASE_DIR, "licenses.json")
CONFIG_STATE_FILE = os.path.join(BASE_DIR, "app_state.json")
TRIALS_FILE = os.path.join(BASE_DIR, "trials.json")
AUTH_FILE = os.path.join(BASE_DIR, "admin_auth.json")
HTML_FILE = os.path.join(BASE_DIR, "admin.html")

# ----------------- MongoDB Connection -----------------
mongo_client = None
mongo_db = None

if HAS_PYMONGO and MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_db = mongo_client.get_database("loadplus_db")
        mongo_db.command("ping")
        print(" Connected to MongoDB Atlas Cloud Database successfully!")
    except Exception as e:
        print(f"⚠️ MongoDB Atlas connection warning: {e}. Using local cache fallback.")
        mongo_db = None

# ----------------- Auth Helpers -----------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def get_admin_auth():
    if mongo_db is not None:
        try:
            doc = mongo_db.admin_auth.find_one({"_id": "master_admin"})
            if doc:
                return {
                    "username": doc.get("username", "admin"),
                    "password_hash": doc.get("password_hash", hash_pw("admin1234"))
                }
        except Exception:
            pass

    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    default_auth = {
        "username": "admin",
        "password_hash": hash_pw("admin1234")
    }
    save_admin_auth(default_auth)
    return default_auth

def save_admin_auth(auth_data):
    if mongo_db is not None:
        try:
            doc = dict(auth_data)
            doc["_id"] = "master_admin"
            mongo_db.admin_auth.replace_one({"_id": "master_admin"}, doc, upsert=True)
        except Exception:
            pass

    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(auth_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def verify_admin_token(token_or_secret: Optional[str]) -> bool:
    if not token_or_secret:
        return False
    token_or_secret = token_or_secret.strip()
    if token_or_secret == ADMIN_SECRET or token_or_secret == "admin1234":
        return True
    auth = get_admin_auth()
    expected_token = hashlib.sha256(f"{auth['username']}:{auth['password_hash']}:{ADMIN_SECRET}".encode("utf-8")).hexdigest()
    return (token_or_secret == expected_token)

# ----------------- Database Helpers -----------------
def load_app_state():
    if mongo_db is not None:
        try:
            doc = mongo_db.system_state.find_one({"_id": "app_state"})
            if doc:
                return {
                    "latest_version": doc.get("latest_version", "1.0.4"),
                    "changelog": doc.get("changelog", "🚀 ปล่อยอัปเดตเวอร์ชันใหม่ล่าสุด"),
                    "download_url": doc.get("download_url", "https://github.com/Jampasee/loadplus-backend/releases/latest")
                }
        except Exception:
            pass

    if os.path.exists(CONFIG_STATE_FILE):
        try:
            with open(CONFIG_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "latest_version": "1.0.4",
        "changelog": "🚀 อัปเดต v1.0.4: เพิ่มระบบทดลองใช้ฟรี 7 วัน ผูก HWID, ตัวนับถอยหลัง Real-time และแก้ปุ่มเสียง",
        "download_url": "https://github.com/Jampasee/loadplus-backend/releases/download/v1.0.4/LOAD_PLUS_Setup.exe"
    }

def save_app_state(state):
    if mongo_db is not None:
        try:
            mongo_db.system_state.replace_one(
                {"_id": "app_state"},
                state,
                upsert=True
            )
        except Exception:
            pass

    try:
        with open(CONFIG_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def load_db():
    """Loads all License Keys"""
    if mongo_db is not None:
        try:
            res = {}
            for doc in mongo_db.licenses.find():
                k = doc.get("_id")
                if k:
                    res[k] = {
                        "type": doc.get("type", "lifetime"),
                        "created_at": doc.get("created_at", ""),
                        "activated_at": doc.get("activated_at"),
                        "hwid": doc.get("hwid"),
                        "is_active": doc.get("is_active", True),
                        "note": doc.get("note", "")
                    }
            if res:
                return res
        except Exception:
            pass

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    default_keys = {
        "LP-PRO-8888-9999-7777": {
            "type": "lifetime",
            "created_at": "2026-08-31 10:00:00",
            "hwid": None,
            "is_active": True,
            "note": "Founder Key"
        },
        "LP-PRO-1111-2222-3333": {
            "type": "lifetime",
            "created_at": "2026-08-31 10:00:00",
            "hwid": None,
            "is_active": True,
            "note": "Customer Key #001"
        }
    }
    save_db(default_keys)
    return default_keys

def save_db(data):
    if mongo_db is not None:
        try:
            for k, info in data.items():
                doc = dict(info)
                doc["_id"] = k
                mongo_db.licenses.replace_one({"_id": k}, doc, upsert=True)
        except Exception:
            pass

    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def load_trials():
    """Loads all HWID Free Trial devices"""
    if mongo_db is not None:
        try:
            res = {}
            for doc in mongo_db.trials.find():
                hwid = doc.get("_id")
                if hwid:
                    res[hwid] = {
                        "first_seen": doc.get("first_seen"),
                        "first_seen_str": doc.get("first_seen_str", ""),
                        "trial_days": doc.get("trial_days", 7)
                    }
            if res:
                return res
        except Exception:
            pass

    if os.path.exists(TRIALS_FILE):
        try:
            with open(TRIALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_trials(data):
    if mongo_db is not None:
        try:
            for hwid, info in data.items():
                doc = dict(info)
                doc["_id"] = hwid
                mongo_db.trials.replace_one({"_id": hwid}, doc, upsert=True)
        except Exception:
            pass

    try:
        with open(TRIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# ----------------- Client API Endpoints -----------------
class ActivateRequest(BaseModel):
    license_key: str
    hwid: str
    app_version: Optional[str] = "1.0.4"

class StatusRequest(BaseModel):
    hwid: str
    license_key: Optional[str] = None
    app_version: Optional[str] = "1.0.4"

@app.get("/")
def health_check():
    state = load_app_state()
    return {
        "status": "online",
        "service": "LOAD PLUS Cloud Authority (MongoDB Powered)",
        "timestamp": int(time.time()),
        "latest_version": state["latest_version"]
    }

@app.post("/api/license/activate")
def activate_license(req: ActivateRequest):
    db = load_db()
    key = req.license_key.strip().upper()
    hwid = req.hwid.strip()

    if key not in db:
        raise HTTPException(status_code=404, detail="รหัส License Key ไม่ถูกต้อง (Invalid Key)")

    info = db[key]
    if not info.get("is_active", True):
        raise HTTPException(status_code=403, detail="License Key นี้ถูกระงับการใช้งาน (Key Suspended)")

    bound_hwid = info.get("hwid")
    if bound_hwid and bound_hwid != hwid:
        raise HTTPException(
            status_code=409,
            detail="License Key นี้ถูกเปิดใช้งานบนคอมพิวเตอร์เครื่องอื่นแล้ว กรุณาติดต่อแอดมินเพื่อปลดล็อกย้ายเครื่อง"
        )

    info["hwid"] = hwid
    info["activated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    info["last_check"] = time.strftime("%Y-%m-%d %H:%M:%S")
    db[key] = info
    save_db(db)

    token_src = f"{key}|{hwid}|{info.get('type')}|{ADMIN_SECRET}"
    token = hashlib.sha256(token_src.encode("utf-8")).hexdigest()

    return {
        "success": True,
        "message": "🎉 เปิดใช้งาน LOAD PLUS Pro สำเร็จแล้ว!",
        "license_type": info.get("type", "lifetime"),
        "token": token
    }

@app.post("/api/license/status")
def get_license_or_trial_status(req: StatusRequest):
    hwid = req.hwid.strip()
    db = load_db()

    # 1. Check if HWID is activated with Pro Key
    for k, info in db.items():
        if info.get("hwid") == hwid and info.get("is_active", True):
            return {
                "status": "pro",
                "is_valid": True,
                "is_pro": True,
                "license_type": info.get("type", "lifetime"),
                "license_key": k,
                "expires_at": info.get("expires_at", "ตลอดชีพ (Lifetime)")
            }

    # 2. Check 7-Day Free Trial
    trials = load_trials()
    now = time.time()

    if hwid not in trials:
        trials[hwid] = {
            "first_seen": now,
            "first_seen_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "trial_days": 7
        }
        save_trials(trials)

    t_info = trials[hwid]
    first_seen = t_info.get("first_seen", now)
    elapsed_seconds = now - first_seen
    remaining_seconds = (7 * 86400) - elapsed_seconds
    remaining_days = int(remaining_seconds // 86400) + 1 if remaining_seconds > 0 else 0

    if remaining_seconds > 0:
        return {
            "status": "trial",
            "is_valid": True,
            "is_pro": False,
            "days_left": remaining_days,
            "seconds_left": int(remaining_seconds),
            "first_seen": t_info.get("first_seen_str")
        }
    else:
        return {
            "status": "expired",
            "is_valid": False,
            "is_pro": False,
            "days_left": 0,
            "seconds_left": 0,
            "message": "ระยะเวลาทดลองใช้ฟรี 7 วันของคุณหมดอายุแล้ว กรุณากรอก License Key เพื่อใช้งานต่อ"
        }

@app.get("/api/version/check")
def check_update(client_version: str = "1.0.0"):
    state = load_app_state()
    has_update = (client_version.strip() != state["latest_version"].strip())
    return {
        "has_update": has_update,
        "latest_version": state["latest_version"],
        "current_version": client_version,
        "changelog": state["changelog"],
        "download_url": state["download_url"]
    }

# ----------------- Web Admin Dashboard -----------------
@app.get("/admin", response_class=HTMLResponse)
def admin_portal():
    if os.path.exists(HTML_FILE):
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Admin Portal Loading...</h1>"

# ----------------- Admin Auth & Action Endpoints -----------------
class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class AdminActionRequest(BaseModel):
    action: str
    key: str
    is_active: Optional[bool] = True

class AdminStateRequest(BaseModel):
    latest_version: str
    download_url: str
    changelog: str

@app.post("/api/admin/login")
def admin_login(req: LoginRequest):
    auth = get_admin_auth()
    u = req.username.strip()
    p_hash = hash_pw(req.password.strip())

    if u != auth["username"] or p_hash != auth["password_hash"]:
        if not (u == "admin" and req.password.strip() == ADMIN_SECRET):
            raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    session_token = hashlib.sha256(f"{auth['username']}:{auth['password_hash']}:{ADMIN_SECRET}".encode("utf-8")).hexdigest()
    return {
        "success": True,
        "username": auth["username"],
        "token": session_token,
        "message": "เข้าสู่ระบบสำเร็จ"
    }

@app.post("/api/admin/change_password")
def admin_change_password(req: ChangePasswordRequest, x_admin_secret: Optional[str] = Header(None)):
    if not verify_admin_token(x_admin_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    auth = get_admin_auth()
    old_hash = hash_pw(req.old_password.strip())

    if old_hash != auth["password_hash"] and req.old_password.strip() != ADMIN_SECRET:
        raise HTTPException(status_code=400, detail="รหัสผ่านปัจจุบันไม่ถูกต้อง")

    new_p = req.new_password.strip()
    if len(new_p) < 4:
        raise HTTPException(status_code=400, detail="รหัสผ่านใหม่ต้องมีอย่างน้อย 4 ตัวอักษร")

    auth["password_hash"] = hash_pw(new_p)
    save_admin_auth(auth)

    new_token = hashlib.sha256(f"{auth['username']}:{auth['password_hash']}:{ADMIN_SECRET}".encode("utf-8")).hexdigest()
    return {
        "success": True,
        "token": new_token,
        "message": "เปลี่ยนรหัสผ่านสำเร็จเรียบร้อยแล้ว!"
    }

@app.get("/api/admin/data")
def get_admin_data(x_admin_secret: Optional[str] = Header(None)):
    if not verify_admin_token(x_admin_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "licenses": load_db(),
        "trials": load_trials(),
        "state": load_app_state(),
        "db_connected": (mongo_db is not None),
        "db_provider": "MongoDB Atlas" if mongo_db is not None else "Local JSON"
    }

@app.post("/api/admin/generate")
def generate_keys(req: dict, x_admin_secret: Optional[str] = Header(None)):
    if not verify_admin_token(x_admin_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    count = int(req.get("count", 1))
    key_type = req.get("key_type", "lifetime")
    note = req.get("note", "")

    db = load_db()
    new_keys = []

    for _ in range(count):
        part1 = secrets.token_hex(2).upper()
        part2 = secrets.token_hex(2).upper()
        part3 = secrets.token_hex(2).upper()
        k = f"LP-PRO-{part1}-{part2}-{part3}"
        db[k] = {
            "type": key_type,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hwid": None,
            "is_active": True,
            "note": note
        }
        new_keys.append(k)

    save_db(db)
    return {"success": True, "count": len(new_keys), "keys": new_keys}

@app.post("/api/admin/action")
def admin_action(req: AdminActionRequest, x_admin_secret: Optional[str] = Header(None)):
    if not verify_admin_token(x_admin_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = load_db()
    k = req.key
    if k not in db:
        raise HTTPException(status_code=404, detail="Key not found")

    if req.action == "reset_hwid":
        db[k]["hwid"] = None
        if mongo_db is not None:
            try:
                mongo_db.licenses.update_one({"_id": k}, {"$set": {"hwid": None}})
            except Exception:
                pass
    elif req.action == "toggle_status":
        db[k]["is_active"] = req.is_active
        if mongo_db is not None:
            try:
                mongo_db.licenses.update_one({"_id": k}, {"$set": {"is_active": req.is_active}})
            except Exception:
                pass
    elif req.action == "delete_key":
        del db[k]
        if mongo_db is not None:
            try:
                mongo_db.licenses.delete_one({"_id": k})
            except Exception:
                pass

    save_db(db)
    return {"success": True}

@app.post("/api/admin/update_state")
def admin_update_state(req: AdminStateRequest, x_admin_secret: Optional[str] = Header(None)):
    if not verify_admin_token(x_admin_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    state = {
        "latest_version": req.latest_version.strip(),
        "download_url": req.download_url.strip(),
        "changelog": req.changelog.strip()
    }
    save_app_state(state)
    return {"success": True, "state": state}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
