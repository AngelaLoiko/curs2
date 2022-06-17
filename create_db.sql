CREATE DATABASE vkinder;

CREATE TABLE IF NOT EXISTS status (
	status_id int PRIMARY KEY,
	status varchar(80)
	);

CREATE TABLE IF NOT EXISTS users (
	user_id serial PRIMARY KEY,
	vk_id varchar(40) UNIQUE NOT NULL,
	first_name varchar(80),
	last_name varchar(80),
	sex bool,
	city varchar(80),
	age int,
	status_id int REFERENCES status (status_id)
	);

CREATE TABLE IF NOT EXISTS users_candidates (
	user_id int REFERENCES users (user_id),
	candidate_id int REFERENCES users (user_id),
	PRIMARY KEY (user_id, candidate_id)
	);

CREATE TABLE IF NOT EXISTS photos (
	photo_id serial PRIMARY KEY,
	user_id int REFERENCES users (user_id),
	link varchar(160) NOT NULL,
	likes int
	);
