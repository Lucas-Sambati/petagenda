"""Ponto de entrada do PetAgenda.

Como executar:
    python run.py

Depois, acesse no navegador: http://127.0.0.1:5000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
