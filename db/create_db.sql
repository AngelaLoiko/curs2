CREATE DATABASE vkinder;

CREATE TABLE IF NOT EXISTS status (
	id_status smallint PRIMARY KEY,
	status varchar(20) NOT NULL
	);

CREATE TABLE IF NOT EXISTS relation (
	id_relation smallint PRIMARY KEY,
	relation varchar(40) NOT NULL
	);

CREATE TABLE IF NOT EXISTS sex (
	id_sex smallint PRIMARY KEY,
	sex varchar(10)
	);

CREATE TABLE IF NOT EXISTS users (
	id_user serial PRIMARY KEY,
	id_vk int NOT NULL,
	id_vk_str varchar(80) NOT NULL,
	first_name varchar(80),
	last_name varchar(80),
	id_sex smallint REFERENCES sex (id_sex),
	id_city int,
	bdate date,
	id_relation int REFERENCES relation (id_relation),
	url varchar(160) NOT NULL
	);

CREATE TABLE IF NOT EXISTS user_candidate (
	id_user_candidate serial PRIMARY KEY,
	id_user int REFERENCES users (id_user),
	id_candidate int REFERENCES users (id_user),
	id_status smallint REFERENCES status (id_status),
	search_date timestamp
	);

CREATE TABLE IF NOT EXISTS photo (
	id_photo serial PRIMARY KEY,
	id_user int REFERENCES users (id_user),
	url varchar(160) NOT NULL,
	likes_count int,
	liked bool
	);

CREATE TABLE IF NOT EXISTS req_params (
	id_user int PRIMARY KEY REFERENCES users (id_user),
	id_sex smallint REFERENCES sex (id_sex),
	id_city int,
	age_from int,
	age_to int,
	id_relation smallint REFERENCES relation (id_relation)
	);

INSERT INTO status (id_status, status) 
VALUES
	(0, 'Не просмотрено'),
	(1, 'Просмотрено'),
	(2, 'Избранное'),
	(3, 'Чёрный список')
;

INSERT INTO relation (id_relation, relation)
VALUES
	(0, 'Не определено'),
	(1, 'Не женат/Не замужем'),
	(2, 'Есть друг/подруга'),
	(3, 'Помолвлен(-а)'),
	(4, 'Женат/Замужем'),
	(5, 'Всё сложно'),
	(6, 'В активном поиске'),
	(7, 'Влюблён(-а)'),
	(8, 'В гражданском браке')
;
