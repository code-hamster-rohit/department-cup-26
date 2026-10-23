"""
Admin Management CLI for Department Cup.
Allows managing admin emails in MongoDB department_cup.admins collection.

Usage:
    python manage_admins.py list
    python manage_admins.py add <email> [name]
    python manage_admins.py remove <email>
    python manage_admins.py check <email>
"""

import sys
from database.mongo import (
    get_all_admin_emails,
    add_admin_email,
    remove_admin_email,
    is_admin_email,
    get_admins_collection
)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "list":
        admins = get_all_admin_emails()
        print(f"\n--- Registered Department Cup Admins ({len(admins)}) ---")
        if not admins:
            print("No admins found in MongoDB department_cup.admins.")
            print("Add one using: python manage_admins.py add <your_google_email>")
        else:
            for idx, email in enumerate(admins, 1):
                print(f" {idx}. {email}")
        print("--------------------------------------------------\n")

    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Error: Missing email. Usage: python manage_admins.py add <email> [name]")
            return
        email = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else ""
        if add_admin_email(email, name, added_by="cli"):
            print(f"Success: '{email}' is now registered as an administrator in MongoDB.")
        else:
            print(f"Failed to add '{email}' to MongoDB.")

    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("Error: Missing email. Usage: python manage_admins.py remove <email>")
            return
        email = sys.argv[2]
        if remove_admin_email(email):
            print(f"Success: '{email}' was removed from administrators.")
        else:
            print(f"Admin '{email}' not found or could not be removed.")

    elif cmd == "check":
        if len(sys.argv) < 3:
            print("Error: Missing email. Usage: python manage_admins.py check <email>")
            return
        email = sys.argv[2]
        is_adm = is_admin_email(email)
        status = "VERIFIED ADMIN" if is_adm else "NOT AN ADMIN"
        print(f"Status for '{email}': {status}")

    else:
        print(f"Unknown command: '{cmd}'")
        print(__doc__)


if __name__ == "__main__":
    main()
