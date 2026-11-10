"""Configurações do PetAgenda.

As configurações ficam em classes para facilitar a troca entre o ambiente
de desenvolvimento (Config) e o ambiente de testes automatizados (TestConfig).
"""
import os
from datetime import time


class Config:
    # Chave usada pelo Flask para assinar o cookie de sessão (login).
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-petagenda-troque-esta-chave")

    # Banco SQLite salvo em arquivo na pasta instance/ do projeto.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///petagenda.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Proteção contra CSRF nos formulários (RNF03).
    CSRF_ENABLED = True

    # Popula o banco com dados de exemplo na primeira execução.
    SEED_AUTOMATICO = True

    # Mostra os usuários de demonstração na tela de login (desligar em produção).
    EXIBIR_ACESSO_DEMO = True

    # Regras de funcionamento do pet shop (RN05).
    HORA_ABERTURA = time(8, 0)
    HORA_FECHAMENTO = time(18, 0)
    DIAS_FUNCIONAMENTO = {0, 1, 2, 3, 4, 5}  # segunda (0) a sábado (5)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CSRF_ENABLED = False
    SEED_AUTOMATICO = False
