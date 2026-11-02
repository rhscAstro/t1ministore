from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

vendas_bp = Blueprint(
    "vendas",
    "vendas.routes",
    url_prefix="/vendas",
    template_folder="templates",
)


def _cursor(conn):
    try:
        return conn.cursor(dictionary=True)
    except TypeError:
        import pymysql.cursors
        return conn.cursor(pymysql.cursors.DictCursor)


def _buscar_clientes():
    conn = get_connection()
    cur = _cursor(conn)
    cur.execute("SELECT * FROM clientes")
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    clientes.sort(key=lambda c: str(c.get("nome", "")).lower())
    return clientes


def _buscar_produtos():
    conn = get_connection()
    cur = _cursor(conn)
    cur.execute("SELECT id, codigo, nome, preco FROM produtos ORDER BY nome")
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    return produtos


@vendas_bp.route("/")
def listar():
    conn = get_connection()
    cur = _cursor(conn)
    cur.execute(
        "SELECT id, id_cliente, data_venda, total FROM vendas ORDER BY id DESC"
    )
    vendas = cur.fetchall()
    cur.close()
    conn.close()

    nomes = {c["id"]: c.get("nome", "") for c in _buscar_clientes()}
    for venda in vendas:
        venda["cliente"] = nomes.get(venda["id_cliente"], "(cliente removido)")
    return render_template("vendas/lista.html", vendas=vendas)


@vendas_bp.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "GET":
        return render_template(
            "vendas/form.html",
            clientes=_buscar_clientes(),
            produtos=_buscar_produtos(),
        )

    id_cliente = request.form.get("id_cliente", "").strip()
    data_txt = request.form.get("data_venda", "").strip()
    ids = request.form.getlist("produto_id[]")
    quantidades = request.form.getlist("quantidade[]")

    if not id_cliente.isdigit():
        flash("Selecione o cliente.", "danger")
        return redirect(url_for("vendas.nova"))

    try:
        dia = datetime.strptime(data_txt, "%Y-%m-%d")
        data_venda = datetime.combine(dia.date(), datetime.now().time())
    except ValueError:
        data_venda = datetime.now()

    itens = []
    for pid, qtd in zip(ids, quantidades):
        if not pid.isdigit():
            continue
        if not qtd.isdigit() or int(qtd) < 1:
            flash("A quantidade deve ser um número maior que zero.", "danger")
            return redirect(url_for("vendas.nova"))
        itens.append((int(pid), int(qtd)))

    if not itens:
        flash("Adicione pelo menos um produto à venda.", "danger")
        return redirect(url_for("vendas.nova"))

    conn = get_connection()
    cur = _cursor(conn)
    try:
        total = Decimal("0")
        linhas = []
        for pid, qtd in itens:
            cur.execute("SELECT id, preco FROM produtos WHERE id = %s", (pid,))
            produto = cur.fetchone()
            if produto is None:
                raise ValueError("Um dos produtos não existe mais.")
            preco = Decimal(str(produto["preco"]))
            total += preco * qtd
            linhas.append((pid, qtd, preco))

        cur.execute(
            "INSERT INTO vendas (id_cliente, data_venda, total) VALUES (%s, %s, %s)",
            (int(id_cliente), data_venda, total),
        )
        id_venda = cur.lastrowid

        for pid, qtd, preco in linhas:
            cur.execute(
                "INSERT INTO itens_venda "
                "(id_venda, id_produto, quantidade, preco_unitario) "
                "VALUES (%s, %s, %s, %s)",
                (id_venda, pid, qtd, preco),
            )
        conn.commit()
        flash("Venda registrada com sucesso.", "success")
        destino = redirect(url_for("vendas.detalhe", id=id_venda))
    except ValueError as erro:
        conn.rollback()
        flash(str(erro), "danger")
        destino = redirect(url_for("vendas.nova"))
    except Exception:
        conn.rollback()
        flash("Não foi possível registrar a venda.", "danger")
        destino = redirect(url_for("vendas.nova"))
    finally:
        cur.close()
        conn.close()
    return destino


@vendas_bp.route("/<int:id>")
def detalhe(id):
    conn = get_connection()
    cur = _cursor(conn)
    cur.execute(
        "SELECT id, id_cliente, data_venda, total FROM vendas WHERE id = %s",
        (id,),
    )
    venda = cur.fetchone()
    if venda is None:
        cur.close()
        conn.close()
        return redirect(url_for("vendas.listar"))

    cur.execute(
        """
        SELECT i.quantidade, i.preco_unitario, p.codigo, p.nome
        FROM itens_venda i
        LEFT JOIN produtos p ON p.id = i.id_produto
        WHERE i.id_venda = %s
        ORDER BY i.id
        """,
        (id,),
    )
    itens = cur.fetchall()
    cur.close()
    conn.close()

    nomes = {c["id"]: c.get("nome", "") for c in _buscar_clientes()}
    venda["cliente"] = nomes.get(venda["id_cliente"], "(cliente removido)")
    return render_template("vendas/detalhe.html", venda=venda, itens=itens)


@vendas_bp.route("/<int:id>/excluir", methods=["POST"])
def excluir(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM itens_venda WHERE id_venda = %s", (id,))
        cur.execute("DELETE FROM vendas WHERE id = %s", (id,))
        conn.commit()
        flash("Venda excluída.", "success")
    except Exception:
        conn.rollback()
        flash("Não foi possível excluir a venda.", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("vendas.listar"))