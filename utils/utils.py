import hashlib


def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием алгоритма SHA-256.

    Args:
        password (str): Пароль для хеширования.

    Returns:
        str: Захешированный пароль.
    """
    return hashlib.sha256(password.encode()).hexdigest()
