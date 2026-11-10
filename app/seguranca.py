"""Autenticação, controle de acesso por perfil e proteção CSRF (RNF01 a RNF03)."""
import secrets
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from .extensions import db
from .models import Usuario


def gerar_csrf_token():
    """Gera (uma vez por sessão) o token que acompanha todos os formulários."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


def init_seguranca(app):
    app.jinja_env.globals["csrf_token"] = gerar_csrf_token

    @app.before_request
    def carregar_usuario_logado():
        """Disponibiliza o usuário logado em ``g.usuario`` para views e templates."""
        usuario_id = session.get("usuario_id")
        usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
        g.usuario = usuario if usuario is not None and usuario.ativo else None

    @app.before_request
    def proteger_contra_csrf():
        if not app.config.get("CSRF_ENABLED", True) or request.method != "POST":
            return
        token_sessao = session.get("_csrf_token", "")
        token_form = request.form.get("csrf_token", "")
        if not token_sessao or not secrets.compare_digest(token_sessao, token_form):
            abort(400, description="Sua sessão expirou. Recarregue a página e tente novamente.")


def login_required(view):
    """Permite o acesso apenas a usuários autenticados (RNF02)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.get("usuario") is None:
            if request.path != "/":
                flash("Faça login para acessar o sistema.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    """Permite o acesso apenas ao perfil Administrador (RN10)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.get("usuario") is None:
            flash("Faça login para acessar o sistema.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        if not g.usuario.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper
