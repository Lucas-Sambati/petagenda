"""UC02 - Manter clientes (RF03 a RF06)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Cliente
from ..seguranca import login_required
from ..validacoes import somente_digitos, validar_cliente

bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@bp.route("/")
@login_required
def listar():
    """RF04 - Consultar clientes, com busca por nome, CPF ou telefone."""
    termo = (request.args.get("q") or "").strip()
    consulta = db.select(Cliente).order_by(Cliente.nome)
    if termo:
        filtros = [Cliente.nome.ilike(f"%{termo}%")]
        digitos = somente_digitos(termo)
        if digitos:
            filtros += [Cliente.cpf.contains(digitos), Cliente.telefone.contains(digitos)]
        consulta = consulta.where(db.or_(*filtros))
    clientes = db.session.scalars(consulta).all()
    return render_template("clientes/lista.html", clientes=clientes, termo=termo)


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    """RF03 - Cadastrar cliente."""
    erros = {}
    if request.method == "POST":
        dados, erros = validar_cliente(request.form)
        if not erros:
            cliente = Cliente(**dados)
            db.session.add(cliente)
            db.session.commit()
            flash("Cliente cadastrado com sucesso!", "success")
            return redirect(url_for("clientes.detalhe", cliente_id=cliente.id))
        flash("Não foi possível salvar. Corrija os campos destacados.", "danger")
    return render_template("clientes/form.html", cliente=None, valores=request.form, erros=erros)


@bp.route("/<int:cliente_id>")
@login_required
def detalhe(cliente_id):
    """RF04 - Consultar os dados de um cliente e seus pets."""
    cliente = db.get_or_404(Cliente, cliente_id)
    return render_template("clientes/detalhe.html", cliente=cliente)


@bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_required
def editar(cliente_id):
    """RF05 - Alterar os dados do cliente."""
    cliente = db.get_or_404(Cliente, cliente_id)
    erros = {}
    if request.method == "POST":
        dados, erros = validar_cliente(request.form, cliente_id=cliente.id)
        if not erros:
            for campo, valor in dados.items():
                setattr(cliente, campo, valor)
            db.session.commit()
            flash("Dados do cliente atualizados com sucesso!", "success")
            return redirect(url_for("clientes.detalhe", cliente_id=cliente.id))
        flash("Não foi possível salvar. Corrija os campos destacados.", "danger")
        valores = request.form
    else:
        valores = {
            "nome": cliente.nome,
            "cpf": cliente.cpf_formatado,
            "telefone": cliente.telefone_formatado,
            "email": cliente.email or "",
            "endereco": cliente.endereco or "",
        }
    return render_template("clientes/form.html", cliente=cliente, valores=valores, erros=erros)


@bp.route("/<int:cliente_id>/excluir", methods=["POST"])
@login_required
def excluir(cliente_id):
    """RF06 - Excluir cliente (RN08: não exclui cliente que possui pets)."""
    cliente = db.get_or_404(Cliente, cliente_id)
    if cliente.possui_pets():
        flash("Não é possível excluir: este cliente possui pets cadastrados. "
              "Exclua os pets ou transfira-os para outro tutor antes.", "warning")
        return redirect(url_for("clientes.detalhe", cliente_id=cliente.id))
    db.session.delete(cliente)
    db.session.commit()
    flash(f"Cliente {cliente.nome} excluído com sucesso!", "success")
    return redirect(url_for("clientes.listar"))
