from random import randrange

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import settings
import json


with open('keyboard.json', encoding='utf-8') as fp:
    keyboard_4btn = json.dumps(json.load(fp))


vk = vk_api.VkApi(token=settings.group_record["TOKEN_GROUP"])
longpoll = VkBotLongPoll(vk, group_id=213985884)


def write_msg(chat_id, message, keyboard=keyboard_4btn):
    vk.method('messages.send', {'chat_id': chat_id, 'message': message, 'keyboard': keyboard,
                                'random_id': randrange(10 ** 7)})


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        # print('MESSAGE RECEIVED!')
        request = event.message['text']
        write_msg(event.chat_id, 'hey')
