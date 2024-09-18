import logging
import random
import time

from environs import Env
import redis
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api.exceptions import VkApiError
from dict_create import create_dict_with_questions


def ask_question(chat_id):
    dict_with_questions = create_dict_with_questions()
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
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)

    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    vk_api.messages.send(
        peer_id=peer_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message='Приветствуем тебя в нашей викторине! На жми "Новый вопрос"'
    )


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('VK_BOT_TOKEN')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.int('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    redis_connection = redis.Redis(host=redis_host, port=redis_port,
                                   password=redis_password, db=0, decode_responses=True)
    vk_session = vk.VkApi(token=bot_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        peer_id = event.peer_id
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'привет':
                create_keyboard(vk_api, peer_id)
            elif event.text == 'Новый вопрос':
                question, answer = ask_question(peer_id)
                redis_connection.set(str(peer_id), question)
                send_text(question, event, vk_api)
                print(answer)
            elif event.text == 'Сдаться':
                question = redis_connection.get(peer_id)
                questions = create_dict_with_questions()
                answer = questions[question]
                send_text(answer, event, vk_api)
                question, answer = ask_question(peer_id)
                redis_connection.set(str(peer_id), question)
                send_text(question, event, vk_api)
                print(answer)
            else:
                question = redis_connection.get(peer_id)
                questions = create_dict_with_questions()
                answer = questions[question]
                print(answer)
                if event.text == answer:
                    text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
                    redis_connection.delete(peer_id)
                    send_text(text, event, vk_api)
                else:
                    text = 'Неправильно… Попробуешь ещё раз?'
                    send_text(text, event, vk_api)


if __name__ == "__main__":
    main()