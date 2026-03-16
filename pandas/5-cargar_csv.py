import sqlalchemy as sa
import csv
import os
from datetime import datetime

# Configuracion de conexion
motor_bd = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# Abrimos archivo SQL para guardar los inserts
archivo_sql = open('carga_datos_csv.sql', 'w', encoding='utf-8')
archivo_sql.write("USE ProyectoFutbol;\nGO\n\n")


def asegurar_datos_base(conexion):
    """Crea registros por defecto para evitar errores de Foreign Key"""
    try:
        # 1. Asegurar Estadio 1
        estadio_existe = conexion.execute(sa.text("SELECT 1 FROM estadio WHERE id_estadio = 1")).fetchone()
        if not estadio_existe:
            conexion.execute(sa.text("INSERT INTO estadio (id_estadio, nombre, ciudad) VALUES (1, 'Estadio Genérico', 'Desconocida')"))
            print("  [Setup] Estadio por defecto creado.")

        # 2. Asegurar Competicion 1
        comp_existe = conexion.execute(sa.text("SELECT 1 FROM competicion WHERE id_competicion = 1")).fetchone()
        if not comp_existe:
            conexion.execute(sa.text("INSERT INTO competicion (id_competicion, nombre) VALUES (1, 'Competición Genérica')"))
            print("  [Setup] Competición por defecto creada.")

        # 3. Asegurar Temporada 1
        temp_existe = conexion.execute(sa.text("SELECT 1 FROM temporada WHERE id_temporada = 1")).fetchone()
        if not temp_existe:
            conexion.execute(sa.text("INSERT INTO temporada (id_temporada, anio_inicio, anio_fin) VALUES (1, 2022, 2022)"))
            print("  [Setup] Temporada por defecto creada.")
            
        conexion.commit()
    except Exception as e:
        print(f"Error al asegurar datos base: {e}")
        
        
def valor_sql(valor):
    """Convierte cualquier valor a formato SQL valido"""
    if valor is None or valor == '':
        return 'NULL'
    if isinstance(valor, str):
        # Escapar comillas simples
        valor_escapado = valor.replace("'", "''")
        return f"'{valor_escapado}'"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, bool):
        return '1' if valor else '0'
    if isinstance(valor, datetime):
        return f"'{valor.strftime('%Y-%m-%d %H:%M:%S')}'"
    return f"'{str(valor)}'"

def obtener_id_equipo_por_nombre(nombre_equipo, conexion):
    """Busca el id de un equipo por su nombre"""
    try:
        resultado = conexion.execute(
            sa.text("SELECT id_equipo FROM equipo WHERE nombre = :nombre"),
            {"nombre": nombre_equipo}
        ).fetchone()
        if resultado:
            return resultado[0]
        else:
            # Intentar insertar el equipo si no existe
            max_id = conexion.execute(sa.text("SELECT ISNULL(MAX(id_equipo), 0) + 1 FROM equipo")).scalar()
            conexion.execute(
                sa.text("INSERT INTO equipo (id_equipo, nombre) VALUES (:id, :nombre)"),
                {"id": max_id, "nombre": nombre_equipo}
            )
            conexion.commit()
            return max_id
    except Exception as error:
        print(f"Error obteniendo equipo {nombre_equipo}: {error}")
        return None

def obtener_id_partido_por_fecha_y_equipos(fecha, equipo_local, equipo_visitante, conexion):
    """Busca el id de un partido por fecha y equipos"""
    try:
        resultado = conexion.execute(
            sa.text("""
                SELECT p.id_partido 
                FROM partido p
                JOIN equipo el ON p.id_equipo_local = el.id_equipo
                JOIN equipo ev ON p.id_equipo_visita = ev.id_equipo
                WHERE p.fecha = :fecha 
                  AND el.nombre = :local 
                  AND ev.nombre = :visitante
            """),
            {"fecha": fecha, "local": equipo_local, "visitante": equipo_visitante}
        ).fetchone()
        return resultado[0] if resultado else None
    except Exception as error:
        print(f"Error obteniendo partido: {error}")
        return None






