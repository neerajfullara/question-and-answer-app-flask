from flask import g
import sqlite3

def connect_db():
    sql = sqlite3.connect('C:/Users/fullara/Documents/Codes/Project/question-and-answer-app-flask/schemas.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db