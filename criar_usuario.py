from getpass import getpass
from werkzeug.security import generate_password_hash
from database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        senha_hash VARCHAR(255) NOT NULL,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()

username = input("Nome de usuário: ").strip()
senha = getpass("Senha (não aparece enquanto digita): ")
confirmar = getpass("Repita a senha: ")

if not username or not senha:
    print("Usuário e senha são obrigatórios.")
elif senha != confirmar:
    print("As senhas não conferem. Nada foi salvo.")
elif len(senha) < 6:
    print("Use uma senha com pelo menos 6 caracteres.")
else:
    try:
        cur.execute(
            "INSERT INTO usuarios (username, senha_hash) VALUES (%s, %s)",
            (username, generate_password_hash(senha)),
        )
        conn.commit()
        print("Usuário criado com sucesso.")
    except Exception as erro:
        print("Não foi possível criar o usuário (talvez o nome já exista):", erro)

cur.close()
conn.close()