# 1. PROCESAR fifa_ranking_2022-10-06.csv
print("Procesando fifa_ranking_2022-10-06.csv...")
ruta_ranking = '../datos/Copa del mundo/fifa_ranking_2022-10-06.csv'

if os.path.exists(ruta_ranking):
    with motor_bd.connect() as conexion:
        asegurar_datos_base(conexion)
        
        with open(ruta_ranking, 'r', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            archivo_sql.write("-- Inserts desde fifa_ranking_2022-10-06.csv\n")
            
            for fila in lector:
                nombre_equipo = fila['team']
                codigo_equipo = fila['team_code']
                asociacion = fila['association']
                ranking = int(fila['rank'])
                puntos = float(fila['points'])
                
                # Buscar o insertar equipo
                id_equipo = obtener_id_equipo_por_nombre(nombre_equipo, conexion)
                
                if id_equipo:
                    # Insertar en estadistica_partido? El ranking no esta asociado a un partido
                    # Podriamos crear una tabla especifica de ranking pero no esta en el modelo
                    # Por ahora solo registramos que vimos el equipo
                    print(f"  Equipo procesado: {nombre_equipo} (Ranking: {ranking})")
            
            archivo_sql.write("\n")
    print("  Listo")
else:
    print(f"  Archivo no encontrado: {ruta_ranking}")








# 2. PROCESAR Fifa_world_cup_matches_2022.csv (ESTE ES EL MAS IMPORTANTE)

print("\nProcesando Fifa_world_cup_matches_2022.csv...")
ruta_mundial = '../datos/Copa del mundo/Fifa_world_cup_matches_2022.csv'

if os.path.exists(ruta_mundial):
    with motor_bd.connect() as conexion:
        asegurar_datos_base(conexion)
        
        
        with open(ruta_mundial, 'r', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            archivo_sql.write("\n-- Inserts desde Fifa_world_cup_matches_2022.csv\n")
            
            for fila in lector:
                equipo_local_nombre = fila['team1']
                equipo_visit_nombre = fila['team2']
                
                # Obtener IDs de equipos
                id_local = obtener_id_equipo_por_nombre(equipo_local_nombre, conexion)
                id_visit = obtener_id_equipo_por_nombre(equipo_visit_nombre, conexion)
                
                if not id_local or not id_visit:
                    print(f"  Error: No se encontraron equipos para {equipo_local_nombre} vs {equipo_visit_nombre}")
                    continue
                
                # Procesar fecha
                fecha_str = fila['date']
                try:
                    # Formato: "20 NOV 2022"
                    fecha_obj = datetime.strptime(fecha_str, "%d %b %Y")
                    fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
                except:
                    fecha_formateada = None
                
                # Buscar si el partido ya existe
                id_partido = None
                if fecha_formateada:
                    id_partido = obtener_id_partido_por_fecha_y_equipos(
                        fecha_formateada, equipo_local_nombre, equipo_visit_nombre, conexion
                    )
                
                if not id_partido:
                    # Si el partido no existe, lo creamos para poder meterle estadísticas

                    max_id_p = conexion.execute(sa.text("SELECT ISNULL(MAX(id_partido), 0) + 1 FROM partido")).scalar()
                    conexion.execute(
                        sa.text("""
                            INSERT INTO partido (id_partido, id_equipo_local, id_equipo_visita, fecha, id_estadio, id_competicion, id_temporada) 
                            VALUES (:id, :loc, :vis, :fec, 1, 1, 1) 
                        """),
                        {"id": max_id_p, "loc": id_local, "vis": id_visit, "fec": fecha_formateada}
                    )
                    id_partido = max_id_p
                    conexion.commit()
                    print(f"  Partido creado: {equipo_local_nombre} vs {equipo_visit_nombre}")
                
                # Extraer estadisticas para equipo local
                try:
                    posesion_local = float(fila['possession team1'].replace('%', '')) if fila['possession team1'] else None
                except:
                    posesion_local = None
                
                tiros_local = int(fila['total attempts team1']) if fila['total attempts team1'] else 0
                tiros_puerta_local = int(fila['on target attempts team1']) if fila['on target attempts team1'] else 0
                pases_local = int(fila['passes team1']) if fila['passes team1'] else 0
                pases_comp_local = int(fila['passes completed team1']) if fila['passes completed team1'] else 0
                corners_local = int(fila['corners team1']) if fila['corners team1'] else 0
                faltas_local = int(fila['fouls against team1']) if fila['fouls against team1'] else 0
                amarillas_local = int(fila['yellow cards team1']) if fila['yellow cards team1'] else 0
                rojas_local = int(fila['red cards team1']) if fila['red cards team1'] else 0
                fueras_local = int(fila['offsides team1']) if fila['offsides team1'] else 0
                
                # Insertar estadistica para equipo local
                try:
                    conexion.execute(
                        sa.text("""
                            INSERT INTO estadistica_partido 
                            (posesion, tiros_totales, tiros_a_puerta, pases_totales, pases_completados,
                             corners, faltas, tarjetas_amarillas, tarjetas_rojas, fueras_de_juego,
                             id_partido, id_equipo)
                            VALUES 
                            (:pos, :tiros, :tir_puer, :pases_tot, :pases_comp,
                             :corn, :falt, :amar, :roj, :fueras,
                             :id_part, :id_eq)
                        """),
                        {
                            "pos": posesion_local,
                            "tiros": tiros_local,
                            "tir_puer": tiros_puerta_local,
                            "pases_tot": pases_local,
                            "pases_comp": pases_comp_local,
                            "corn": corners_local,
                            "falt": faltas_local,
                            "amar": amarillas_local,
                            "roj": rojas_local,
                            "fueras": fueras_local,
                            "id_part": id_partido,
                            "id_eq": id_local
                        }
                    )
                    conexion.commit()
                    
                    # Guardar en archivo SQL
                    archivo_sql.write(
                        f"INSERT INTO estadistica_partido (posesion, tiros_totales, tiros_a_puerta, "
                        f"pases_totales, pases_completados, corners, faltas, tarjetas_amarillas, "
                        f"tarjetas_rojas, fueras_de_juego, id_partido, id_equipo) VALUES "
                        f"({valor_sql(posesion_local)}, {tiros_local}, {tiros_puerta_local}, "
                        f"{pases_local}, {pases_comp_local}, {corners_local}, {faltas_local}, "
                        f"{amarillas_local}, {rojas_local}, {fueras_local}, "
                        f"{id_partido}, {id_local});\n"
                    )
                    
                    print(f"  Estadisticas insertadas para local: {equipo_local_nombre}")
                    
                except Exception as error:
                    print(f"  Error insertando estadisticas local: {error}")
                    conexion.rollback()
                
                # Extraer estadisticas para equipo visitante
                try:
                    posesion_visit = float(fila['possession team2'].replace('%', '')) if fila['possession team2'] else None
                except:
                    posesion_visit = None
                
                tiros_visit = int(fila['total attempts team2']) if fila['total attempts team2'] else 0
                tiros_puerta_visit = int(fila['on target attempts team2']) if fila['on target attempts team2'] else 0
                pases_visit = int(fila['passes team2']) if fila['passes team2'] else 0
                pases_comp_visit = int(fila['passes completed team2']) if fila['passes completed team2'] else 0
                corners_visit = int(fila['corners team2']) if fila['corners team2'] else 0
                faltas_visit = int(fila['fouls against team2']) if fila['fouls against team2'] else 0
                amarillas_visit = int(fila['yellow cards team2']) if fila['yellow cards team2'] else 0
                rojas_visit = int(fila['red cards team2']) if fila['red cards team2'] else 0
                fueras_visit = int(fila['offsides team2']) if fila['offsides team2'] else 0
                
                # Insertar estadistica para equipo visitante
                try:
                    conexion.execute(
                        sa.text("""
                            INSERT INTO estadistica_partido 
                            (posesion, tiros_totales, tiros_a_puerta, pases_totales, pases_completados,
                             corners, faltas, tarjetas_amarillas, tarjetas_rojas, fueras_de_juego,
                             id_partido, id_equipo)
                            VALUES 
                            (:pos, :tiros, :tir_puer, :pases_tot, :pases_comp,
                             :corn, :falt, :amar, :roj, :fueras,
                             :id_part, :id_eq)
                        """),
                        {
                            "pos": posesion_visit,
                            "tiros": tiros_visit,
                            "tir_puer": tiros_puerta_visit,
                            "pases_tot": pases_visit,
                            "pases_comp": pases_comp_visit,
                            "corn": corners_visit,
                            "falt": faltas_visit,
                            "amar": amarillas_visit,
                            "roj": rojas_visit,
                            "fueras": fueras_visit,
                            "id_part": id_partido,
                            "id_eq": id_visit
                        }
                    )
                    conexion.commit()
                    
                    # Guardar en archivo SQL
                    archivo_sql.write(
                        f"INSERT INTO estadistica_partido (posesion, tiros_totales, tiros_a_puerta, "
                        f"pases_totales, pases_completados, corners, faltas, tarjetas_amarillas, "
                        f"tarjetas_rojas, fueras_de_juego, id_partido, id_equipo) VALUES "
                        f"({valor_sql(posesion_visit)}, {tiros_visit}, {tiros_puerta_visit}, "
                        f"{pases_visit}, {pases_comp_visit}, {corners_visit}, {faltas_visit}, "
                        f"{amarillas_visit}, {rojas_visit}, {fueras_visit}, "
                        f"{id_partido}, {id_visit});\n"
                    )
                    
                    print(f"  Estadisticas insertadas para visitante: {equipo_visit_nombre}")
                    
                except Exception as error:
                    print(f"  Error insertando estadisticas visitante: {error}")
                    conexion.rollback()
            
            archivo_sql.write("\n")
    print("  Listo")
else:
    print(f"  Archivo no encontrado: {ruta_mundial}")









# 3. PROCESAR international_matches.csv

print("\nProcesando international_matches.csv...")
ruta_internacional = '../datos/Copa del mundo/international_matches.csv'

if os.path.exists(ruta_internacional):
    with motor_bd.connect() as conexion:
        asegurar_datos_base(conexion)
        
        
        with open(ruta_internacional, 'r', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            archivo_sql.write("\n-- Inserts desde international_matches.csv\n")
            
            for fila in lector:
                # Este archivo tiene informacion util pero no encaja directamente
                # Podriamos usarlo para completar equipos o ranking
                equipo_local = fila['home_team']
                equipo_visit = fila['away_team']
                ranking_local = fila['home_team_fifa_rank']
                ranking_visit = fila['away_team_fifa_rank']
                
                # Asegurar que los equipos existen
                id_local = obtener_id_equipo_por_nombre(equipo_local, conexion)
                id_visit = obtener_id_equipo_por_nombre(equipo_visit, conexion)
                
                print(f"  Partido internacional: {equipo_local} vs {equipo_visit}")
            
            archivo_sql.write("\n")
    print("  Listo")
else:
    print(f"  Archivo no encontrado: {ruta_internacional}")






# 4. PROCESAR WorldCupMatches.csv
print("\nProcesando WorldCupMatches.csv...")
ruta_wc_matches = '../datos/Copa del mundo/WorldCupMatches.csv'

if os.path.exists(ruta_wc_matches):
    with motor_bd.connect() as conexion:
        asegurar_datos_base(conexion)
        
        with open(ruta_wc_matches, 'r', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            
            for fila in lector:
                # VALIDACIÓN: Si no hay año o equipo, saltar la fila (limpia las filas vacías del CSV)
                if not fila['Year'] or not fila['Home Team Name']:
                    continue
                
                anio = fila['Year']
                equipo_local = fila['Home Team Name']
                equipo_visit = fila['Away Team Name']
                goles_local = int(fila['Home Team Goals']) if fila['Home Team Goals'] else 0
                goles_visit = int(fila['Away Team Goals']) if fila['Away Team Goals'] else 0
                estadio_nombre = fila['Stadium']
                ciudad = fila['City']
                
                # Buscar o crear estadio
                try:
                    max_id = conexion.execute(sa.text("SELECT ISNULL(MAX(id_estadio), 0) + 1 FROM estadio")).scalar()
                    conexion.execute(
                        sa.text("""
                            IF NOT EXISTS (SELECT 1 FROM estadio WHERE nombre = :nombre)
                            INSERT INTO estadio (id_estadio, nombre, ciudad) VALUES (:id, :nombre, :ciudad)
                        """),
                        {"id": max_id, "nombre": estadio_nombre, "ciudad": ciudad}
                    )
                    conexion.commit()
                except:
                    pass
                
                # Asegurar equipos
                id_local = obtener_id_equipo_por_nombre(equipo_local, conexion)
                id_visit = obtener_id_equipo_por_nombre(equipo_visit, conexion)
                
                print(f"  Partido mundial {anio}: {equipo_local} {goles_local}-{goles_visit} {equipo_visit}")
            
            archivo_sql.write("\n")
    print("  Listo")
else:
    print(f"  Archivo no encontrado: {ruta_wc_matches}")






# 5. PROCESAR WorldCupPlayers.csv

print("\nProcesando WorldCupPlayers.csv...")
ruta_wc_players = '../datos/Copa del mundo/WorldCupPlayers.csv'

if os.path.exists(ruta_wc_players):
    with motor_bd.connect() as conexion:
        asegurar_datos_base(conexion)
        
        
        with open(ruta_wc_players, 'r', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            archivo_sql.write("\n-- Inserts desde WorldCupPlayers.csv\n")
            
            for fila in lector:
                match_id = fila['MatchID']
                equipo_iniciales = fila['Team Initials']
                entrenador_nombre = fila['Coach Name']
                jugador_nombre = fila['Player Name']
                posicion = fila['Position']
                evento = fila['Event']
                
                # Procesar entrenador
                if entrenador_nombre and entrenador_nombre.strip():
                    try:
                        # Limpiar nombre del entrenador
                        nombre_limpio = entrenador_nombre.split(' (')[0]
                        max_id = conexion.execute(sa.text("SELECT ISNULL(MAX(id_entrenador), 0) + 1 FROM entrenador")).scalar()
                        conexion.execute(
                            sa.text("""
                                IF NOT EXISTS (SELECT 1 FROM entrenador WHERE nombre = :nombre)
                                INSERT INTO entrenador (id_entrenador, nombre) VALUES (:id, :nombre)
                            """),
                            {"id": max_id, "nombre": nombre_limpio}
                        )
                        conexion.commit()
                    except:
                        pass
                
                # Procesar jugador
                if jugador_nombre and jugador_nombre.strip():
                    try:
                        # Buscar si el jugador ya existe
                        existe = conexion.execute(
                            sa.text("SELECT id_jugador FROM jugador WHERE nombre = :nombre"),
                            {"nombre": jugador_nombre}
                        ).fetchone()
                        
                        if not existe:
                            max_id = conexion.execute(sa.text("SELECT ISNULL(MAX(id_jugador), 0) + 1 FROM jugador")).scalar()
                            conexion.execute(
                                sa.text("INSERT INTO jugador (id_jugador, nombre) VALUES (:id, :nombre)"),
                                {"id": max_id, "nombre": jugador_nombre}
                            )
                            conexion.commit()
                    except:
                        pass
                
                # Procesar posicion
                if posicion and posicion.strip():
                    try:
                        max_id = conexion.execute(sa.text("SELECT ISNULL(MAX(id_posicion), 0) + 1 FROM posicion")).scalar()
                        conexion.execute(
                            sa.text("""
                                IF NOT EXISTS (SELECT 1 FROM posicion WHERE nombre = :nombre)
                                INSERT INTO posicion (id_posicion, nombre) VALUES (:id, :nombre)
                            """),
                            {"id": max_id, "nombre": posicion}
                        )
                        conexion.commit()
                    except:
                        pass
            
            archivo_sql.write("\n")
    print("  Listo")
else:
    print(f"  Archivo no encontrado: {ruta_wc_players}")

# Cerrar archivo SQL
archivo_sql.write("\nGO\n")
archivo_sql.close()

print("\n" + "="*50)
print("PROCESO COMPLETADO")
print(f"Archivo SQL generado: carga_datos_csv.sql")
print("="*50)