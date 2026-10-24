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


# The 12 primary tournament sports mapped to their dedicated collections in department_cup
SPORT_COLLECTIONS: list[str] = [
    "badminton",
    "basketball",
    "box_cricket",
    "carrom",
    "cricket",
    "discuss_throw",
    "football",
    "long_jump",
    "shotput",
    "table_tennis",
    "tug_of_war",
    "volleyball"
]

SPORT_COLLECTION_ALIASES: dict[str, str] = {
    "cricket_boys": "cricket",
    "box_cricket_girls": "box_cricket",
    "football_boys": "football",
    "football_girls": "football",
    "volleyball_boys": "volleyball",
    "badminton_mix": "badminton",
    "tt_boys": "table_tennis",
    "carrom_mix": "carrom",
    "tow_boys": "tug_of_war",
    "tow_girls": "tug_of_war",
    "shotput_boys": "shotput",
    "shotput_girls": "shotput",
    "discus_boys": "discuss_throw",
    "discus_girls": "discuss_throw",
    "discus_throw": "discuss_throw",
    "long_jump_boys": "long_jump",
    "long_jump_girls": "long_jump",
    "basketball_shootout": "basketball",
}


def get_sport_collection_name(sport_id: str | None) -> str:
    """Returns the dedicated MongoDB collection name for any sport ID or alias."""
    if not sport_id:
        return "cricket"
    sid = str(sport_id).lower().strip()
    if sid in SPORT_COLLECTIONS:
        return sid
    return SPORT_COLLECTION_ALIASES.get(sid, "cricket")


def get_sport_collection(sport_id: str | None) -> Collection | None:
    """Returns the Collection instance for a given sport ID."""
    db = get_db()
    if db is None:
        return None
    col_name = get_sport_collection_name(sport_id)
    return db[col_name]


def sync_match_to_mongo(match: dict[str, Any]):
    """
    Syncs a match document comprehensively to its dedicated sport collection
    in MongoDB department_cup (e.g. 'badminton', 'cricket', 'football', etc.).
    Guarantees persistence of:
      - Which departments played (team_a, team_b)
      - Who were the players (squads, captain, playing XI/roster, substitutes)
      - The complete scorecard (score)
      - The final result & winner (winner, winner_code, winner_name, result)
    """
    db = get_db()
    if db is None or not match or "id" not in match:
        return
    try:
        col_name = get_sport_collection_name(match.get("sport_id") or match.get("collection_name"))
        match_copy = dict(match)
        match_copy.pop("_id", None)
        match_copy["collection_name"] = col_name

        # Persist comprehensively into the sport collection
        db[col_name].replace_one({"id": match["id"]}, match_copy, upsert=True)
        # Also maintain unified backup in 'matches' collection if it exists
        existing_cols = db.list_collection_names()
        if "matches" in existing_cols:
            db["matches"].replace_one({"id": match["id"]}, match_copy, upsert=True)
    except Exception as e:
        print(f"[MongoDB] Error syncing match {match.get('id')} to {match.get('sport_id')}: {e}")


def delete_match_from_mongo(match_id: str, sport_id: str | None = None):
    """Deletes an unconcluded match from its sport collection and any backup collection."""
    db = get_db()
    if db is None:
        return
    try:
        query = {"$or": [{"id": match_id}, {"_id": match_id}]}
        if sport_id:
            col_name = get_sport_collection_name(sport_id)
            db[col_name].delete_many(query)
        for col in SPORT_COLLECTIONS:
            db[col].delete_many(query)
        existing_cols = db.list_collection_names()
        if "matches" in existing_cols:
            db["matches"].delete_many(query)
        print(f"[MongoDB] Successfully deleted unconcluded match {match_id} from database collections.")
    except Exception as e:
        print(f"[MongoDB] Error deleting match {match_id}: {e}")


def load_matches_from_mongo() -> dict[str, dict[str, Any]]:
    """
    Loads all matches across the 12 primary sport collections in MongoDB department_cup.
    Only loads matches between the 3 valid departments: AMSC, PPE, and PPT.
    """
    valid_departments = {"amsc", "ppe", "ppt"}
    db = get_db()
    if db is None:
        return {}
    try:
        matches = {}
        for col_name in SPORT_COLLECTIONS:
            for doc in db[col_name].find():
                doc.pop("_id", None)
                if "id" in doc:
                    ta = doc.get("team_a", {}).get("code", "").lower()
                    tb = doc.get("team_b", {}).get("code", "").lower()
                    if ta in valid_departments and tb in valid_departments:
                        matches[doc["id"]] = doc
                    else:
                        # Prune invalid legacy record from DB
                        try:
                            db[col_name].delete_one({"id": doc["id"]})
                        except Exception:
                            pass
        # Also check unified 'matches' collection for any legacy records
        existing_cols = db.list_collection_names()
        if "matches" in existing_cols:
            for doc in db["matches"].find():
                doc.pop("_id", None)
                if "id" in doc and doc["id"] not in matches:
                    ta = doc.get("team_a", {}).get("code", "").lower()
                    tb = doc.get("team_b", {}).get("code", "").lower()
                    if ta in valid_departments and tb in valid_departments:
                        matches[doc["id"]] = doc
                    else:
                        try:
                            db["matches"].delete_one({"id": doc["id"]})
                        except Exception:
                            pass
        return matches
    except Exception as e:
        print(f"[MongoDB] Error loading matches across sport collections: {e}")
        return {}
