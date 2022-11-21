from datetime import datetime
from flask import Flask
from flask import request
from telegram import Update
from telegram.ext import (Updater, CommandHandler, CallbackContext)
from loguru import logger as log
import pytz
import mysql.connector
import dotenv
import os

app = Flask(__name__)
dotenv.load_dotenv()
database = mysql.connector.connect(
    host=os.getenv("BOT_MYSQL_HOST"),
    port=os.getenv("BOT_MYSQL_PORT"),
    user=os.getenv("BOT_MYSQL_USER"),
    password=os.getenv("BOT_MYSQL_PASS"),
    database="lightsout"
)


def get_current_timestamp():
    return datetime.now(pytz.timezone('Europe/Kyiv'))


def get_database_connection():
    if database.is_connected():
        return database
    else:
        log.info("Reconnecting to database...")
        database.reconnect()
        return database


def get_telegram_subscribers():
    cursor = database.cursor()
    cursor.execute("SELECT user_id FROM telegram_subscribers")
    return [item[0] for item in cursor.fetchall()]


def add_telegram_subscriber(user_id: int):
    cursor = database.cursor()
    cursor.execute("INSERT INTO telegram_subscribers (user_id) VALUES (%s)", (user_id,))
    database.commit()
    log.info(f"Added user {user_id} to subscribers list")


def remove_telegram_subscriber(user_id: int):
    cursor = database.cursor()
    cursor.execute("DELETE FROM telegram_subscribers WHERE user_id = %s", (user_id,))
    database.commit()
    log.info(f"Removed user {user_id} from subscribers list")


def is_authorized_blackout_notifier(headers):
    return 'X-API-KEY' in headers and headers['X-API-KEY'] == os.getenv("BOT_API_KEY")


def is_telegram_user_subscribed(user_id: int):
    cursor = database.cursor()
    cursor.execute("SELECT * FROM telegram_subscribers WHERE user_id = %s", (user_id,))
    return len(cursor.fetchall()) > 0


def is_telegram_user_authorized(user_id: int):
    cursor = database.cursor()
    cursor.execute("SELECT * FROM telegram_authorized_users WHERE user_id = %s", (user_id,))
    return len(cursor.fetchall()) > 0


def register_power_off(timestamp: datetime):
    cursor = get_database_connection().cursor()
    cursor.execute("INSERT INTO power_outages (time_started) VALUES (%s)", (timestamp.strftime('%Y-%m-%d %H:%M:%S'),))
    database.commit()


def register_power_on(timestamp: datetime):
    cursor = get_database_connection().cursor()
    cursor.execute("SELECT id FROM power_outages ORDER BY id DESC LIMIT 1")
    last_id = cursor.fetchall()[0][0]
    cursor.execute("UPDATE power_outages SET time_ended = %s WHERE time_ended IS NULL AND id = %s", (timestamp.strftime('%Y-%m-%d %H:%M:%S'), last_id))
    database.commit()


def telegram_send_notifications(notification_text: str):
    for subscriber in get_telegram_subscribers():
        telegram_updater.bot.send_message(chat_id=subscriber, text=notification_text)


def telegram_handler_start(update: Update, context: CallbackContext) -> None:
    if is_telegram_user_authorized(update.message.from_user.id):
        update.message.reply_text('Тепер ви отримуватимете сповіщення щодо наявності світла!')
        if not is_telegram_user_subscribed(update.message.from_user.id):
            add_telegram_subscriber(update.message.from_user.id)


def telegram_handler_stop(update: Update, context: CallbackContext) -> None:
    if is_telegram_user_authorized(update.message.from_user.id):
        remove_telegram_subscriber(update.message.from_user.id)
        update.message.reply_text('Сповіщення вимкнені!')


def handle_power_off():
    event_timestamp = get_current_timestamp()
    log.info(f"Power outage detected on {event_timestamp}!")
    register_power_off(event_timestamp)
    telegram_send_notifications(f'\U00002757 Електропостачання припинено о {event_timestamp.strftime("%H:%M")}!')


def handle_power_on():
    event_timestamp = get_current_timestamp()
    log.info(f"Power restored on {event_timestamp}!")
    register_power_on(event_timestamp)
    telegram_send_notifications(f'\U00002b50 Електропостачання відновлено о {event_timestamp.strftime("%H:%M")}!')


@app.route('/power_on', methods=['POST'])
def light_on():
    if is_authorized_blackout_notifier(request.headers):
        handle_power_on()
        return 'OK'
    else:
        log.warning(f"Unauthorized power on request: {request}")
        return 'Unauthorized', 401


@app.route('/power_off', methods=['POST'])
def light_off():
    if is_authorized_blackout_notifier(request.headers):
        handle_power_off()
        return 'OK'
    else:
        log.warning(f"Unauthorized power off request: {request}")
        return 'Unauthorized', 401


telegram_updater = Updater(os.getenv("TELEGRAM_TOKEN"))
telegram_updater.dispatcher.add_handler(CommandHandler("start", telegram_handler_start))
telegram_updater.dispatcher.add_handler(CommandHandler("stop", telegram_handler_stop))
telegram_updater.start_polling()
app.run(host="0.0.0.0", port=8080)
