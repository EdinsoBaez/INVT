# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import shutil, os
from PIL import Image, ImageTk
import database as db

db.init_db()

PHOTOS_DIR = "product_photos"
os.makedirs(PHOTOS_DIR, exist_ok=True)

# ── Paleta ────────────────────────────────────────────────
BG       = "#0f0f1a"
SIDEBAR  = "#16162a"
CARD     = "#1e1e35"
CARD2    = "#252540"
ACCENT   = "#6d28d9"
ACCENT_H = "#7c3aed"
GREEN    = "#059669"
GREEN_H  = "#10b981"
RED      = "#dc2626"
RED_H    = "#ef4444"
AMBER    = "#d97706"
FG       = "#f1f5f9"
FG2      = "#94a3b8"
FG3      = "#64748b"
BORDER   = "#2d2d50"

# ── Helpers ───────────────────────────────────────────────
def _lighten(h):
    r, g, b_ = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(min(r+25,255), min(g+25,255), min(b_+25,255))

def btn(parent, text, cmd, color=ACCENT, hover=None, **kw):
    hc = hover or _lighten(color)
    b  = tk.Button(parent, text=text, command=cmd, bg=color, fg=FG,
                   relief="flat", font=("Segoe UI", 10, "bold"),
                   padx=14, pady=7, cursor="hand2",
                   activebackground=hc, activeforeground=FG, bd=0, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=hc))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

def mk_card_frame(parent, **kw):
    return tk.Frame(parent, bg=CARD, **kw)

def _hex(h):
    return (int(h[1:3],16), int(h[3:5],16), int(h[5:7],16), 255)

def load_img(path, size):
    try:
        img   = Image.open(path).convert("RGBA")
        ratio = max(size[0] / img.width, size[1] / img.height)
        nw    = max(1, int(img.width  * ratio))
        nh    = max(1, int(img.height * ratio))
        img   = img.resize((nw, nh), Image.LANCZOS)
        l     = (nw - size[0]) // 2
        t     = (nh - size[1]) // 2
        img   = img.crop((l, t, l + size[0], t + size[1]))
        out   = Image.new("RGB", size, (_hex(CARD2)[0], _hex(CARD2)[1], _hex(CARD2)[2]))
        if img.mode == "RGBA":
            out.paste(img, (0, 0), img.split()[3])
        else:
            out.paste(img, (0, 0))
        return ImageTk.PhotoImage(out)
    except Exception:
        return None

# ── Ventana principal ─────────────────────────────────────
root = tk.Tk()
root.title("Inventario Pro")
root.configure(bg=BG)
root.resizable(True, True)
root.withdraw()
try: root.iconbitmap(default="")
except: pass

# ── Splash ────────────────────────────────────────────────
splash = tk.Toplevel()
splash.overrideredirect(True)
splash.configure(bg=SIDEBAR)
SW, SH = 380, 280
splash.geometry(f"{SW}x{SH}+{(splash.winfo_screenwidth()-SW)//2}+{(splash.winfo_screenheight()-SH)//2}")
splash.lift()

tk.Label(splash, text="📦", bg=SIDEBAR, fg=FG, font=("Segoe UI",54)).pack(pady=(34,0))
tk.Label(splash, text="Inventario Pro", bg=SIDEBAR, fg=FG, font=("Segoe UI",18,"bold")).pack(pady=(6,2))
tk.Label(splash, text="Sistema de gestión de inventario", bg=SIDEBAR, fg=FG2, font=("Segoe UI",9)).pack()

_pvar = tk.DoubleVar()
_ssty = ttk.Style()
_ssty.theme_use("clam")
_ssty.configure("S.Horizontal.TProgressbar", troughcolor=CARD, background=ACCENT, borderwidth=0, thickness=5)
ttk.Progressbar(splash, variable=_pvar, maximum=100, style="S.Horizontal.TProgressbar", length=300).pack(pady=(20,0))
_slbl = tk.Label(splash, text="Iniciando...", bg=SIDEBAR, fg=FG3, font=("Segoe UI",8))
_slbl.pack(pady=(6,0))

