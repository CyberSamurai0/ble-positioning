import os
import sys
import datetime
from hmac import compare_digest as safe_str_cmp

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# ------------------------------------------------------
# Environment / runtime checks
# ------------------------------------------------------
PYTHON_VERSION = sys.version_info
if PYTHON_VERSION.major == 3 and PYTHON_VERSION.minor >= 14:
    # Warn but do not crash; Azure Log Stream will show this message.
    print(
        "WARNING: Running on Python {0}.{1}. "
        "Flask ecosystem may not be fully compatible. "
        "Recommended: use Python 3.10 - 3.12 on Azure App Service.".format(
            PYTHON_VERSION.major, PYTHON_VERSION.minor
        ),
        flush=True,
    )

# Lazy import of PyJWT so missing package doesn't crash import-time
try:
    import jwt  # PyJWT exposes module name 'jwt'
    PYJWT_AVAILABLE = True
except Exception as e:
    jwt = None
    PYJWT_AVAILABLE = False
    print("WARNING: PyJWT (jwt) import failed: %s" % (e,), flush=True)

# ------------------------------------------------------
# Load secrets
# ------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-prod")
REGISTRATION_SECRET = os.getenv("REGISTRATION_SECRET", "change-me-in-prod")

# ------------------------------------------------------
# Convert Azure PostgreSQL connection string → SQLAlchemy URL
# ------------------------------------------------------
def convert_azure_pg_connstr(raw: str) -> str:
    """
    Convert Azure-style Postgres connection string into SQLAlchemy URL.
    Example Azure format:
      Server=tcp:xxx.postgres.database.azure.com;Database=dbname;Port=5432;User Id=user@xxx;Password=pass;
    Returns SQLAlchemy URL:
      postgresql+psycopg2://user:pass@xxx.postgres.database.azure.com:5432/dbname
    """
    if not raw:
        return None

    parts = dict(segment.split("=", 1) for segment in raw.split(";") if "=" in segment)

    host = parts.get("Server", "").replace("tcp:", "")
    db = parts.get("Database")
    port = parts.get("Port", "5432")
    user = parts.get("User Id")
    pwd = parts.get("Password")

    if not all([host, db, user, pwd]):
        raise RuntimeError("Invalid Azure PostgreSQL connection string format")

    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


# ------------------------------------------------------
# Azure Connection String Handling (robust)
# ------------------------------------------------------
raw_azure_conn = None
for key, val in os.environ.items():
    if key.startswith("POSTGRESQLCONNSTR_"):
        raw_azure_conn = val
        break

if not raw_azure_conn:
    # Do not raise at import time; put an informative message in logs instead
    print(
        "ERROR: No Azure PostgreSQL connection string found. "
        "Define a Connection String in Azure Portal (type: PostgreSQL).",
        flush=True,
    )
    DB_URL = None
else:
    DB_URL = convert_azure_pg_connstr(raw_azure_conn)

# ------------------------------------------------------
# Flask + DB
# ------------------------------------------------------
app = Flask(__name__)
if DB_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------------------------------------------
# Models
# ------------------------------------------------------
class ActiveJWT(db.Model):
    __tablename__ = "active_jwts"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, unique=True, nullable=False)
    device_id = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


class Position(db.Model):
    __tablename__ = "positions"
    id = db.Column(db.BigInteger, primary_key=True)
    device_id = db.Column(db.String(255), nullable=False)
    building_id = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    loc_east = db.Column(db.Integer, nullable=False)
    loc_north = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


# ------------------------------------------------------
# Create tables on first request (safe, non-fatal)
# ------------------------------------------------------
@app.before_first_request
def init_database():
    if not DB_URL:
        print(
            "Skipping db.create_all() because DB_URL is not configured.", flush=True
        )
        return

    try:
        db.create_all()
        print("Database tables created/verified.", flush=True)
    except Exception as exc:
        # Do not raise — log for Azure diagnostics
        print("DATABASE INITIALIZATION ERROR: %s" % (exc,), flush=True)


# ------------------------------------------------------
# JWT helpers (use lazy checks)
# ------------------------------------------------------
def create_device_jwt(device_id: str) -> str:
    if not PYJWT_AVAILABLE:
        # Return a clear server error later when endpoint is called
        raise RuntimeError(
            "PyJWT is not installed in the environment. "
            "Install PyJWT (e.g. add 'PyJWT' to requirements.txt) and redeploy."
        )

    payload = {"device_id": device_id, "iat": datetime.datetime.utcnow()}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    # PyJWT >=2 returns a str; ensure str is returned
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def verify_jwt(token: str):
    if not PYJWT_AVAILABLE:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None


# ------------------------------------------------------
# Routes
# ------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register_device():
    if not PYJWT_AVAILABLE:
        return (
            jsonify(
                {
                    "error": "PyJWT dependency not installed. Add 'PyJWT' to requirements.txt and redeploy."
                }
            ),
            500,
        )

    data = request.get_json(silent=True) or {}
    provided_secret = data.get("secret")
    device_id = data.get("device_id")

    if not provided_secret or not device_id:
        return jsonify({"error": "secret and device_id required"}), 400

    if not safe_str_cmp(provided_secret, REGISTRATION_SECRET):
        return jsonify({"error": "invalid secret"}), 403

    try:
        token = create_device_jwt(device_id)
    except RuntimeError as e:
        print("JWT creation error: %s" % (e,), flush=True)
        return jsonify({"error": str(e)}), 500

    try:
        entry = ActiveJWT(token=token, device_id=device_id)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        # Log and continue — return an error to the caller
        print("DB error saving active_jwt: %s" % (e,), flush=True)
        return jsonify({"error": "database error saving token"}), 500

    return jsonify({"jwt": token})


@app.route("/api/position", methods=["POST"])
def position():
    # Authentication
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401

    token = auth_header.replace("Bearer ", "").strip()
    payload = verify_jwt(token)
    if not payload:
        return jsonify({"error": "invalid token"}), 401

    device_id = payload.get("device_id")
    if not device_id:
        return jsonify({"error": "token missing device_id"}), 401

    # Data validation
    data = request.get_json(silent=True) or {}
    required = ["building_id", "floor", "loc_east", "loc_north"]
    if not all(k in data for k in required):
        return jsonify({"error": "missing required fields"}), 400

    try:
        entry = Position(
            device_id=device_id,
            building_id=data["building_id"],
            floor=data["floor"],
            loc_east=data["loc_east"],
            loc_north=data["loc_north"],
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        print("DB error saving position: %s" % (e,), flush=True)
        return jsonify({"error": "database error saving position"}), 500

    return jsonify({"status": "ok"}), 200


# Health check
@app.route("/", methods=["GET"])
def root():
    return "API is running."


# Local dev only
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
