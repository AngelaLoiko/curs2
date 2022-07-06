with open('tokens/token_vk.txt') as f:
    token_vk = f.read()
with open('tokens/token_group.txt') as f:
    token_group = f.read()

user_record = {
    "TOKEN_VK": token_vk,
    "version_api_vk": "5.131",
    "max_Candidates": 5,
    "older": 2,  # ищу кандидатов старше на столько лет
    "younger": 5  # ищу кандидатов младше на столько лет
}

group_record = {
    "TOKEN_GROUP": token_group
}

params = {
    'use_database': True,
    'DBCONNECT': 'postgresql+psycopg2://postgres:dbadmin@localhost/postgres'
}
