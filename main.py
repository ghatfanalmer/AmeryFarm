import os
import logging
import sqlite3
import json
from flask import Flask, send_file
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Amery Farm Bot Aktif!", 200

@app.route('/health')
def health():
    return "OK", 200

DB_FILE = "amery_farm.db"

@app.route('/download-db')
def download_db():
    try:
        return send_file(DB_FILE, as_attachment=True)
    except Exception as e:
        return str(e), 404 

# ==================== SETUP DATABASE ====================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            nama TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            uang INTEGER DEFAULT 1000,
            energi INTEGER DEFAULT 100,
            bibit_wortel INTEGER DEFAULT 5,
            bibit_padi INTEGER DEFAULT 3,
            kayu INTEGER DEFAULT 0,
            batu INTEGER DEFAULT 0,
            ikan INTEGER DEFAULT 0,
            telur INTEGER DEFAULT 0,
            ayam INTEGER DEFAULT 0,
            sapi INTEGER DEFAULT 0,
            kebun TEXT DEFAULT '[]'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id: int, default_name: str = "Petani"):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute('''
            INSERT INTO users (user_id, nama, level, exp, uang, energi, bibit_wortel, bibit_padi, kayu, batu, ikan, telur, ayam, sapi, kebun)
            VALUES (?, ?, 1, 0, 1000, 100, 5, 3, 0, 0, 0, 0, 0, 0, '[]')
        ''', (user_id, default_name))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
    
    conn.close()
    return row

def save_user(user_id, data_dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET 
            nama = ?, level = ?, exp = ?, uang = ?, energi = ?,
            bibit_wortel = ?, bibit_padi = ?, kayu = ?, batu = ?, ikan = ?, telur = ?,
            ayam = ?, sapi = ?, kebun = ?
        WHERE user_id = ?
    ''', (
        data_dict["nama"], data_dict["level"], data_dict["exp"], data_dict["uang"], data_dict["energi"],
        data_dict["bibit_wortel"], data_dict["bibit_padi"], data_dict["kayu"], data_dict["batu"],
        data_dict["ikan"], data_dict["telur"], data_dict["ayam"], data_dict["sapi"],
        json.dumps(data_dict["kebun"]), user_id
    ))
    conn.commit()
    conn.close()

def row_to_dict(row):
    return {
        "nama": row["nama"],
        "level": row["level"],
        "exp": row["exp"],
        "uang": row["uang"],
        "energi": row["energi"],
        "inventaris": {
            "bibit_wortel": row["bibit_wortel"],
            "bibit_padi": row["bibit_padi"],
            "kayu": row["kayu"],
            "batu": row["batu"],
            "ikan": row["ikan"],
            "telur": row["telur"],
        },
        "kebun": json.loads(row["kebun"]),
        "ternak": {
            "ayam": row["ayam"],
            "sapi": row["sapi"],
        }
    }

# ==================== SETUP FLASK & LOGGING ====================
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
    row = get_user(user.id, user.first_name or "Petani")
    data = row_to_dict(row)
    
    if data["nama"] != (user.first_name or "Petani"):
        data["nama"] = user.first_name or "Petani"
        save_user(user.id, data)

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
    row = get_user(user_id, query.from_user.first_name or "Petani")
    data = row_to_dict(row)
    data_menu = query.data

    # ---------- KEBUN ----------
    if data_menu == "menu_kebun":
        text = "🌱 <b>Kebun</b>\n\nTanaman yang sedang tumbuh:\n"
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
            save_user(user_id, data)
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
            save_user(user_id, data)
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
            save_user(user_id, data)
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
            save_user(user_id, data)
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
            save_user(user_id, data)
            await query.edit_message_text(
                "🐟 Kamu berhasil menangkap <b>2 Ikan</b>!\nEnergi tersisa: ⚡ " + str(data["energi"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_mancing")]]),
                parse_mode="HTML"
            )
        else:
            await query.answer("Energi tidak cukup!", show_alert=True)

    elif data_menu == "ambil_telur":
        if data["ternak"]["ayam"] > 0:
            telur = data["ternak"]["ayam"]
            data["inventaris"]["telur"] += telur
            save_user(user_id, data)
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
            save_user(user_id, data)
            await query.answer("✅ Berhasil membeli Bibit Wortel!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_padi":
        if data["uang"] >= 80:
            data["uang"] -= 80
            data["inventaris"]["bibit_padi"] += 1
            save_user(user_id, data)
            await query.answer("✅ Berhasil membeli Bibit Padi!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_ayam":
        if data["uang"] >= 500:
            data["uang"] -= 500
            data["ternak"]["ayam"] += 1
            save_user(user_id, data)
            await query.answer("✅ Berhasil membeli 1 Ayam!", show_alert=True)
        else:
            await query.answer("Uang tidak cukup!", show_alert=True)

    elif data_menu == "beli_sapi":
        if data["uang"] >= 2000:
            data["uang"] -= 2000
            data["ternak"]["sapi"] += 1
            save_user(user_id, data)
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

    logger.info("Starting Amery Farm bot with SQLite...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
