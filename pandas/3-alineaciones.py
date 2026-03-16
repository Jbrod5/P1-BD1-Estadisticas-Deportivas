import pandas as pandas
import sqlalchemy as sqlalchemy
import json
import os
import numpy as numpy
import re # Para limpiar los IDs de los nombres de archivos

# Conexion principal a nuestra base de datos en SQL Server
engine = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def asegurar_jugador_con_nacionalidad(conexion, id_jugador, nombre_jugador, id_nacionalidad):
    """Garantiza que el jugador y su pais existan antes de unirlos a la alineacion."""
    if id_jugador:
        if id_nacionalidad:
            instruccion_nacionalidad = sqlalchemy.text("""
                IF NOT EXISTS (SELECT 1 FROM nacionalidad WHERE id_nacionalidad = :id) 
                INSERT INTO nacionalidad (id_nacionalidad, nombre) VALUES (:id, 'Desconocida')
            """)
            conexion.execute(instruccion_nacionalidad, {"id": id_nacionalidad})
        
        instruccion_jugador = sqlalchemy.text("""
            IF NOT EXISTS (SELECT 1 FROM jugador WHERE id_jugador = :id)
                INSERT INTO jugador (id_jugador, nombre, id_nacionalidad) VALUES (:id, :nom, :nac)
            ELSE
                UPDATE jugador SET id_nacionalidad = ISNULL(id_nacionalidad, :nac) WHERE id_jugador = :id
        """)
        conexion.execute(instruccion_jugador, {"id": id_jugador, "nom": nombre_jugador, "nac": id_nacionalidad})

def procesar_jugadores_comun(lista_jugadores, id_alineacion, conexion, archivo_sql):
    """Inserta cada jugador de la lista en alineacion_jugador."""
    for datos_jugador in lista_jugadores:
        id_p = datos_jugador.get('player_id') or datos_jugador.get('player', {}).get('id')
        nombre_p = datos_jugador.get('player_name') or datos_jugador.get('player', {}).get('name')
        id_nacionalidad = datos_jugador.get('country', {}).get('id')
        
        id_posicion, nombre_posicion = None, None
        
        # Caso A: Estructura de archivo de Alineacion
        if 'positions' in datos_jugador and isinstance(datos_jugador['positions'], list) and len(datos_jugador['positions']) > 0:
            id_posicion = datos_jugador['positions'][0].get('position_id')
            nombre_posicion = datos_jugador['positions'][0].get('position')
        
        # Caso B: Estructura de archivo de Eventos (Starting XI)
        elif 'position' in datos_jugador and isinstance(datos_jugador['position'], dict):
            id_posicion = datos_jugador['position'].get('id')
            nombre_posicion = datos_jugador['position'].get('name')

        if id_posicion:
            instruccion_posicion = sqlalchemy.text("""
                IF NOT EXISTS (SELECT 1 FROM posicion WHERE id_posicion = :id) 
                INSERT INTO posicion (id_posicion, nombre) VALUES (:id, :nom)
            """)
            conexion.execute(instruccion_posicion, {"id": id_posicion, "nom": nombre_posicion})
        
        asegurar_jugador_con_nacionalidad(conexion, id_p, nombre_p, id_nacionalidad)
        dorsal = datos_jugador.get('jersey_number')
        
        try:
            conexion.execute(sqlalchemy.text("""
                INSERT INTO alineacion_jugador (id_alineacion, id_jugador, id_posicion, dorsal) 
                VALUES (:al, :jug, :pos, :dor)
            """), {"al": id_alineacion, "jug": id_p, "pos": id_posicion, "dor": dorsal})
        except Exception:
            conexion.rollback()

def formatear_valor_sql(valor):
    return "NULL" if valor is None else str(valor)