_steps = [(25,"Cargando base de datos..."),(55,"Preparando inventario..."),(80,"Cargando interfaz..."),(100,"¡Listo!")]

def _tick(i=0):
    if i < len(_steps):
        _pvar.set(_steps[i][0]); _slbl.config(text=_steps[i][1])
        splash.after(350, _tick, i+1)
    else:
        splash.after(300, _done)

def _done():
    splash.destroy()
    mw, mh = 1100, 680
    root.geometry(f"{mw}x{mh}+{(root.winfo_screenwidth()-mw)//2}+{(root.winfo_screenheight()-mh)//2}")
    root.deiconify()

splash.after(120, _tick)

# ── Layout ────────────────────────────────────────────────
sidebar   = tk.Frame(root, bg=SIDEBAR, width=200)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)
main_area = tk.Frame(root, bg=BG)
main_area.pack(side="left", fill="both", expand=True)

# ── Sidebar ───────────────────────────────────────────────
tk.Label(sidebar, text="📦", bg=SIDEBAR, fg=FG, font=("Segoe UI",28)).pack(pady=(28,4))
tk.Label(sidebar, text="Inventario\nPro", bg=SIDEBAR, fg=FG, font=("Segoe UI",13,"bold"), justify="center").pack()
tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=20)

_nav_btns    = {}
_active_page = [None]
pages        = {}

def nav_btn(text, icon, key):
    f     = tk.Frame(sidebar, bg=SIDEBAR, cursor="hand2")
    f.pack(fill="x", padx=10, pady=2)
    inner = tk.Frame(f, bg=SIDEBAR)
    inner.pack(fill="x", padx=6, pady=6)
    tk.Label(inner, text=icon, bg=SIDEBAR, fg=FG2, font=("Segoe UI",14)).pack(side="left", padx=(4,8))
    tk.Label(inner, text=text, bg=SIDEBAR, fg=FG2, font=("Segoe UI",10,"bold")).pack(side="left")
    def go(e=None): show_page(key)
    for w in [f, inner] + inner.winfo_children(): w.bind("<Button-1>", go)
    _nav_btns[key] = (f, inner)

def set_nav_active(key):
    for k,(f,inner) in _nav_btns.items():
        c = ACCENT if k==key else SIDEBAR
        fc = FG if k==key else FG2
        f.config(bg=c); inner.config(bg=c)
        for w in inner.winfo_children(): w.config(bg=c, fg=fc)

def show_page(key):
    for p in pages.values(): p.pack_forget()
    pages[key].pack(fill="both", expand=True)
    set_nav_active(key)
    _active_page[0] = key

nav_btn("Inventario",  "🗃", "inv")
nav_btn("Nueva Venta", "🛒", "venta")
nav_btn("Historial",   "📋", "hist")

# ttk styles
style = ttk.Style()
style.configure("TScrollbar", background=CARD2, troughcolor=BG, borderwidth=0)
style.configure("TCombobox",  fieldbackground=CARD2, background=CARD2, foreground=FG, selectbackground=ACCENT)
style.configure("Hist.Treeview", background=CARD, foreground=FG, fieldbackground=CARD,
                rowheight=32, font=("Segoe UI",10), borderwidth=0)
style.configure("Hist.Treeview.Heading", background=CARD2, foreground=FG2,
                font=("Segoe UI",9,"bold"), relief="flat")
style.map("Hist.Treeview", background=[("selected", ACCENT)])

# ═══════════════════════════════════════════════════════════
# PÁGINA INVENTARIO
# ═══════════════════════════════════════════════════════════
p_inv = tk.Frame(main_area, bg=BG)
pages["inv"] = p_inv

