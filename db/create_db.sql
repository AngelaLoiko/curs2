CREATE DATABASE vkinder;

CREATE TABLE IF NOT EXISTS status (
	id_status smallint PRIMARY KEY,
	status varchar(80)
	);

CREATE TABLE IF NOT EXISTS user (
	id_user serial PRIMARY KEY,
	id_vk integer,
	id_vk_str varchar(80),
	first_name varchar(80),
	last_name varchar(80),
	sex smallint,
	id_city integer,
	bdate date,
	age_from smallint,
	age_to smallint,
	id_status int REFERENCES status (id_status),
	url varchar(160)
	);

CREATE TABLE IF NOT EXISTS user_candidate (
    id_user_candidate serial PRIMARY KEY,
	id_user int REFERENCES users (id_user),
	id_candidate int REFERENCES users (id_user),
	elected boolean,
	blacklisted boolean,
	search_date timestamptz

	PRIMARY KEY (id_user_candidate)
	);

CREATE TABLE IF NOT EXISTS photo (
	id_photo serial PRIMARY KEY,
	id_user int REFERENCES user (id_user),
	link varchar(160) NOT NULL,
	likes_count int,
	like boolean
	);
