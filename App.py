from flask import Flask, render_template, request, jsonify
import database

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transacoes', methods=["GET"])
def listar_transacoes():
    mes = request.args.get('mes')
    transacoes = database.get_transacoes(mes)
    return jsonify(transacoes)

@app.route('/api/transacoes', methods=["POST"])
def adicionar_transacao():
    dados = request.json
    database.inserir_transacao(
        descricao=dados["descricao"],
        valor=float(dados["valor"]) ,
        tipo=dados["tipo"],
        data=dados["data"]
        )

@app.route('/api/transacoes/<int:id>', methods=['DELETE'])
def excluir_transacao(id):
    database.excluir_transacao(id)
    return jsonify({"ok": True})

@app.route('/api/transacoes/<int:id>', methods=['PUT'])
def atualizar_transacao(id):
    dados = request.json
    database.atualizar_transacao(
        id=id,
        descricao=dados["descricao"],
        valor=float(dados["valor"]),
        tipo=dados["tipo"],
        data=dados["data"]
    )
    return jsonify({"ok": True})

@app.route("api/resumo", methods=["GET"])
def resumo():
    mes = request.args.get("mes")
    dados = database.resumo_mensal(mes)
    return jsonify(dados)

if __name__ == "__main__":
    database.inicializar_db()
    print("\n Servidor rodando em http://localhost:5000")
    app.run(debug=True)