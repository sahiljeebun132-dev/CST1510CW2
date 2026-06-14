"""
cli.py
------
Command-line authentication tool (CW2 Videos 02 & 03).

This reproduces the original terminal menu from the video series — Register,
Log in, Exit in a `while True` loop — but backed by the SQLite database and the
canonical functions in app_model (create_user_table, add_user, get_user) rather
than a flat users.txt file. It's handy for the code walkthrough in your demo
video, showing the journey from CLI to the Streamlit web app.

Run:
    python cli.py
"""

from app_model import db, security
from app_model import users as users_model


def register_user(conn):
    name = input('Enter your name: > ')
    password = input('Enter your password: > ')
    if users_model.get_user(conn, name) is not None:
        print('That username is already taken.')
        return
    hash_password = security.generate_hash(password)
    users_model.add_user(conn, name, hash_password)
    print('User successfully registered!')


def login_user(conn):
    name = input('Enter your name: > ')
    password = input('Enter your password: > ')
    user = users_model.get_user(conn, name)
    if user is not None and security.is_valid_hash(password, user['password_hash']):
        return True
    return False


def main():
    conn = db.get_connection()
    users_model.create_user_table(conn)
    while True:
        print('\n1. To Register\n2. To Log in\n3. To Exit')
        choice = input(': > ')
        if choice == '1':
            register_user(conn)
        elif choice == '2':
            print('Login successful!' if login_user(conn) else 'Incorrect login.')
        elif choice == '3':
            print('Goodbye!')
            break
        else:
            print('Please choose 1, 2 or 3.')


if __name__ == '__main__':
    main()
