import pandas as pandas
import sqlalchemy as sqlalchemy
import json
import os
import numpy as numpy 

# Configuramos la conexion principal a la base de datos de SQL Server
engine = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def formatear_valor_sql(valor):
    """
    Esta funcion prepara los datos para que SQL los entienda.
    Si un texto tiene una comilla simple (como 'O'Hara'), la duplica para que no rompa la consulta.
    """
    if valor is None: 
        return "NULL"
    if isinstance(valor, str): 
        valor_limpio = valor.replace("'", "''")
        return f"'{valor_limpio}'"
    return str(valor)



def cargar_archivo_partidos(ruta_archivo):
    print(f"--- Iniciando procesamiento: {ruta_archivo} ---")
    try:
        # Abrimos el archivo JSON que contiene la informacion de los encuentros
        with open(ruta_archivo, encoding='utf-8') as archivo:
            datos_partidos = json.load(archivo)
        
        # Convertimos la lista de partidos en una tabla de datos
        tabla_partidos = pandas.json_normalize(datos_partidos)
        
        # Reemplazamos los valores vacios NaN por None para que SQL los trate como NULL xd
        tabla_partidos = tabla_partidos.replace({numpy.nan: None})

        with engine.connect() as conexion:
            with open('carga_datos.sql', 'a', encoding='utf-8') as archivo_sql:
                
                # --- 1. NACIONALIDADES ---
                # Recolectamos todos los paises mencionados (equipos y arbitros) para llenar el catalogo de nacionalidades
                lista_paises_encontrados = []
                
                if 'home_team.country.id' in tabla_partidos.columns:
                                                                # Se pasa id y nombre,                                                luego se renombran a solo id y nombre
                    lista_paises_encontrados.append(tabla_partidos[['home_team.country.id', 'home_team.country.name']].rename(columns={'home_team.country.id':'id', 'home_team.country.name':'nombre'}))
                
                if 'away_team.country.id' in tabla_partidos.columns:
                    lista_paises_encontrados.append(tabla_partidos[['away_team.country.id', 'away_team.country.name']].rename(columns={'away_team.country.id':'id', 'away_team.country.name':'nombre'}))
                
                if 'referee.country.id' in tabla_partidos.columns:
                    lista_paises_encontrados.append(tabla_partidos[['referee.country.id', 'referee.country.name']].rename(columns={'referee.country.id':'id', 'referee.country.name':'nombre'}))
                
                
                if lista_paises_encontrados:
                    # Unimos todos los paises en una sola lista y quitamos los repetidos
                    todas_las_nacionalidades = pandas.concat(lista_paises_encontrados).dropna().drop_duplicates()
                    for _, fila in todas_las_nacionalidades.iterrows():
                        instruccion_nacionalidad = sqlalchemy.text("""
                            IF NOT EXISTS (SELECT 1 FROM nacionalidad WHERE id_nacionalidad = :id) 
                            INSERT INTO nacionalidad (id_nacionalidad, nombre) VALUES (:id, :n)
                        """)
                        conexion.execute(instruccion_nacionalidad, {"id": fila['id'], "n": fila['nombre']})



                # --- 2. ESTADIOS ---
                if 'stadium.id' in tabla_partidos.columns:
                    print("Actualizando catalogo de estadios - - - - - - -")
                    # Algunos archivos no traen el nombre de la ciudad, asi que verificamos primero
                    existe_columna_ciudad = 'stadium.city.name' in tabla_partidos.columns
                    columnas_necesarias = ['stadium.id', 'stadium.name', 'stadium.country.name']
                    
                    if existe_columna_ciudad:
                        columnas_necesarias.append('stadium.city.name')
                    
                    estadios_encontrados = tabla_partidos[columnas_necesarias].dropna(subset=['stadium.id']).drop_duplicates()
                    
                    for _, fila in estadios_encontrados.iterrows():
                        nombre_ciudad = fila['stadium.city.name'] if existe_columna_ciudad else 'Desconocida'
                        instruccion_estadio = sqlalchemy.text("""
                            IF NOT EXISTS (SELECT 1 FROM estadio WHERE id_estadio = :id) 
                            INSERT INTO estadio (id_estadio, nombre, ciudad, pais) VALUES (:id, :nombre, :ciudad, :pais)
                        """)
                        conexion.execute(instruccion_estadio, {
                            "id": int(fila['stadium.id']), 
                            "nombre": fila['stadium.name'], 
                            "ciudad": nombre_ciudad, 
                            "pais": fila['stadium.country.name']
                        })
        
        
        
                # --- 3. ARBITROS ---
                if 'referee.id' in tabla_partidos.columns:
                    arbitros_encontrados = tabla_partidos[['referee.id', 'referee.name', 'referee.country.id']].dropna(subset=['referee.id']).drop_duplicates()
                    for _, fila in arbitros_encontrados.iterrows():
                        instruccion_arbitro = sqlalchemy.text("""
                            IF NOT EXISTS (SELECT 1 FROM arbitro WHERE id_arbitro = :id) 
                            INSERT INTO arbitro (id_arbitro, nombre, id_nacionalidad) VALUES (:id, :nombre, :id_nacionalidad)
                        """)
                        conexion.execute(instruccion_arbitro, {
                            "id": fila['referee.id'], 
                            "nombre": fila['referee.name'], 
                            "id_nacionalidad": fila['referee.country.id']
                        })

                # --- 4. EQUIPOS ---
                print("Verificando equipos participantes - - - - - - - -")
                equipos_locales = tabla_partidos[['home_team.home_team_id', 'home_team.home_team_name']].rename(columns={'home_team.home_team_id':'id', 'home_team.home_team_name':'nombre'})
                equipos_visitantes = tabla_partidos[['away_team.away_team_id', 'away_team.away_team_name']].rename(columns={'away_team.away_team_id':'id', 'away_team.away_team_name':'nombre'})
                
                todos_los_equipos = pandas.concat([equipos_locales, equipos_visitantes]).drop_duplicates()
                
                for _, fila in todos_los_equipos.iterrows():
                    instruccion_equipo = sqlalchemy.text("""
                        IF NOT EXISTS (SELECT 1 FROM equipo WHERE id_equipo = :id) 
                        INSERT INTO equipo (id_equipo, nombre) VALUES (:id, :nombre)
                    """)
                    conexion.execute(instruccion_equipo, {"id": fila['id'], "nombre": fila['nombre']})
                    
                    

                # --- 5. REGISTRO FINAL DE PARTIDOS ---
                print("Guardando informacion de los encuentros - - - - - - -")
                for _, fila in tabla_partidos.iterrows():
                    try:
                        # Preparamos todos los datos del partido en un diccionario
                        parametros_partido = {
                            "id": int(fila['match_id']), 
                            "fecha": str(fila['match_date']), 
                            "hora": str(fila['kick_off']), 
                            "goles_local": int(fila['home_score']), 
                            "goles_visita": int(fila['away_score']), 
                            "fase": str(fila.get('competition_stage.name', 'Regular')), 
                            "jornada": int(fila.get('match_week', 0)),
                            "id_competicion": int(fila['competition.competition_id']), 
                            "id_temporada": int(fila['season.season_id']),
                            "id_estadio": int(fila['stadium.id']) if fila.get('stadium.id') else None, 
                            "id_equipo_local": int(fila['home_team.home_team_id']), 
                            "id_equipo_visita": int(fila['away_team.away_team_id']), 
                            "id_arbitro": int(fila['referee.id']) if fila.get('referee.id') else None
                        }

                        # Insertamos en la base de datos si el partido no existe aun
                        instruccion_partido = sqlalchemy.text("""
                            IF NOT EXISTS (SELECT 1 FROM partido WHERE id_partido = :id)
                            INSERT INTO partido (id_partido, fecha, kick_off, goles_local, goles_visita, fase, jornada, 
                                               id_competicion, id_temporada, id_estadio, id_equipo_local, id_equipo_visita, id_arbitro)
                            VALUES (:id, :fecha, :hora, :goles_local, :goles_visita, :fase, :jornada, :id_competicion, 
                                    :id_temporada, :id_estadio, :id_equipo_local, :id_equipo_visita, :id_arbitro)
                        """)
                        conexion.execute(instruccion_partido, parametros_partido)
                        
                        # Escribimos la version SQL para nuestro archivo de respaldo carga_datos.sql
                        archivo_sql.write(
                            f"IF NOT EXISTS (SELECT 1 FROM partido WHERE id_partido = {parametros_partido['id']}) "
                            f"INSERT INTO partido VALUES ({parametros_partido['id']}, '{parametros_partido['fecha']}', "
                            f"'{parametros_partido['hora']}', {parametros_partido['goles_local']}, {parametros_partido['goles_visita']}, "
                            f"'{parametros_partido['fase']}', {parametros_partido['jornada']}, {parametros_partido['id_competicion']}, "
                            f"{parametros_partido['id_temporada']}, {formatear_valor_sql(parametros_partido['id_estadio'])}, "
                            f"{parametros_partido['id_equipo_local']}, {parametros_partido['id_equipo_visita']}, "
                            f"{formatear_valor_sql(parametros_partido['id_arbitro'])});\n"
                        )

                    except Exception as error_partido:
                        print(f"No se pudo guardar el partido {fila['match_id']}: {error_partido}")
                
                # Guardamos los cambios permanentemente en la base de datos
                conexion.commit()
                archivo_sql.write("GO\n")

    except Exception as error_general:
        print(f"Error al procesar el archivo {ruta_archivo}: {error_general}")

    
                      
        
        
        

