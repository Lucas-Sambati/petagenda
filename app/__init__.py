"""Pacote principal do PetAgenda (aplicação Flask).

A função ``create_app`` monta a aplicação: carrega as configurações, conecta
o banco de dados, registra as rotas (blueprints) e cria as tabelas.
"""
import os
import sqlite3

import click
from flask import Flask, render_template
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config

from .extensions import db


@event.listens_for(Engine, "connect")
def _ativar_chaves_estrangeiras(conexao, _registro):
    """O SQLite só aplica as FOREIGN KEYs com este PRAGMA ativado (RNF06)."""
    if isinstance(conexao, sqlite3.Connection):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from .filtros import registrar_filtros
    from .seguranca import init_seguranca
    init_seguranca(app)
    registrar_filtros(app)

    # Controllers: um blueprint para cada caso de uso.
    from .routes import agendamentos, auth, clientes, main, pets, servicos
    app.register_blueprint(auth.bp)          # UC01 - Autenticar usuário
    app.register_blueprint(main.bp)          # Painel inicial
    app.register_blueprint(clientes.bp)      # UC02 - Manter clientes
    app.register_blueprint(pets.bp)          # UC03 - Manter pets
    app.register_blueprint(servicos.bp)      # UC04 - Manter serviços
    app.register_blueprint(agendamentos.bp)  # UC05 - Manter agendamentos

    registrar_paginas_de_erro(app)
    registrar_comandos(app)

    with app.app_context():
        db.create_all()
        if app.config.get("SEED_AUTOMATICO"):
            from .seed import popular_banco
            popular_banco()

    return app


def registrar_paginas_de_erro(app):
    @app.errorhandler(400)
    def requisicao_invalida(erro):
        return render_template("erro.html", codigo=400, titulo="Requisição inválida",
                               mensagem=erro.description), 400

    @app.errorhandler(403)
    def acesso_negado(_erro):
        return render_template("erro.html", codigo=403, titulo="Acesso negado",
                               mensagem="Esta funcionalidade é restrita ao perfil Administrador."), 403

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("erro.html", codigo=404, titulo="Página não encontrada",
                               mensagem="O registro ou a página que você procurou não existe."), 404


def registrar_comandos(app):
    from .models import Perfil, Usuario
    from .seed import popular_banco

    @app.cli.command("reset-db")
    def reset_db():
        """Apaga e recria o banco com os dados de exemplo."""
        db.drop_all()
        db.create_all()
        popular_banco(forcar=True)
        click.echo("Banco de dados recriado com os dados de exemplo.")

    @app.cli.command("banco")
    def mostrar_banco():
        """Mostra o conteúdo do banco SQLite usando consultas SQL."""
        click.echo(f"Banco de dados: {db.engine.url.database}\n")
        click.echo("SELECT COUNT(*) FROM <tabela>;")
        for tabela in ("usuario", "cliente", "pet", "servico", "agendamento"):
            total = db.session.execute(db.text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
            click.echo(f"  {tabela:<12} {total:>3} registro(s)")

        sql = ("SELECT a.id, a.data_hora_inicio, p.nome AS pet, c.nome AS tutor,\n"
               "       s.nome AS servico, a.valor, a.status\n"
               "  FROM agendamento a\n"
               "  JOIN pet p ON p.id = a.pet_id\n"
               "  JOIN cliente c ON c.id = p.cliente_id\n"
               "  JOIN servico s ON s.id = a.servico_id\n"
               " ORDER BY a.id DESC LIMIT 5")
        click.echo(f"\n{sql};\n")
        click.echo(f"  {'ID':<4}{'INÍCIO':<18}{'PET':<8}{'TUTOR':<18}{'SERVIÇO':<24}{'VALOR':>8}  STATUS")
        for linha in db.session.execute(db.text(sql)):
            inicio = str(linha.data_hora_inicio)[:16]
            click.echo(f"  {linha.id:<4}{inicio:<18}{linha.pet:<8}{linha.tutor:<18}"
                       f"{linha.servico:<24}{float(linha.valor):>8.2f}  {linha.status}")

    @app.cli.command("criar-usuario")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--senha", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--perfil", type=click.Choice(["ADMIN", "ATENDENTE"]), default="ATENDENTE")
    def criar_usuario(nome, email, senha, perfil):
        """Cria um usuário de acesso ao sistema."""
        usuario = Usuario(nome=nome, email=email.strip().lower(), perfil=Perfil[perfil])
        usuario.definir_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuário {usuario.email} criado com o perfil {usuario.perfil.value}.")
