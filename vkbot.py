import settings
import vk_api
import traceback
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from random import randrange, shuffle

from util import pilot
from vk_inter import vkqueries
#from util.pilot import MessageEventData
from datetime import date

class VKBot:
    def __init__(self):
        self.token_vk = settings.user_record['TOKEN_VK']
        self.token_group = settings.group_record['TOKEN_GROUP']
        self.vk = None
        self.max_Candidates = settings.user_record['max_Candidates']
        self.offset = 0

        try:
            self.vk = vk_api.VkApi(token=self.token_vk)
            self.vk_user = self.vk.get_api()
            self.vk = vk_api.VkApi(token=self.token_group)
            self.vk_group = self.vk.get_api()
        except Exception as E:
            pilot.interrupt(f'Авторизация не прошла: {E}')

        if not (self.vk_group and self.vk_user):
            pilot.interrupt('Бот не авторизовался, запуск невозможен!')

# todo нужна такая структура из базы данных
        self.vk_dic = {
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

        self.vk_candidates = vkqueries.VKCandidates(self.vk_user, self.vk_dic)
        self.vk_send_mess = vkqueries.VKSendMess(self.vk_group)

    def _update_user(self, vkuser: vkqueries.VkUser):
        user_id = vkuser.data.get('user_id', None)
        if user_id:
            self.users[user_id] = vkuser.data

    def check_event(self, new_event):
        # Получено новое сообщение от пользователя. Определяем пользователя и получаем его инфо
        if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me and new_event.text:
            self.id_user = new_event.user_id
            self.vk_us = vkqueries.VkUser(self.vk_user, self.id_user)
            self.name_user = self.vk_us.get_user_data()
            uid = new_event.user_id  # id отправителя
            msg_id = new_event.message_id  # id сообщения
            dt = new_event.timestamp  # время сообщения
            msg = new_event.text  # текст сообщения
            #contact_id = pilot.contact_id_from_dict(new_event.extra_values)  # id контакта вызова кнопки
            #event_data = MessageEventData(self.id_user, msg_id, dt, msg, contact_id)

            if new_event.text.lower() in ['привет', 'hello', 'hi', 'здравствуй', 'здравствуйте']:
                keyboard = VkKeyboard()
                buttons = ['НАЧАТЬ ПОИСК', 'СЛЕДУЮЩИЙ КАНДИДАТ', 'ДОБАВИТЬ В ИЗБРАННОЕ', 'ПОСМОТРЕТЬ ИЗБРАННЫХ КАНДИДАТОВ']
                buttons_color = [VkKeyboardColor.PRIMARY, VkKeyboardColor.POSITIVE, VkKeyboardColor.NEGATIVE,
                                 VkKeyboardColor.PRIMARY]

                for btn, btn_color in zip(buttons, buttons_color):
                    keyboard.add_button(btn, btn_color)
                    if btn != buttons[-1]:
                        keyboard.add_line()

                self.key_start(keyboard)


            elif new_event.text.lower() in ['начать поиск']:
                self.key_seach()
            elif new_event.text.lower() in ['следующий кандидат']:
                self.key_next()
            elif new_event.text.lower() in ['добавить в избранное']:
                self.key_add_to_favor()
            elif new_event.text.lower() in ['посмотреть избранных кандидатов']:
                self.key_watch_favor()
            else:
                self.key_unnamed()

    def key_start(self, keyboard=None):
        message = f'Добрый день, {self.name_user}!\nЯ помогу Вам найти друга, на основании вашего местоположение, возраста и статуса и покажу его ТОП-3 фото.\
                   Нажмите кнопку "НАЧАТЬ ПОИСК"'

        values = {
            'user_id': self.id_user,
            'message': message,
            'random_id': randrange(10 ** 7)
        }

        if keyboard:
            values['keyboard'] = keyboard.get_keyboard()

        self.vk.method('messages.send', values)

    def key_next(self, keyboard=None):
        self.current_candidate += 1
        if self.current_candidate < self.max_Candidates:
            self.get_current_candidate()
        if self.current_candidate == self.max_Candidates:
            self.current_candidate = 0
            self.offset += self.max_Candidates
            self.key_seach()


    def key_seach(self):
        # self.select_command(data, user_vk)  # обработка входящего сообщения

        search_params = {
            'sort': 0,
            'has_photo': 1,
            'offset': self.offset,
            'count': self.max_Candidates,
            'sex': 2,
            'fields': 'photo_max, photo_id, sex, bdate, home_town, status, city, relation'
        }
        bdate = self.vk_us.data.get('bdate', None)
        city = self.vk_us.data['city']['id']
        # print(bdate)
        if bdate and len(bdate) > 7:
            search_params['age_from'] = date.today().year - int(bdate[-4:]) - 4
            search_params['age_to'] = date.today().year - int(bdate[-4:]) + 4

        if self.vk_us.data.get('city', None):
            search_params['city'] = city
        #            elif vk_user.data.get('home_town', None):
        elif self.vk_us.data.get('home_town', None):
            search_params['hometown'] = self.vk_us.data.get['home_town']
        search_params['sex'] = 3 - self.vk_us.data['sex']
        self.candidate_list = self.vk_candidates.get_users_search(**search_params)
        self.current_candidate = 0
        self.get_current_candidate()

    def get_current_candidate(self):

        rec_cand = self.candidate_list['items'][self.current_candidate]
        message = f'{rec_cand["first_name"]} {rec_cand["last_name"]}\nhttps://vk.com/id{rec_cand["id"]}'
        dict_photos = None
        try:
            dict_photos = self.vk_candidates._get_user_photos(rec_cand['id'])
        except Exception as Error:
            if "This profile is private" in traceback.format_exc():
                message += f'\nВ этом аккаунте фотографии скрыты.'

        self.candidate = {
            'first_name': rec_cand["first_name"],
            'last_name': rec_cand["last_name"],
            'vk_id': rec_cand["id"]
        }
        params = {}
        if dict_photos:
            photos = dict_photos.get('photos', None)
            photo = [f'photo{value["owner_id"]}_{value["photo_id"]}_{self.token_vk}' for value in photos]
            if photo:
                params['attachment'] = photo
            else:
                message += f'\nНет фото.'

        # Формирование сообщения
        params['message_text'] = message

        # Формирование адресата
        params['receiver_user_id'] = self.id_user

        # Отправка сообщения
        self.vk_send_mess.send_message(**params)


    def startbot(self):
        """Главная функция запуска бота - ожидание новых событий (сообщений)"""
        self.long_poll = VkLongPoll(vk=self.vk)

        if not self.long_poll:
            pilot.interrupt('Не удалось получить значения Long Poll сервера!')
        bots = {}
        while True:
            for event in self.long_poll.listen():
                self.check_event(event)

