"""Extensões compartilhadas pela aplicação."""
from flask_sqlalchemy import SQLAlchemy

# Objeto do ORM (SQLAlchemy) que faz a ponte entre as classes Python e o banco.
db = SQLAlchemy()
