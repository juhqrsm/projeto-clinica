DROP DATABASE IF EXISTS clinica;
CREATE DATABASE clinica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE clinica;

-- 1. ESTRUTURA DAS TABELAS

CREATE TABLE usuario (
  id_usuario INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome       VARCHAR(80)  NOT NULL,
  email      VARCHAR(120) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  perfil     ENUM('admin','recepcao') NOT NULL DEFAULT 'recepcao',
  criado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_usuario),
  UNIQUE KEY uq_usuario_email (email)
) ENGINE = InnoDB;

CREATE TABLE paciente (
  id_paciente      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome             VARCHAR(100) NOT NULL,
  cpf_cripto       VARCHAR(255) NOT NULL,
  cpf_hash         CHAR(64)     NOT NULL,
  data_nascimento  DATE         NOT NULL,
  telefone_cripto  VARCHAR(255) NOT NULL,
  email            VARCHAR(120) NULL,
  consentimento_em DATETIME     NOT NULL,
  criado_em        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_paciente),
  UNIQUE KEY uq_paciente_cpf (cpf_hash),
  INDEX idx_paciente_nome (nome)
) ENGINE = InnoDB;

CREATE TABLE medico (
  id_medico     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome          VARCHAR(100) NOT NULL,
  crm           VARCHAR(20)  NOT NULL,
  especialidade VARCHAR(60)  NOT NULL,
  email         VARCHAR(120) NULL,
  PRIMARY KEY (id_medico),
  UNIQUE KEY uq_medico_crm (crm)
) ENGINE = InnoDB;

CREATE TABLE agendamento (
  id_agendamento INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_paciente    INT UNSIGNED NOT NULL,
  id_medico      INT UNSIGNED NOT NULL,
  data_consulta  DATE         NOT NULL,
  hora_consulta  TIME         NOT NULL,
  status         ENUM('agendada','realizada','cancelada') NOT NULL DEFAULT 'agendada',
  observacao     VARCHAR(255) NULL,
  criado_por     INT UNSIGNED NOT NULL,
  criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_agendamento),
  UNIQUE KEY uq_medico_horario (id_medico, data_consulta, hora_consulta),
  INDEX idx_agenda_data (data_consulta, hora_consulta),
  CONSTRAINT fk_agenda_paciente FOREIGN KEY (id_paciente) REFERENCES paciente (id_paciente),
  CONSTRAINT fk_agenda_medico   FOREIGN KEY (id_medico)   REFERENCES medico (id_medico),
  CONSTRAINT fk_agenda_usuario  FOREIGN KEY (criado_por)  REFERENCES usuario (id_usuario)
) ENGINE = InnoDB;

-- 2. CARGA INICIAL DE DADOS VALIDOS

-- Usuários de teste (Senhas: Recepcao@2026 e Admin@2026)
INSERT INTO usuario (nome, email, senha_hash, perfil) VALUES
  ('Carla Mendes', 'carla@clinicavida.com',
   'scrypt:32768:8:1$3B5t8JrOJqBhdyl3$8e1f364d2189bd059965223f922235d5153b94b87867f64d0bb7acc37c07058bf449629141409983ed953479a81b499ddc727f1019704ce49cdae9759d821ebb', 'recepcao'),
  ('Rafael Lima', 'rafael@clinicavida.com',
   'scrypt:32768:8:1$ryyLI4SBKBJXWZ4h$f328c05bab9099f1ed511cb10fcb6bcd04f45cd5b1283b4343e21910f9836f7baa31d93f9fefb7adac48a33003af89ce03964b7acac859bdc1eb032e03d3d1eb', 'admin'),
  ('Juliana Rocha', 'juliana@clinicavida.com',
   'scrypt:32768:8:1$4Pdd21agCk5tQXLt$d50460ec54ccf3ad748186b4b97b4498e2f473294b2f74d897dd823d3b99eaaa5582166b703e885a32dddb7f48bb44068c01a469b773a000abaa28d8841ca8d9', 'recepcao');

-- Pacientes criptografados com as chaves do .env ativo
INSERT INTO paciente (nome, cpf_cripto, cpf_hash, data_nascimento, telefone_cripto, email, consentimento_em) VALUES
  ('Ana Beatriz Souza',
   'gAAAAABqxEsfXQ7qBKHZRXCKHBiq4BsTWwde1EBQyFONQ85cNtpmjoQG703pEh-CJ4iBtgOUCNLh8XaIBpgbtC_tkfb9mniqnA==',
   '292f69455b1c1a84dac1b603b70f4cc087709a70ef210a427be82a8b9d03a3c4',
   '1990-04-12', 'gAAAAABqxEsfBC90rM_AIk1tbeg4zkL5VQanS6pexOhBJg_V4J1qFwfpaX7CVnuIJLsePC-H3se4-JDsEopYruM8ZOT6GHEKyA==',
   'ana.souza@email.com', '2026-09-01 09:00:00'),
  ('Bruno Henrique Lima',
   'gAAAAABqxEsfOsIeqvav41QzgJ_Y2NavaHjyAN4IrnxpJcxcF5Wk-x6ydusL3_iKYqR0zB2HhZ7tUDrM0ONhZSlT3QQo--VyVQ==',
   '3a76cd9807054d6a10fb12a31aa940f7c4a959aa1ee3a4e69c274cf65b9a11a1',
   '1985-09-30', 'gAAAAABqxEsfWLqeHSpcVu33O3o51njYosXPAuGLmwQ0wFlQzEGlZxxa9wGJLv1lk3aTW0hGgfis1S1MGjADsSXPV_21RwJKcQ==',
   NULL, '2026-09-02 09:00:00'),
  ('Carlos Eduardo Silva',
   'gAAAAABqxEsf4jAF0d5WccRG9jXZvm6nJrB9MPJu6d9KJH0HjKICDxQxc5j69zs78Q_R2CqxkV0nrYnFWlJd74dEcHnhBEUc4Q==',
   '1e97a512eb16da3e4d964c3a87e3738c8ab295dff5ec99489eabfa97fec7e52a',
   '1972-01-18', 'gAAAAABqxEsf0ZxVQqoGEX9UC_ZKkhTBJ1tfNrGdtg19fLoEbcUN1HphDK5wo1vzUH4gCAN6SvCKnmPUIJ1LFeaNU0gzKz_Dxg==',
   'carlos.silva@email.com', '2026-09-03 09:00:00'),
  ('Daniela Silva Costa',
   'gAAAAABqxEsfaVk89fNa_rDbwjiJolLmnvCbUECipudtaK7e1S-NiAKvqbfG2HXdSpMYJcMbkb6JjMk8o6z39WdfZHbbjF4kig==',
   '8af2675f452db3e1a6cba4792153927eecb7c43c125ca9899ec5c13fa0aa4638',
   '2001-11-05', 'gAAAAABqxEsfz2EqPPXjRhjUajUXI50WPbjMXv_gnR1GWnC25oJeT35xSKGrBgWsTNsCUrwLDrjaF1AvIOaOtgamOYe8pdHpPg==',
   'dani.costa@email.com', '2026-09-04 09:00:00');

-- Corpo clínico
INSERT INTO medico (nome, crm, especialidade, email) VALUES
  ('Dr. Marcos Oliveira', 'CRM-SP 123456', 'Cardiologia',  'marcos@clinicavida.com'),
  ('Dra. Fernanda Alves', 'CRM-SP 234567', 'Pediatria',    'fernanda@clinicavida.com'),
  ('Dr. Ricardo Nunes',   'CRM-SP 345678', 'Ortopedia