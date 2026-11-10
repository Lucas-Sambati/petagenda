"""UC05 - Manter agendamentos (RF15 a RF19)."""
from datetime import date, datetime, time, timedelta

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Agendamento, Pet, Servico, StatusAgendamento
from ..seguranca import login_required
from ..validacoes import enum_por_nome, para_data, validar_agendamento

bp = Blueprint("agendamentos", __name__, url_prefix="/agendamentos")


def _contexto_formulario():
    """Listas usadas nos campos de seleção do formulário."""
    return {
        "pets": db.session.scalars(db.select(Pet).order_by(Pet.nome)).all(),
        "servicos": db.session.scalars(
            db.select(Servico).where(Servico.ativo.is_(True)).order_by(Servico.nome)
        ).all(),
        "hoje": date.today().isoformat(),
    }


def _url_agenda_do_dia(agendamento):
    return url_for("agendamentos.listar", data=agendamento.data_hora_inicio.date().isoformat())


@bp.route("/")
@login_required
def listar():
    """RF16 - Consultar a agenda, com filtros por data e por status."""
    data_filtro = para_data(request.args.get("data"))
    status_filtro = enum_por_nome(StatusAgendamento, request.args.get("status"))
    historico = request.args.get("historico") == "1"

    consulta = db.select(Agendamento).order_by(Agendamento.data_hora_inicio)
    if data_filtro:
        inicio_dia = datetime.combine(data_filtro, time.min)
        consulta = consulta.where(Agendamento.data_hora_inicio >= inicio_dia,
                                  Agendamento.data_hora_inicio < inicio_dia + timedelta(days=1))
    elif not historico:  # padrão: de hoje em diante
        consulta = consulta.where(Agendamento.data_hora_inicio >= datetime.combine(date.today(), time.min))
    if status_filtro:
        consulta = consulta.where(Agendamento.status == status_filtro)

    agendamentos = db.session.scalars(consulta).all()
    return render_template("agendamentos/lista.html", agendamentos=agendamentos,
                           data_filtro=data_filtro, status_filtro=status_filtro,
                           historico=historico, status_opcoes=list(StatusAgendamento))


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    """RF15 - Cadastrar agendamento (RN03, RN04, RN05, RN06 e RN09)."""
    erros = {}
    valores = request.form if request.method == "POST" else {"pet_id": request.args.get("pet_id", "")}
    if request.method == "POST":
        dados, erros = validar_agendamento(request.form)
        if not erros:
            servico = dados["servico"]
            agendamento = Agendamento(
                pet=dados["pet"],
                servico=servico,
                usuario=g.usuario,
                data_hora_inicio=dados["inicio"],
                data_hora_fim=dados["fim"],
                valor=servico.preco,  # RN06: preço vigente no momento do agendamento
                observacoes=dados["observacoes"],
            )
            db.session.add(agendamento)
            db.session.commit()
            flash(f"Agendamento confirmado: {agendamento.pet.nome} em "
                  f"{agendamento.data_hora_inicio:%d/%m/%Y} às {agendamento.data_hora_inicio:%H:%M}.", "success")
            return redirect(_url_agenda_do_dia(agendamento))
        flash("Não foi possível agendar. Verifique os campos destacados.", "danger")
    return render_template("agendamentos/form.html", agendamento=None, valores=valores, erros=erros,
                           **_contexto_formulario())


@bp.route("/<int:agendamento_id>/editar", methods=["GET", "POST"])
@login_required
def editar(agendamento_id):
    """RF17 - Alterar (remarcar) agendamento (RN07)."""
    agendamento = db.get_or_404(Agendamento, agendamento_id)
    if not agendamento.pode_alterar():
        flash("Somente agendamentos com status Agendado podem ser alterados.", "warning")
        return redirect(_url_agenda_do_dia(agendamento))

    erros = {}
    if request.method == "POST":
        dados, erros = validar_agendamento(request.form, agendamento_id=agendamento.id)
        if not erros:
            if dados["servico"].id != agendamento.servico_id:
                agendamento.valor = dados["servico"].preco  # trocou o serviço: vale o novo preço
            agendamento.pet = dados["pet"]
            agendamento.servico = dados["servico"]
            agendamento.data_hora_inicio = dados["inicio"]
            agendamento.data_hora_fim = dados["fim"]
            agendamento.observacoes = dados["observacoes"]
            db.session.commit()
            flash("Agendamento alterado com sucesso!", "success")
            return redirect(_url_agenda_do_dia(agendamento))
        flash("Não foi possível salvar. Verifique os campos destacados.", "danger")
        valores = request.form
    else:
        valores = {
            "pet_id": agendamento.pet_id,
            "servico_id": agendamento.servico_id,
            "data": agendamento.data_hora_inicio.date().isoformat(),
            "hora": agendamento.data_hora_inicio.strftime("%H:%M"),
            "observacoes": agendamento.observacoes or "",
        }
    return render_template("agendamentos/form.html", agendamento=agendamento, valores=valores,
                           erros=erros, **_contexto_formulario())


@bp.route("/<int:agendamento_id>/status", methods=["POST"])
@login_required
def alterar_status(agendamento_id):
    """RF18 - Concluir ou cancelar um agendamento (RN07)."""
    agendamento = db.get_or_404(Agendamento, agendamento_id)
    acao = request.form.get("acao")
    if acao not in ("concluir", "cancelar"):
        abort(400)
    try:
        if acao == "concluir":
            agendamento.concluir()
            mensagem = f"Atendimento de {agendamento.pet.nome} marcado como concluído."
        else:
            agendamento.cancelar()
            mensagem = f"Agendamento de {agendamento.pet.nome} cancelado. O horário foi liberado."
        db.session.commit()
        flash(mensagem, "success")
    except ValueError as erro:
        flash(str(erro), "warning")

    if request.form.get("voltar") == "painel":
        return redirect(url_for("main.painel"))
    return redirect(_url_agenda_do_dia(agendamento))


@bp.route("/<int:agendamento_id>/excluir", methods=["POST"])
@login_required
def excluir(agendamento_id):
    """RF19 - Excluir agendamento."""
    agendamento = db.get_or_404(Agendamento, agendamento_id)
    destino = _url_agenda_do_dia(agendamento)
    db.session.delete(agendamento)
    db.session.commit()
    flash("Agendamento excluído com sucesso!", "success")
    return redirect(destino)
