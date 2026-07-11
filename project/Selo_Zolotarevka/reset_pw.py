import sqlite3
import bcrypt
import os

# Path to the database
DB_PATH = "/var/www/zolotarevka-fastapi/zolotarevka.db"
NEW_PASSWORD = "admin123"
USERNAME = "admin"

def reset_password():
    try:
        # Hash the new password
        pw_hash = bcrypt.hashpw(NEW_PASSWORD.encode(), bcrypt.gensalt()).decode()
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Update the user password
        cur.execute("UPDATE users SET password_hash = ? WHERE username = ?", (pw_hash, USERNAME))
        
        if cur.rowcount == 0:
            print(f"Error: User {USERNAME} not found in database.")
        else:
            conn.commit()
            print(f"✅ Password for user {USERNAME} has been reset to {NEW_PASSWORD}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_password()
