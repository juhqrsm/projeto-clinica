# Clínica Vida — sistema de agendamento (Flask + MySQL)

## Como rodar
1. Execute `schema.sql` no MySQL Workbench (cria o banco `clinica` com dados de exemplo).
2. Crie o ambiente virtual e instale as dependências:
   ```
   python -m venv venv
   venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
   pip install -r requirements.txt
   ```
3. Copie o `.env` e coloque a senha do seu MySQL em `DB_PASSWORD`.
4. Rode `python app.py` e abra http://127.0.0.1:5000

## Usuários de teste
| E-mail | Senha |
|---|---|
| carla@clinicavida.com | Recepcao@2026 |
| rafael@clinicavida.com | Admin@2026 |
| juliana@clinicavida.com | Clinica@2026 |

## Estrutura
```
clinica/
├── app.py              rotas, login, sessão
├── db.py               conexão com o MySQL
├── seguranca.py        criptografia, HMAC, validação de CPF
├── gerar_dados.py      gera os INSERTs protegidos
├── schema.sql          script do banco + dados de exemplo
├── requirements.txt
├── .env                segredos (fora do Git)
├── docs/
│   ├── requisitos.md   RF, RNF e regras de negócio
│   └── der.png         diagrama exportado do Workbench
├── static/css/style.css
└── templates/          base, login, painel, pacientes, médicos, agendamentos
```

## Segurança e LGPD
- Senhas: hash scrypt (`generate_password_hash`), nunca o texto.
- CPF e telefone: criptografados com Fernet; a chave fica no `.env`.
- CPF também tem um HMAC (`cpf_hash`) para busca e para impedir duplicidade.
- Na tela, o CPF aparece mascarado: `***.982.247-**`.
- O cadastro exige o consentimento do paciente (`consentimento_em`).
- Sessão expira após 15 minutos sem uso.

## DER
No Workbench: Database > Reverse Engineer > banco `clinica` > exporte em File > Export > PNG.