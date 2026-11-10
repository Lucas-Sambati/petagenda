"""UC01 - Autenticar usuário (RF01 e RF02)."""
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Usuario

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """RF01 - Autenticar o usuário com e-mail e senha."""
    if g.usuario:
        return redirect(url_for("main.painel"))

    email = ""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""
        usuario = db.session.scalar(db.select(Usuario).where(Usuario.email == email))

        if usuario is None or not usuario.ativo or not usuario.verificar_senha(senha):
            flash("E-mail ou senha inválidos.", "danger")
        else:
            session.clear()  # evita reaproveitar uma sessão anterior
            session["usuario_id"] = usuario.id
            flash(f"Bem-vindo(a), {usuario.nome}!", "success")
            destino = request.args.get("next", "")
            if not destino.startswith("/") or destino.startswith("//"):
                destino = url_for("main.painel")
            return redirect(destino)

    return render_template("auth/login.html", email=email)


@bp.route("/logout", methods=["POST"])
def logout():
    """RF02 - Encerrar a sessão do usuário."""
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))