# Encabezado
hdr = tk.Frame(p_inv, bg=BG)
hdr.pack(fill="x", padx=24, pady=(20,0))
tk.Label(hdr, text="Inventario", bg=BG, fg=FG, font=("Segoe UI",18,"bold")).pack(side="left")
btn(hdr, "+ Nuevo Producto", lambda: abrir_form_producto(), GREEN, GREEN_H).pack(side="right")

# Búsqueda
sf = tk.Frame(p_inv, bg=BG)
sf.pack(fill="x", padx=24, pady=(10,6))
tk.Label(sf, text="🔍", bg=BG, fg=FG2, font=("Segoe UI",12)).pack(side="left", padx=(0,6))
e_search = tk.Entry(sf, width=30, bg=CARD2, fg=FG, insertbackground=FG,
                    relief="flat", font=("Segoe UI",10), highlightthickness=1,
                    highlightbackground=BORDER, highlightcolor=ACCENT)
e_search.pack(side="left", ipady=5)
e_search.bind("<KeyRelease>", lambda e: cargar_inventario())

# Estilos tabla
style.configure("Inv.Treeview", background=CARD, foreground=FG, fieldbackground=CARD,
                rowheight=34, font=("Segoe UI",10), borderwidth=0)
style.configure("Inv.Treeview.Heading", background=CARD2, foreground=FG2,
                font=("Segoe UI",9,"bold"), relief="flat")
style.map("Inv.Treeview", background=[("selected", ACCENT)])

# Contenedor tabla + scrollbar
tbl_wrap = tk.Frame(p_inv, bg=BG)
tbl_wrap.pack(fill="both", expand=True, padx=24, pady=(0,0))
tbl_wrap.rowconfigure(0, weight=1)
tbl_wrap.columnconfigure(0, weight=1)

cols_inv = ("codigo", "nombre", "cantidad", "precio")
tree_inv = ttk.Treeview(tbl_wrap, columns=cols_inv, show="headings",
                         style="Inv.Treeview", selectmode="browse")
for c, w, a in [("codigo",120,"center"),("nombre",340,"w"),("cantidad",100,"center"),("precio",110,"center")]:
    tree_inv.heading(c, text={"codigo":"Código","nombre":"Producto","cantidad":"Stock","precio":"Precio"}[c])
    tree_inv.column(c, width=w, anchor=a)

tree_inv.tag_configure("low",  foreground=AMBER)
tree_inv.tag_configure("zero", foreground=RED_H)

sb_inv = ttk.Scrollbar(tbl_wrap, orient="vertical", command=tree_inv.yview)
tree_inv.configure(yscrollcommand=sb_inv.set)
tree_inv.grid(row=0, column=0, sticky="nsew")
sb_inv.grid(row=0, column=1, sticky="ns")

# Botones bajo la tabla
act_frame = tk.Frame(p_inv, bg=BG)
act_frame.pack(fill="x", padx=24, pady=(6,14))

def editar_sel():
    sel = tree_inv.selection()
    if not sel: return messagebox.showwarning("Aviso", "Selecciona un producto.")
    vals = tree_inv.item(sel[0])["values"]
    prod = next((p for p in db.get_productos()
                 if str(p[1]) == str(vals[0]) and p[2] == vals[1]), None)
    if prod: abrir_form_producto(prod)

def eliminar_sel():
    sel = tree_inv.selection()
    if not sel: return
    vals = tree_inv.item(sel[0])["values"]
    prod = next((p for p in db.get_productos()
                 if str(p[1]) == str(vals[0]) and p[2] == vals[1]), None)
    if prod and messagebox.askyesno("Confirmar", f"¿Eliminar '{prod[2]}'?"):
        db.eliminar_producto(prod[0]); cargar_inventario()

btn(act_frame, "✏ Editar",   editar_sel,   ACCENT, ACCENT_H).pack(side="left", padx=(0,8))
btn(act_frame, "🗑 Eliminar", eliminar_sel, RED,    RED_H   ).pack(side="left")

