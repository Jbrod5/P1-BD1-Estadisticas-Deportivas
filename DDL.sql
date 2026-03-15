/* Jorge Anibal Bravo Rodríguez
    202131782
    ID #3
*/



-- REINICIAR LA BASE DE DATOOOOS


USE master; -- salir de la base de datos para poder borrarla
GO

-- 1. Borrar la base de datos si ya existe
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'ProyectoFutbol')
BEGIN
    -- El 'ROLLBACK IMMEDIATE' expulsa a cualquier usuario conectado para que se pueda borrar :3
    ALTER DATABASE ProyectoFutbol SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE ProyectoFutbol;
END
GO

-- 2. Crearla de nuevo
CREATE DATABASE ProyectoFutbol;
GO

-- 3. Empezar a usarla para crear las tablas
USE ProyectoFutbol;
GO


-- = = = = = = = = = = = = = = = = = = = = = = = = = = ENTIDADES FUERTES (Las que no dependen de nadie :D) = = = = = = = = = = = = = = = = = = = = = = = = = =
CREATE TABLE nacionalidad (
    id_nacionalidad INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE posicion (
    id_posicion INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

CREATE TABLE tipo_evento (
    id_tipo INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

CREATE TABLE parte_cuerpo (
    id_parte_cuerpo INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

CREATE TABLE estadio (
    id_estadio INT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    ciudad VARCHAR(100),
    pais VARCHAR(100)
);

CREATE TABLE competicion (
    id_competicion INT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL
);

CREATE TABLE temporada (
    id_temporada INT PRIMARY KEY,
    anio_inicio INT NOT NULL,
    anio_fin INT NOT NULL
);

CREATE TABLE equipo (
    id_equipo INT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL
);

CREATE TABLE entrenador (
    id_entrenador INT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL
);







-- = = = = = = = = = = = = = = = = = = = = = = = = = = = = ENTIDADES DEBILES (con llaves foraneas :3) = = = = = = = = = = = = = = = = = = = = = = = = = = = =
CREATE TABLE arbitro (
    id_arbitro INT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,

    id_nacionalidad INT FOREIGN KEY REFERENCES nacionalidad(id_nacionalidad)
);

CREATE TABLE jugador (
    id_jugador INT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,

    id_nacionalidad INT FOREIGN KEY REFERENCES nacionalidad(id_nacionalidad)
);

CREATE TABLE partido (
    id_partido INT PRIMARY KEY,
    fecha DATE,
    kick_off TIME,
    goles_local INT DEFAULT 0,
    goles_visita INT DEFAULT 0,
    fase VARCHAR(50),
    jornada INT,


    id_competicion INT FOREIGN KEY REFERENCES competicion(id_competicion),
    id_temporada INT FOREIGN KEY REFERENCES temporada(id_temporada),
    id_estadio INT FOREIGN KEY REFERENCES estadio(id_estadio),
    id_equipo_local INT FOREIGN KEY REFERENCES equipo(id_equipo),
    id_equipo_visita INT FOREIGN KEY REFERENCES equipo(id_equipo),
    id_arbitro INT FOREIGN KEY REFERENCES arbitro(id_arbitro)
);



-- ALINEACIONES = = = = = = = = = = = = = = = = = = = = = = = = = = =
CREATE TABLE alineacion (
    id_alineacion INT PRIMARY KEY IDENTITY(1,1),
    formacion VARCHAR(20),

    id_partido INT FOREIGN KEY REFERENCES partido(id_partido),
    id_equipo INT FOREIGN KEY REFERENCES equipo(id_equipo)
);

CREATE TABLE alineacion_jugador (
    id_al_jugador INT PRIMARY KEY IDENTITY(1,1),
    dorsal INT,
    minuto_inicio INT,
    minuto_fin INT,

    id_alineacion INT FOREIGN KEY REFERENCES alineacion(id_alineacion),
    id_jugador INT FOREIGN KEY REFERENCES jugador(id_jugador),
    id_posicion INT FOREIGN KEY REFERENCES posicion(id_posicion)
);



-- ESTADISTICAS (para csv del mundial 2022 y calculos de UCL/Liga :D) = = = = = = = = = = = = = 
CREATE TABLE estadistica_partido (
    id_estadistica      INT PRIMARY KEY IDENTITY(1,1),
    posesion            FLOAT,
    tiros_totales       INT,
    tiros_a_puerta      INT,
    pases_totales       INT,
    pases_completados   INT,
    corners             INT,
    faltas              INT,
    tarjetas_amarillas  INT,
    tarjetas_rojas      INT,
    fueras_de_juego     INT,

    id_partido          INT NOT NULL FOREIGN KEY REFERENCES partido(id_partido),
    id_equipo           INT NOT NULL FOREIGN KEY REFERENCES equipo(id_equipo)
);



--  EVENTOS (VARCHAR 36 para soportar UUIDs) = = = = = = = = = = = = = 
CREATE TABLE evento (
    id_evento VARCHAR(36) PRIMARY KEY,
    minuto INT,
    segundo INT,
    periodo INT,
    x_inicio FLOAT,
    y_inicio FLOAT,
    duracion FLOAT,

    id_equipo_posesion INT FOREIGN KEY REFERENCES equipo(id_equipo),
    id_evento_relacionado VARCHAR(36) FOREIGN KEY REFERENCES evento(id_evento),
    id_partido INT FOREIGN KEY REFERENCES partido(id_partido),
    id_tipo INT FOREIGN KEY REFERENCES tipo_evento(id_tipo),
    id_jugador INT FOREIGN KEY REFERENCES jugador(id_jugador),
    id_equipo INT FOREIGN KEY REFERENCES equipo(id_equipo)
);





-- = = = = = = = = = = = = = = =  ESPECIALIZACIONES (Relación 1:1 con Evento) = = = = = = = = = = = = = = = 
CREATE TABLE gol (
    id_evento VARCHAR(36) PRIMARY KEY FOREIGN KEY REFERENCES evento(id_evento),
    tipo_gol VARCHAR(50),
    x_fin FLOAT,
    y_fin FLOAT,

    id_parte_cuerpo INT FOREIGN KEY REFERENCES parte_cuerpo(id_parte_cuerpo),
    id_asistente INT FOREIGN KEY REFERENCES jugador(id_jugador)
);

CREATE TABLE tarjeta (
    id_evento VARCHAR(36) PRIMARY KEY FOREIGN KEY REFERENCES evento(id_evento),
    color VARCHAR(20) -- 'Amarilla', 'Roja'
);

CREATE TABLE pase (
    id_evento VARCHAR(36) PRIMARY KEY FOREIGN KEY REFERENCES evento(id_evento),
    longitud FLOAT,
    angulo FLOAT,
    altura VARCHAR(50),
    completado BIT DEFAULT 1,
    x_fin FLOAT,
    y_fin FLOAT,


    id_parte_cuerpo INT FOREIGN KEY REFERENCES parte_cuerpo(id_parte_cuerpo),
    id_receptor INT FOREIGN KEY REFERENCES jugador(id_jugador)
);

CREATE TABLE disparo (
    id_evento VARCHAR(36) PRIMARY KEY FOREIGN KEY REFERENCES evento(id_evento),
    x_fin FLOAT,
    y_fin FLOAT,
    outcome VARCHAR(50),
    
    id_parte_cuerpo INT FOREIGN KEY REFERENCES parte_cuerpo(id_parte_cuerpo)
);

CREATE TABLE conduccion (
    id_evento VARCHAR(36) PRIMARY KEY FOREIGN KEY REFERENCES evento(id_evento),
    x_fin FLOAT,
    y_fin FLOAT
);

CREATE TABLE sustitucion (
    id_evento VARCHAR(36) PRIMARY KEY FOREIGN KEY REFERENCES evento(id_evento),
    id_jugador_sale INT NOT NULL FOREIGN KEY REFERENCES jugador(id_jugador),
    id_jugador_entra INT NOT NULL FOREIGN KEY REFERENCES jugador(id_jugador)
);

CREATE TABLE penal (
    id_evento VARCHAR(36) PRIMARY KEY FOREIGN KEY REFERENCES evento(id_evento),
    resultado VARCHAR(20) NOT NULL, -- 'Anotado', 'Fallado', 'Atajado'
    id_portero INT FOREIGN KEY REFERENCES jugador(id_jugador)
);






-- 6. RELACIONES MUCHOS A MUCHOS (Contratos)
CREATE TABLE contrato_equipo_jugador (
    id_contrato INT PRIMARY KEY IDENTITY(1,1),
    id_jugador INT FOREIGN KEY REFERENCES jugador(id_jugador),
    id_equipo INT FOREIGN KEY REFERENCES equipo(id_equipo),
    fecha_inicio DATE,
    fecha_fin DATE
);

CREATE TABLE contrato_entrenador (
    id_contrato INT PRIMARY KEY IDENTITY(1,1),
    id_entrenador INT FOREIGN KEY REFERENCES entrenador(id_entrenador),
    id_equipo INT FOREIGN KEY REFERENCES equipo(id_equipo),
    fecha_inicio DATE,
    fecha_fin DATE
);