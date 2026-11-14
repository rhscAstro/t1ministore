from flask import Flask, request, session, redirect, url_for
from clientes.routes import clientes_bp
from dashboard.routes import dashboard_bp
from categorias.routes import categorias_bp
from produtos.routes import produtos_bp
from vendas.routes import vendas_bp
from auth.routes import auth_bp


app = Flask("app")

app.secret_key = 'ministore-secret-key-2026'


app.register_blueprint(auth_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(produtos_bp)
app.register_blueprint(vendas_bp)


@app.before_request
def exigir_login():
    """Bloqueia qualquer página para quem não fez login."""
    if request.endpoint is None or request.endpoint in ("auth.login", "static"):
        return None
    if "usuario_id" not in session:
        return redirect(url_for("auth.login", next=request.path))
    return None


if True:
    app.run(debug=True)