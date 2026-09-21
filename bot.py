import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================= የእርስዎ መረጃ =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CHANNEL_USERNAME = "@ab_tech8"
# ==============================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member = await check_membership(user_id, context)

    if is_member:
        await update.message.reply_text("✅ እንኳን ደህና መጡ!\n\n🤖 ማንኛውንም ፅሁፍ ይላኩ፣ AI መልስ ይሰጣል።")
    else:
        keyboard = [
            [InlineKeyboardButton("📢 ቻናሉን ተቀላቀል", url="https://t.me/ab_tech8")],
            [InlineKeyboardButton("✅ I Have Joined", callback_data="check_join")]
        ]
        await update.message.reply_text(
            "👋 እንኳን ደህና መጡ!\n\nቦቱን ለመጠቀም መጀመሪያ ቻናላችንን መቀላቀል አለብዎት።\nከዚያ 'I Have Joined' ይጫኑ።",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_join":
        user_id = query.from_user.id
        is_member = await check_membership(user_id, context)
        if is_member:
            await query.message.edit_text("✅ አባልነትዎ ተረጋግጧል!\n\n🤖 ማንኛውንም ፅሁፍ ይላኩ፣ AI መልስ ይሰጣል።")
        else:
            await query.answer("❌ እባክዎ መጀመሪያ ቻናሉን ይቀላሉ!", show_alert=True)

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member = await check_membership(user_id, context)
    
    if not is_member:
        await update.message.reply_text("❌ እባክዎ መጀመሪያ ቻናሉን ይቀላቀሉ! /start")
        return
    
    user_message = update.message.text
    await update.message.chat.send_action("typing")
    
    try:
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"❌ ስህተት ተፈጥሯል: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
    print("🤖 ቦቱ በስራ ላይ ነው...")
    app.run_polling()

# ================= የPort ማዳመጫ (Render እንዲያረጋግጥ) =================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    main()
