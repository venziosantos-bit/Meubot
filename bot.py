import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== CONFIGURAÇÕES =====
TOKEN = "8958451748:AAH3auDxSmouvUD928Zwd5n36gKZNfvHHQA"
CHAVE_PIX = "77991204628"

# ===== BANCO DE DADOS =====
def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY, 
                  saldo REAL DEFAULT 0, 
                  data_cadastro TEXT)''')
    conn.commit()
    conn.close()

def adicionar_usuario(user_id):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO usuarios (id, data_cadastro) VALUES (?, ?)', 
              (user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_saldo(user_id):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('SELECT saldo FROM usuarios WHERE id = ?', (user_id,))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else 0.0

def atualizar_saldo(user_id, valor):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('UPDATE usuarios SET saldo = saldo + ? WHERE id = ?', (valor, user_id))
    conn.commit()
    conn.close()

# ===== FUNÇÕES DO BOT =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nome = update.effective_user.first_name
    
    adicionar_usuario(user_id)
    saldo = get_saldo(user_id)
    
    mensagem = (
        f"💳 Bem vindo à central de vendas, {nome}!\n"
        f"Explore o bot pelos botões abaixo.\n\n"
        f"🏦 Carteira\n"
        f" ├ ID: {user_id}\n"
        f" ├💰 Saldo: R$ {saldo:.2f}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎁 Comprar Gift Card", callback_data="comprar")],
        [InlineKeyboardButton("👤 Minha conta", callback_data="conta")],
        [InlineKeyboardButton("💰 Adicionar saldo", callback_data="pix")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(mensagem, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data == "comprar":
        keyboard = [
            [InlineKeyboardButton("Steam R$ 50", callback_data="steam")],
            [InlineKeyboardButton("PlayStation R$ 60", callback_data="ps")],
            [InlineKeyboardButton("Xbox R$ 55", callback_data="xbox")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]
        ]
        await query.edit_message_text("Escolha o gift:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data in ["steam", "ps", "xbox"]:
        precos = {"steam": 50, "ps": 60, "xbox": 55}
        preco = precos[query.data]
        saldo = get_saldo(user_id)
        
        if saldo >= preco:
            atualizar_saldo(user_id, -preco)
            await query.edit_message_text(f"✅ Compra de {query.data.upper()} realizada! Código enviado em breve.\nNovo saldo: R$ {get_saldo(user_id):.2f}")
        else:
            await query.edit_message_text(f"❌ Saldo insuficiente! Preço: R$ {preco:.2f} | Seu saldo: R$ {saldo:.2f}")
    
    elif query.data == "conta":
        saldo = get_saldo(user_id)
        await query.edit_message_text(
            f"🏦 Sua Carteira\n"
            f" ├ ID: {user_id}\n"
            f" ├💰 Saldo: R$ {saldo:.2f}\n"
            f" 📅 Cadastro: {datetime.now().strftime('%d/%m/%Y')}"
        )
    
    elif query.data == "pix":
        await query.edit_message_text(
            f"💰 Adicione saldo via PIX\n\n"
            f"📌 **Chave Pix:** `{CHAVE_PIX}`\n"
            f"💰 Valor mínimo: R$ 10,00\n\n"
            f"⚠️ **Após o pagamento:**\n"
            f"1️⃣ Envie o comprovante para @LuckyZEROON\n"
            f"2️⃣ Informe seu ID: `{user_id}`\n\n"
            f"⏳ O saldo será adicionado manualmente em até 30 minutos."
        )
    
    elif query.data == "voltar":
        await start(update, context)

# ===== COMANDOS ADMIN =====
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != 8836053664:
        await update.message.reply_text("🚫 Sem permissão.")
        return
    
    try:
        args = context.args
        if len(args) >= 2:
            alvo = int(args[0])
            valor = float(args[1])
            atualizar_saldo(alvo, valor)
            await update.message.reply_text(f"✅ Saldo de {alvo} atualizado em R$ {valor:.2f}")
        else:
            await update.message.reply_text("📌 Uso: /admin ID VALOR")
    except:
        await update.message.reply_text("❌ Erro! Use /admin ID VALOR")

async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != 8836053664:
        await update.message.reply_text("🚫 Sem permissão.")
        return
    
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('SELECT id, saldo, data_cadastro FROM usuarios LIMIT 10')
    usuarios = c.fetchall()
    conn.close()
    
    if usuarios:
        msg = "📋 Últimos usuários:\n\n"
        for uid, saldo, data in usuarios:
            msg += f"ID: {uid} | Saldo: R$ {saldo:.2f} | Cadastro: {data[:10]}\n"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("📭 Nenhum usuário cadastrado.")

# ===== MAIN =====
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("listar", listar))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🔥 Bot rodando, arrombado!")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )

if __name__ == "__main__":
    main()