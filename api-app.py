import os
import json
import jwt
import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import safe_str_cmp

# ------------------------------------------------------
# Load secrets
# ------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-prod")
REGISTRATION_SECRET = os.getenv("REGISTRATION_SECRET", "change-me-in-prod")

# ------------------------------------------------------
# Convert Azure PostgreSQL connection string to SQLAlchemy URI
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


# Read the Azure-injected connection string
raw_azure_conn = os.getenv("POSTGRESQLCONNSTR_AZURE_POSTGRESQL_CONNECTIONSTRING")
DB_URL = convert_azure_pg_connstr(raw_azure_conn)

if not DB_URL:
    raise RuntimeError(
        "Azure PostgreSQL connection string not found. "
        "Ensure a connection string named AZURE_POSTGRESQL_CONNECTIONSTRING "
        "is defined in Settings > Configuration > Connection strings."
    )

# ------------------------------------------------------
# Flask + Database Setup
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


# Creates tables automatically if they don't exist
with app.app_context():
    db.create_all()


# ------------------------------------------------------
# JWT Helpers
# ------------------------------------------------------
def create_device_jwt(device_id: str) -> str:
    payload = {
        "device_id": device_id,
        "iat": datetime.datetime.utcnow(),
        # No expiration – per your spec
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


def verify_jwt(token: str):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.InvalidTokenError:
        return None


# ------------------------------------------------------
# /api/register — Issues JWTs to devices
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

    # Save active token
    entry = ActiveJWT(token=token, device_id=device_id)
    db.session.add(entry)
    db.session.commit()

    return jsonify({"jwt": token})


# ------------------------------------------------------
# /api/position — Accepts telemetry data
# ------------------------------------------------------
@app.route("/api/position", methods=["POST"])
def position():
    # Authenticate
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
    if not all(key in data for key in required):
        return jsonify({"error": "missing required fields"}), 400

    # Save position
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
# Required for Azure
# ------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
