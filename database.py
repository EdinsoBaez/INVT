# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime

DB = "inventario.db"

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo     TEXT    UNIQUE,
                nombre     TEXT    NOT NULL UNIQUE,
                cantidad   INTEGER NOT NULL DEFAULT 0,
                precio     REAL    NOT NULL DEFAULT 0.0,
                foto_path  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                cantidad    INTEGER,
                total       REAL,
                fecha       TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        # Migración: añadir columnas si la BD ya existía sin ellas
        cols = [r[1] for r in conn.execute("PRAGMA table_info(productos)").fetchall()]
        if "codigo"    not in cols: conn.execute("ALTER TABLE productos ADD COLUMN codigo    TEXT")
        if "foto_path" not in cols: conn.execute("ALTER TABLE productos ADD COLUMN foto_path TEXT")

def agregar_producto(codigo, nombre, cantidad, precio, foto_path=None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO productos (codigo, nombre, cantidad, precio, foto_path) VALUES (?,?,?,?,?)",
            (codigo or None, nombre, cantidad, precio, foto_path)
        )

def actualizar_producto(pid, codigo, nombre, cantidad, precio, foto_path=None):
    with get_conn() as conn:
        conn.execute(
            "UPDATE productos SET codigo=?, nombre=?, cantidad=?, precio=?, foto_path=? WHERE id=?",
            (codigo or None, nombre, cantidad, precio, foto_path, pid)
        )

def actualizar_cantidad(producto_id, cantidad):
    with get_conn() as conn:
        conn.execute("UPDATE productos SET cantidad = cantidad + ? WHERE id = ?", (cantidad, producto_id))

def get_productos():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, codigo, nombre, cantidad, precio, foto_path FROM productos ORDER BY nombre"
        ).fetchall()

def get_producto(pid):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, codigo, nombre, cantidad, precio, foto_path FROM productos WHERE id=?", (pid,)
        ).fetchone()

def registrar_ventas(items):
    """items: lista de (producto_id, cantidad_vendida)"""
    from datetime import datetime
    fecha_local = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    resultados = []
    with get_conn() as conn:
        for producto_id, cantidad_vendida in items:
            row = conn.execute("SELECT cantidad, precio FROM productos WHERE id=?", (producto_id,)).fetchone()
            if not row:
                return None, f"Producto ID {producto_id} no encontrado"
            stock, precio = row
            if stock < cantidad_vendida:
                return None, f"Stock insuficiente para producto ID {producto_id}. Disponible: {stock}"
            total = precio * cantidad_vendida
            conn.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id = ?", (cantidad_vendida, producto_id))
            conn.execute(
                "INSERT INTO ventas (producto_id, cantidad, total, fecha) VALUES (?,?,?,?)",
                (producto_id, cantidad_vendida, total, fecha_local)
            )
            resultados.append(total)
    return sum(resultados), None

    with get_conn() as conn:
        row = conn.execute("SELECT cantidad, precio FROM productos WHERE id=?", (producto_id,)).fetchone()
        if not row:
            return None, "Producto no encontrado"
        stock, precio = row
        if stock < cantidad_vendida:
            return None, f"Stock insuficiente. Disponible: {stock}"
        total       = precio * cantidad_vendida
        fecha_local = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        conn.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id = ?", (cantidad_vendida, producto_id))
        conn.execute(
            "INSERT INTO ventas (producto_id, cantidad, total, fecha) VALUES (?,?,?,?)",
            (producto_id, cantidad_vendida, total, fecha_local)
        )
        return total, stock - cantidad_vendida

def get_ventas():
    with get_conn() as conn:
        return conn.execute("""
            SELECT v.id, p.codigo, p.nombre, v.cantidad, v.total, v.fecha
            FROM ventas v JOIN productos p ON v.producto_id = p.id
            ORDER BY v.id DESC LIMIT 100
        """).fetchall()

def eliminar_producto(producto_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM productos WHERE id=?", (producto_id,))
