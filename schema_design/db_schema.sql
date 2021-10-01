
CREATE SCHEMA IF NOT EXISTS content;

create table if not exists content.film_work
(
    id uuid PRIMARY KEY,
    title         VARCHAR(255) not null,
    description   TEXT,
    creation_date DATE,
    certificate   TEXT,
    file_path     text,
    rating        real,
    type          varchar(20) not null,
    created_at    timestamp with time zone,
    updated_at    timestamp with time zone
);

create table if not exists content.genre
(
    id uuid PRIMARY KEY,
    name        VARCHAR(255) not null,
    description TEXT,
    created_at  timestamp with time zone,
    updated_at  timestamp with time zone
);

create table if not exists content.genre_film_work
(
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    genre_id     uuid NOT NULL,
    created_at   timestamp with time zone
);

create unique index if not exists content_film_work_genre_idx
    on content.genre_film_work (film_work_id, genre_id);


create table if not exists content.person
(
    id uuid PRIMARY KEY,
    full_name  VARCHAR(255) not null,
    birth_date DATE,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

create table if not exists content.person_film_work
(
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    person_id    uuid NOT NULL,
    role         varchar(20) not null,
    created_at   timestamp with time zone
);

create unique index if not exists content_film_work_person_role_idx
    on content.person_film_work (film_work_id, person_id, role);
