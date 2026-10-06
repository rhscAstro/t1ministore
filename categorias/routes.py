from flask import Blueprint, render_template, request, redirect, url_for
from database import get_connection

categorias_bp = Blueprint(
    "categorias",
    __name__,
    url_prefix="/categorias",
    template_folder="templates",
)


def _cursor(conn):
    try:
        return conn.cursor(dictionary=True)
    except TypeError:
        import pymysql.cursors
        return conn.cursor(pymysql.cursors.DictCursor)


@categorias_bp.route("/")
def listar():
    conn = get_connection()
    cur = _cursor(conn)
    cur.execute("SELECT id, nome, descricao FROM categorias ORDER BY nome")
    categorias = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("categorias/lista.html", categorias=categorias)


@categorias_bp.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        descricao = request.form.get("descricao", "").strip()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO categorias (nome, descricao) VALUES (%s, %s)",
            (nome, descricao),
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("categorias.listar"))
    return render_template("categorias/form.html", categoria=None)


@categorias_bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    conn = get_connection()
    cur = _cursor(conn)

    if request.method == "POST":
        nome = request.form["nome"].strip()
        descricao = request.form.get("descricao", "").strip()
        cur.execute(
            "UPDATE categorias SET nome = %s, descricao = %s WHERE id = %s",
            (nome, descricao, id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("categorias.listar"))

    cur.execute("SELECT id, nome, descricao FROM categorias WHERE id = %s", (id,))
    categoria = cur.fetchone()
    cur.close()
    conn.close()
    if categoria is None:
        return redirect(url_for("categorias.listar"))
    return render_template("categorias/form.html", categoria=categoria)


@categorias_bp.route("/<int:id>/excluir", methods=["POST"])
def excluir(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM categorias WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("categorias.listar"))
