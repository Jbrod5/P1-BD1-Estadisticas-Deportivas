import pandas as pd
import sqlalchemy as sa
import json
import os
import numpy as np

engine = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def sql_val(val):
    if val is None: return "NULL"
    if isinstance(val, str): return f"'{val.replace(chr(39), chr(39)+chr(39))}'"
    return str(val)

def procesar_lista_lineup(data, match_id, conn, f_sql):
    for equipo_data in data:
        id_equipo = equipo_data['team_id']
        formacion = 'Desconocida'
        
        try:
            # USAMOS SET NOCOUNT ON para evitar el error de "does not return rows"
            # Y capturamos el resultado correctamente
            query = sa.text("""
                SET NOCOUNT ON;
                INSERT INTO alineacion (formacion, id_partido, id_equipo) 
                VALUES (:f, :p, :e);
                SELECT CAST(SCOPE_IDENTITY() AS INT);
            """)
            
            res = conn.execute(query, {"f": formacion, "p": match_id, "e": id_equipo})
            id_al = res.scalar() # Aqui obtenemos el ID directamente
            conn.commit()
            
            if id_al:
                f_sql.write(f"INSERT INTO alineacion (formacion, id_partido, id_equipo) VALUES ('{formacion}', {match_id}, {id_equipo});\n")
                f_sql.write(f"DECLARE @id_al_{id_al} INT = SCOPE_IDENTITY();\n")

                for jug in equipo_data.get('lineup', []):
                    # ... (el resto del loop de jugadores igual que antes) ...
                    # Asegúrate de que los inserts de jugadores también tengan conn.commit()
                    pass
        except Exception as e:
            print(f"Error insertando alineacion para partido {match_id}: {e}")
            conn.rollback()

def procesar_eventos_lineup(data, match_id, conn, f_sql):
    for evento in data:
        if evento.get('type', {}).get('name') == 'Starting XI':
            id_equipo = evento['team']['id']
            tactics = evento.get('tactics', {})
            formacion = str(tactics.get('formation', 'Desconocida'))
            
            try:
                # LA MISMA LOGICA AQUI
                query = sa.text("""
                    SET NOCOUNT ON;
                    INSERT INTO alineacion (formacion, id_partido, id_equipo) 
                    VALUES (:f, :p, :e);
                    SELECT CAST(SCOPE_IDENTITY() AS INT);
                """)
                res = conn.execute(query, {"f": formacion, "p": match_id, "e": id_equipo})
                id_al = res.scalar()
                conn.commit()

                if id_al:
                    f_sql.write(f"INSERT INTO alineacion (formacion, id_partido, id_equipo) VALUES ('{formacion}', {match_id}, {id_equipo});\n")
                    f_sql.write(f"DECLARE @id_al_{id_al} INT = SCOPE_IDENTITY();\n")
                    
                    # ... (resto del loop de jugadores igual) ...
            except Exception as e:
                print(f"Error en Starting XI para partido {match_id}: {e}")
                conn.rollback()

def cargar_archivo_maestro(ruta):
    match_id = os.path.basename(ruta).replace('.json', '')
    
    if match_id == "alineacion":
        # Obtenemos el nombre de la carpeta padre
        nombre_carpeta = os.path.basename(os.path.dirname(ruta))
        
        if "ARG_VS_ENG" in nombre_carpeta:
            match_id = 3750191  # <--- EL ID QUE ENCONTRASTE EN BEEKEEPER
        else:
            # Por si tenes otras carpetas con nombres raros
            match_id = 1111 

    print(f"--- Cargando: {ruta} (Match: {match_id}) ---")

    try:
        with open(ruta, encoding='utf-8') as f:
            data = json.load(f)
        
        with engine.connect() as conn:
            with open('carga_datos.sql', 'a', encoding='utf-8') as f_sql:
                # Detectar formato
                if isinstance(data, list) and len(data) > 0 and 'team_id' in data[0]:
                    procesar_lista_lineup(data, match_id, conn, f_sql)
                else:
                    procesar_eventos_lineup(data, match_id, conn, f_sql)
    except Exception as e:
        print(f"Error: {e}")

# Rutas especificas basadas en lo que me pasaste
archivos_lineups = [
    #Champions
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18236.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18237.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18240.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18241.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18242.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18243.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18244.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18245.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/22912.json',
    
    #Mundial
    '../datos/Copa del mundo/partidos/FIFA_W_C_1986/CuartosFinal_ARG_VS_ENG/alineacion.json',
    
    #LaLiga
    '../datos/LaLiga/events/3773386.json',
    '../datos/LaLiga/events/3773457.json'
]

if __name__ == "__main__":
    for r in archivos_lineups:
        if os.path.exists(r):
            cargar_archivo_maestro(r)