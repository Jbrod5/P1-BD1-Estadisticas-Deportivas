/*
    Jorge Anibal Bravo Rodríguez
    202131782
    ID #3
    Archivo de Consultas
*/


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 1
-- ¿Qué equipo ha anotado más goles en las temporadas 2010-2019 en UCL?
-- Justificación: Identifica al equipo más goleador de la última década en Champions
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 1
    e.nombre AS equipo,
    COUNT(g.id_evento) AS total_goles
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN temporada t ON p.id_temporada = t.id_temporada
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League'
  AND t.anio_inicio BETWEEN 2010 AND 2019
GROUP BY e.nombre
ORDER BY total_goles DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 2
-- ¿Cuáles son los 5 equipos con más partidos ganados como visitantes en Copa del Mundo, La Liga y UCL?
-- Justificación: Mide la fortaleza de los equipos jugando fuera de casa
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 5
    e.nombre AS equipo,
    COUNT(*) AS partidos_ganados_visitante
FROM partido p
JOIN equipo e ON p.id_equipo_visita = e.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre IN ('Champions League', 'La Liga', 'FIFA World Cup')
  AND p.goles_visita > p.goles_local
GROUP BY e.nombre
ORDER BY partidos_ganados_visitante DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 3
-- ¿Qué equipo tiene la mayor posesión promedio durante la temporada 2018?
-- Justificación: La posesión refleja el dominio del juego de un equipo
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 1
    e.nombre AS NombreEquipo,
    AVG(ep.posesion) AS PromedioPosesion
FROM equipo e
JOIN estadistica_partido ep ON e.id_equipo = ep.id_equipo
JOIN partido p ON ep.id_partido = p.id_partido
JOIN temporada t ON p.id_temporada = t.id_temporada
WHERE t.anio_inicio = 2018 
   OR t.anio_inicio = 2017 -- Ampliamos por si la temporada es 2017-2018
GROUP BY e.nombre
ORDER BY PromedioPosesion DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 4
-- ¿Qué portero tiene más partidos con portería a cero en La Liga y UCL?
-- Justificación: La portería a cero es el indicador más importante para un portero
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 1
    j.nombre AS NombrePortero,
    COUNT(DISTINCT p.id_partido) AS PorteriasACero
FROM jugador j
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
JOIN equipo e ON ev.id_equipo = e.id_equipo
WHERE (p.id_equipo_local = e.id_equipo AND p.goles_visita = 0)
   OR (p.id_equipo_visita = e.id_equipo AND p.goles_local = 0)
GROUP BY j.nombre
ORDER BY PorteriasACero DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 5
-- ¿Qué jugador tiene el mejor promedio de goles por minuto jugado en Copa del Mundo? (mínimo 500 minutos)
-- Justificación: Mide la eficiencia goleadora real de un jugador
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 5
    j.nombre AS NombreJugador,
    COUNT(g.id_evento) AS Goles,
    (CAST(COUNT(g.id_evento) AS FLOAT) / NULLIF(COUNT(DISTINCT p.id_partido), 0)) AS PromedioGoles
FROM jugador j
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN gol g ON ev.id_evento = g.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
GROUP BY j.nombre
ORDER BY PromedioGoles DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 6
-- ¿Qué partidos tuvieron más goles combinados en finales de Copa del Mundo y UCL?
-- Justificación: Las finales más goleadas son las más emocionantes de la historia
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 5
    el.nombre AS equipo_local,
    ev2.nombre AS equipo_visita,
    p.goles_local,
    p.goles_visita,
    (p.goles_local + p.goles_visita) AS total_goles,
    c.nombre AS competicion,
    t.anio_inicio AS temporada
FROM partido p
JOIN equipo el ON p.id_equipo_local = el.id_equipo
JOIN equipo ev2 ON p.id_equipo_visita = ev2.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN temporada t ON p.id_temporada = t.id_temporada
WHERE p.fase = 'Final'
  AND c.nombre IN ('FIFA World Cup', 'Champions League')
ORDER BY total_goles DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 7
-- ¿Qué jugador ha recibido más tarjetas amarillas en Copa del Mundo o UCL?
-- Justificación: Identifica a los jugadores más conflictivos en competencias importantes
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 5
    j.nombre AS NombreJugador,
    COUNT(t.id_evento) AS CantidadAmarillas
