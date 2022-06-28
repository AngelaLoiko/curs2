import hues
import vk_api
from vk_api.vk_api import VkApiMethod
from vk_api.utils import get_random_id  # использование get_random_id для messages.send
import settings
from datetime import datetime

class VkUser:
    def __init__(self, vk_api_object: VkApiMethod, user_id):
        self.vk_api_object = vk_api_object
        self.data = None
        self.user_id = user_id

    def get_user_data(self):
        params = {
            'user_id': self.user_id,
            'fields': 'screen_name, bdate, sex, relation, status, home_town, city'
        }
        try:
            # Данные пользователя ВК
            self.data = self.vk_api_object.users.get(**params)[0]
            self.data['offset'] = [0, 0, 0]

            if self.data.get('first_name', None) and self.data.get('last_name', None):
                self.data['name'] = f'{self.data["first_name"]} {self.data["last_name"]}'
            return self.data['name']

        except Exception as Err:
            self.data = Err

    def get_user_sex(self):
        return self.vk_api_object.users.get(user_ids=self.user_id, fields='sex')[0]['sex']

    def get_user_city(self):
        return self.vk_api_object.users.get(user_ids=self.user_id, fields='city')[0]['city']['title']

    def get_user_age(self):
        current_year = datetime.now().year
        bdate = self.vk_api_object.users.get(user_ids=self.user_id, fields='bdate')[0]['bdate']
        return current_year - int(bdate[-4:])

class VKCandidates:
    vk_dic = {
        "sex": {
            "1": "женский",
            "2": "мужской"
        },
        "relation": {
            "1": "не женат/не замужем",
            "2": "есть друг/есть подруга",
            "3": "помолвлен/помолвлена",
            "4": "женат/замужем",
            "5": "всё сложно",
            "6": "в активном поиске",
            "7": "влюблён/влюблена",
            "8": "в гражданском браке"
        }
    }
    def __init__(self, vk_api_object: VkApiMethod, vk_dic):
        self.vk = vk_api_object
        self.data = None
        self.vk_dic = vk_dic

        self.dic = {
            "sex": {
            "1": "женский",
            "2": "мужской"
        },
        "relation": {
            "1": "не женат/не замужем",
            "2": "есть друг/есть подруга",
            "3": "помолвлен/помолвлена",
            "4": "женат/замужем",
            "5": "всё сложно",
            "6": "в активном поиске",
            "7": "влюблён/влюблена",
            "8": "в гражданском браке"
        }
    }

    def get_users_search(self, **kwargs):
        #**kwargs: параметры запроса - пол, возраст, город, семейное положение

        result = self.vk.users.search(**kwargs)

        return result

    def get_users_photos(self, **kwargs):
        #kwargs: owner_id, album_id...

        result = self.vk.photos.get(**kwargs)

        return result

    def get_cities_by_id(self, **kwargs):
        #Поиск названий городов в ВК, по их идентификаторам.
        #kwargs: параметры запроса - список идентификаторов городов
        result = self.vk.database.getCitiesById(**kwargs)

        return result

    def _get_user_photos(self, owner_id) -> dict:

        # Параметры запроса
        photos_params = {
            'extended': 1,
            'owner_id': owner_id,
            'album_id': 'profile'
        }

        # Запрос к ресурсу
        result = self.get_users_photos(**photos_params)

        # Проверка на наличие необходимых данных в ответе сервера
        len_result = len(result.get('items', None))
        if len_result == 0:
            return {}

        # Создание списка фоток с подсчетом количества лайков и комментов
        new_result = []
        for key, value in enumerate(result['items']):
            new_result.append({
                'photo_id': value['id'],
                'owner_id': value['owner_id'],
                'likes': value['likes']['count'] + value['comments']['count']
            })

        if len_result < 3:
            photo_result = {
                'photos': [new_result[photo] for photo in range(len_result)]
            }
        else:
            # Сортировка фоток по значению атрибута 'likes'
            new_result = sorted(new_result, key=lambda x: x.get('likes'), reverse=True)
            # Выборка ТОП-3 фоток
            photo_result = {
                'photos': [new_result[photo] for photo in range(3)]
            }

        return photo_result



class VKSendMess:
            """
            Класс для отправки сообщений с помощью библиотеки vk_api
            """

            # Флаг отсутствия клавиатуры к сообщению
            NONE_KEY_BOARD = '{\n "one_time": true,\n "buttons": []\n}'

            def __init__(self, vk_api_object: VkApiMethod):
                self.vk = vk_api_object

            def send_message(self, receiver_user_id: str = None,
                             message_text: str = '',
                             #keyboard: str = NONE_KEY_BOARD,
                             attachment: str = None):
                """
                Отправка сообщения от лица авторизованного пользователя
                :param receiver_user_id: уникальный идентификатор получателя сообщения
                :param message_text: текст отправляемого сообщения
                :param keyboard: клавиатура к сообщению
                :param attachment: фото или что-то другое, прикрепленное к сообщению
                """

                # Параметры сообщения
                params_message = {
                    'user_id': receiver_user_id,
                    'message': message_text,
                    #'keyboard': keyboard,
                    'random_id': get_random_id()
                }

                # Добавление вложенной, инфы если она заполнена
                if attachment:
                    params_message['attachment'] = attachment

#                try:
                self.vk.messages.send(**params_message)
