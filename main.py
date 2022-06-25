from random import randrange

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from datetime import datetime
import json
import settings
import vk.vk as vkc
import db.base_db as db


with open('keyboard.json', encoding='utf-8') as fp:
    keyboard_4btn = json.dumps(json.load(fp))


vk = vk_api.VkApi(token=settings.group_record["TOKEN_GROUP"])
longpoll = VkBotLongPoll(vk, group_id=213985884)


def write_msg(chat_id, message, keyboard=keyboard_4btn):
    vk.method('messages.send', {'chat_id': chat_id, 'message': message, 'keyboard': keyboard,
                                'random_id': randrange(10 ** 7)})


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        # Получено новое сообщение от пользователя. Определяем пользователя и получаем его инфо
        id_user = event.message['from_id']
        user = vkc.VkUser(id_user)
        user.get_user_data()
        user_age = datetime.now().year - datetime.strptime(user.data['bdate'], '%d.%M.%Y').year
        # TODO set parameters and search for candidates
        # Получаем параметры для поиска кандидатов
        candidate = vkc.VKCandidates(sex=3-user.get_user_sex(), relation=1)
        cand_list = candidate.get_users_search(**{'count': 10, 'city': user.data['city']['id'], 'sex': candidate.sex,
                                                  'status': candidate.relation, 'age_from': user_age - 3,
                                                  'age_to': user_age + 3})
        # Заносим пользователя и кандидатов в users, потенциальные пары в user_candidate
        # TODO insert data into DB
        db_user = db.Users(user.user_id, user.data['screen_name'], user.data['first_name'], user.data['last_name'],
                           user.data['sex'], user.data['city']['id'], user.data['bdate'], user.data.get['relation'],
                           'https://vk.com/' + user.data['screen_name'])
        db_user.insert()
        for cand in cand_list:
            # TODO cand in cand_list must be vkc.VkUser object with data from vkc.get_user_data()
            db_cand = db.Users(cand.user_id, cand.data['screen_name'], cand.data['first_name'], cand.data['last_name'],
                               cand.data['sex'], cand.data['city']['id'], cand.data['bdate'], cand.data.get['relation'],
                               'https://vk.com/' + cand.data['screen_name'])
            db_cand.insert()
            db_pair = db.UserCandidate(db_user, db_cand)
            db_pair.insert()

        # TODO show candidate
        cand_to_show = db_user.select_pair()
        # TODO get photos from vk; add them to table photo; show to user in attachment
        photos_to_show = db.select_photos(cand_to_show.id_candidate)
        write_msg(event.chat_id, "ПОКАЗЫВАЕМ КАНДИДАТА")

        request = event.message.get('payload')
        if request:
            btn = request.split('"')[-2]
            if btn == 'Next':
                # Меняем статус в "просмотрено"
                cand_to_show.update(id_status=1)
            elif btn == 'Like':
                # Меняем статус в "избранное"
                cand_to_show.update(id_status=2)
            elif btn == 'BL':
                # Меняем статус в "чс"
                cand_to_show.update(id_status=3)
            elif btn == 'Favorites':
                # TODO show favorites
                pass
            else:
                write_msg(event.chat_id, 'Пожалуйста, выберите команду')
        else:
            write_msg(event.chat_id, 'Пожалуйста, выберите команду')