# ── Modal nuevo/editar producto ───────────────────────────
def abrir_form_producto(prod=None):
    win = tk.Toplevel(root)
    win.title("Nuevo Producto" if not prod else "Editar Producto")
    win.configure(bg=CARD)
    win.resizable(False, False)
    win.grab_set(); win.lift(); win.focus_force()

    foto_path = [prod[5] if prod else None]
    _ref      = [None]

    tk.Label(win, text="Nuevo Producto" if not prod else "Editar Producto",
             bg=CARD, fg=FG, font=("Segoe UI",14,"bold")).pack(pady=(18,10), padx=30, anchor="w")

    form = tk.Frame(win, bg=CARD, padx=30)
    form.pack(fill="x")

    def field(lbl, val=""):
        tk.Label(form, text=lbl, bg=CARD, fg=FG2, font=("Segoe UI",9,"bold")).pack(anchor="w", pady=(6,2))
        e = tk.Entry(form, bg=CARD2, fg=FG, insertbackground=FG, relief="flat",
                     font=("Segoe UI",10), highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT)
        e.pack(fill="x", ipady=5)
        if val: e.insert(0, str(val))
        return e

    e_cod  = field("Código de producto", prod[1] if prod else "")
    e_nom  = field("Nombre",             prod[2] if prod else "")
    e_cant = field("Cantidad",           prod[3] if prod else "")
    e_prec = field("Precio ($)",         prod[4] if prod else "")

    tk.Label(form, text="Foto del producto", bg=CARD, fg=FG2,
             font=("Segoe UI",9,"bold")).pack(anchor="w", pady=(10,4))
    frow = tk.Frame(form, bg=CARD)
    frow.pack(anchor="w")

    fbox = tk.Frame(frow, bg=CARD2, width=72, height=72)
    fbox.pack(side="left"); fbox.pack_propagate(False)
    ilbl = tk.Label(fbox, bg=CARD2, text="Sin\nfoto", fg=FG3, font=("Segoe UI",8))
    ilbl.place(relx=.5, rely=.5, anchor="center")

    def refresh():
        if foto_path[0] and os.path.exists(foto_path[0]):
            im = load_img(foto_path[0], (72,72))
            if im: _ref[0]=im; ilbl.config(image=im, text="")
    refresh()

    def pick_foto():
        p = filedialog.askopenfilename(title="Seleccionar imagen",
            filetypes=[("Imágenes","*.png *.jpg *.jpeg *.webp *.bmp *.gif")])
        if p:
            ext      = os.path.splitext(p)[1].lower()
            safename = "".join(c if c.isalnum() or c in "._-" else "_"
                               for c in (e_nom.get().strip() or "prod"))
            dest = os.path.join(PHOTOS_DIR, f"{safename}{ext}")
            shutil.copy2(p, dest)
            foto_path[0] = dest
            refresh()

    btn(frow, "📷 Seleccionar foto", pick_foto, CARD2, BORDER).pack(side="left", padx=(12,0))

    tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(18,0))

    def guardar():
        codigo = e_cod.get().strip()
        nombre = e_nom.get().strip()
        try:
            cant   = int(e_cant.get())
            precio = float(e_prec.get())
            assert nombre and cant >= 0 and precio >= 0
        except:
            return messagebox.showerror("Error",
                "Verifica: nombre no vacío, cantidad (entero ≥ 0) y precio (número ≥ 0).")
        try:
            if prod: db.actualizar_producto(prod[0], codigo, nombre, cant, precio, foto_path[0])
            else:    db.agregar_producto(codigo, nombre, cant, precio, foto_path[0])
            cargar_inventario(); win.destroy()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    br2 = tk.Frame(win, bg=CARD)
    br2.pack(pady=18)
    btn(br2, "💾  Guardar",  guardar,     GREEN, GREEN_H).pack(side="left", padx=(0,10), ipadx=12)
    btn(br2, "✕  Cancelar", win.destroy, RED,   RED_H  ).pack(side="left", ipadx=12)

    win.update_idletasks()
    h = win.winfo_reqheight()
    wx = root.winfo_x() + (root.winfo_width()  - 460) // 2
    wy = root.winfo_y() + (root.winfo_height() - h)   // 2
    win.geometry(f"460x{h}+{wx}+{wy}")