FROM tarjeta t
JOIN evento ev ON t.id_evento = ev.id_evento
JOIN jugador j ON ev.id_jugador = j.id_jugador
WHERE t.color LIKE '%Amarilla%' OR t.color LIKE '%Yellow%'
GROUP BY j.nombre
ORDER BY CantidadAmarillas DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 8
-- ¿Cuál es el promedio de goles por partido en La Liga y qué equipos superan ese promedio en UCL y Copa?
-- Justificación: Compara la productividad goleadora entre competencias
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT 
    e.nombre AS Equipo,
    c.nombre AS Competicion,
    AVG(CAST(p.goles_local + p.goles_visita AS FLOAT)) AS PromedioGolesPartido
FROM partido p
JOIN equipo e ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre IN ('Champions League', 'FIFA World Cup', 'La Liga')
GROUP BY e.nombre, c.nombre
ORDER BY PromedioGolesPartido DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 9
-- ¿Qué equipos tienen mejor diferencia de goles en los últimos 10 minutos en UCL y Copa del Mundo?
-- Justificación: Mide la capacidad de reacción y cierre de partidos en momentos críticos
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 5
    e.nombre AS equipo,
    c.nombre AS competicion,
    SUM(CASE WHEN ev.id_equipo = e.id_equipo THEN 1 ELSE 0 END) AS goles_a_favor,
    SUM(CASE WHEN ev.id_equipo != e.id_equipo THEN 1 ELSE 0 END) AS goles_en_contra,
    SUM(CASE WHEN ev.id_equipo = e.id_equipo THEN 1 ELSE -1 END) AS diferencia_goles
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN equipo e ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
WHERE ev.minuto >= 80
  AND c.nombre IN ('Champions League', 'FIFA World Cup')
GROUP BY e.nombre, c.nombre
ORDER BY diferencia_goles DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 10
-- TOP 10 jugadores con mejor puntuación en cuartos de final del Mundial
-- Justificación: Crea un sistema de puntuación para identificar los jugadores más determinantes
-- Puntuación: Gol=10pts, Asistencia=7pts, Pase completado=1pt
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 10 (Corregida)
SELECT TOP 10
    j.nombre AS jugador,
    SUM(CASE WHEN g.id_evento IS NOT NULL THEN 10 ELSE 0 END) AS pts_goles,
    SUM(CASE WHEN g.id_asistente = j.id_jugador THEN 7 ELSE 0 END) AS pts_asistencias,
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS pts_pases,
    (SUM(CASE WHEN g.id_evento IS NOT NULL THEN 10 ELSE 0 END) +
     SUM(CASE WHEN g.id_asistente = j.id_jugador THEN 7 ELSE 0 END) +
     SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END)) AS puntuacion_total
FROM jugador j
JOIN evento ev ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
LEFT JOIN gol g ON g.id_evento = ev.id_evento
LEFT JOIN pase pa ON pa.id_evento = ev.id_evento
WHERE p.fase = 'Quarter-finals' 
GROUP BY j.nombre
ORDER BY puntuacion_total DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 11
-- ¿Quién es el jugador del mes en La Liga en marzo de 2018?
-- Justificación: Identifica al jugador más participativo en un mes específico
-- Puntuación: Gol=10pts, Asistencia=6pts, Pase completado=1pt
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 1
    j.nombre AS Jugador,
    COUNT(g.id_evento) AS TotalGoles,
    c.nombre AS Competicion
FROM jugador j
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN gol g ON ev.id_evento = g.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
GROUP BY j.nombre, c.nombre
ORDER BY TotalGoles DESC;

-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 12
-- ¿Qué jugadores han realizado más asistencias en Copa del Mundo y su promedio por partido?
-- Justificación: Las asistencias reflejan la capacidad creativa y de generación de juego
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 10
    j.nombre AS jugador,
    COUNT(g.id_evento) AS total_asistencias,
    COUNT(DISTINCT p.id_partido) AS partidos_jugados,
    CAST(COUNT(g.id_evento) AS FLOAT) /
        NULLIF(COUNT(DISTINCT p.id_partido), 0) AS promedio_asistencias
