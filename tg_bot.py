import random

from environs import Env
import redis
import telegram
from telegram import ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from dict_create import create_dict_with_questions


QUESTION, RESPONSE  = range(2)


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
    r = redis.Redis(host='redis-12998.c299.asia-northeast1-1.gce.redns.redis-cloud.com', port=12998,
                    password='tzo2yKYPlXlqsGTkZA4IPKTfOvoBuSl1', db=0, decode_responses=True)
    question, answer = random.choice(list(dict_with_questions.items()))
    r.set(str(chat_id), question)
    question = r.get(str(chat_id))
    update.message.reply_text(question)
    answer = dict_with_questions[question]
    payload = {'answer': answer}
    context.bot_data.update(payload)
    return RESPONSE


def handle_attempt_surrender(update, context):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=context.bot_data['answer'])
    del context.bot_data['answer']
    handle_new_question_request(update, context)
    return RESPONSE


def handle_solution_attempt(update, context):
    chat_id = update.message.chat_id
    if update.message.text == context.bot_data['answer']:
        context.bot.send_message(chat_id=chat_id,
                                 text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос')
        del context.bot_data['answer']
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
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
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


if __name__ == '__main__':
    main()
