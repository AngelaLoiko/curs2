import vk_api
import settings
from datetime import datetime
from datetime import date

class VkUser:
    def __init__(self, user_id, token = settings.user_record["TOKEN_VK"] ):
        self.vk = vk_api.VkApi(token=token)
        self.vk_api = self.vk.get_api()
        self.data = None
        self.user_id = user_id

    def get_user_data(self):
        params = {
            'user_id': self.user_id,
            'fields': 'screen_name, bdate, sex, relation, status, home_town, city'
        }
        try:
            # Данные пользователя ВК
            self.data = self.vk_api.users.get(**params)[0]
           #self.data['offset'] = [0, 0, 0]

            if self.data.get('first_name', None) and self.data.get('last_name', None):
                self.data['name'] = f'{self.data["first_name"]} {self.data["last_name"]}'

        except Exception as Err:
            self.data = Err

    def get_user_sex(self):
        return self.vk_api.users.get(user_ids=self.user_id, fields='sex')[0]['sex']

    def get_user_city(self):
        return self.vk_api.users.get(user_ids=self.user_id, fields='city')[0]['city']['title']

    def get_user_age(self):
        current_year = datetime.now().year
        bdate = self.vk_api.users.get(user_ids=self.user_id, fields='bdate')[0]['bdate']
        return current_year - int(bdate[-4:])

class VKCandidates:

    def __init__(self, sex, relation, token = settings.user_record["TOKEN_VK"]  ):
        self.vk = vk_api.VkApi(token=token)
        self.vk_api = self.vk.get_api()
        self.data = None
        self.sex = sex
        self.relation = relation

    def get_users_search(self, **kwargs):
        #**kwargs: параметры запроса - пол, возраст, город, семейное положение

        result = self.vk_api.users.search(**kwargs)

        return result

    def get_users_photos(self, **kwargs):
        #kwargs: owner_id, album_id...

        result = self.vk_api.photos.get(**kwargs)

        return result

    def get_cities_by_id(self, **kwargs):
        #Поиск названий городов в ВК, по их идентификаторам.
        #kwargs: параметры запроса - список идентификаторов городов
        result = self.vk_api.database.getCitiesById(**kwargs)

        return result


        """
        Это тесты функций взаимодействия с Вконтакте... 
        Функционал нужно переносить в какую-то другую библиотеку
        Тут останутся только классы! 
        """



vk_user = VkUser(user_id='18768947')
print(vk_user)
print(vk_user.get_user_sex())
print(vk_user.get_user_city())
print(vk_user.get_user_age())
vk_user.get_user_data()
print(vk_user.data)


sex = {
        "0": "любой",
        "1": "женский",
        "2": "мужской"
    }

relation = {
        "1": "не женат/не замужем",
        "2": "есть друг/есть подруга",
        "3": "помолвлен/помолвлена",
        "4": "женат/замужем",
        "5": "всё сложно",
        "6": "в активном поиске",
        "7": "влюблён/влюблена",
        "8": "в гражданском браке"
    }

vk_candidates = VKCandidates(sex = sex, relation = relation, token = settings.user_record["TOKEN_VK"] )

photos_params = {
    'extended': 1,
    'owner_id': '18768947',
    'album_id': 'profile'
}

print(vk_candidates.get_users_photos(**photos_params))

search_params = {
    'sort': 0,
    'has_photo': 1,
    'offset': 4,
    'count': 4,
    'sex': 1,
    'fields': 'photo_max, photo_id, sex, bdate, home_town, status, city, interests,'
              'books, music, relation, is_closed'
}

bdate = vk_user.data.get('bdate', None)
#print(bdate)
if bdate and len(bdate) > 7:
     search_params['age_from'] = date.today().year - int(bdate[-4:]) - 4
     search_params['age_to'] = date.today().year - int(bdate[-4:]) + 4

if vk_user.data.get('city', None):
     search_params['city'] = vk_user.data['city']['id']
elif vk_user.data.get('home_town', None):
     search_params['hometown'] = vk_user.data['home_town']


print(vk_candidates.get_users_search(**search_params))



