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


def is_admin_email(email: str | None) -> bool:
    """
    Checks if an email address exists in the MongoDB 'admins' collection
    under the 'department_cup' database.
    Case-insensitive matching for both 'email' string or 'emails' list fields.
    """
    if not email:
        return False
    
    clean_email = email.strip().lower()
    admins_col = get_admins_collection()
    if admins_col is None:
        print("[MongoDB] Warning: Admins collection unavailable. Rejecting admin check.")
        return False
    
    try:
        rgx = re.compile(f"^{re.escape(clean_email)}$", re.IGNORECASE)
        # Check both single email field and list of emails
        found = admins_col.find_one({
            "$or": [
                {"email": rgx},
                {"emails": rgx}
            ]
        })
        return found is not None
    except Exception as e:
        print(f"[MongoDB] Error checking admin status for {email}: {e}")
        return False


def get_all_admin_emails() -> list[str]:
    """Retrieves all registered admin emails from MongoDB."""
    admins_col = get_admins_collection()
    if admins_col is None:
        return []
    try:
        admins = []
        for doc in admins_col.find({}, {"email": 1, "emails": 1, "name": 1}):
            if "email" in doc and doc["email"]:
                admins.append(doc["email"])
            if "emails" in doc and isinstance(doc["emails"], list):
                admins.extend(doc["emails"])
        return sorted(list(set(admins)))
    except Exception as e:
        print(f"[MongoDB] Error listing admins: {e}")
        return []


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
