"""Testes do UC03 - Manter pets."""
from datetime import date, datetime, time, timedelta

from app.extensions import db
from app.models import Agendamento, Pet
from conftest import texto


def _form_pet(cliente_id, **extra):
    return {"cliente_id": cliente_id, "nome": "Nina", "especie": "GATO", "porte": "PEQUENO",
            "raca": "Siamês", "data_nascimento": "2022-05-10", "observacoes": "", **extra}


def test_cadastrar_pet_vinculado_ao_cliente(admin, dados):
    resposta = admin.post("/pets/novo", data=_form_pet(dados["cliente"].id), follow_redirects=True)
    assert "Pet Nina cadastrado com sucesso!" in texto(resposta)
    pet = db.session.scalar(db.select(Pet).where(Pet.nome == "Nina"))
    assert pet.cliente_id == dados["cliente"].id
    assert pet.especie.value == "Gato"


def test_pet_exige_cliente_existente(admin, dados):
    resposta = admin.post("/pets/novo", data=_form_pet(9999))
    assert "Selecione o tutor" in texto(resposta)
    assert db.session.scalar(db.select(Pet).where(Pet.nome == "Nina")) is None


def test_nao_aceita_data_de_nascimento_futura(admin, dados):
    futura = (date.today() + timedelta(days=10)).isoformat()
    resposta = admin.post("/pets/novo", data=_form_pet(dados["cliente"].id, data_nascimento=futura))
    assert "não pode estar no futuro" in texto(resposta)


def test_listar_e_buscar_pets(admin, dados):
    admin.post("/pets/novo", data=_form_pet(dados["cliente"].id))
    pagina = texto(admin.get("/pets/?q=maria"))  # busca pelo nome do tutor
    assert "Rex" in pagina and "Nina" in pagina


def test_alterar_pet(admin, dados):
    pet_id = dados["pet"].id
    resposta = admin.post(f"/pets/{pet_id}/editar",
                          data=_form_pet(dados["cliente"].id, nome="Rex Junior", especie="CAO", porte="GRANDE"),
                          follow_redirects=True)
    assert "atualizados com sucesso" in texto(resposta)
    db.session.expire_all()
    pet = db.session.get(Pet, pet_id)
    assert pet.nome == "Rex Junior" and pet.porte.value == "Grande"


def test_excluir_pet_sem_agendamentos(admin, dados):
    pet_id = dados["pet"].id
    resposta = admin.post(f"/pets/{pet_id}/excluir", follow_redirects=True)
    assert "excluído com sucesso" in texto(resposta)
    db.session.expire_all()
    assert db.session.get(Pet, pet_id) is None


def test_nao_exclui_pet_com_agendamentos(admin, dados):
    inicio = datetime.combine(date.today() - timedelta(days=1), time(10, 0))
    db.session.add(Agendamento(pet=dados["pet"], servico=dados["servico"], usuario_id=1,
                               data_hora_inicio=inicio, data_hora_fim=inicio + timedelta(hours=1),
                               valor=dados["servico"].preco))
    db.session.commit()
    resposta = admin.post(f"/pets/{dados['pet'].id}/excluir", follow_redirects=True)
    assert "possui agendamentos registrados" in texto(resposta)
    assert db.session.get(Pet, dados["pet"].id) is not None
