/**
 * bot.js  —  Bot de WhatsApp con Baileys
 * Genera QR en terminal, no requiere Chromium.
 *
 * Comandos:
 *   !catalogo          → lista todos los productos
 *   !buscar <texto>    → busca por nombre o código
 *   !precio <nombre>   → precio y stock de un producto
 *   !cotizar           → cotización interactiva multi-producto
 *   !ayuda             → menú de comandos
 */

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require("baileys");
const qrcode = require("qrcode-terminal");
const axios  = require("axios");
const pino   = require("pino");
const path   = require("path");

const API          = "http://localhost:5000";
const AUTH_FOLDER  = path.join(__dirname, "auth_info");

// Número del dueño — formato: "573001234567" (sin + ni espacios)
const OWNER_NUMBER = "numero"; // <-- cambia esto

const sesiones = {};

async function iniciarBot() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
    const { version }          = await fetchLatestBaileysVersion();

    const sock = makeWASocket({
        version,
        auth:   state,
        logger: pino({ level: "silent" }),   // silencia logs internos
        printQRInTerminal: false,            // lo manejamos nosotros
        browser: ["Inventario Bot", "Chrome", "1.0.0"],
    });

    // ── QR ────────────────────────────────────────────────
    sock.ev.on("connection.update", async ({ connection, lastDisconnect, qr }) => {
        if (qr) {
            console.clear();
            console.log("╔══════════════════════════════════════╗");
            console.log("║   📱  Escanea el QR con WhatsApp     ║");
            console.log("║   Dispositivos vinculados → Vincular  ║");
            console.log("╚══════════════════════════════════════╝\n");
            qrcode.generate(qr, { small: true });
        }

        if (connection === "open") {
            console.log("\n✅ Bot conectado a WhatsApp.\n");
            // Enviar catálogo al dueño al iniciar
            try {
                const { data } = await axios.get(`${API}/productos`);
                const cat = data.length ? formatCatalogo(data) : "📭 No hay productos aún.";
                const msg = `🤖 *Bot de Inventario iniciado*\n${"─".repeat(28)}\nEl bot está activo y listo.\n\n${cat}`;
                await sock.sendMessage(`${OWNER_NUMBER}@s.whatsapp.net`, { text: msg });
                console.log("📨 Catálogo enviado al dueño.");
            } catch (e) {
                console.warn("⚠️  No se pudo enviar el catálogo inicial:", e.message);
            }
        }

        if (connection === "close") {
            const code = lastDisconnect?.error?.output?.statusCode;
            const reconectar = code !== DisconnectReason.loggedOut;
            console.log("🔌 Conexión cerrada. Código:", code);
            if (reconectar) {
                console.log("🔄 Reconectando...");
                iniciarBot();
            } else {
                console.log("❌ Sesión cerrada. Borra la carpeta auth_info y vuelve a iniciar.");
            }
        }
    });

    sock.ev.on("creds.update", saveCreds);

    // ── Mensajes ──────────────────────────────────────────
    sock.ev.on("messages.upsert", async ({ messages, type }) => {
        if (type !== "notify") return;

        for (const msg of messages) {
            if (!msg.message || msg.key.fromMe) continue;

            const from  = msg.key.remoteJid;
            const body  = (
                msg.message.conversation ||
                msg.message.extendedTextMessage?.text || ""
            ).trim();
            const lower = body.toLowerCase();

            const reply = async (text) => {
                await sock.sendMessage(from, { text }, { quoted: msg });
            };

            // Sesión activa de cotización
            if (sesiones[from]) {
                await manejarSesion(reply, from, body, lower);
                continue;
            }

            if (lower === "!ayuda" || lower === "!hola" || lower === "!menu") {
                await reply(textoAyuda()); continue;
            }

            if (lower === "!catalogo") {
                try {
                    const { data } = await axios.get(`${API}/productos`);
                    await reply(data.length ? formatCatalogo(data) : "📭 No hay productos en el inventario.");
                } catch { await reply("❌ No se pudo conectar con el servidor."); }
                continue;
            }

            if (lower.startsWith("!buscar ")) {
                const q = body.slice(8).trim();
                try {
                    const { data } = await axios.get(`${API}/productos?q=${encodeURIComponent(q)}`);
                    await reply(data.length ? formatCatalogo(data) : `🔍 No se encontraron productos para *"${q}"*.`);
                } catch { await reply("❌ Error al buscar productos."); }
                continue;
            }

            if (lower.startsWith("!precio ")) {
                const q = body.slice(8).trim();
                try {
                    const { data } = await axios.get(`${API}/productos?q=${encodeURIComponent(q)}`);
                    if (!data.length) { await reply(`❌ Producto *"${q}"* no encontrado.`); continue; }
                    const p = data[0];
                    await reply(
                        `📦 *${p.nombre}*\n` +
                        `Código: ${p.codigo || "—"}\n` +
                        `💰 Precio: $${p.precio.toFixed(2)}\n` +
                        (p.stock > 0 ? `✅ Disponible: ${p.stock} unidades` : `❌ Sin stock`)
                    );
                } catch { await reply("❌ Error al consultar el precio."); }
                continue;
            }

            if (lower === "!cotizar") {
                sesiones[from] = { paso: "esperando_items", items: [] };
                await reply(
                    `🛒 *Iniciando cotización*\n\n` +
                    `Escribe cada producto en este formato:\n` +
                    `*nombre del producto, cantidad*\n\n` +
                    `Ejemplo:\n_Camisa azul, 3_\n_Pantalón negro, 2_\n\n` +
                    `Escribe *listo* para ver el total.\n` +
                    `Escribe *cancelar* para salir.`
                );
                continue;
            }

            await reply(`👋 No entendí ese mensaje.\nEscribe *!ayuda* para ver los comandos.`);
        }
    });
}

