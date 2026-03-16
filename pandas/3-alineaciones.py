import pandas as pd
import sqlalchemy as sa
import json
import os
import numpy as np

engine = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def asegurar_jugador_con_nacionalidad(conn, p_id, p_nom, nac_id):
    """Inserta o actualiza al jugador y su nacionalidad."""
    if p_id:
        if nac_id:
            conn.execute(sa.text("IF NOT EXISTS (SELECT 1 FROM nacionalidad WHERE id_nacionalidad = :id) "
                               "INSERT INTO nacionalidad (id_nacionalidad, nombre) VALUES (:id, 'Desconocida')"), {"id": nac_id})
        
        conn.execute(sa.text("""
            IF NOT EXISTS (SELECT 1 FROM jugador WHERE id_jugador = :id)
                INSERT INTO jugador (id_jugador, nombre, id_nacionalidad) VALUES (:id, :nom, :nac)
            ELSE
                UPDATE jugador SET id_nacionalidad = ISNULL(id_nacionalidad, :nac) WHERE id_jugador = :id
        """), {"id": p_id, "nom": p_nom, "nac": nac_id})

def procesar_jugadores_comun(jugadores_list, id_al, conn, f_sql):
    for jug in jugadores_list:
        p_id = jug.get('player_id') or jug.get('player', {}).get('id')
        p_nom = jug.get('player_name') or jug.get('player', {}).get('name')
        nac_id = jug.get('country', {}).get('id')
        
        # --- FIX: Navegación segura para posiciones ---
        pos_id, pos_nom = None, None
        
        # Caso 1: Estructura de 'lineups' (lista de posiciones)
        if 'positions' in jug and isinstance(jug['positions'], list) and len(jug['positions']) > 0:
            pos_id = jug['positions'][0].get('position_id')
            pos_nom = jug['positions'][0].get('position')
        # Caso 2: Estructura de 'events' (objeto único de posición)
        elif 'position' in jug and isinstance(jug['position'], dict):
            pos_id = jug['position'].get('id')
            pos_nom = jug['position'].get('name')

        # Si encontramos posición, la aseguramos en el catálogo
        if pos_id:
            conn.execute(sa.text("IF NOT EXISTS (SELECT 1 FROM posicion WHERE id_posicion = :id) "
                               "INSERT INTO posicion (id_posicion, nombre) VALUES (:id, :nom)"), 
                               {"id": pos_id, "nom": pos_nom})
        
        asegurar_jugador_con_nacionalidad(conn, p_id, p_nom, nac_id)

        dorsal = jug.get('jersey_number')
        try:
            conn.execute(sa.text("""
                INSERT INTO alineacion_jugador (id_alineacion, id_jugador, id_posicion, dorsal) 
                VALUES (:al, :jug, :pos, :dor)
            """), {"al": id_al, "jug": p_id, "pos": pos_id, "dor": dorsal})
            
            f_sql.write(f"INSERT INTO alineacion_jugador (id_alineacion, id_jugador, id_posicion, dorsal) "
                        f"VALUES ({id_al}, {p_id}, {sql_val(pos_id)}, {sql_val(dorsal)});\n")
        except Exception:
            conn.rollback()

def sql_val(val):
    if val is None: return "NULL"
    return str(val)

# ... (Las funciones procesar_lista_lineup, procesar_eventos_lineup y cargar_archivo_maestro se mantienen igual) ...

def procesar_lista_lineup(data, match_id, conn, f_sql):
    for equipo_data in data:
        id_equipo = equipo_data['team_id']
        try:
            res = conn.execute(sa.text("""
                SET NOCOUNT ON;
                INSERT INTO alineacion (formacion, id_partido, id_equipo) VALUES ('Desconocida', :p, :e);
                SELECT CAST(SCOPE_IDENTITY() AS INT);
            """), {"p": match_id, "e": id_equipo})
            id_al = res.scalar()
            conn.commit()
            if id_al:
                procesar_jugadores_comun(equipo_data.get('lineup', []), id_al, conn, f_sql)
        except Exception as e:
            print(f" Error en lineup equipo {id_equipo} (Match {match_id}): {e}")

def procesar_eventos_lineup(data, match_id, conn, f_sql):
    for evento in data:
        if evento.get('type', {}).get('name') == 'Starting XI':
            id_equipo = evento['team']['id']
            tactics = evento.get('tactics', {})
            formacion = str(tactics.get('formation', 'Desconocida'))
            try:
                res = conn.execute(sa.text("""
                    SET NOCOUNT ON;
                    INSERT INTO alineacion (formacion, id_partido, id_equipo) VALUES (:f, :p, :e);
                    SELECT CAST(SCOPE_IDENTITY() AS INT);
                """), {"f": formacion, "p": match_id, "e": id_equipo})
                id_al = res.scalar()
                conn.commit()
                if id_al:
                    procesar_jugadores_comun(tactics.get('lineup', []), id_al, conn, f_sql)
            except Exception as e:
                print(f" Error en Starting XI {match_id}: {e}")

def cargar_archivo_maestro(ruta):
    match_id = os.path.basename(ruta).replace('.json', '')
    if match_id == "alineacion":
        nombre_carpeta = os.path.basename(os.path.dirname(ruta))
        match_id = 3750191 if "ARG_VS_ENG" in nombre_carpeta else 1111

    print(f"--- Procesando Alineación: {match_id} ---")
    try:
        with open(ruta, encoding='utf-8') as f:
            data = json.load(f)
        with engine.connect() as conn:
            with open('carga_datos.sql', 'a', encoding='utf-8') as f_sql:
                if isinstance(data, list) and len(data) > 0 and 'team_id' in data[0]:
                    procesar_lista_lineup(data, match_id, conn, f_sql)
                else:
                    procesar_eventos_lineup(data, match_id, conn, f_sql)
    except Exception as e:
        print(f"Error procesando {ruta}: {e}")

archivos_lineups = [
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18236.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18237.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18240.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18241.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18242.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18243.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18244.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18245.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/22912.json',
    '../datos/Copa del mundo/partidos/FIFA_W_C_1986/CuartosFinal_ARG_VS_ENG/alineacion.json',
    '../datos/LaLiga/events/3773386.json',
    '../datos/LaLiga/events/3773457.json'
]

if __name__ == "__main__":
    for r in archivos_lineups:
        if os.path.exists(r):
            cargar_archivo_maestro(r)