"""
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic inline bot example. Applies different text transformations.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging
import os
from io import BytesIO
from uuid import uuid4
from time import sleep

import telegram
from dotenv import load_dotenv
from telegram import (Bot, InlineQueryResultArticle, InlineQueryResultAudio,
                      InlineQueryResultCachedAudio, InputTextMessageContent,
                      ParseMode, Update)
from telegram.ext import (CallbackContext, CommandHandler, InlineQueryHandler,
                          Updater)
from telegram.utils.helpers import escape_markdown

import data_handler

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

admins = os.environ.get('ADMINS').split(';')

def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    x = update.message.reply_audio(
        open('music.mp3', 'rb'),
        performer = 'pp',
        title = 'ze title',
        )
    print(x, x.audio.file_id)
    print(update.effective_user.name in admins)
    


def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def cache_data(update: Update, _: CallbackContext) -> None:
    if update.effective_user.name in admins:
        data = data_handler.raw_data
        index = {}
        for tf2class, l in data.items():
            index [tf2class] = []
            for e in l[:5]:
                retry = True
                while retry:
                    try:
                        retry = False
                        x = update.message.reply_audio(
                            BytesIO(e['data']),
                            performer = tf2class,
                            title = e['text'],
                            )
                        index[tf2class].append({'file_id': x.audio.file_id, 'text': e['text']})
                    except Exception as e:
                        print('caching data error'+repr(e))
                        retry = True
                        sleep(3)
        data_handler.generate_index(index)
    else:
        update.message.reply_text("You are not an admin, silly")



def inlinequery(update: Update, _: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query
   # a = Bot.send_audio(self = None, chat_id = 223150767, audio =  open('music.wav', 'rb'))

    if query == "":
        return

    query_results = data_handler.find(query)

    results = [
        InlineQueryResultCachedAudio(
            id = str(uuid4()),
            audio_file_id= e
        )
        for e in query_results
    ]

    update.inline_query.answer(results)


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ.get("TOKEN"))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("admin_cache_data", cache_data))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(InlineQueryHandler(inlinequery))

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
