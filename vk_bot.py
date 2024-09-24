import logging
import random
import time

from environs import Env
import redis
import telegram
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from dict_create import create_dict_with_questions
from logs_handler import TelegramLogsHandler, logger


ERROR_CHECKING_DELAY = 10


def ask_question(dict_with_questions):
    question, answer = random.choice(list(dict_with_questions.items()))
    return question, answer


def send_text(message, event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message=message,
        random_id=random.randint(1, 1000)
    )


def create_keyboard(vk_api, peer_id):
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    vk_api.messages.send(
        peer_id=peer_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message='Приветствуем тебя в нашей викторине! Нажми "Новый вопрос"'
    )


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('VK_BOT_TOKEN')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.int('REDIS_PORT')
    chat_id = env.str('TG_CHAT_ID')
    redis_password = env.str('REDIS_PASSWORD')
    logger_bot = telegram.Bot(token=env.str('TG_LOGGER_BOT_TOKEN'))
    questions = create_dict_with_questions()
    vk_session = vk.VkApi(token=bot_token)
    vk_api = vk_session.get_api()
    logger.setLevel(logging.DEBUG)
    telegram_handler = TelegramLogsHandler(chat_id, logger_bot)
    telegram_handler.setLevel(logging.DEBUG)
    logger.addHandler(telegram_handler)
    logger.info('VK-бот запущен')
    while True:
        try:
            redis_connection = redis.Redis(host=redis_host, port=redis_port,
                                           password=redis_password, db=0, decode_responses=True)
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                peer_id = event.peer_id
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text == 'привет':
                        create_keyboard(vk_api, peer_id)
                        continue
                    if event.text == 'Новый вопрос':
                        question, answer = ask_question(questions)
                        redis_connection.set(peer_id, question)
                        send_text(question, event, vk_api)
                        continue
                    if event.text == 'Сдаться':
                        question = redis_connection.get(peer_id)
                        answer = questions[question]
                        send_text(answer, event, vk_api)
                        question, answer = ask_question(questions)
                        redis_connection.set(peer_id, question)
                        send_text(question, event, vk_api)
                        continue
                    question = redis_connection.get(peer_id)
                    if not question:
                        continue
                    answer = questions[question]
                    if event.text == answer:
                        text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
                        redis_connection.delete(peer_id)
                        send_text(text, event, vk_api)
                    else:
                        text = 'Неправильно… Попробуешь ещё раз?'
                        send_text(text, event, vk_api)
        except Exception:
            logger.exception('VK-бот упал с ошибкой:')
            time.sleep(ERROR_CHECKING_DELAY)


if __name__ == "__main__":
    main()