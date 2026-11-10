// Comportamentos simples de interface do PetAgenda.

// Pede confirmação antes de enviar formulários de exclusão/cancelamento.
document.querySelectorAll("form[data-confirmar]").forEach((form) => {
  form.addEventListener("submit", (evento) => {
    if (!window.confirm(form.dataset.confirmar)) {
      evento.preventDefault();
    }
  });
});

// Máscaras de digitação para CPF e telefone.
const mascaras = {
  cpf: (valor) => valor.replace(/\D/g, "").slice(0, 11)
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2"),
  telefone: (valor) => {
    const digitos = valor.replace(/\D/g, "").slice(0, 11);
    if (digitos.length <= 10) {
      return digitos.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{4})(\d)/, "$1-$2");
    }
    return digitos.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{5})(\d)/, "$1-$2");
  },
};

document.querySelectorAll("input[data-mascara]").forEach((campo) => {
  const aplicar = mascaras[campo.dataset.mascara];
  if (aplicar) {
    campo.addEventListener("input", () => { campo.value = aplicar(campo.value); });
  }
});
