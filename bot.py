# reference: https://docs.python-telegram-bot.org/en/stable/examples.echobot.html, 
#            https://openai.com/blog/introducing-chatgpt-and-whisper-apis
import openai
import json
import os
import logging
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import config


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Remember to export your OPENAI_API_KEY and BOT_TOKEN.
openai.api_key = os.getenv("MY_OPENAI_API_KEY")
bot_token = os.getenv("MY_BOT_TOKEN")

system_message = config["general_assistant"]["system_message"]
messages = [system_message]
temperature = 1
top_p = 1
n_choice = 1
stream = False
stop = None
max_tokens = 2**32
presence_penalty = 0
frequency_penalty = 0
logit_bias = None # a map
user = None # string

continuity = True

def do_config(assistant: str):
    global messages, system_message, temperature, continuity
    system_message = config[assistant]["system_message"]
    temperature = config[assistant]["temperature"]
    continuity = config[assistant]["continuity"]
    # clear messages
    messages = [system_message]

    return config[assistant]["preface"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Supported command:\n\n \
    /help this message\n\n \
    /clear restore general purpose assistant\n\n \
    /ppolish 中文论文修改器\n\n \
    ")

async def ppolish_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(do_config("paper_polisher"))

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(do_config("general_assistant"))

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    global messages
    messages.append({"role": "user", "content": update.message.text})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=messages,
        temperature=temperature,
    )

    response_message = response['choices'][0]['message']

    # for saving tokens reason, reset conversation if more than 15 turns of talk.
    if len(messages) > 30 or (not continuity):
        messages = [system_message]
    else:
        # save conversation
        messages.append({"role": response_message['role'], "content": response_message['content']})

    await update.message.reply_text(response_message['content'])

def main() -> None:

    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("ppolish", ppolish_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
