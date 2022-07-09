import settings
import vk_api
import traceback
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import db.base_db as dbo
from sqlalchemy.orm.exc import DetachedInstanceError, NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError
from random import randrange, shuffle

from util import pilot
from vk_inter import vkqueries
from datetime import date


class VKBot:
    def __init__(self):
        if not (settings.user_record['TOKEN_VK'] or settings.group_record['TOKEN_GROUP']):
            pilot.interrupt('Заполните параметры "TOKEN_VK" и "TOKEN_GROUP" в настроечном файле settings.py')
        self.token_vk = settings.user_record['TOKEN_VK']
        self.token_group = settings.group_record['TOKEN_GROUP']
        self.younger = settings.user_record['younger']
        self.older = settings.user_record['older']
        self.vk = None
        self.vk_user = None
        self.vk_group = None
        self.max_Candidates = settings.user_record['max_Candidates']
        self.offset = -1 # Офсет запроса кандидатов для вызова API Вконтакте. offset=-1 признак того, что он еще не инициализирован из базы данных
        self.current_candidate = 0
        self.count_recursion = 0 # Количество реккурсивных вызовов если Вконтакте перестает возвращать новых кандидатов при смещении офсета
        self.candidate_list = None
        self.elected_user = []
        try:
            self.vk = vk_api.VkApi(token=self.token_vk)
            self.vk_user = self.vk.get_api()
            self.vk = vk_api.VkApi(token=self.token_group)
            self.vk_group = self.vk.get_api()
        except Exception as E:
            pilot.interrupt(f'Авторизация не прошла: {E}')

        if not (self.vk_group and self.vk_user):
            pilot.interrupt('Бот не авторизовался, запуск невозможен!')

        self.vk_dic = dbo.get_dic()
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
            self.id_peer = new_event.peer_id
            self.vk_us = vkqueries.VkUser(self.vk_user, self.id_user)
            self.name_user = self.vk_us.get_user_data()
            if not self.name_user:
                pilot.interrupt('Не удалось выполнить запрос к vk_api, возможно TOKEN_VK истёк. \n Заполните действительный TOKEN_VK в файле settings.py')

            # Получаем количество записей из базы данных для текущего пользователя для установки первоначального офсета
            if self.offset == -1:
                self.offset = dbo.get_offset(self.id_user)

            if new_event.text.lower() in ['привет', 'hello', 'hi', 'hi!', 'здравствуй', 'здравствуйте', 'привет!',
                                          'здорово!', 'здорово']:
                keyboard = VkKeyboard()
                buttons = ['НАЧАТЬ ПОИСК', 'СЛЕДУЮЩИЙ КАНДИДАТ', 'ДОБАВИТЬ В ИЗБРАННОЕ',
                           'ПОСМОТРЕТЬ ИЗБРАННЫХ КАНДИДАТОВ']
                buttons_color = [VkKeyboardColor.SECONDARY, VkKeyboardColor.PRIMARY, VkKeyboardColor.POSITIVE,
                                 VkKeyboardColor.PRIMARY]

                for btn, btn_color in zip(buttons, buttons_color):
                    keyboard.add_button(btn, btn_color)
                    if btn != buttons[-1]:
                        keyboard.add_line()

                self.key_start(keyboard)

            elif 'начать поиск' in new_event.text.lower():
                self.key_search()
            elif 'следующий кандидат' in new_event.text.lower():
