from random import randrange

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import settings


#token = input('Token: ')

vk = vk_api.VkApi(token=settings.group_record["TOKEN_GROUP"])
longpoll = VkBotLongPoll(vk, group_id=213985884)


def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:

        if event.from_user:
            request = event.message

            if request == "привет":
                write_msg(event.chat_id, f"Хай, {event.chat_id}")
            elif request == "пока":
                write_msg(event.chat_id, "Пока((")
            else:
                write_msg(event.chat_id, "Не поняла вашего ответа...")
