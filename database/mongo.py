"""
MongoDB Atlas Client & Tournament Database Operations.
Manages connection to the 'department_cup' database and 'admins' collection.
"""

import os
import re
from typing import Any
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection

load_dotenv()

MONGO_URI: str = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI", "")
DATABASE_NAME: str = os.getenv("DATABASE_NAME", "department_cup")

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient | None:
    """Returns singleton MongoDB client with connection pooling."""
    global _client
    if _client is not None:
        return _client
    if not MONGO_URI:
        print("[MongoDB] No MONGO_URI provided in .env")
        return None
    try:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, maxPoolSize=20)
        # Verify connection
        _client.admin.command("ping")
        print(f"[MongoDB] Successfully connected to cluster! Database: {DATABASE_NAME}")
        return _client
    except Exception as e:
        print(f"[MongoDB] Connection error: {e}")
        return None


def get_db():
    """Returns MongoDB database instance for department_cup."""
    client = get_mongo_client()
    if client is not None:
        return client[DATABASE_NAME]
    return None


def get_admins_collection() -> Collection | None:
    """Returns the 'admins' collection from department_cup."""
    db = get_db()
    if db is not None:
        return db["admins"]
    return None


# Static Master Admin Emails (Guaranteed instant authorization)
STATIC_ADMIN_EMAILS: set[str] = {
    "rohit_k@amsc.iitr.ac.in",
    "rohitkumar.patna1008@gmail.com",
    "organizer_sports@iitr.ac.in",
}

# Also support comma-separated admin emails from environment variable
_env_admins = os.getenv("ADMIN_EMAILS", "")
if _env_admins:
    for _e in _env_admins.split(","):
        if _e.strip():
            STATIC_ADMIN_EMAILS.add(_e.strip().lower())


def is_admin_email(email: str | None) -> bool:
    """
    Checks if an email address exists in the static admin list or in the
    MongoDB 'admins' collection under 'department_cup'.
    """
    if not email:
        return False
    
    clean_email = email.strip().lower()

    # 1. Fast check against verified static/env admin emails (guarantees verification on Vercel)
    if clean_email in STATIC_ADMIN_EMAILS:
        return True
    
    # 2. Dynamic check against MongoDB Atlas collection
    admins_col = get_admins_collection()
    if admins_col is None:
        return False
    
    try:
        # Match case-insensitively with flexible whitespace trimming
        rgx = re.compile(rf"^\s*{re.escape(clean_email)}\s*$", re.IGNORECASE)
        found = admins_col.find_one({
            "$or": [
                {"email": rgx},
                {"emails": rgx},
                {"email": clean_email}
            ]
        })
        return found is not None
    except Exception as e:
        print(f"[MongoDB] Error checking admin status for {email}: {e}")
        return False


def get_all_admin_emails() -> list[str]:
    """Retrieves all registered admin emails from static list and MongoDB."""
    combined = set(STATIC_ADMIN_EMAILS)
    admins_col = get_admins_collection()
    if admins_col is not None:
        try:
            for doc in admins_col.find({}, {"email": 1, "emails": 1, "name": 1}):
                if "email" in doc and doc["email"]:
                    combined.add(doc["email"].strip().lower())
                if "emails" in doc and isinstance(doc["emails"], list):
                    for em in doc["emails"]:
                        combined.add(em.strip().lower())
        except Exception as e:
            print(f"[MongoDB] Error listing admins: {e}")
    return sorted(list(combined))


def add_admin_email(email: str, name: str = "", added_by: str = "system") -> bool:
    """Adds a new admin email to MongoDB department_cup.admins collection."""
    if not email:
        return False
    clean_email = email.strip().lower()
    if is_admin_email(clean_email):
        return True
    
    admins_col = get_admins_collection()
    if admins_col is None:
        return False
    
    try:
        admins_col.insert_one({
            "email": clean_email,
            "name": name or clean_email.split("@")[0],
            "role": "admin",
            "added_by": added_by,
            "created_at": datetime.utcnow().isoformat()
        })
        print(f"[MongoDB] Successfully added admin: {clean_email}")
        return True
    except Exception as e:
        print(f"[MongoDB] Error adding admin {clean_email}: {e}")
        return False


def remove_admin_email(email: str) -> bool:
    """Removes an admin email from MongoDB department_cup.admins collection."""
    if not email:
        return False
    clean_email = email.strip().lower()
    admins_col = get_admins_collection()
    if admins_col is None:
        return False
    try:
        rgx = re.compile(f"^{re.escape(clean_email)}$", re.IGNORECASE)
        res = admins_col.delete_many({"$or": [{"email": rgx}, {"emails": rgx}]})
        return res.deleted_count > 0
    except Exception as e:
        print(f"[MongoDB] Error removing admin {clean_email}: {e}")
        return False


def sync_match_to_mongo(match: dict[str, Any]):
    """Syncs a match document to MongoDB 'matches' collection."""
    db = get_db()
    if db is None or not match or "id" not in match:
        return
    try:
        # Create a copy and clean any non-serializable fields if needed
        match_copy = dict(match)
        db["matches"].replace_one({"id": match["id"]}, match_copy, upsert=True)
    except Exception as e:
        print(f"[MongoDB] Error syncing match {match.get('id')}: {e}")


def delete_match_from_mongo(match_id: str):
    """Deletes a match from MongoDB 'matches' collection."""
    db = get_db()
    if db is None:
        return
    try:
        db["matches"].delete_one({"id": match_id})
    except Exception as e:
        print(f"[MongoDB] Error deleting match {match_id}: {e}")


def load_matches_from_mongo() -> dict[str, dict[str, Any]]:
    """Loads all matches from MongoDB 'matches' collection."""
    db = get_db()
    if db is None:
        return {}
    try:
        matches = {}
        for doc in db["matches"].find():
            doc.pop("_id", None)
            if "id" in doc:
                matches[doc["id"]] = doc
        return matches
    except Exception as e:
        print(f"[MongoDB] Error loading matches: {e}")
        return {}
