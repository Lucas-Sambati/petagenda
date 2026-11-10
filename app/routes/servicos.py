"""UC04 - Manter serviços (RF11 a RF14). Alterações restritas ao Administrador (RN10)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Servico
from ..seguranca import admin_required, login_required
from ..validacoes import validar_servico

bp = Blueprint("servicos", __name__, url_prefix="/servicos")


@bp.route("/")
@login_required
def listar():
    """RF12 - Consultar serviços (disponível para todos os perfis)."""
    servicos = db.session.scalars(
        db.select(Servico).order_by(Servico.ativo.desc(), Servico.nome)
    ).all()
    return render_template("servicos/lista.html", servicos=servicos)


@bp.route("/novo", methods=["GET", "POST"])
@admin_required
def novo():
    """RF11 - Cadastrar serviço."""
    erros = {}
    valores = request.form if request.method == "POST" else {"ativo": "on"}
    if request.method == "POST":
        dados, erros = validar_servico(request.form)
        if not erros:
            servico = Servico(**dados)
            db.session.add(servico)
            db.session.commit()
            flash(f"Serviço {servico.nome} cadastrado com sucesso!", "success")
            return redirect(url_for("servicos.listar"))
        flash("Não foi possível salvar. Corrija os campos destacados.", "danger")
    return render_template("servicos/form.html", servico=None, valores=valores, erros=erros)


@bp.route("/<int:servico_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(servico_id):
    """RF13 - Alterar serviço (preço, duração, situação)."""
    servico = db.get_or_404(Servico, servico_id)
    erros = {}
    if request.method == "POST":
        dados, erros = validar_servico(request.form, servico_id=servico.id)
        if not erros:
            for campo, valor in dados.items():
                setattr(servico, campo, valor)
            db.session.commit()
            flash(f"Serviço {servico.nome} atualizado com sucesso!", "success")
            return redirect(url_for("servicos.listar"))
        flash("Não foi possível salvar. Corrija os campos destacados.", "danger")
        valores = request.form
    else:
        valores = {
            "nome": servico.nome,
            "descricao": servico.descricao or "",
            "preco": f"{servico.preco:.2f}",
            "duracao_minutos": servico.duracao_minutos,
            "ativo": "on" if servico.ativo else "",
        }
    return render_template("servicos/form.html", servico=servico, valores=valores, erros=erros)


@bp.route("/<int:servico_id>/excluir", methods=["POST"])
@admin_required
def excluir(servico_id):
    """RF14 - Excluir serviço (RN09: com agendamentos, apenas inativar)."""
    servico = db.get_or_404(Servico, servico_id)
    if servico.possui_agendamentos():
        flash("Não é possível excluir: o serviço já foi usado em agendamentos. "
              "Edite o serviço e desmarque a opção \"Ativo\" para retirá-lo da agenda.", "warning")
        return redirect(url_for("servicos.listar"))
    db.session.delete(servico)
    db.session.commit()
    flash(f"Serviço {servico.nome} excluído com sucesso!", "success")
    return redirect(url_for("servicos.listar"))
