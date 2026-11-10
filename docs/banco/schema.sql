-- Modelo físico do banco de dados do PetAgenda (SQLite)
-- Gerado a partir das classes do arquivo app/models.py (SQLAlchemy).
-- As tabelas são criadas automaticamente ao executar a aplicação.

PRAGMA foreign_keys = ON;

CREATE TABLE cliente (
	id INTEGER NOT NULL,
	nome VARCHAR(100) NOT NULL,
	cpf VARCHAR(11) NOT NULL,
	telefone VARCHAR(11) NOT NULL,
	email VARCHAR(120),
	endereco VARCHAR(200),
	criado_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (cpf)
);

CREATE TABLE servico (
	id INTEGER NOT NULL,
	nome VARCHAR(80) NOT NULL,
	descricao VARCHAR(255),
	preco NUMERIC(10, 2) NOT NULL,
	duracao_minutos INTEGER NOT NULL,
	ativo BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (nome)
);

CREATE TABLE usuario (
	id INTEGER NOT NULL,
	nome VARCHAR(100) NOT NULL,
	email VARCHAR(120) NOT NULL,
	senha_hash VARCHAR(255) NOT NULL,
	perfil VARCHAR(20) NOT NULL,
	ativo BOOLEAN NOT NULL,
	criado_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (email),
	CONSTRAINT perfil CHECK (perfil IN ('ADMIN', 'ATENDENTE'))
);

CREATE TABLE pet (
	id INTEGER NOT NULL,
	cliente_id INTEGER NOT NULL,
	nome VARCHAR(60) NOT NULL,
	especie VARCHAR(20) NOT NULL,
	raca VARCHAR(60),
	porte VARCHAR(20) NOT NULL,
	data_nascimento DATE,
	observacoes TEXT,
	criado_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(cliente_id) REFERENCES cliente (id) ON DELETE RESTRICT,
	CONSTRAINT especie CHECK (especie IN ('CAO', 'GATO', 'OUTRO')),
	CONSTRAINT porte CHECK (porte IN ('PEQUENO', 'MEDIO', 'GRANDE'))
);
CREATE INDEX ix_pet_cliente_id ON pet (cliente_id);

CREATE TABLE agendamento (
	id INTEGER NOT NULL,
	pet_id INTEGER NOT NULL,
	servico_id INTEGER NOT NULL,
	usuario_id INTEGER NOT NULL,
	data_hora_inicio DATETIME NOT NULL,
	data_hora_fim DATETIME NOT NULL,
	valor NUMERIC(10, 2) NOT NULL,
	status VARCHAR(20) NOT NULL,
	observacoes TEXT,
	criado_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(pet_id) REFERENCES pet (id) ON DELETE RESTRICT,
	FOREIGN KEY(servico_id) REFERENCES servico (id) ON DELETE RESTRICT,
	FOREIGN KEY(usuario_id) REFERENCES usuario (id) ON DELETE RESTRICT,
	CONSTRAINT statusagendamento CHECK (status IN ('AGENDADO', 'CONCLUIDO', 'CANCELADO'))
);
CREATE INDEX ix_agendamento_data_hora_inicio ON agendamento (data_hora_inicio);
CREATE INDEX ix_agendamento_pet_id ON agendamento (pet_id);
CREATE INDEX ix_agendamento_servico_id ON agendamento (servico_id);
CREATE INDEX ix_agendamento_usuario_id ON agendamento (usuario_id);
