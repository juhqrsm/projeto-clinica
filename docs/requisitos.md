# Clínica Vida — Documento de Requisitos

## Problema
O controle manual de agendamentos e cadastros causa perda de consultas,
duplicidade de informações, falhas no armazenamento e risco de
descumprimento da LGPD (CPF dos pacientes sem proteção).

## Requisitos funcionais (RF)
| Código | Descrição | Onde está |
|---|---|---|
| RF01 | Autenticar o usuário por e-mail e senha | /login |
| RF02 | Exibir mensagem quando a autenticação falhar | login() |
| RF03 | Encerrar a sessão após 15 minutos sem uso | login_obrigatorio |
| RF04 | Exibir o nome do usuário logado, o menu e a opção Sair | base.html |
| RF05 | Listar os pacientes e buscar por nome ou CPF | /pacientes?q= |
| RF06 | Cadastrar paciente com consentimento (LGPD) | /pacientes/novo |
| RF07 | Listar e cadastrar médicos | /medicos |
| RF08 | Listar os agendamentos por data e horário, com paciente e médico | /agendamentos |
| RF09 | Cadastrar agendamento associado a um paciente e a um médico | /agendamentos/novo |
| RF10 | Impedir dois agendamentos do mesmo médico no mesmo horário | UNIQUE + IntegrityError |

## Requisitos não funcionais (RNF)
| Código | Descrição |
|---|---|
| RNF01 | Senhas guardadas só como hash (scrypt, werkzeug) |
| RNF02 | CPF e telefone criptografados no banco (Fernet/AES) |
| RNF03 | Chaves e senhas fora do código, no arquivo .env |
| RNF04 | Consultas SQL parametrizadas (%s), contra SQL injection |
| RNF05 | Cookie de sessão HttpOnly e SameSite=Lax |
| RNF06 | Interface responsiva (computador e celular) |
| RNF07 | Banco MySQL 8 com chaves primárias e estrangeiras (InnoDB) |

## Regras de negócio (RN)
| Código | Regra |
|---|---|
| RN01 | Pelo menos três registros em todas as tabelas do script |
| RN02 | Validação em caso de falha na autenticação |
| RN03 | Dados sensíveis criptografados no banco |
| RN04 | Página principal com usuário logado, acesso aos recursos e saída |
| RN05 | Busca de pacientes por termo, com a listagem atualizada |
| RN06 | Agendamentos ordenados por data e horário, com dados do paciente e do médico |
| RN07 | Todo agendamento associado a um paciente e a um médico |
| RN08 | Dados pessoais do paciente tratados conforme a LGPD |