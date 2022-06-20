CREATE TABLE IF NOT EXISTS status (
	id_status smallint PRIMARY KEY,
	status varchar(20) NOT NULL
	);
COMMENT ON TABLE status IS 'Справочник состояний кандидатов';

CREATE TABLE IF NOT EXISTS relation (
	id_relation smallint PRIMARY KEY,
	relation varchar(40) NOT NULL
	);
COMMENT ON TABLE relation IS 'Справочник статусов пользователей Вконтакте';

CREATE TABLE IF NOT EXISTS  sex (
	id_sex smallint PRIMARY KEY,
	sex varchar(20) NOT NULL
);

COMMENT ON TABLE sex IS 'Справочник пола';
INSERT INTO sex (id_sex, sex) VALUES(0, 'любой');
INSERT INTO sex (id_sex, sex) VALUES(1, 'женский');
INSERT INTO sex (id_sex, sex) VALUES(2, 'мужской');

CREATE TABLE IF NOT EXISTS users (
	id_user serial PRIMARY KEY,
	id_vk int NOT NULL,
	id_vk_str varchar(80) NOT NULL,
	first_name varchar(80),
	last_name varchar(80),
	id_sex smallint NOT NULL REFERENCES sex (id_sex) default 0,
	id_city int,
	bdate date,
	id_relation int REFERENCES relation (id_relation),
	url varchar(160) NOT NULL
	);
COMMENT ON TABLE users IS 'Таблица пользователей Вконтакте';

CREATE TABLE IF NOT EXISTS user_candidate (
	id_user_candidate serial PRIMARY KEY,
	id_user int REFERENCES users (id_user),
	id_candidate int REFERENCES users (id_user),
	id_status smallint REFERENCES status (id_status),
	search_date timestamp
	);
COMMENT ON TABLE user_candidate IS 'Таблица кандидатов';

CREATE TABLE IF NOT EXISTS photo (
	id_photo serial PRIMARY KEY,
	id_user int REFERENCES users (id_user),
	url varchar(160) NOT NULL,
	likes_count int,
	liked bool
	);
COMMENT ON TABLE photo IS 'Таблица фотографий пользователей';

CREATE TABLE IF NOT EXISTS req_params (
	id_user int PRIMARY KEY REFERENCES users (id_user),
	id_sex smallint REFERENCES sex (id_sex) default 0,
	id_city int,
	age_from int,
	age_to int,
	id_relation smallint REFERENCES relation (id_relation)
	);
COMMENT ON TABLE req_params IS 'Таблица параметров запроса';