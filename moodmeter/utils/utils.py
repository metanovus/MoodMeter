import hashlib
import logging
import os

if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием алгоритма SHA-256.

    Args:
        password (str): Пароль для хеширования.

    Returns:
        str: Захешированный пароль.
    """
    return hashlib.sha256(password.encode()).hexdigest()
