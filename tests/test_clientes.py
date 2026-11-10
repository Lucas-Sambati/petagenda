"""Testes do UC02 - Manter clientes."""
from app.extensions import db
from app.models import Cliente
from app.validacoes import cpf_valido
from conftest import texto

NOVO_CLIENTE = {
    "nome": "Fernanda Lima",
    "cpf": "987.654.321-00",
    "telefone": "(43) 98888-7777",
    "email": "fernanda@example.com",
    "endereco": "Rua Pará, 300 - Londrina/PR",
}


def _contar_clientes():
    return db.session.scalar(db.select(db.func.count(Cliente.id)))


def test_regra_de_validacao_do_cpf():
    assert cpf_valido("529.982.247-25")
    assert cpf_valido("11144477735")
    assert not cpf_valido("529.982.247-26")
    assert not cpf_valido("111.111.111-11")
    assert not cpf_valido("123")


def test_cadastrar_cliente(admin):
    resposta = admin.post("/clientes/novo", data=NOVO_CLIENTE, follow_redirects=True)
    assert "Cliente cadastrado com sucesso!" in texto(resposta)
    cliente = db.session.scalar(db.select(Cliente).where(Cliente.cpf == "98765432100"))
    assert cliente.nome == "Fernanda Lima"
    assert cliente.telefone == "43988887777"


def test_nao_cadastra_cliente_com_cpf_invalido(admin):
    resposta = admin.post("/clientes/novo", data={**NOVO_CLIENTE, "cpf": "123.456.789-00"})
    assert "CPF inválido" in texto(resposta)
    assert _contar_clientes() == 0


def test_nao_cadastra_cliente_com_cpf_duplicado(admin, dados):
    resposta = admin.post("/clientes/novo", data={**NOVO_CLIENTE, "cpf": "529.982.247-25"})
    assert "Já existe um cliente cadastrado com este CPF." in texto(resposta)
    assert _contar_clientes() == 1


def test_campos_obrigatorios(admin):
    resposta = admin.post("/clientes/novo", data={"nome": "", "cpf": "", "telefone": ""})
    pagina = texto(resposta)
    assert "Informe o nome completo" in pagina
    assert "Informe o telefone com DDD" in pagina
    assert _contar_clientes() == 0


def test_listar_e_buscar_clientes(admin, dados):
    admin.post("/clientes/novo", data=NOVO_CLIENTE)
    assert "Fernanda Lima" in texto(admin.get("/clientes/"))
    busca_nome = texto(admin.get("/clientes/?q=fernanda"))
    assert "Fernanda Lima" in busca_nome and "Maria Teste" not in busca_nome
    assert "Maria Teste" in texto(admin.get("/clientes/?q=529.982"))


def test_alterar_cliente(admin, dados):
    cliente_id = dados["cliente"].id
    resposta = admin.post(f"/clientes/{cliente_id}/editar",
                          data={**NOVO_CLIENTE, "cpf": "529.982.247-25", "nome": "Maria Alterada"},
                          follow_redirects=True)
    assert "atualizados com sucesso" in texto(resposta)
    db.session.expire_all()
    assert db.session.get(Cliente, cliente_id).nome == "Maria Alterada"


def test_excluir_cliente_sem_pets(admin):
    admin.post("/clientes/novo", data=NOVO_CLIENTE)
    cliente = db.session.scalar(db.select(Cliente))
    resposta = admin.post(f"/clientes/{cliente.id}/excluir", follow_redirects=True)
    assert "excluído com sucesso" in texto(resposta)
    assert _contar_clientes() == 0


def test_nao_exclui_cliente_com_pets(admin, dados):
    resposta = admin.post(f"/clientes/{dados['cliente'].id}/excluir", follow_redirects=True)
    assert "possui pets cadastrados" in texto(resposta)
    assert _contar_clientes() == 1
