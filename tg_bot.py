import logging
import random
import time

from environs import Env
import redis
import telegram
from telegram import ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from dict_create import create_dict_with_questions
from logs_handler import TelegramLogsHandler, logger


QUESTION, RESPONSE  = range(2)
ERROR_CHECKING_DELAY = 10


def start(update, context):
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
    return QUESTION


def handle_new_question_request(update, context):
    dict_with_questions = create_dict_with_questions()
    chat_id = update.message.chat_id
    # r = redis.Redis(host='redis-12998.c299.asia-northeast1-1.gce.redns.redis-cloud.com', port=12998,
    #                 password='tzo2yKYPlXlqsGTkZA4IPKTfOvoBuSl1', db=0, decode_responses=True)
    redis_connection = context.bot_data['redis_connection']
    question, answer = random.choice(list(dict_with_questions.items()))
    redis_connection.set(chat_id, question)
    question = redis_connection.get(chat_id)
    update.message.reply_text(question)
    answer = dict_with_questions[question]
    print(answer)
    # payload = {'answer': answer}
    # context.bot_data.update(payload)
    return RESPONSE


def handle_attempt_surrender(update, context):
    chat_id = update.message.chat_id
    redis_connection = context.bot_data['redis_connection']
    question = redis_connection.get(chat_id)
    dict_with_questions = context.bot_data['dict_with_questions']
    answer = dict_with_questions[question]

    context.bot.send_message(chat_id=chat_id,
                             text=answer)
    redis_connection.delete(chat_id)
    handle_new_question_request(update, context)
    return RESPONSE


def handle_solution_attempt(update, context):
    chat_id = update.message.chat_id
    redis_connection = context.bot_data['redis_connection']
    question = redis_connection.get(chat_id)
    dict_with_questions = context.bot_data['dict_with_questions']
    answer = dict_with_questions[question]

    if update.message.text == answer:
        context.bot.send_message(chat_id=chat_id,
                                 text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос')
        redis_connection.delete(chat_id)
        return QUESTION
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text='Неправильно… Попробуешь ещё раз?')
        return RESPONSE


def cancel(update, context):
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              )
    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('TG_BOT_TOKEN')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.int('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    chat_id = env.str('TG_CHAT_ID')
    dict_with_questions = create_dict_with_questions()
    logger_bot = telegram.Bot(token=env.str('TG_LOGGER_BOT_TOKEN'))
    logger.setLevel(logging.DEBUG)
    telegram_handler = TelegramLogsHandler(chat_id, logger_bot)
    telegram_handler.setLevel(logging.DEBUG)
    logger.addHandler(telegram_handler)
    logger.info('Телеграм-бот запущен')
    updater = Updater(bot_token)
    while True:
        try:
            redis_connection = redis.Redis(host=redis_host, port=redis_port,
                                           password=redis_password, db=0, decode_responses=True)
            dispatcher = updater.dispatcher
            dispatcher.bot_data['redis_connection'] = redis_connection
            dispatcher.bot_data['dict_with_questions'] = dict_with_questions
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler('start', start)],

                states = {

                    QUESTION: [MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request)
                               ],

                    RESPONSE: [MessageHandler(Filters.text & ~Filters.regex('^Новый вопрос$')
                                              & ~Filters.regex('^Сдаться'), handle_solution_attempt),
                               MessageHandler(Filters.regex('^Сдаться$'), handle_attempt_surrender)
                               ],
                },

                fallbacks=[CommandHandler('cancel', cancel)]

            )

            dispatcher.add_handler(conv_handler)
            updater.start_polling()
            updater.idle()
        except Exception:
            logger.exception('Телеграм-бот упал с ошибкой:')
            time.sleep(ERROR_CHECKING_DELAY)


if __name__ == '__main__':
    main()
