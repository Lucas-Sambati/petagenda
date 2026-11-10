"""Filtros Jinja para exibir valores no padrão brasileiro."""
from datetime import date

DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
               "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def data_extenso(valor):
    """date(2026, 11, 9) -> 'segunda-feira, 9 de novembro de 2026'"""
    return f"{DIAS_SEMANA[valor.weekday()]}, {valor.day} de {MESES[valor.month - 1]} de {valor.year}"


def hoje_por_extenso():
    return "Hoje é " + data_extenso(date.today())


def hoje_iso():
    return date.today().isoformat()


def moeda(valor):
    """1234.5 -> 'R$ 1.234,50'"""
    if valor is None:
        return "—"
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def data_br(valor):
    return valor.strftime("%d/%m/%Y") if valor else "—"


def data_hora_br(valor):
    return valor.strftime("%d/%m/%Y %H:%M") if valor else "—"


def hora(valor):
    return valor.strftime("%H:%M") if valor else "—"


def duracao(minutos):
    """90 -> '1h30'"""
    if not minutos:
        return "—"
    horas, resto = divmod(int(minutos), 60)
    if horas and resto:
        return f"{horas}h{resto:02d}"
    return f"{horas}h" if horas else f"{resto} min"


def registrar_filtros(app):
    app.add_template_global(hoje_por_extenso)
    app.add_template_global(hoje_iso)
    app.add_template_filter(data_extenso)
    app.add_template_filter(moeda)
    app.add_template_filter(data_br)
    app.add_template_filter(data_hora_br)
    app.add_template_filter(hora)
    app.add_template_filter(duracao)
