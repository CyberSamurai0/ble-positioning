import os
import json
import datetime
import jwt
from hmac import compare_digest as safe_str_cmp

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

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
    Azure example:
      Database=mydb;Server=myserver.postgres.database.azure.com;
      User Id=user@myserver;Password=pass;Port=5432;
    Returns:
      postgresql+psycopg2://user:pass@host:port/dbname
    """
    if not raw:
        return None

    # Split Azure semicolon style "Key=Value"
    parts = dict(
        segment.split("=", 1) for segment in raw.split(";") if "=" in segment
    )

    host = parts.get("Server", "").replace("tcp:", "")
    db = parts.get("Database")
    port = parts.get("Port", "5432")
    user = parts.get("User Id")
    pwd = parts.get("Password")

    if not all([host, db, user, pwd]):
        raise RuntimeError("Invalid Azure PostgreSQL connection string format")

    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


# ------------------------------------------------------
# Azure Connection String Handling
# ------------------------------------------------------
# Azure injects a variable: POSTGRESQLCONNSTR_<NAME>
# If your connection string is called AZURE_POSTGRESQL_CONNECTIONSTRING,
# Azure will expose: POSTGRESQLCONNSTR_AZURE_POSTGRESQL_CONNECTIONSTRING
raw_azure_conn = None
for key, val in os.environ.items():
    if key.startswith("POSTGRESQLCONNSTR_"):
        raw_azure_conn = val
        break

if not raw_azure_conn:
    raise RuntimeError(
        "No Azure PostgreSQL connection string found. "
        "Define a Connection String under Settings > Configuration > Connection Strings "
        "with type 'PostgreSQL' and name 'AZURE_POSTGRESQL_CONNECTIONSTRING'."
    )

DB_URL = convert_azure_pg_connstr(raw_azure_conn)

# ------------------------------------------------------
# Flask Setup
# ------------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------------------------------------------
# Database Models
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
# Run table creation only on actual boot, not import
# ------------------------------------------------------
@app.before_first_request
def init_database():
    try:
        db.create_all()
    except Exception as e:
        print("DATABASE INITIALIZATION ERROR:", e, flush=True)


# ------------------------------------------------------
# JWT Helpers
# ------------------------------------------------------
def create_device_jwt(device_id: str) -> str:
    payload = {
        "device_id": device_id,
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None


# ------------------------------------------------------
# /api/register — Issues JWTs
# ------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register_device():
    data = request.get_json(silent=True) or {}
    provided_secret = data.get("secret")
    device_id = data.get("device_id")

    if not provided_secret or not device_id:
        return jsonify({"error": "secret and device_id required"}), 400

    if not safe_str_cmp(provided_secret, REGISTRATION_SECRET):
        return jsonify({"error": "invalid secret"}), 403

    token = create_device_jwt(device_id)

    entry = ActiveJWT(token=token, device_id=device_id)
    db.session.add(entry)
    db.session.commit()

    return jsonify({"jwt": token})


# ------------------------------------------------------
# /api/position — Device telemetry ingestion
# ------------------------------------------------------
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

    entry = Position(
        device_id=device_id,
        building_id=data["building_id"],
        floor=data["floor"],
        loc_east=data["loc_east"],
        loc_north=data["loc_north"]
    )
    db.session.add(entry)
    db.session.commit()

    return jsonify({"status": "ok"}), 200


# ------------------------------------------------------
# Health Check
# ------------------------------------------------------
@app.route("/", methods=["GET"])
def root():
    return "API is running."


# ------------------------------------------------------
# Local Development Only
# Azure will ignore this and use Gunicorn
# ------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
