"""UC03 - Manter pets (RF07 a RF10)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Cliente, Especie, Pet, Porte
from ..seguranca import login_required
from ..validacoes import validar_pet

bp = Blueprint("pets", __name__, url_prefix="/pets")


def _contexto_formulario():
    """Opções (valor, texto) dos campos de seleção do formulário."""
    clientes = db.session.scalars(db.select(Cliente).order_by(Cliente.nome)).all()
    return {
        "opcoes_clientes": [(c.id, f"{c.nome} — CPF {c.cpf_formatado}") for c in clientes],
        "opcoes_especies": [(e.name, e.value) for e in Especie],
        "opcoes_portes": [(p.name, p.value) for p in Porte],
    }


@bp.route("/")
@login_required
def listar():
    """RF08 - Consultar pets, com busca pelo nome do pet ou do tutor."""
    termo = (request.args.get("q") or "").strip()
    consulta = db.select(Pet).join(Pet.cliente).order_by(Pet.nome)
    if termo:
        consulta = consulta.where(db.or_(Pet.nome.ilike(f"%{termo}%"),
                                         Cliente.nome.ilike(f"%{termo}%")))
    pets = db.session.scalars(consulta).all()
    return render_template("pets/lista.html", pets=pets, termo=termo)


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    """RF07 - Cadastrar pet vinculado a um cliente (RN02)."""
    erros = {}
    valores = request.form if request.method == "POST" else {"cliente_id": request.args.get("cliente_id", "")}
    if request.method == "POST":
        dados, erros = validar_pet(request.form)
        if not erros:
            pet = Pet(**dados)
            db.session.add(pet)
            db.session.commit()
            flash(f"Pet {pet.nome} cadastrado com sucesso!", "success")
            return redirect(url_for("clientes.detalhe", cliente_id=pet.cliente_id))
        flash("Não foi possível salvar. Corrija os campos destacados.", "danger")
    return render_template("pets/form.html", pet=None, valores=valores, erros=erros,
                           **_contexto_formulario())


@bp.route("/<int:pet_id>/editar", methods=["GET", "POST"])
@login_required
def editar(pet_id):
    """RF09 - Alterar os dados do pet."""
    pet = db.get_or_404(Pet, pet_id)
    erros = {}
    if request.method == "POST":
        dados, erros = validar_pet(request.form)
        if not erros:
            for campo, valor in dados.items():
                setattr(pet, campo, valor)
            db.session.commit()
            flash(f"Dados do pet {pet.nome} atualizados com sucesso!", "success")
            return redirect(url_for("pets.listar"))
        flash("Não foi possível salvar. Corrija os campos destacados.", "danger")
        valores = request.form
    else:
        valores = {
            "cliente_id": pet.cliente_id,
            "nome": pet.nome,
            "especie": pet.especie.name,
            "raca": pet.raca or "",
            "porte": pet.porte.name,
            "data_nascimento": pet.data_nascimento.isoformat() if pet.data_nascimento else "",
            "observacoes": pet.observacoes or "",
        }
    return render_template("pets/form.html", pet=pet, valores=valores, erros=erros,
                           **_contexto_formulario())


@bp.route("/<int:pet_id>/excluir", methods=["POST"])
@login_required
def excluir(pet_id):
    """RF10 - Excluir pet (RN08: não exclui pet com agendamentos)."""
    pet = db.get_or_404(Pet, pet_id)
    if pet.possui_agendamentos():
        flash("Não é possível excluir: este pet possui agendamentos registrados "
              "(o histórico de atendimentos deve ser preservado).", "warning")
        return redirect(url_for("pets.listar"))
    db.session.delete(pet)
    db.session.commit()
    flash(f"Pet {pet.nome} excluído com sucesso!", "success")
    return redirect(url_for("pets.listar"))
