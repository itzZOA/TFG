import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        print("Conexión exitosa")
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn):
    try:
        query = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            medical_info TEXT,
            conversation FOREIGNKEY
        );
        '''
        conn.execute(query)
        print("Tabla users creada exitosamente")
    except Error as e:
        print(e)

    try:
        query = '''
        CREATE TABLE IF NOT EXISTS appointment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            place TEXT NOT NULL,
            userid INTEGER NOT NULL,
            FOREIGN KEY(userid) REFERENCES users(id)
        );
        '''
        conn.execute(query)
        print("Tabla appointment creada exitosamente")
    except Error as e:
        print(e)
    try:
            query = '''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                userid INTEGER NOT NULL,
                FOREIGN KEY(userid) REFERENCES users(id)
            );
            '''
            conn.execute(query)
            print("Tabla history creada exitosamente")
    except Error as e:
            print(e)
    
    try:
        query = '''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            name TEXT NOT NULL,
            frecuency TEXT,
            userid INTEGER NOT NULL,
            FOREIGN KEY(userid) REFERENCES users(id)
        );
        '''
        conn.execute(query)
        print("Tabla reminders creada exitosamente")
    except Error as e:
        print(e)

    try:
        query = '''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            question TEXT NOT NULL,
            answer TEXT,
            userid INTEGER NOT NULL,
            FOREIGN KEY(userid) REFERENCES users(id)
        );
        '''
        conn.execute(query)
        print("Tabla conversations creada exitosamente")
    except Error as e:
        print(e)

def insert_user(conn, name, password, medical_info):
    try:
        query = '''
        INSERT INTO users (name, password, medical_info) VALUES (?, ?, ?);
        '''
        conn.execute(query, (name, password, medical_info))
        conn.commit()
        print("Usuario insertado exitosamente")
    except Error as e:
        print(e)

def get_user(conn, name, password):
    try:
        query = '''
        SELECT * FROM users WHERE name = ? AND password = ?;
        '''
        cursor = conn.execute(query, (name, password))
        user = cursor.fetchone()
        if user:
            return {
                'id': user[0],
                'name': user[1],
                'password': user[2],
                'medical_info': user[3],
                'conversation': user[4]
            }
        else:
            return None
    except Error as e:
        print(e)
        return None

def get_user_id(conn, id):
    try:
        query = '''
        SELECT * FROM users WHERE id = ?;
        '''
        cursor = conn.execute(query, (id))
        user = cursor.fetchone()
        if user:
            return {
                'id': user[0],
                'name': user[1],
                'password': user[2],
                'medical_info': user[3],
                'conversation': user[4]
            }
        else:
            return None
    except Error as e:
        print(e)
        return None

def update_conversation(conn, user_id, conversation):
    try:
        query = '''
        UPDATE users SET conversation = ? WHERE id = ?;
        '''
        conn.execute(query, (conversation, user_id))
        conn.commit()
        print("Conversación actualizada exitosamente")
    except Error as e:
        print(e)

def user_ava(conn, name):
    try:
        query = '''
        SELECT name FROM users WHERE name = ?;
        '''
        result = conn.execute(query, (name,))
        name_ = result.fetchone()[0]
        
        if name_:
            return  name_
        else:
            return None
    except Error as e:
        print(e)
        return None
