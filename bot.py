import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")
CHAVE_PIX = os.environ.get("CHAVE_PIX")

def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY, saldo REAL DEFAULT 0, data_cadastro TEXT)''')
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
            await query.edit_message_text(
                f"✅ Compra de {query.data.upper()} realizada!\n"
                f"Novo saldo: R$ {get_saldo(user_id):.2f}"
            )
        else:
            await query.edit_message_text(
                f"❌ Saldo insuficiente!\n"
                f"Preço: R$ {preco:.2f} | Seu saldo: R$ {saldo:.2f}"
            )
    
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
            f"📌 Chave Pix: `{CHAVE_PIX}`\n\n"
            f"⚠️ Após o pagamento, envie o comprovante para @LuckyZEROON com seu ID: `{user_id}`"
        )
    
    elif query.data == "voltar":
        await start(update, context)

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🔥 Bot rodando, arrombado!")
    app.run_polling()  # Agora usa polling, que é mais simples

if __name__ == "__main__":
    main()
