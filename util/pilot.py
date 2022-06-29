import json
import re

class MessageEventData:

    def __init__(self, uid: int, msg_id: int, dt: int, body: str, contact_id: int):
        self.user_id = uid
        self.message_id = msg_id
        self.time = dt
        self.text = body
        self.text_normalize = get_normalize_set(self.text)
        self.contact_id = contact_id

    def __repr__(self):
        return self.text

def get_normalize_set(string_: str) -> frozenset:
    """
    Нормализация строки к одному общему виду, разбиения на отдельные слова.
    :param string_: исходная строка;
    :return: множество из отдельных слов в нижнем регистре
    """
    new_string = string_.lower()
    set_of_words = frozenset(re.findall(r'[a-zA-Zа-яА-ЯЁё]+', new_string))
    return set_of_words

def read_json(file_name: str) -> dict:
    """
    Функция чтения json-файла.
    :param file_name: имя файла для чтения;
    :return: словарь, или ОШИБКУ в случае отсутствия файла
    """
    try:
        with open(file_name, encoding='utf-8') as f:
            return json.load(f)

    except Exception as err:
        print(f'ОШИБКА загрузки необходимых сведений: {err}')
        print(f'Проверьте наличие данных в файле - {file_name}.')

