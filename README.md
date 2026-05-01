# 📦 Inventario Pro

Sistema de gestión de inventario con interfaz gráfica y bot de WhatsApp para cotizaciones.

## Características

- Gestión de productos con código, nombre, cantidad, precio y foto
- Registro de ventas con carrito multi-producto
- Historial de ventas con fecha y hora local
- Búsqueda en tiempo real
- Alertas de stock bajo (≤5) y agotado
- Splash screen al iniciar
- Bot de WhatsApp para consultas y cotizaciones

## Requisitos

- Python 3.12+
- Node.js 18+

## Instalación

### App de escritorio
```bash
pip install pillow flask
python app.py
```

### Bot de WhatsApp
```bash
cd bot
npm install
```
Edita `bot/bot.js` y cambia `TUNUMERO` por tu número en formato internacional (ej: `573001234567`).

## Uso

### App de escritorio
```bash
python app.py
# o doble clic en iniciar.bat
```

### Bot + API
```bash
# doble clic en iniciar_bot.bat
# o manualmente:
python api.py          # terminal 1
cd bot && node bot.js  # terminal 2
```

### Comandos del bot de WhatsApp
| Comando | Descripción |
|---|---|
| `!catalogo` | Lista todos los productos |
| `!buscar <texto>` | Busca por nombre o código |
| `!precio <nombre>` | Precio y stock de un producto |
| `!cotizar` | Inicia cotización interactiva |
| `!ayuda` | Muestra el menú |

## Estructura
```
invt/
├── app.py              # Interfaz gráfica (Tkinter)
├── database.py         # Lógica de base de datos (SQLite)
├── api.py              # API REST (Flask) para el bot
├── iniciar.bat         # Inicia la app de escritorio
├── iniciar_bot.bat     # Inicia API + bot de WhatsApp
└── bot/
    ├── bot.js          # Bot de WhatsApp (Baileys)
    └── package.json
```
