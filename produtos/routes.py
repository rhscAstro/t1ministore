from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

produtos_bp = Blueprint(
    "produtos",
    __name__,
    url_prefix="/produtos",
    template_folder="templates",
)


def _cursor(conn):
    try:
        return conn.cursor(dictionary=True)
    except TypeError:
        import pymysql.cursors
        return conn.cursor(pymysql.cursors.DictCursor)


def _buscar_categorias():
    conn = get_connection()
    cur = _cursor(conn)
    cur.execute("SELECT id, nome FROM categorias ORDER BY nome")
    categorias = cur.fetchall()
    cur.close()
    conn.close()
    return categorias


def _ler_formulario():
    """Lê e valida o formulário. Devolve (dados, erro)."""
    codigo = request.form.get("codigo", "").strip()
    nome = request.form.get("nome", "").strip()
    descricao = request.form.get("descricao", "").strip()
    preco_txt = request.form.get("preco", "").strip().replace(",", ".")
    id_cat = request.form.get("id_categoria", "").strip()

    dados = {
        "codigo": codigo,
        "nome": nome,
        "descricao": descricao,
        "preco": preco_txt,
        "id_categoria": int(id_cat) if id_cat.isdigit() else None,
    }

    erro = None
    if not codigo or not nome:
        erro = "Código e nome são obrigatórios."
    else:
        try:
            preco = Decimal(preco_txt)
            if not preco.is_finite() or preco < 0:
                raise InvalidOperation
        except InvalidOperation:
            erro = "Informe um preço válido (exemplo: 19.90)."
    return dados, erro


@produtos_bp.route("/")
def listar():
    conn = get_connection()
    cur = _cursor(conn)
    cur.execute(
        """
        SELECT p.id, p.codigo, p.nome, p.descricao, p.preco,
               c.nome AS categoria
        FROM produtos p
        LEFT JOIN categorias c ON c.id = p.id_categoria
        ORDER BY p.nome
        """
    )
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("produtos/lista.html", produtos=produtos)


@produtos_bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        dados, erro = _ler_formulario()
        if erro:
            flash(erro, "danger")
            return render_template(
                "produtos/form.html",
                produto=dados,
                categorias=_buscar_categorias(),
            )
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO produtos (codigo, nome, descricao, preco, id_categoria) "
            "VALUES (%s, %s, %s, %s, %s)",
            (dados["codigo"], dados["nome"], dados["descricao"],
             dados["preco"], dados["id_categoria"]),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Produto cadastrado com sucesso.", "success")
        return redirect(url_for("produtos.listar"))
    return render_template(
        "produtos/form.html", produto=None, categorias=_buscar_categorias()
    )


@produtos_bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    if request.method == "POST":
        dados, erro = _ler_formulario()
        if erro:
            flash(erro, "danger")
            dados["id"] = id
            return render_template(
                "produtos/form.html",
                produto=dados,
                categorias=_buscar_categorias(),
            )
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE produtos SET codigo = %s, nome = %s, descricao = %s, "
            "preco = %s, id_categoria = %s WHERE id = %s",
            (dados["codigo"], dados["nome"], dados["descricao"],
             dados["preco"], dados["id_categoria"], id),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Produto atualizado com sucesso.", "success")
        return redirect(url_for("produtos.listar"))

    conn = get_connection()
    cur = _cursor(conn)
    cur.execute(
        "SELECT id, codigo, nome, descricao, preco, id_categoria "
        "FROM produtos WHERE id = %s",
        (id,),
    )
    produto = cur.fetchone()
    cur.close()
    conn.close()
    if produto is None:
        return redirect(url_for("produtos.listar"))
    return render_template(
        "produtos/form.html", produto=produto, categorias=_buscar_categorias()
    )


@produtos_bp.route("/<int:id>/excluir", methods=["POST"])
def excluir(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM produtos WHERE id = %s", (id,))
        conn.commit()
        flash("Produto excluído.", "success")
    except Exception:
        conn.rollback()
        flash("Não foi possível excluir: o produto já está em alguma venda.", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("produtos.listar"))