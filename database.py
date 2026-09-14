import sqlite3
import json
import os
from config import DATABASE_PATH

def init_db():
    # إنشاء المجلد الخاص بـ Volume إذا لم يكن موجوداً
    dir_path = os.path.dirname(DATABASE_PATH)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tracked_users (
        user_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        last_presence INTEGER,
        last_place_id INTEGER,
        friends_json TEXT,
        known_badges TEXT
    )
    ''')
    conn.commit()
    conn.close()

def get_all_tracked():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, channel_id, last_presence, last_place_id, friends_json, known_badges FROM tracked_users")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_tracked_user(user_id, channel_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO tracked_users (user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
    conn.commit()
    conn.close()

def remove_tracked_user(user_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tracked_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_data(user_id, presence=None, place_id=None, friends_json=None, badges_str=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    if presence is not None:
        cursor.execute("UPDATE tracked_users SET last_presence = ?, last_place_id = ? WHERE user_id = ?", (presence, place_id, user_id))
    if friends_json is not None:
        cursor.execute("UPDATE tracked_users SET friends_json = ? WHERE user_id = ?", (friends_json, user_id))
    if badges_str is not None:
        cursor.execute("UPDATE tracked_users SET known_badges = ? WHERE user_id = ?", (badges_str, user_id))
    conn.commit()
    conn.close()