#                if self.candidate_list is None:
                if self.candidate_list is None or self.candidate_list['count'] == 0:
                        self.key_search()
                else:
                    self.key_next()
            elif 'добавить в избранное' in new_event.text.lower():
                self.key_add_to_favor()
            elif 'посмотреть избранных кандидатов' in new_event.text.lower():
                self.key_watch_favor()
            else:
                self.key_unnamed()

    def key_add_to_favor(self, keyboard=None):
        if self.candidate_list:
            dbo.couple_update(self.vk_us.user_id, self.candidate['vk_id'], new_status=2)
            first_name = self.candidate['first_name']
            last_name = self.candidate['last_name']
            self.candidate['elected'] = True
            if next((x for x in self.elected_user if x['vk_id'] == self.candidate['vk_id']), None):
                message = f'Пользователь {first_name} {last_name} уже был добавлен в "Избранное" ранее.'
            else:
                self.elected_user.append(self.candidate)
                message = f'Пользователь {first_name} {last_name} добавлен в "Избранное".'
        else:
            message = f'Сначала запустите поиск кандидатов!'
        self.vk.method('messages.send',
                       {'peer_id': self.id_peer, 'message': message, 'random_id': randrange(10 ** 7)})

    def key_watch_favor(self, keyboard=None):

        self.elected_user = dbo.show_favorites(self.vk_us.user_id)
        message = 'Список избранных:\n'
        number_user = 0
        for elected_user in self.elected_user:
            number_user += 1
            message = message + f'{number_user:2}. {elected_user["first_name"]} {elected_user["last_name"]} https://vk.com/id{elected_user["vk_id"]}\n'

        self.vk.method('messages.send',
                       {'peer_id': self.id_peer, 'message': message, 'random_id': randrange(10 ** 7)})

    def key_unnamed(self, keyboard=None):
        message = f'Не понимаю Вас, но давайте попробуем, {self.name_user}!\n\nЯ помогу Вам найти друга, на основании вашего местоположение, возраста и статуса и покажу его ТОП-3 фото.\
                   Нажмите кнопку "НАЧАТЬ ПОИСК"'

        values = {
            'user_id': self.id_user,
            'peer_id': self.id_peer,
            'message': message,
            'random_id': randrange(10 ** 7)
        }

        if keyboard:
            values['keyboard'] = keyboard.get_keyboard()

        self.vk.method('messages.send', values)

    def key_start(self, keyboard=None):
        message = f'Добрый день, {self.name_user}!\n\nЯ помогу Вам найти друга, на основании вашего местоположение, возраста и статуса и покажу его ТОП-3 фото.\
                   Нажмите кнопку "НАЧАТЬ ПОИСК"'

        values = {
            'user_id': self.id_user,
            'peer_id': self.id_peer,
            'message': message,
            'random_id': randrange(10 ** 7)
        }

        if keyboard:
            values['keyboard'] = keyboard.get_keyboard()

        self.vk.method('messages.send', values)

    def key_next(self, keyboard=None):

        if self.current_candidate < self.candidate_list['count']:
            self.get_current_candidate()
            self.offset += 1
        else:
            self.key_search()

    def key_search(self):

        self.candidate_list = dbo.select_candidates(self.id_user) # Вернуть из базы непросмотренных кандидатов

        search_params = {
            'sort': 0,
            'has_photo': 1,
            'offset': self.offset,
            'count': self.max_Candidates,
            'sex': 2,
            'fields': 'photo_max, photo_id, sex, bdate, home_town, status, city, relation, screen_name'
        }
        bdate = self.vk_us.data.get('bdate', None)
        city = self.vk_us.data['city']['id']
        # print(bdate)
        if bdate and len(bdate) > 7:
            search_params['age_from'] = date.today().year - int(bdate[-4:]) - self.younger
            search_params['age_to'] = date.today().year - int(bdate[-4:]) + self.older

        if self.vk_us.data.get('city', None):
            search_params['city'] = city
        #            elif vk_user.data.get('home_town', None):
        elif self.vk_us.data.get('home_town', None):
            search_params['hometown'] = self.vk_us.data.get['home_town']
        search_params['sex'] = 3 - self.vk_us.data['sex']
        if not self.candidate_list['items']:
            self.candidate_list = self.vk_candidates.get_users_search(**search_params)
            # Трекинг количества возвращаемых из ВК кандидатов
            # if len(self.candidate_list['items']) != settings.user_record['max_Candidates']:
            #     print(f'■■■■■■■■■ Received {len(self.candidate_list["items"])} records from VK')

        '''candidate_list сохраняется в базу- передается как параметр в процедуру, которая сохраняет в базу.'''
        dbo.add_candidates(self.vk_us.data, self.candidate_list)
        self.candidate_list = dbo.select_candidates(self.id_user)
        self.current_candidate = 0

        '''Если из ВКонтакте пришли все повторные кандидаты, база данных вернула пустой список
        Мы должны сместить офсет дополнительно, чтобы процедура начала возвращать новых кандидатов
        Иначе показываем 1го кандидата из полученного списка
        '''
        if len(self.candidate_list['items']) == 0:
            self.offset += self.max_Candidates
            self.count_recursion += 1
            if self.count_recursion > 10:
                pilot.interrupt('Вконтакте перестал выдавать новую информацию. Останавливаем бота')
            self.key_search()
        else:
            self.count_recursion = 0
            self.offset += 1
            self.get_current_candidate()

    def get_current_candidate(self):
        rec_cand = self.candidate_list['items'][self.current_candidate]
        message = f'{rec_cand["first_name"]} {rec_cand["last_name"]}\nhttps://vk.com/id{rec_cand["id"]}'
        dict_photos = dbo.select_photos(rec_cand['id'])
        if not dict_photos['photos']:
            try:
                dict_photos = self.vk_candidates._get_user_photos(rec_cand['id'])
            except Exception as Error:
                if "This profile is private" in traceback.format_exc():
                    message += f'\nВ этом аккаунте фотографии скрыты.'
                else:
                    pilot.interrupt(Error)

            if 'photos' in dict_photos.keys():
                # insert photos into PHOTO
                for photo in dict_photos['photos']:
                    db_photo = dbo.Photo(photo['owner_id'], photo['photo_id'], photo['likes'])
                    db_photo.insert()
            else:
                message += f'\nВ этом аккаунте нет фото в профайле.'

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
        params['receiver_user_id'] = self.id_peer

        # Отправка сообщения
        self.vk_send_mess.send_message(**params)

        # Обновление статуса кандидата в "Просмотрен"
        dbo.couple_update(self.id_user, self.candidate['vk_id'], new_status=1)

        self.current_candidate += 1

    def startbot(self):
        """Главная функция запуска бота - ожидание новых событий (сообщений)"""
        try:
            self.long_poll = VkLongPoll(vk=self.vk)
        except Exception as E:
            pilot.interrupt(f'Бот не запустился. VkLongPoll не удалось создать. \n {E}')

        while True:
            for event in self.long_poll.listen():
                self.check_event(event)
