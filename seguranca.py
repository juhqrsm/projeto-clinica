"""seguranca.py — criptografia dos dados sensíveis (LGPD)."""
import hashlib
import hmac
import os
import re

from cryptography.fernet import Fernet

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