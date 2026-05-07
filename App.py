from flask import Flask, render_template, request, jsonify, Response
import database
import csv
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transacoes', methods=["GET"])
def listar_transacoes():
    mes = request.args.get('mes')
    transacoes = database.buscar_transacoes(mes)
    return jsonify(transacoes)

@app.route('/api/transacoes', methods=["POST"])
def adicionar_transacao():
    dados = request.json
    database.inserir_transacao(
        descricao=dados["descricao"],
        valor=float(dados["valor"]),
        tipo=dados["tipo"],
        data=dados["data"]
    )
    return jsonify({"ok": True})

@app.route('/api/transacoes/<int:id>', methods=['DELETE'])
def excluir_transacao(id):
    database.deletar_transacao(id)
    return jsonify({"ok": True})

@app.route("/api/resumo", methods=["GET"])
def resumo():
    mes = request.args.get("mes")
    dados = database.resumo_mensal(mes)
    return jsonify(dados)

@app.route("/api/exportar", methods=["GET"])
def exportar():
    de  = request.args.get("de")
    ate = request.args.get("ate")
    transacoes = database.buscar_periodo(de, ate)

    saida = io.StringIO()
    writer = csv.writer(saida)
    writer.writerow(["descricao", "valor", "tipo", "data"])
    for t in transacoes:
        writer.writerow([t["descricao"], t["valor"], t["tipo"], t["data"]])

    nome = f"financeboard_{de or 'inicio'}_{ate or 'fim'}.csv"
    return Response(
        saida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nome}"}
    )

@app.route("/api/importar", methods=["POST"])
def importar():
    arquivo = request.files.get("arquivo")
    if not arquivo:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    conteudo = arquivo.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(conteudo))

    inseridos = 0
    erros = []
    for i, linha in enumerate(reader, start=2):
        try:
            database.inserir_transacao(
                descricao=linha["descricao"],
                valor=float(linha["valor"]),
                tipo=linha["tipo"],
                data=linha["data"]
            )
            inseridos += 1
        except Exception as e:
            erros.append(f"Linha {i}: {str(e)}")

    return jsonify({"inseridos": inseridos, "erros": erros})

@app.route("/api/template", methods=["GET"])
def template_csv():
    saida = io.StringIO()
    writer = csv.writer(saida)
    writer.writerow(["descricao", "valor", "tipo", "data"])
    writer.writerow(["Exemplo entrada", "1500.00", "entrada", "2026-05-01"])
    writer.writerow(["Exemplo saida",   "300.00",  "saida",   "2026-05-02"])

    return Response(
        saida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_financeboard.csv"}
    )

if __name__ == "__main__":
    database.inicializar_db()
    print("\n Servidor rodando em http://localhost:5000")
    app.run(debug=True)