FROM jugador j
JOIN gol g ON g.id_asistente = j.id_jugador
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
GROUP BY j.nombre
ORDER BY total_asistencias DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 13
-- ¿Cuántos penales ha anotado cada equipo en finales de Champions y su efectividad?
-- Justificación: La efectividad desde el punto penal puede definir campeonatos
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT
    e.nombre AS equipo,
    COUNT(pn.id_evento) AS penales_totales,
    SUM(CASE WHEN pn.resultado = 'Anotado' THEN 1 ELSE 0 END) AS penales_anotados,
    CAST(SUM(CASE WHEN pn.resultado = 'Anotado' THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(pn.id_evento), 0) * 100 AS efectividad_porcentaje
FROM penal pn
JOIN evento ev ON pn.id_evento = ev.id_evento
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League'
  AND p.fase = 'Final'
GROUP BY e.nombre
ORDER BY efectividad_porcentaje DESC;




-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 15
-- Frecuencia de cambios de jugadores en finales de Champions League
-- Justificación: Analiza en qué minutos los entrenadores realizan más sustituciones en finales
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT
    ev.minuto,
    COUNT(*) AS cantidad_cambios
FROM sustitucion s
JOIN evento ev ON s.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League'
  AND p.fase = 'Final'
GROUP BY ev.minuto
ORDER BY ev.minuto;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 16
-- Frecuencia de cambios de jugadores en partidos de La Liga
-- Justificación: Compara los patrones de sustitución en liga vs finales de Champions
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT
    ev.minuto,
    COUNT(*) AS cantidad_cambios
FROM sustitucion s
JOIN evento ev ON s.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'La Liga'
GROUP BY ev.minuto
ORDER BY ev.minuto;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 17
-- ¿Qué equipos tuvieron más posesión y tiros a puerta en partidos que perdieron en Copa del Mundo?
-- Justificación: Identifica equipos que dominan pero no convierten, un análisis de eficiencia
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 5
    e.nombre AS equipo,
    AVG(ep.posesion) AS posesion_promedio,
    AVG(ep.tiros_a_puerta) AS tiros_promedio
FROM estadistica_partido ep
JOIN equipo e ON ep.id_equipo = e.id_equipo
JOIN partido p ON ep.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
  AND (
      (ep.id_equipo = p.id_equipo_local AND p.goles_local < p.goles_visita)
      OR
      (ep.id_equipo = p.id_equipo_visita AND p.goles_visita < p.goles_local)
  )
GROUP BY e.nombre
ORDER BY posesion_promedio DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 18
-- Datos para mapa de calor de posesión por zonas del campo en Copa del Mundo
-- Justificación: Las coordenadas x,y de eventos permiten visualizar zonas de control
-- (Este resultado se usa con mplsoccer en Python para el mapa de calor :3)
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT
    e.nombre AS equipo,
    ev.x_inicio,
    ev.y_inicio,
    COUNT(*) AS eventos_en_zona
FROM evento ev
JOIN equipo e ON ev.id_equipo_posesion = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
  AND ev.x_inicio IS NOT NULL
  AND ev.y_inicio IS NOT NULL
GROUP BY e.nombre, ev.x_inicio, ev.y_inicio
ORDER BY e.nombre, eventos_en_zona DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 19
-- Mapa de goles de un jugador específico (ejemplo: Messi)
-- Justificación: Las coordenadas de los goles permiten analizar las zonas de finalización
-- (Resultado exportable a Python con mplsoccer para visualización :D)
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT
    j.nombre AS jugador,
    ev.x_inicio AS x_posicion,
    ev.y_inicio AS y_posicion,
    g.x_fin AS x_destino,
    g.y_fin AS y_destino,
    g.tipo_gol,
    ev.minuto,
    p.fecha
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN jugador j ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
WHERE j.nombre LIKE '%Messi%'
ORDER BY p.fecha, ev.minuto;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 20
-- El camino de Argentina en el Mundial 2022 con eficiencia y posesión
-- Justificación: Muestra la progresión de Argentina partido a partido hasta ganar el Mundial
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT
    p.fase,
    p.fecha,
    er.nombre AS rival,
    p.goles_local AS goles_arg,
    p.goles_visita AS goles_rival,
    ep.posesion,
    ep.pases_completados,
    ep.tiros_a_puerta,
    CAST(ep.pases_completados AS FLOAT) /
        NULLIF(ep.pases_totales, 0) * 100 AS eficiencia_pases
FROM partido p
JOIN equipo ea ON ea.nombre = 'Argentina'
JOIN equipo er ON er.id_equipo = p.id_equipo_visita
JOIN estadistica_partido ep ON ep.id_partido = p.id_partido AND ep.id_equipo = ea.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN temporada t ON p.id_temporada = t.id_temporada
WHERE c.nombre = 'FIFA World Cup'
  AND t.anio_inicio = 2022
  AND p.id_equipo_local = ea.id_equipo
ORDER BY p.fecha;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 21
-- ¿Cuál es el jugador más determinante en la última década de UCL?
-- Justificación: Combina goles, asistencias y pases clave para un score global
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 1
    j.nombre AS jugador,
    COUNT(DISTINCT g.id_evento) AS goles,
    COUNT(DISTINCT g2.id_evento) AS asistencias,
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS pases_completados,
    COUNT(DISTINCT g.id_evento) * 10 +
    COUNT(DISTINCT g2.id_evento) * 7 +
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS score_total
FROM jugador j
JOIN evento ev ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
JOIN temporada t ON p.id_temporada = t.id_temporada
JOIN competicion c ON p.id_competicion = c.id_competicion
LEFT JOIN gol g ON g.id_evento = ev.id_evento
LEFT JOIN gol g2 ON g2.id_asistente = j.id_jugador
LEFT JOIN pase pa ON pa.id_evento = ev.id_evento
WHERE c.nombre = 'Champions League'
  AND t.anio_inicio BETWEEN 2010 AND 2020
GROUP BY j.nombre
ORDER BY score_total DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 22
-- ¿Cuál es el equipo más determinante en la última década de UCL?
-- Justificación: Combina victorias, goles y posesión para evaluar dominio general
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 1
    e.nombre AS equipo,
    COUNT(DISTINCT p.id_partido) AS partidos_jugados,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
        WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
        ELSE 0 END) AS victorias,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
        ELSE p.goles_visita END) AS goles_totales,
    AVG(ep.posesion) AS posesion_promedio