# ── Cargar inventario como tabla ─────────────────────────
def cargar_inventario():
    q = e_search.get().strip().lower()
    tree_inv.delete(*tree_inv.get_children())
    for p in db.get_productos():
        pid, cod, nom, cant, precio, foto = p
        if q and q not in nom.lower() and q not in (cod or "").lower():
            continue
        tag = "zero" if cant == 0 else ("low" if cant <= 5 else "")
        tree_inv.insert("", "end",
                        values=(cod or "—", nom, cant, f"${precio:.2f}"),
                        tags=(tag,))
    if "_productos_map" in globals():
        actualizar_combo_venta()

# ═══════════════════════════════════════════════════════════
# PÁGINA VENTAS — carrito multi-producto
# ═══════════════════════════════════════════════════════════
p_venta = tk.Frame(main_area, bg=BG)
pages["venta"] = p_venta

tk.Label(p_venta, text="Registrar Venta", bg=BG, fg=FG,
         font=("Segoe UI",18,"bold")).pack(anchor="w", padx=24, pady=(20,12))

vbody = tk.Frame(p_venta, bg=BG)
vbody.pack(fill="both", expand=True, padx=24, pady=(0,16))

# ─ Panel izquierdo: agregar al carrito ────────────────────
v_left = mk_card_frame(vbody)
v_left.pack(side="left", fill="y", padx=(0,14), ipadx=18, ipady=18)

tk.Label(v_left, text="Agregar producto", bg=CARD, fg=FG,
         font=("Segoe UI",11,"bold")).pack(anchor="w", pady=(0,10))

tk.Label(v_left, text="Producto", bg=CARD, fg=FG2,
         font=("Segoe UI",9,"bold")).pack(anchor="w", pady=(0,3))
combo_producto = ttk.Combobox(v_left, width=30, state="readonly", font=("Segoe UI",10))
combo_producto.pack(anchor="w", pady=(0,10))

tk.Label(v_left, text="Cantidad", bg=CARD, fg=FG2,
         font=("Segoe UI",9,"bold")).pack(anchor="w", pady=(0,3))
e_venta_cant = tk.Entry(v_left, width=10, bg=CARD2, fg=FG, insertbackground=FG,
                         relief="flat", font=("Segoe UI",11), highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=ACCENT)
e_venta_cant.pack(anchor="w", ipady=5, pady=(0,12))

add_msg_var = tk.StringVar()
tk.Label(v_left, textvariable=add_msg_var, bg=CARD, fg=AMBER,
         font=("Segoe UI",9), wraplength=240).pack(anchor="w", pady=(0,4))

# ─ Panel central: carrito ───────────────────────────────
v_mid = mk_card_frame(vbody)
v_mid.pack(side="left", fill="both", expand=True, padx=(0,14), ipadx=18, ipady=18)

tk.Label(v_mid, text="Carrito", bg=CARD, fg=FG,
         font=("Segoe UI",11,"bold")).pack(anchor="w", pady=(0,8))

style.configure("Cart.Treeview", background=CARD2, foreground=FG, fieldbackground=CARD2,
                rowheight=30, font=("Segoe UI",10), borderwidth=0)
style.configure("Cart.Treeview.Heading", background=CARD, foreground=FG2,
                font=("Segoe UI",9,"bold"), relief="flat")
style.map("Cart.Treeview", background=[("selected", ACCENT)])

