from flask import Flask
from clientes.routes import clientes_bp
from dashboard.routes import dashboard_bp
from categorias.routes import categorias_bp
from produtos.routes import produtos_bp


app = Flask("app")

app.secret_key = 'ministore-secret-key-2026'


app.register_blueprint(clientes_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(produtos_bp)


if True:
    app.run(debug=True)