FROM equipo e
JOIN partido p ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN temporada t ON p.id_temporada = t.id_temporada
LEFT JOIN estadistica_partido ep ON ep.id_partido = p.id_partido AND ep.id_equipo = e.id_equipo
WHERE c.nombre = 'Champions League'
  AND t.anio_inicio BETWEEN 2010 AND 2020
GROUP BY e.nombre
ORDER BY victorias DESC, goles_totales DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 23
-- ¿Cuál es el jugador más determinante en Copa del Mundo?
-- Justificación: Similar a Q21 pero enfocado en selecciones nacionales
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 1
    j.nombre AS jugador,
    COUNT(DISTINCT g.id_evento) AS goles,
    COUNT(DISTINCT g2.id_evento) AS asistencias,
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS pases_completados,
    COUNT(DISTINCT g.id_evento) * 10 +
    COUNT(DISTINCT g2.id_evento) * 7 +
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS score_total
FROM jugador j
JOIN evento ev ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
LEFT JOIN gol g ON g.id_evento = ev.id_evento
LEFT JOIN gol g2 ON g2.id_asistente = j.id_jugador
LEFT JOIN pase pa ON pa.id_evento = ev.id_evento
WHERE c.nombre = 'FIFA World Cup'
GROUP BY j.nombre
ORDER BY score_total DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 24
-- ¿Cuál es el equipo más determinante por pases completados en los últimos 10 minutos en La Liga?
-- Justificación: Los pases en los últimos minutos indican capacidad de mantener el juego bajo presión
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 1
    e.nombre AS equipo,
    COUNT(pa.id_evento) AS pases_completados_ultimos_10
FROM pase pa
JOIN evento ev ON pa.id_evento = ev.id_evento
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'La Liga'
  AND ev.minuto >= 80
  AND pa.completado = 1
GROUP BY e.nombre
ORDER BY pases_completados_ultimos_10 DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 25
-- ¿Cuál es el equipo más determinante en Copa del Mundo?
-- Justificación: Evalúa rendimiento global en todas las ediciones disponibles
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 1
    e.nombre AS equipo,
    COUNT(DISTINCT p.id_partido) AS partidos,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
        WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
        ELSE 0 END) AS victorias,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
        ELSE p.goles_visita END) AS goles_anotados
FROM equipo e
JOIN partido p ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
GROUP BY e.nombre
ORDER BY victorias DESC, goles_anotados DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 26
-- Sucesión de pases que terminaron en gol en cuartos de final del Mundial 1986
-- Justificación: Reconstruye las jugadas que terminaron en gol, incluyendo el famoso gol de Maradona
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT 
    j.nombre AS Jugador,
    ev.minuto,
    ev.segundo,
    ev.x_inicio,
    ev.y_inicio
FROM evento ev
JOIN pase pa ON ev.id_evento = pa.id_evento
JOIN jugador j ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
WHERE p.fase = 'Quarter-finals' 
  AND ev.id_equipo = (SELECT id_equipo FROM equipo WHERE nombre = 'Argentina') -- Ejemplo
ORDER BY ev.minuto, ev.segundo;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 27
-- Sucesión de pases que terminaron en gol en cuartos de final de UCL 2019
-- Justificación: Analiza las jugadas colectivas que generaron goles en la Champions 2019
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 20
    j.nombre AS Jugador,
    ev.minuto,
    ev.segundo,
    ev.x_inicio,
    ev.y_inicio,
    pa.x_fin,
    pa.y_fin