// ── Flujo de cotización ───────────────────────────────────
async function manejarSesion(reply, from, body, lower) {
    const sesion = sesiones[from];

    if (lower === "cancelar") {
        delete sesiones[from];
        await reply("❌ Cotización cancelada.");
        return;
    }

    if (sesion.paso === "esperando_items") {
        if (lower === "listo") {
            if (!sesion.items.length) {
                await reply("⚠️ No agregaste ningún producto. Escribe *cancelar* para salir.");
                return;
            }
            try {
                const { data } = await axios.post(`${API}/cotizar`, sesion.items);
                let resp = `✅ *Cotización*\n${"─".repeat(28)}\n`;
                for (const it of data.items) {
                    resp += `• ${it.nombre}\n  ${it.cantidad} x $${it.precio_unit.toFixed(2)} = *$${it.subtotal.toFixed(2)}*\n`;
                }
                resp += `${"─".repeat(28)}\n💰 *TOTAL: $${data.total.toFixed(2)}*\n\n_¿Confirmar pedido? Responde *sí* o *no*._`;
                sesion.paso = "confirmando";
                sesion.cotizacion = data;
                await reply(resp);
            } catch (err) {
                await reply(`❌ ${err.response?.data?.error || "Error al calcular la cotización."}`);
                delete sesiones[from];
            }
            return;
        }

        const partes   = body.split(",");
        const nombre   = partes[0]?.trim();
        const cantidad = parseInt(partes[1]?.trim());
        if (partes.length < 2 || !nombre || isNaN(cantidad) || cantidad <= 0) {
            await reply(`⚠️ Formato: *nombre, cantidad*\nEjemplo: _Camisa azul, 3_\nO escribe *listo* / *cancelar*.`);
            return;
        }
        try {
            const { data } = await axios.get(`${API}/productos?q=${encodeURIComponent(nombre)}`);
            if (!data.length) { await reply(`❌ No encontré *"${nombre}"*. Verifica el nombre.`); return; }
            const prod     = data[0];
            const existing = sesion.items.find(i => i.nombre.toLowerCase() === prod.nombre.toLowerCase());
            if (existing) {
                existing.cantidad += cantidad;
            } else {
                sesion.items.push({ nombre: prod.nombre, cantidad });
            }
            await reply(
                `✅ *${prod.nombre}* x${cantidad} — $${(prod.precio * cantidad).toFixed(2)}\n\n` +
                `Agrega más o escribe *listo* para ver el total.`
            );
        } catch { await reply("❌ Error al verificar el producto."); }
        return;
    }

    if (sesion.paso === "confirmando") {
        if (["sí","si","s","yes"].includes(lower)) {
            await reply(
                `🎉 *¡Pedido registrado!*\n` +
                `Total: *$${sesion.cotizacion.total.toFixed(2)}*\n\n` +
                `Nos pondremos en contacto para coordinar la entrega. ¡Gracias! 🙏`
            );
        } else {
            await reply("👍 Entendido. Escribe *!cotizar* cuando quieras intentarlo de nuevo.");
        }
        delete sesiones[from];
    }
}

// ── Helpers ───────────────────────────────────────────────
function formatCatalogo(prods) {
    let txt = `📦 *Catálogo de productos*\n${"─".repeat(28)}\n`;
    for (const p of prods) {
        txt += `*${p.nombre}*\n`;
        txt += `  Cód: ${p.codigo || "—"}  |  💰 $${p.precio.toFixed(2)}  |  ${p.stock > 0 ? `✅ ${p.stock} uds` : "❌ Sin stock"}\n\n`;
    }
    txt += `_Escribe !cotizar para solicitar una cotización._`;
    return txt;
}

function textoAyuda() {
    return (
        `🤖 *Bot de Inventario*\n${"─".repeat(28)}\n` +
        `!catalogo — Ver todos los productos\n` +
        `!buscar <texto> — Buscar producto\n` +
        `!precio <nombre> — Precio y stock\n` +
        `!cotizar — Solicitar cotización\n` +
        `!ayuda — Ver este menú\n` +
        `${"─".repeat(28)}\n_Escribe un comando para comenzar._`
    );
}

iniciarBot();