cart_wrap = tk.Frame(v_mid, bg=CARD)
cart_wrap.pack(fill="both", expand=True)
cart_wrap.rowconfigure(0, weight=1)
cart_wrap.columnconfigure(0, weight=1)

cols_cart = ("nombre", "cant", "precio", "subtotal")
tree_cart = ttk.Treeview(cart_wrap, columns=cols_cart, show="headings",
                          style="Cart.Treeview", selectmode="browse", height=8)
for c, w, a in [("nombre",200,"w"),("cant",60,"center"),("precio",80,"center"),("subtotal",90,"center")]:
    tree_cart.heading(c, text={"nombre":"Producto","cant":"Cant.","precio":"Precio","subtotal":"Subtotal"}[c])
    tree_cart.column(c, width=w, anchor=a)
sb_cart = ttk.Scrollbar(cart_wrap, orient="vertical", command=tree_cart.yview)
tree_cart.configure(yscrollcommand=sb_cart.set)
tree_cart.grid(row=0, column=0, sticky="nsew")
sb_cart.grid(row=0, column=1, sticky="ns")

# Total y botones del carrito
cart_footer = tk.Frame(v_mid, bg=CARD)
cart_footer.pack(fill="x", pady=(10,0))

total_var = tk.StringVar(value="Total:  $0.00")
tk.Label(cart_footer, textvariable=total_var, bg=CARD, fg=GREEN_H,
         font=("Segoe UI",13,"bold")).pack(side="left")

# ─ Panel derecho: resultado ────────────────────────────
v_right = mk_card_frame(vbody)
v_right.pack(side="left", fill="y", ipadx=18, ipady=18)

tk.Label(v_right, text="Resumen", bg=CARD, fg=FG,
         font=("Segoe UI",11,"bold")).pack(anchor="w", pady=(0,10))
resultado_var = tk.StringVar()
resultado_lbl = tk.Label(v_right, textvariable=resultado_var, bg=CARD, fg=FG2,
                          font=("Segoe UI",10), wraplength=220, justify="left")
resultado_lbl.pack(anchor="w")

# ─ Estado interno del carrito ──────────────────────────
# carrito: lista de dicts {pid, nombre, cant, precio}
_carrito = []
_productos_map = {}

def actualizar_combo_venta():
    global _productos_map
    _productos_map = {}
    for p in db.get_productos():
        pid, cod, nom, cant, precio, foto = p
        _productos_map[f"{nom}  [{cod or '—'}]  (stock: {cant})"] = p
    combo_producto["values"] = list(_productos_map.keys())

def _refresh_cart():
    tree_cart.delete(*tree_cart.get_children())
    total = 0.0
    for item in _carrito:
        sub = item["cant"] * item["precio"]
        total += sub
        tree_cart.insert("", "end", values=(
            item["nombre"], item["cant"],
            f"${item['precio']:.2f}", f"${sub:.2f}"
        ))
    total_var.set(f"Total:  ${total:.2f}")

def agregar_al_carrito():
    sel = combo_producto.get()
    if not sel or sel not in _productos_map:
        add_msg_var.set("Selecciona un producto."); return
    try:
        cant = int(e_venta_cant.get()); assert cant > 0
    except:
        add_msg_var.set("Cantidad inválida."); return

    prod = _productos_map[sel]
    pid, cod, nom, cant_stock, precio, foto = prod

    # Si ya está en el carrito, sumar cantidad
    for item in _carrito:
        if item["pid"] == pid:
            nueva = item["cant"] + cant
            if nueva > cant_stock:
                add_msg_var.set(f"Stock insuficiente. Máx: {cant_stock}"); return
            item["cant"] = nueva
            add_msg_var.set("")
            e_venta_cant.delete(0, "end")
            _refresh_cart()
            return

    if cant > cant_stock:
        add_msg_var.set(f"Stock insuficiente. Disponible: {cant_stock}"); return

    _carrito.append({"pid": pid, "nombre": nom, "cant": cant, "precio": precio})
    add_msg_var.set("")
    e_venta_cant.delete(0, "end")
    combo_producto.set("")
    _refresh_cart()
    resultado_var.set("")

