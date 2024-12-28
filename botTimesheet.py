import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import xmlrpc.client

# Konfigurasi API Token dan Chat ID untuk Telegram Bot
API_TOKEN = '<your Telegram bot token>'
chat_id = '<your Telegram chat ID>'

# Koneksi ke Odoo
ODOO_URL = '<your Odoo URL>'  # URL Odoo Anda
ODOO_DB = '<your Odoo DB name>'  # Nama database Odoo
ODOO_USER = '<your Odoo username>'  # Username Odoo
ODOO_PASSWORD = '<your Odoo password'  # Password Odoo

# Fungsi untuk melakukan autentikasi ke Odoo
def connect_to_odoo():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return models, uid

# Fungsi untuk mencatat timesheet di Odoo
def log_timesheet(description, start_time, end_time, task_id, user_id):
    models, uid = connect_to_odoo()

    # Membuat entri timesheet
    timesheet_data = {
        'name': description,
        'unit_amount': 1,  # Anda bisa menyesuaikan unit_amount dengan lama waktu
        'task_id': task_id,  # ID tugas di Odoo, jika ada
        'employee_id': user_id,  # ID karyawan yang mengisi timesheet
        'sheet_id': user_id,  # ID sheet timesheet karyawan
        'start_datetime': start_time,
        'end_datetime': end_time
    }

    timesheet_entry = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'account.analytic.line', 'create', [timesheet_data])
    print("Timesheet entry created:", timesheet_entry)

# Fungsi untuk mengirimkan pengingat
def send_reminder(context):
    bot = context.bot
    bot.send_message(chat_id=chat_id, text=f"Jam {datetime.datetime.now().strftime('%H:%M')}: Apa yang sedang Anda kerjakan?")

# Fungsi untuk menerima input kegiatan dari pengguna dan menghubungkannya ke Odoo
def handle_message(update: Update, context):
    user_input = update.message.text  # Kegiatan yang diinputkan oleh pengguna
    current_time = datetime.datetime.now()
    start_time = current_time.replace(second=0, microsecond=0)  # Jam mulai kegiatan
    end_time = start_time + datetime.timedelta(hours=1)  # Waktu selesai, misalnya 1 jam setelah start

    # Tentukan ID Task dan ID Karyawan (misalnya dengan menggunakan ID pengguna Telegram)
    task_id = 1  # Sesuaikan dengan task ID yang ada di Odoo
    user_id = 1  # Sesuaikan dengan ID karyawan yang sesuai di Odoo

    # Mencatat timesheet ke Odoo
    log_timesheet(user_input, start_time, end_time, task_id, user_id)

    # Memberi konfirmasi kepada pengguna bahwa data sudah dicatat
    update.message.reply_text(f"Timesheet untuk '{user_input}' telah dicatat.")

# Fungsi untuk memulai bot dan scheduler
def start_bot():
    application = Application.builder().token(API_TOKEN).build()

    scheduler = BackgroundScheduler()

    # Pengingat otomatis setiap jam pada jam kerja
    scheduler.add_job(send_reminder, 'interval', hours=1, start_date='2024-01-01 08:30:00', end_date='2024-01-01 17:30:00', args=[application])
    scheduler.start()

    # Menangani pesan dari pengguna
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    start_bot()