def procesar_archivo_lineup(datos_json, id_partido, conexion, archivo_sql):
    """Maneja archivos tipo 'lineup'."""
    for datos_equipo in datos_json:
        id_equipo = datos_equipo['team_id']
        try:
            resultado = conexion.execute(sqlalchemy.text("""
                SET NOCOUNT ON;
                INSERT INTO alineacion (formacion, id_partido, id_equipo) VALUES ('Desconocida', :p, :e);
                SELECT CAST(SCOPE_IDENTITY() AS INT);
            """), {"p": int(id_partido), "e": id_equipo}) # Forzamos INT para evitar error 22018
            
            id_al = resultado.scalar()
            conexion.commit()
            if id_al:
                procesar_jugadores_comun(datos_equipo.get('lineup', []), id_al, conexion, archivo_sql)
        except Exception as error:
            print(f" Error en equipo {id_equipo}: {error}")

def procesar_eventos_de_inicio(datos_json, id_partido, conexion, archivo_sql):
    """Maneja archivos tipo 'events' buscando el Starting XI."""
    for evento in datos_json:
        if evento.get('type', {}).get('name') == 'Starting XI':
            id_equipo = evento['team']['id']
            tacticas = evento.get('tactics', {}) # Definimos la variable en español
            formacion = str(tacticas.get('formation', 'Desconocida'))
            try:
                resultado = conexion.execute(sqlalchemy.text("""
                    SET NOCOUNT ON;
                    INSERT INTO alineacion (formacion, id_partido, id_equipo) VALUES (:f, :p, :e);
                    SELECT CAST(SCOPE_IDENTITY() AS INT);
                """), {"f": formacion, "p": int(id_partido), "e": id_equipo}) # Forzamos INT
                
                id_al = resultado.scalar()
                conexion.commit()
                if id_al:
                    # CORRECCIoN: Usamos 'tacticas' que es la variable definida arriba
                    procesar_jugadores_comun(tacticas.get('lineup', []), id_al, conexion, archivo_sql)
            except Exception as error:
                print(f" Error Starting XI en partido {id_partido}: {error}")

def cargar_alineaciones_principal(ruta_archivo):
    nombre_base = os.path.basename(ruta_archivo).replace('.json', '')
    numeros = re.findall(r'\d+', nombre_base)
    
    # Logica inteligente para extraer el ID correcto
    if "ARG_VS_ENG" in ruta_archivo:
        id_partido = 3750191
    elif numeros:
        # Buscamos si algun numero de la lista tiene 5 o mas digitos 
        ids_candidatos = [n for n in numeros if len(n) >= 5]
        if ids_candidatos:
            id_partido = ids_candidatos[0] # Tomamos el primero que parezca un ID real
        else:
            id_partido = numeros[0] # Si no, el primero que aparezca
    else:
        id_partido = "0"

    print(f"--- Procesando ID Corregido: {id_partido} | Archivo: {nombre_base} ---")

    

    
    try:
        with open(ruta_archivo, encoding='utf-8') as archivo:
            datos_json = json.load(archivo)
        
        with engine.connect() as conexion:
            with open('carga_datos.sql', 'a', encoding='utf-8') as archivo_sql:
                if isinstance(datos_json, list) and len(datos_json) > 0 and 'team_id' in datos_json[0]:
                    procesar_archivo_lineup(datos_json, id_partido, conexion, archivo_sql)
                else:
                    procesar_eventos_de_inicio(datos_json, id_partido, conexion, archivo_sql)
    except Exception as error:
        print(f"Error fatal en archivo {ruta_archivo}: {error}")

# Lista de rutas 
archivos_lineups = [
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18236.json',
    '../datos/Champios/alineaciones_Finales_champions_2010-2019/18242.json',
    '../datos/Copa del mundo/partidos/FIFA_W_C_1986/CuartosFinal_ARG_VS_ENG/alineacion.json',
    '../datos/LaLiga/events/3773386.json',
    '../datos/Champios/Eventos/22912 _ Eventos_FInal_UCL_2019.json',
    '../datos/Champios/Eventos/Event_2015_18242.json',
    '../datos/Copa del mundo/partidos/FIFA_W_C_1986/CuartosFinal_ARG_VS_ENG/EventosDelPartido.json'
]

if __name__ == "__main__":
    for r in archivos_lineups:
        if os.path.exists(r):
            cargar_alineaciones_principal(r)
    print("\n--- Carga de alineaciones finalizada con exito! :D ---")