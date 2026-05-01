# -*- coding: utf-8 -*-
"""
api.py  —  Servidor HTTP local que expone el inventario al bot de WhatsApp.
Ejecutar:  python api.py
Puerto:    5000
"""
from flask import Flask, jsonify, request
import database as db

db.init_db()
app = Flask(__name__)

@app.route("/productos", methods=["GET"])
def listar_productos():
    q = request.args.get("q", "").strip().lower()
    prods = db.get_productos()
    if q:
        prods = [p for p in prods
                 if q in p[2].lower() or q in (p[1] or "").lower()]
    return jsonify([
        {"id": p[0], "codigo": p[1], "nombre": p[2],
         "stock": p[3], "precio": p[4]}
        for p in prods
    ])

@app.route("/cotizar", methods=["POST"])
def cotizar():
    """
    Body JSON: [{"nombre": "Producto A", "cantidad": 2}, ...]
    Devuelve subtotales y total, o error si no hay stock.
    """
    items = request.get_json(force=True) or []
    if not items:
        return jsonify({"error": "Lista vacía"}), 400

    prods = db.get_productos()
    idx   = {p[2].lower(): p for p in prods}   # nombre -> fila
    idx.update({(p[1] or "").lower(): p for p in prods if p[1]})  # codigo -> fila

    lineas = []
    total  = 0.0
    for item in items:
        key  = item.get("nombre", "").strip().lower()
        cant = int(item.get("cantidad", 1))
        prod = idx.get(key)
        if not prod:
            return jsonify({"error": f"Producto '{item.get('nombre')}' no encontrado"}), 404
        if prod[3] < cant:
            return jsonify({"error": f"Stock insuficiente para '{prod[2]}'. Disponible: {prod[3]}"}), 409
        sub = prod[4] * cant
        total += sub
        lineas.append({"nombre": prod[2], "cantidad": cant,
                        "precio_unit": prod[4], "subtotal": sub})

    return jsonify({"items": lineas, "total": total})

if __name__ == "__main__":
    print("API de inventario corriendo en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
