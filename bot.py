import telebot
import os
import time
import requests
import json
from datetime import datetime
from dotenv import load_dotenv  # For loading environment variables

# Load environment variables from a .env file
load_dotenv()

# Retrieve necessary environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
TARGET_BOT_CHAT_ID = os.getenv('TARGET_BOT_CHAT_ID')  # The target bot's chat ID to forward registration details
OWNER_ID = int(os.getenv('OWNER_ID'))  # The owner's Telegram ID
OWNER_NAME = '@Jukerhenapadega'  # Hardcoded owner username

# Initialize the bot with the token
bot = telebot.TeleBot(BOT_TOKEN)

# In-memory storage for banned users
banned_users = []

# Handle /scr command
@bot.message_handler(commands=['scr'])
def scrape_ccs(message):
    chat_id = message.chat.id
    if chat_id in banned_users:
        bot.send_message(chat_id, f"You are banned from using this bot by {OWNER_NAME}.")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Please provide both username and limit. Usage: /scr username limit")
        return
    username = args[1]
    limit = args[2]
    start_time = time.time()
    msg = bot.send_message(chat_id, 'Scraping...')
    
    bot.send_chat_action(chat_id, 'typing')  # Animated typing indicator
    
    try:
        response = requests.get(f'https://scrd-3c14ab273e76.herokuapp.com/scr', params={'username': username, 'limit': limit}, timeout=120)
        raw = response.json()
        if 'error' in raw:
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"Error: {raw['error']}")
        else:
            cards = raw['cards']
            found = str(raw['found'])
            file = f'x{found}_Scrapped_by_{OWNER_NAME}.txt'
            
            if cards:
                with open(file, "w") as f:
                    f.write(cards)
                with open(file, "rb") as f:
                    bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
                    end_time = time.time()
                    time_taken = end_time - start_time
                    cap = (f'<b>Scraped Successfully ✅</b>\n'
                           f'Target: <code>{username}</code>\n'
                           f'Found: <code>{found}</code>\n'
                           f'Time Taken: <code>{time_taken:.2f} seconds</code>\n'
                           f'Scrapped by {OWNER_NAME}\n'
                           f'Requested By: <code>{message.from_user.first_name}</code>')
                    bot.send_document(chat_id=chat_id, document=f, caption=cap, parse_mode='HTML')
                try:
                    os.remove(file)
                except PermissionError as e:
                    bot.send_message(chat_id, f"Error deleting file: {e}")
            else:
                bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text="No cards found.")
    except requests.exceptions.RequestException as e:
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"Request error: {e}")
    except Exception as e:
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"An error occurred: {e}")

# Handle /register command
@bot.message_handler(commands=['register'])
def register(message):
    chat_id = message.chat.id
    if chat_id in banned_users:
        bot.send_message(chat_id, f"You are banned from using this bot by {OWNER_NAME}.")
        return

    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    registration_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    bot.send_chat_action(chat_id, 'typing')  # Animated typing indicator
    time.sleep(1)  # Simulate processing delay

    msg = bot.send_message(chat_id, 'Please provide additional details: Your age, email.')

    # Define a function to handle the user's response
    @bot.message_handler(func=lambda m: m.chat.id == chat_id)
    def handle_registration_response(response):
        details = response.text
        user_info = {
            "telegram_id": chat_id,
            "username": username,
            "first_name": first_name,
            "registration_time": registration_time,
            "details": details
        }

        # Save user info to a text file
        file_name = f'{username}_registration_details.txt'
        try:
            with open(file_name, 'w') as f:
                for key, value in user_info.items():
                    f.write(f'{key}: {value}\n')

            bot.send_message(chat_id, 'Registration successful!')

            # Send the text file with registration details to the target bot
            with open(file_name, 'rb') as f:
                bot.send_document(TARGET_BOT_CHAT_ID, f, caption=f"New registration from @{username}")

            # Clean up the file after sending
            os.remove(file_name)
        except Exception as e:
            bot.send_message(chat_id, f"An error occurred while saving or sending your details: {e}")

# Handle /ban command (owner only)
@bot.message_handler(commands=['ban'])
def ban_user(message):
    chat_id = message.chat.id
    if chat_id != OWNER_ID:  # Only the owner can use this command
        bot.send_message(chat_id, f"You are not authorized to use this command. Contact {OWNER_NAME} for assistance.")
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Please provide a username or user ID to ban. Usage: /ban <username or user_id>")
        return

    user_to_ban = args[1]
    
    try:
        if user_to_ban.isdigit():
            banned_users.append(int(user_to_ban))
        else:
            banned_users.append(user_to_ban)
        bot.send_message(chat_id, f"User {user_to_ban} has been banned by {OWNER_NAME}.")
    except Exception as e:
        bot.send_message(chat_id, f"Failed to ban user: {e}")

# Handle /ping command
@bot.message_handler(commands=['ping'])
def ping(message):
    bot.send_message(message.chat.id, f'Pong! Bot is active and running under the supervision of {OWNER_NAME}.')

# Handle /id command
@bot.message_handler(commands=['id'])
def send_id(message):
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"
    response_text = (f'Your Telegram ID: <code>{chat_id}</code>\n'
                     f'Your Username: @{username}')
    bot.send_message(chat_id, response_text, parse_mode='HTML')

# Handle /credits command to display owner's name
@bot.message_handler(commands=['credits'])
def show_credits(message):
    bot.send_message(message.chat.id, f'This bot was developed and is managed by {OWNER_NAME}.')

# Polling loop
bot.polling()
