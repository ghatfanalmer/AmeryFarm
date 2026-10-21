import os
import logging
from flask iimport os
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==================== SETUP ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

app = Flask(__name__)

@app.route('/')
def home():
    return "Amery Farm Bot Aktif!", 200

@app.route('/health')
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# ==================== DATA SEMENTARA ====================
# Format: user_id -> data
user_data = {}

def get_user(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            "nama": "Petani",
            "level": 1,
            "exp": 0,
            "uang": 1000,
            "energi": 100,
            "inventaris": {
                "bibit_wortel": 5,
                "bibit_padi": 3,
                "kayu": 0,
                "batu": 0,
                "ikan": 0,
                "telur": 0,
            },
            "kebun": [],          # list tanaman yang sedang tumbuh
            "ternak": {
                "ayam": 0,
                "sapi": 0,
            }
        }
    return user_data[user_id]

# ==================== KEYBOARD MENU UTAMA ====================
def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🌱 Kebun", callback_data="menu_kebun"),
            InlineKeyboardButton("⛏️ Tambang", callback_data="menu_tambang"),
        ],
        [
            InlineKeyboardButton("🎣 Mancing", callback_data="menu_mancing"),
            InlineKeyboardButton("🐔 Ternak", callback_data="menu_ternak"),
        ],
        [
            InlineKeyboardButton("🎒 Inventaris", callback_data="menu_inventaris"),
            InlineKeyboardButton("👤 Profil", callback_data="menu_profil"),
        ],
        [
            InlineKeyboardButton("🛒 Toko", callback_data="menu_toko"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== HANDLER ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    data["nama"] = user.first_name or "Petani"

    text = (
        f"🌾 <b>Selamat datang di Amery Farm!</b>\n\n"
        f"Halo <b>{data['nama']}</b>!\n"
        f"Level: {data['level']} | Uang: 💰 {data['uang']:,} | Energi: ⚡ {data['energi']}\n\n"
        f"Pilih menu di bawah untuk mulai bertani:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = get_user(user_id)
    data_menu = query.data

    # ---------- KEBUN ----------
    if data_menu == "menu_kebun":
        text = (
            "🌱 <b>Kebun</b>\n\n"
            "Tanaman yang sedang tumbuh:\n"
        )
        if data["kebun"]:
            for i, tanaman in enumerate(data["kebun"], 1):
                text += f"{i}. {tanaman}\n"
        else:
            text += "Belum ada tanaman.\n"

        text += "\nPilih aksi:"
        keyboard = [
            [
                InlineKeyboardButton("🥕 Tanam Wortel", callback_data="tanam_wortel"),
                InlineKeyboardButton("🌾 Tanam Padi", callback_data="tanam_padi"),
            ],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="kembali")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ---------- TAMBANG ----------
    elif data_menu == "menu_tambang":
        text = (
            "⛏️ <b>Tambang</b>\n\n"
            "Kamu bisa menambang kayu dan batu.\n"
            "Energi yang dibutuhkan: 10\n\n"
            f"Energi saat ini: ⚡ {data['energi']}"
        )
        keyboard = [
            [
                InlineKeyboardButton("🪵 Tambang Kayu", callback_data="tambang_kayu"),
                InlineKeyboardButton("🪨 Tambang Batu", callback_data="tambang_batu"),
            ],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="kembali")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ---------- MANCING ----------
    elif data_menu == "menu_mancing":
        text = (
            "🎣 <b>Mancing</b>\n\n"
            "Pergi mancing untuk mendapatkan ikan.\n"
            "Energi yang dibutuhkan: 15\n\n"
            f"Energi saat ini: ⚡ {data['energi']}"
        )
        keyboard = [
            [InlineKeyboardButton("🎣 Mulai Mancing", callback_data="mancing")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="kembali")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ---------- TERNAK ----------
    elif data_menu == "menu_ternak":
        text = (
            "🐔 <b>Ternak</b>\n\n"
            f"Ayam: {data['ternak']['ayam']} ekor\n"
            f"Sapi: {data['ternak']['sapi']} ekor\n\n"
            "Kamu bisa membeli hewan di Toko."
        )
        keyboard = [
            [InlineKeyboardButton("🥚 Ambil Telur", callback_data="ambil_telur")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="kembali")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ---------- INVENTARIS ----------
    elif data_menu == "menu_inventaris":
        inv = data["inventaris"]
        text = (
            "🎒 <b>Inventaris</b>\n\n"
            f"🥕 Bibit Wortel : {inv['bibit_wortel']}\n"
            f"🌾 Bibit Padi   : {inv['bibit_padi']}\n"
            f"🪵 Kayu         : {inv['kayu']}\n"
            f"🪨 Batu         : {inv['batu']}\n"
            f"🐟 Ikan         : {inv['ikan']}\n"
            f"🥚 Telur        : {inv['telur']}\n"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="kembali")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ---------- PROFIL ----------
    elif data_menu == "menu_profil":
        text = (
            "👤 <b>Profil Petani</b>\n\n"
            f"Nama   : {data['nama']}\n"
            f"Level  : {data['level']}\n"
            f"EXP    : {data['exp']}/100\n"
            f"Uang   : 💰 {data['uang']:,}\n"
            f"Energi : ⚡ {data['energi']}/100\n"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="kembali")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ---------- TOKO ----------
    elif data_menu == "menu_toko":
        text = (
            "🛒 <b>Toko</b>\n\n"
            "Pilih barang yang ingin dibeli:\n\n"
            "🥕 Bibit Wortel - 50💰\n"
            "🌾 Bibit Padi   - 80💰\n"
            "🐔 Ayam         - 500💰\n"
            "🐄 Sapi         - 2000💰"
        )
        keyboard = [
            [
                InlineKeyboardButton("🥕 Beli Bibit Wortel", callback_data="beli_wortel"),
                InlineKeyboardButton("🌾 Beli Bibit Padi", callback_data="beli_padi"),
            ],
            [
                InlineKeyboardButton("🐔 Beli Ayam", callback_data="beli_ayam"),
                InlineKeyboardButton("🐄 Beli Sapi", callback_data="beli_sapi"),
            ],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="kembali")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ---------- AKSI ----------
    elif data_menu == "tanam_wortel":
        if data["inventaris"]["bibit_wortel"] > 0:
            data["inventaris"]["bibit_wortel"] -= 1
            data["kebun"].append("Wortel (sedang tumbuh)")
            await query.edit_message_text(
                "✅ Berhasil menanam <b>Wortel</b>!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Kebun", callback_data="menu_kebun")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Bibit wortel tidak cukup!", show_alert=True)

    elif data_menu == "tanam_padi":
        if data["inventaris"]["bibit_padi"] > 0:
            data["inventaris"]["bibit_padi"] -= 1
            data["kebun"].append("Padi (sedang tumbuh)")
            await query.edit_message_text(
                "✅ Berhasil menanam <b>Padi</b>!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Kebun", callback_data="menu_kebun")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Bibit padi tidak cukup!", show_alert=True)

    elif data_menu == "tambang_kayu":
        if data["energi"] >= 10:
            data["energi"] -= 10
            data["inventaris"]["kayu"] += 3
            await query.edit_message_text(
                "🪵 Kamu mendapatkan <b>3 Kayu</b>!\nEnergi tersisa: ⚡ " + str(data["energi"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_tambang")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Energi tidak cukup!", show_alert=True)

    elif data_menu == "tambang_batu":
        if data["energi"] >= 10:
            data["energi"] -= 10
            data["inventaris"]["batu"] += 2
            await query.edit_message_text(
                "🪨 Kamu mendapatkan <b>2 Batu</b>!\nEnergi tersisa: ⚡ " + str(data["energi"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_tambang")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Energi tidak cukup!", show_alert=True)

    elif data_menu == "mancing":
        if data["energi"] >= 15:
            data["energi"] -= 15
            data["inventaris"]["ikan"] += 2
            await query.edit_message_text(
                "🐟 Kamu berhasil menangkap <b>2 Ikan</b>!\nEnergi tersisa: ⚡ " + str(data["energi"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_mancing")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Energi tidak cukup!", show_alert=True)

    elif data_menu == "ambil_telur":
        if data["ternak"]["ayam"] > 0:
            telur = data["ternak"]["ayam"]  # 1 ayam = 1 telur
            data["inventaris"]["telur"] += telur
            await query.edit_message_text(
                f"🥚 Kamu mendapatkan <b>{telur} Telur</b>!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_ternak")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Kamu belum punya ayam!", show_alert=True)

    # ---------- BELI DI TOKO ----------
    elif data_menu == "beli_wortel":
        if data["uang"] >= 50:
            data["uang"] -= 50
            data["inventaris"]["bibit_wortel"] += 1
            await query.answer("✅ Berhasil membeli Bibit Wortel!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_padi":
        if data["uang"] >= 80:
            data["uang"] -= 80
            data["inventaris"]["bibit_padi"] += 1
            await query.answer("✅ Berhasil membeli Bibit Padi!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_ayam":
        if data["uang"] >= 500:
            data["uang"] -= 500
            data["ternak"]["ayam"] += 1
            await query.answer("✅ Berhasil membeli 1 Ayam!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_sapi":
        if data["uang"] >= 2000:
            data["uang"] -= 2000
            data["ternak"]["sapi"] += 1
            await query.answer("✅ Berhasil membeli 1 Sapi!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    # ---------- KEMBALI KE MENU UTAMA ----------
    elif data_menu == "kembali":
        text = (
            f"🌾 <b>Amery Farm</b>\n\n"
            f"Halo <b>{data['nama']}</b>!\n"
            f"Level: {data['level']} | Uang: 💰 {data['uang']:,} | Energi: ⚡ {data['energi']}\n\n"
            f"Pilih menu:"
        )
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

# ==================== MAIN ====================
def main():
    Thread(target=run_web, daemon=True).start()
    logger.info("Flask web server started")

    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Starting Amery Farm bot...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main() <b>2 Batu</b>!\nEnergi tersisa: ⚡ " + str(data["energi"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_tambang")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Energi tidak cukup!", show_alert=True)

    elif data_menu == "mancing":
        if data["energi"] >= 15:
            data["energi"] -= 15
            data["inventaris"]["ikan"] += 2
            await query.edit_message_text(
                "🐟 Kamu berhasil menangkap <b>2 Ikan</b>!\nEnergi tersisa: ⚡ " + str(data["energi"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_mancing")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Energi tidak cukup!", show_alert=True)

    elif data_menu == "ambil_telur":
        if data["ternak"]["ayam"] > 0:
            telur = data["ternak"]["ayam"]  # 1 ayam = 1 telur
            data["inventaris"]["telur"] += telur
            await query.edit_message_text(
                f"🥚 Kamu mendapatkan <b>{telur} Telur</b>!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_ternak")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Kamu belum punya ayam!", show_alert=True)

    # ---------- BELI DI TOKO ----------
    elif data_menu == "beli_wortel":
        if data["uang"] >= 50:
            data["uang"] -= 50
            data["inventaris"]["bibit_wortel"] += 1
            await query.answer("✅ Berhasil membeli Bibit Wortel!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_padi":
        if data["uang"] >= 80:
            data["uang"] -= 80
            data["inventaris"]["bibit_padi"] += 1
            await query.answer("✅ Berhasil membeli Bibit Padi!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_ayam":
        if data["uang"] >= 500:
            data["uang"] -= 500
            data["ternak"]["ayam"] += 1
            await query.answer("✅ Berhasil membeli 1 Ayam!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_sapi":
        if data["uang"] >= 2000:
            data["uang"] -= 2000
            data["ternak"]["sapi"] += 1
            await query.answer("✅ Berhasil membeli 1 Sapi!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    # ---------- KEMBALI KE MENU UTAMA ----------
    elif data_menu == "kembali":
        text = (
            f"🌾 <b>Amery Farm</b>\n\n"
            f"Halo <b>{data['nama']}</b>!\n"
            f"Level: {data['level']} | Uang: 💰 {data['uang']:,} | Energi: ⚡ {data['energi']}\n\n"
            f"Pilih menu:"
        )
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

# ==================== MAIN ====================
def main():
    Thread(target=run_web, daemon=True).start()
    logger.info("Flask web server started")

    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Starting Amery Farm bot...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
