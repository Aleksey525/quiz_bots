import random
import telegram
from environs import Env
import redis
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


def handle_new_question_request(update: Update, context: CallbackContext):
    dict_with_questions = create_dict_with_questions()
    chat_id = update.message.chat_id
    r = redis.Redis(host='redis-12998.c299.asia-northeast1-1.gce.redns.redis-cloud.com', port=12998,
                    password='tzo2yKYPlXlqsGTkZA4IPKTfOvoBuSl1', db=0, decode_responses=True)
    question, answer = random.choice(list(dict_with_questions.items()))
    r.set(str(chat_id), question)
    question = r.get(str(chat_id))
    update.message.reply_text(question)
    answer = dict_with_questions[question]
    payload = {'answer': answer}
    context.bot_data.update(payload)
    print(context.bot_data)


def handle_solution_attempt(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if 'answer' in context.bot_data and update.message.text == context.bot_data['answer']:
        context.bot.send_message(chat_id=chat_id,
                                 text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос')
        del context.bot_data['answer']  # Clear the answer after checking
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text='Неправильно… Попробуешь ещё раз?')


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('TG_BOT_TOKEN')
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^Новый вопрос$'), handle_new_question_request))
    dispatcher.add_handler(MessageHandler(Filters.update.message & Filters.text, handle_solution_attempt))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()