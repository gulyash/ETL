SELECT fw.id                                                                                                     as id,
       fw.title,
       fw.description,
       fw.rating                                                                                                 as imdb_rating,
       ARRAY_AGG(DISTINCT g.name)                                                                                AS genre,
       ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'director')                                      AS director,
       JSON_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) FILTER (WHERE pfw.role = 'actor')  AS actors,
       JSON_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) FILTER (WHERE pfw.role = 'writer') AS writers,
       ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'actor')                                         AS actors_names,
       ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'writer')                                        AS writers_names,
       fw.updated_at                                                                                             as updated_at
FROM content.film_work fw
         LEFT OUTER JOIN content.genre_film_work gfw ON fw.id = gfw.film_work_id
         LEFT OUTER JOIN content.genre g ON (gfw.genre_id = g.id)
         LEFT OUTER JOIN content.person_film_work pfw ON (fw.id = pfw.film_work_id)
         LEFT OUTER JOIN content.person p ON (pfw.person_id = p.id)
WHERE fw.updated_at > %s
GROUP BY fw.id, fw.title, fw.description, fw.rating
ORDER BY fw.updated_at;
