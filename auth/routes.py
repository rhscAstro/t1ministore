from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import get_connection

auth_bp = Blueprint(
    "auth",
    "auth.routes",
    template_folder="templates",
)


def _cursor(conn):
    try:
        return conn.cursor(dictionary=True)
    except TypeError:
        import pymysql.cursors
        return conn.cursor(pymysql.cursors.DictCursor)


def _destino_seguro(destino):
    """Só aceita caminhos internos (evita redirecionar para outro site)."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("dashboard.index")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")

        conn = get_connection()
        cur = _cursor(conn)
        cur.execute(
            "SELECT id, username, senha_hash FROM usuarios WHERE username = %s",
            (username,),
        )
        usuario = cur.fetchone()
        cur.close()
        conn.close()

        if usuario and check_password_hash(usuario["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario"] = usuario["username"]
            return redirect(_destino_seguro(request.args.get("next")))

        flash("Usuário ou senha incorretos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("auth.login"))