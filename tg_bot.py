import random
import telegram
from environs import Env
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from dict_create import create_dict_with_questions


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.message.chat_id
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=chat_id,
                             text='Появились кнопки',
                             reply_markup=reply_markup)


def make_question(update: Update, context: CallbackContext) -> None:
    dict_with_questions = create_dict_with_questions()
    if update.message.text == 'Новый вопрос':
        question, answer = random.choice(list(dict_with_questions.items()))
        update.message.reply_text(question)


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('TG_BOT_TOKEN')
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()