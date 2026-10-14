"""seguranca.py — criptografia dos dados sensíveis (LGPD)."""
import hashlib
import hmac
import os
import re
from dotenv import load_dotenv

from cryptography.fernet import Fernet
# Carrega as variáveis do ficheiro .env se existir localmente
load_dotenv()

# os.getenv não lança KeyError se a variável não existir
_chave_hmac = os.getenv("CHAVE_HMAC", "chave_hmac_padrao_para_desenvolvimento_123").encode()

# Faz o mesmo para a chave Fernet para evitar o próximo erro
_chave_fernet = os.getenv("CHAVE_FERNET", "chave_fernet_padrao_para_desenvolvimento")


# As chaves vêm do .env: nunca ficam escritas no código.
_fernet = Fernet(os.environ["CHAVE_FERNET"].encode())
_chave_hmac = os.environ["CHAVE_HMAC"].encode()


def so_digitos(texto):
    """'529.982.247-25' -> '52998224725'"""
    return re.sub(r"\D", "", texto or "")


def criptografar(texto):
    """Criptografia reversível (AES, via Fernet): só quem tem a chave lê."""
    return _fernet.encrypt(texto.encode()).decode()


def descriptografar(token):
    return _fernet.decrypt(token.encode()).decode()


def hash_busca(cpf):
    """HMAC-SHA256 do CPF: sempre o mesmo para o mesmo CPF.
    Serve para buscar e para impedir CPF repetido sem guardar o CPF aberto."""
    return hmac.new(_chave_hmac, so_digitos(cpf).encode(), hashlib.sha256).hexdigest()


def cpf_valido(cpf):
    """Confere os dois dígitos verificadores do CPF."""
    d = so_digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11 % 10
        if digito != int(d[tamanho]):
            return False
    return True


def formatar_cpf(cpf):
    d = so_digitos(cpf)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def mascarar_cpf(cpf):
    """Mostra só o meio do CPF na tela: ***.982.247-**"""
    d = so_digitos(cpf)
    return f"***.{d[3:6]}.{d[6:9]}-**"

import os

chave_env = os.getenv("CHAVE_HMAC")
if not chave_env:
    raise RuntimeError("A variável de ambiente CHAVE_HMAC não foi definida no servidor!")

_chave_hmac = chave_env.encode()