# --- LISTA DE ARCHIVOS A PROCESAR ---
archivos_a_cargar = [
    
    #Copa del mundo
    '../datos/Copa del mundo/partidos/FIDA_W_C_2018/3__MATCHES_FWC_2018.json',
    '../datos/Copa del mundo/partidos/FIFA_W_C_1986/54__MATCHES_FWC_1986.json',
    '../datos/Copa del mundo/partidos/FIFA_W_C_2022/106___Matches__FWC_2022.json',
    
    #Chamions
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/1.json',
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/2.json',
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/4.json',
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/22.json',   
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/23.json',
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/24.json',
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/25.json',
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/26.json',
    '../datos/Champios/Partidos_Finales_Champions_2010-2019/27.json',
    
    #La liga
    '../datos/LaLiga/1.json',
    '../datos/LaLiga/2.json',
    '../datos/LaLiga/4.json',
    '../datos/LaLiga/21.json',
    '../datos/LaLiga/22.json',
    '../datos/LaLiga/23.json',
    '../datos/LaLiga/24.json',
    '../datos/LaLiga/25.json',
    '../datos/LaLiga/26.json',
    '../datos/LaLiga/27.json',
    '../datos/LaLiga/37.json',
    '../datos/LaLiga/38.json',
    '../datos/LaLiga/39.json',
    '../datos/LaLiga/40.json',
    '../datos/LaLiga/41.json',
    '../datos/LaLiga/42.json',
    '../datos/LaLiga/90.json',
    '../datos/LaLiga/278.json',
]

if __name__ == "__main__":
    for ruta in archivos_a_cargar:
        if os.path.exists(ruta):
            cargar_archivo_partidos(ruta)
        else:
            print(f"No se encontro el archivo: {ruta}")