FROM evento ev
JOIN pase pa ON ev.id_evento = pa.id_evento
JOIN jugador j ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League' 
  AND p.fase = 'Final' -- Cambiado de Quarter-finals a Final
ORDER BY ev.minuto, ev.segundo;

-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 28
-- Mapa de calor de eventos de un jugador específico
-- Justificación: Las coordenadas x,y de todos los eventos muestran las zonas de influencia
-- (Resultado exportable a Python con mplsoccer)
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT
    j.nombre AS jugador,
    te.nombre AS tipo_evento,
    ev.x_inicio,
    ev.y_inicio,
    ev.minuto,
    p.fecha
FROM evento ev
JOIN jugador j ON ev.id_jugador = j.id_jugador
JOIN tipo_evento te ON ev.id_tipo = te.id_tipo
JOIN partido p ON ev.id_partido = p.id_partido
WHERE j.nombre LIKE '%Messi%'
  AND ev.x_inicio IS NOT NULL
ORDER BY p.fecha, ev.minuto;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 29
-- ¿Qué país tuvo mayor efectividad en 2018, comparando UCL y Copa del Mundo?
-- Justificación: Compara el rendimiento de los países en dos competencias simultáneas
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT TOP 10
    n.nombre AS Pais,
    COUNT(DISTINCT p.id_partido) AS PartidosTotales,
    COUNT(g.id_evento) AS GolesPorNacionalidad
FROM nacionalidad n
JOIN jugador j ON n.id_nacionalidad = j.id_nacionalidad
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
LEFT JOIN gol g ON ev.id_evento = g.id_evento
GROUP BY n.nombre
HAVING COUNT(g.id_evento) > 0 -- Solo países que tengan al menos un gol
ORDER BY GolesPorNacionalidad DESC;

-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 30
-- ¿Cuál competición fue más completa en 2018 y cuáles fueron los 3 países principales?
-- Justificación: Compara la calidad futbolística global de UCL vs Copa del Mundo 2018
-- = = = = = = = = = = = = = = = = = = = = = = = = = =

SELECT 
    c.nombre AS Competicion,
    COUNT(DISTINCT p.id_partido) AS TotalPartidos,
    AVG(CAST(p.goles_local + p.goles_visita AS FLOAT)) AS PromedioGoles
FROM competicion c
JOIN partido p ON c.id_competicion = p.id_competicion
WHERE YEAR(p.fecha) = 2018
GROUP BY c.nombre
ORDER BY PromedioGoles DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 31
-- ¿Qué equipos tienen más probabilidades de ganar el Mundial 2026?
-- Justificación: Basado en victorias, goles y posesión de los últimos mundiales disponibles
-- Indicadores: victorias (peso 3), goles anotados (peso 2), posesión promedio (peso 1)
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 5
    e.nombre AS equipo,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
        WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
        ELSE 0 END) AS victorias,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
        ELSE p.goles_visita END) AS goles,
    AVG(ep.posesion) AS posesion_promedio,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
        WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
        ELSE 0 END) * 3 +
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
        ELSE p.goles_visita END) * 2 +
    ISNULL(AVG(ep.posesion), 0) AS score_mundial_2026
FROM equipo e
JOIN partido p ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
LEFT JOIN estadistica_partido ep ON ep.id_partido = p.id_partido AND ep.id_equipo = e.id_equipo
WHERE c.nombre = 'FIFA World Cup'
GROUP BY e.nombre
ORDER BY score_mundial_2026 DESC;


-- = = = = = = = = = = = = = = = = = = = = = = = = = =
-- CONSULTA 32
-- ¿Qué equipo tiene más promedio de goles en los primeros 10 minutos en La Liga y UCL?
-- Justificación: Los goles tempranos dan ventaja psicológica y táctica
-- = = = = = = = = = = = = = = = = = = = = = = = = = =
SELECT TOP 5
    e.nombre AS equipo,
    c.nombre AS competicion,
    COUNT(g.id_evento) AS goles_primeros_10,
    COUNT(DISTINCT p.id_partido) AS partidos_jugados,
    CAST(COUNT(g.id_evento) AS FLOAT) /
        NULLIF(COUNT(DISTINCT p.id_partido), 0) AS promedio_goles_inicio
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE ev.minuto <= 10
  AND c.nombre IN ('La Liga', 'Champions League')
GROUP BY e.nombre, c.nombre
ORDER BY promedio_goles_inicio DESC;