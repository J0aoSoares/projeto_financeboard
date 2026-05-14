import os
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import database
import csv
import io

app = Flask(__name__)

UPLOAD_FOLDER = "uploads/invoices"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard', methods=["GET"])
def dashboard_data():
    month = request.args.get('month')
    transactions = database.get_transactions(month)
    return jsonify({
        'summary':             database.monthly_summary(month),
        'history':             database.last_months_summary(6),
        'pending_invoices':    database.pending_invoices(),
        'recent_transactions': transactions[:5],
        'categories':          database.categories_summary(month)
    })

@app.route('/api/transactions', methods=["GET"])
def list_transactions():
    month = request.args.get('month')
    return jsonify(database.get_transactions(month))

@app.route('/api/transactions', methods=["POST"])
def add_transaction():
    data = request.json
    database.insert_transaction(
        description=data["description"],
        amount=float(data["amount"]),
        kind=data["kind"],
        date=data["date"],
        category=data.get("category", "Outros")
    )
    return jsonify({"ok": True})

@app.route('/api/transactions/<int:id>', methods=['PUT'])
def update_transaction(id):
    data = request.json
    database.update_transaction(
        id=id,
        description=data["description"],
        amount=float(data["amount"]),
        kind=data["kind"],
        date=data["date"],
        category=data.get("category", "Outros")
    )
    return jsonify({"ok": True})

@app.route('/api/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    database.remove_transaction(id)
    return jsonify({"ok": True})

@app.route('/api/summary', methods=["GET"])
def summary():
    month = request.args.get('month')
    return jsonify(database.monthly_summary(month))

@app.route('/api/export', methods=["GET"])
def export_csv():
    from_month = request.args.get('from')
    to_month   = request.args.get('to')
    rows = database.get_transactions_by_period(from_month, to_month)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["description", "amount", "kind", "date", "category"])
    for r in rows:
        writer.writerow([r["description"], r["amount"], r["kind"], r["date"], r["category"]])
    filename = f"financeboard_{from_month or 'start'}_{to_month or 'end'}.csv"
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.route('/api/import', methods=["POST"])
def import_csv():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file sent"}), 400
    content = file.read().decode("utf-8")
    reader  = csv.DictReader(io.StringIO(content))
    inserted, errors = 0, []
    for i, row in enumerate(reader, start=2):
        try:
            database.insert_transaction(
                row["description"], float(row["amount"]), row["kind"], row["date"],
                category=row.get("category", "Outros")
            )
            inserted += 1
        except Exception as e:
            errors.append(f"Linha {i}: {str(e)}")
    return jsonify({"inserted": inserted, "errors": errors})

@app.route('/api/template', methods=["GET"])
def csv_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["description", "amount", "kind", "date", "category"])
    writer.writerow(["Exemplo entrada", "1500.00", "income",  "2026-05-01", "Vendas"])
    writer.writerow(["Exemplo saida",   "300.00",  "expense", "2026-05-02", "Materiais"])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=template_financeboard.csv"})

@app.route('/api/invoices', methods=["GET"])
def list_invoices():
    month = request.args.get('month')
    return jsonify(database.get_invoices(month))

@app.route('/api/invoices', methods=["POST"])
def add_invoice():
    file_path = None
    pdf = request.files.get("file")
    if pdf and pdf.filename:
        path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        pdf.save(path)
        file_path = path
    new_id = database.insert_invoice(
        number=request.form["number"],
        supplier=request.form["supplier"],
        description=request.form["description"],
        amount=float(request.form["amount"]),
        issue_date=request.form["issue_date"],
        due_date=request.form["due_date"],
        file_path=file_path
    )
    return jsonify({"ok": True, "id": new_id})

@app.route('/api/invoices/<int:id>', methods=['PUT'])
def update_invoice(id):
    data = request.json
    database.update_invoice(
        id=id,
        number=data["number"],
        supplier=data["supplier"],
        description=data["description"],
        amount=float(data["amount"]),
        issue_date=data["issue_date"],
        due_date=data["due_date"]
    )
    return jsonify({"ok": True})

@app.route('/api/invoices/<int:id>/pay', methods=["POST"])
def pay_invoice(id):
    data = request.json
    transaction_id = database.mark_invoice_paid(id, data["payment_date"])
    return jsonify({"ok": True, "transaction_id": transaction_id})

@app.route('/api/invoices/<int:id>', methods=["DELETE"])
def delete_invoice(id):
    file_path = database.remove_invoice(id)
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    return jsonify({"ok": True})

@app.route('/api/invoices/<int:id>/file', methods=["GET"])
def download_invoice(id):
    invoice = database.get_invoice(id)
    if not invoice or not invoice["file_path"]:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(os.path.abspath(UPLOAD_FOLDER),
                               os.path.basename(invoice["file_path"]))

if __name__ == "__main__":
    database.init_db()
    print("\n Server running at http://localhost:5000")
    app.run(debug=True)