def quitar_del_carrito():
    sel = tree_cart.selection()
    if not sel: return
    idx = tree_cart.index(sel[0])
    _carrito.pop(idx)
    _refresh_cart()

def limpiar_carrito():
    _carrito.clear()
    _refresh_cart()
    resultado_var.set("")
    add_msg_var.set("")

def confirmar_venta():
    if not _carrito:
        return messagebox.showwarning("Aviso", "El carrito está vacío.")
    items = [(i["pid"], i["cant"]) for i in _carrito]
    total, err = db.registrar_ventas(items)
    if err:
        resultado_var.set(f"❌  {err}")
        resultado_lbl.config(fg=RED_H)
    else:
        lineas = "\n".join(f"• {i['nombre']}  x{i['cant']}  ${i['cant']*i['precio']:.2f}"
                           for i in _carrito)
        resultado_var.set(f"✅ Venta confirmada\n\n{lineas}\n\n💰 Total: ${total:.2f}")
        resultado_lbl.config(fg=GREEN_H)
        limpiar_carrito()
        cargar_inventario()
        cargar_historial()

# Botones
btn(v_left, "+ Agregar al carrito", agregar_al_carrito, ACCENT, ACCENT_H).pack(anchor="w", pady=(0,6))

cart_btns = tk.Frame(cart_footer, bg=CARD)
cart_btns.pack(side="right")
btn(cart_btns, "✕ Quitar",  quitar_del_carrito, CARD2, BORDER).pack(side="left", padx=(0,6))
btn(cart_btns, "🗑 Limpiar", limpiar_carrito,    CARD2, BORDER).pack(side="left")

btn(v_right, "✅  Confirmar Venta", confirmar_venta, GREEN, GREEN_H).pack(anchor="w", pady=(10,0), fill="x")

# ═══════════════════════════════════════════════════════════
# PÁGINA HISTORIAL
# ═══════════════════════════════════════════════════════════
p_hist = tk.Frame(main_area, bg=BG)
pages["hist"] = p_hist

tk.Label(p_hist, text="Historial de Ventas", bg=BG, fg=FG,
         font=("Segoe UI",18,"bold")).pack(anchor="w", padx=24, pady=(20,12))

hf = tk.Frame(p_hist, bg=BG)
hf.pack(fill="both", expand=True, padx=24, pady=(0,16))

cols_h = ("id","codigo","nombre","cantidad","total","fecha")
tree_hist = ttk.Treeview(hf, columns=cols_h, show="headings",
                          style="Hist.Treeview", selectmode="browse")
for c,w,a in [("id",40,"center"),("codigo",110,"center"),("nombre",240,"w"),
               ("cantidad",70,"center"),("total",90,"center"),("fecha",170,"w")]:
    tree_hist.heading(c, text={"id":"#","codigo":"Código","nombre":"Producto",
                                "cantidad":"Cant.","total":"Total","fecha":"Fecha y Hora"}[c])
    tree_hist.column(c, width=w, anchor=a)

sb_h = ttk.Scrollbar(hf, orient="vertical", command=tree_hist.yview)
tree_hist.configure(yscrollcommand=sb_h.set)
tree_hist.pack(side="left", fill="both", expand=True)
sb_h.pack(side="left", fill="y")

def cargar_historial():
    tree_hist.delete(*tree_hist.get_children())
    for row in db.get_ventas():
        vid, cod, nom, cant, total, fecha = row
        tree_hist.insert("", "end", values=(vid, cod or "—", nom, cant, f"${total:.2f}", fecha))

# ── Carga inicial ─────────────────────────────────────────
cargar_inventario()
actualizar_combo_venta()
cargar_historial()
show_page("inv")

root.mainloop()
