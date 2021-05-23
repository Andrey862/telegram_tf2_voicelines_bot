"""
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic inline bot example. Applies different text transformations.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import json
import logging
import os
import traceback
from io import BytesIO
from time import sleep
from uuid import uuid4

import telegram
from dotenv import load_dotenv
from telegram import InlineQueryResultCachedAudio, Update
from telegram.error import NetworkError
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, InlineQueryHandler, MessageHandler, Updater)

import query_handler

# ------ loading systeme variables---------
load_dotenv()

admins = os.environ.get('ADMINS').split(';')

# ------- Loggging-----------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# ------- read globals------


with open('static/help_text.md', 'r') as f:
    help_text = f.read()

with open('static/help_text_admin.md', 'r') as f:
    help_text_admin = f.read()


def catch_error_decorator(fun):
    def f(update: Update, context: CallbackContext):
        try:
            return fun(update, context)
        except Exception as e:
            logger.error(traceback.format_exc())
            if update.effective_user.name in admins:
                update.message.reply_text(
                    "Error occured, admin traceback:\n ```\n" + traceback.format_exc()+"\n```", parse_mode='Markdown')
            else:
                update.message.reply_text(
                    "oops! something went wrong " + e, parse_mode='Markdown')
    return f


@catch_error_decorator
def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello!')
    #print(x, x.audio.file_id)
    #print(update.effective_user.name in admins)


@catch_error_decorator
def help_command(update: Update, _: CallbackContext) -> None:
    """ give different help command responce to admins and non-admins"""
    if update.effective_user.name in admins:
        update.message.reply_text(help_text_admin, parse_mode='Markdown')
    else:
        update.message.reply_text(help_text, parse_mode='Markdown')


@catch_error_decorator
def admin_cache_data(update: Update, _: CallbackContext) -> None:
    data = query_handler.get_raw_data()
    audio_ids = {}
    for tf2class, l in data.items():
        audio_ids[tf2class] = []
        for e in l:
            retry = True
            while retry:
                try:
                    retry = False
                    x = update.message.reply_audio(
                        BytesIO(e['data']),
                        performer=tf2class,
                        title=e['text'],
                    )
                    audio_ids[tf2class].append(
                        {'file_id': x.audio.file_id, 'text': e['text']})
                except Exception as error:
                    logger.warning('triggering telegram anti-spam filter')
                    retry = True
                    sleep(3)
    update.message.reply_text('Data cached successfully')
    query_handler.save_ids(audio_ids)

    file = json.dumps(query_handler.audio_ids).encode()
    try:
        update.message.reply_document(file, filename='audio_ids.json')
        update.message.reply_text("use this if you want to move bot")
    except NetworkError:
        update.message.reply_text(
            f'Seems like this file is too large: {len(file)}. Maximum file size is 1.5MB')


@catch_error_decorator
def admin_get_audio_ids(update: Update, _: CallbackContext) -> None:
    file = json.dumps(query_handler.audio_ids).encode()
    try:
        update.message.reply_document(file, filename='audio_ids.json')
    except NetworkError:
        update.message.reply_text(
            f'Seems like this file is too large: {len(file)}. Maximum file size is 1.5MB')


@catch_error_decorator
def admin_upload_audio_ids_command(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'Please upload json file with audio ids or type /cancel to cancel')
    return 0


@catch_error_decorator
def admin_upload_audio_ids_loader(update: Update, _: CallbackContext) -> int:
    try:
        file = json.loads(
            update.message.document.get_file().download_as_bytearray().decode())
        #TODO: Validation
        query_handler.generate_index(file)
        query_handler.audio_ids = file
        update.message.reply_text("audio ids updated successfully")
    except AttributeError as error:
        update.message.reply_text(
            "this doesn't seem to be a correct json file please upload again")
        return 0
    except UnicodeDecodeError as error:
        update.message.reply_text(
            "this doesn't seem to be a text file please upload again")
        return 0
    return ConversationHandler.END


def cancel(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'Canceled'
    )
    return ConversationHandler.END


def inlinequery(update: Update, _: CallbackContext) -> None:
    """Handle the inline query."""
    try:
        query = update.inline_query.query
        logger.info(f'Inline query {update.effective_user.name} ' + query)
        if query == "":
            return

        query_results = query_handler.find(query)

        results = [
            InlineQueryResultCachedAudio(
                id=str(uuid4()),
                audio_file_id=e
            )
            for e in query_results
        ]
        update.inline_query.answer(results)
    except Exception as error:
        logger.error(traceback.format_exc())


def main() -> None:

    # Create filter to check if a user is admin
    admin_only_filter = Filters.user(username=admins)

    updater = Updater(os.environ.get("TOKEN"))

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler(
        "admin_cache_data", admin_cache_data, admin_only_filter))

    dispatcher.add_handler(CommandHandler(
        "admin_get_audio_ids", admin_get_audio_ids, admin_only_filter))

    dispatcher.add_handler(InlineQueryHandler(inlinequery))
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler(
            'admin_upload_audio_ids', admin_upload_audio_ids_command, admin_only_filter)],
        states={
            0: [MessageHandler(Filters.document & admin_only_filter, admin_upload_audio_ids_loader)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    ))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
