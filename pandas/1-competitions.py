import pandas as pandas
import sqlalchemy as sqlalchemy
import json

# Establecemos la conexion con SQL Server usando el nombre completo 'engine'
engine = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def cargar_competencias():
    try:
        # Abrimos el archivo maestro de StatsBomb que contiene los nombres de torneos y años :D
        with open('../datos/competitions.json', encoding='utf-8') as archivo:
            datos_json = json.load(archivo)
        
        # Convertimos los datos a un formato de tabla para manipularlos facilmente
        tabla_competencias = pandas.json_normalize(datos_json)

        # En el startbd.sh este es el primer script que se ejecuta :D 
        # Preparamos nuestro archivo de respaldo SQL con las instrucciones iniciales
        # USE ProyectoFutbol
        # GO
        with open('carga_datos.sql', 'w', encoding='utf-8') as archivo_sql:
            archivo_sql.write("USE ProyectoFutbol;\nGO\n\n")



        # Iniciamos la comunicacion con la base de datos
        with engine.connect() as conexion:
            
            
            
            
            
            # --- SECCION 1: COMPETICIONES ---
            print("Evaluando competiciones - - - - -")
            
            # Filtramos solo las columnas de ID y Nombre, eliminando las que se repiten
            competiciones_unicas = tabla_competencias[['competition_id', 'competition_name']].drop_duplicates()
            
            
            for _, fila in competiciones_unicas.iterrows():
                # Usamos 'IF NOT EXISTS' para no intentar insertar un torneo que ya esta en la base de datos
                instruccion_insercion = sqlalchemy.text("""
                    IF NOT EXISTS (SELECT 1 FROM competicion WHERE id_competicion = :id)
                    INSERT INTO competicion (id_competicion, nombre) VALUES (:id, :nom)
                """)
                
                conexion.execute(instruccion_insercion, {
                    "id": fila['competition_id'], 
                    "nom": fila['competition_name']
                })
                
                # Guardamos la misma instruccion en nuestro archivo de respaldo
                with open('carga_datos.sql', 'a', encoding='utf-8') as archivo_sql:
                    archivo_sql.write(f"IF NOT EXISTS (SELECT 1 FROM competicion WHERE id_competicion = {fila['competition_id']}) "
                                      f"INSERT INTO competicion (id_competicion, nombre) VALUES ({fila['competition_id']}, '{fila['competition_name']}');\n")




            # --- SECCIoN 2: TEMPORADAS ---
            print("Evaluando temporadas - - - - -")
            
            # Creamos una copia de la tabla para procesar los años de las temporadas
            tabla_temporadas = tabla_competencias[['season_id', 'season_name']].copy()
            
            # El nombre de la temporada suele ser algo como 2018/2019 
            # Aqui extraemos el primer año (inicio) y el ultimo (fin)
            tabla_temporadas['anio_inicio'] = tabla_temporadas['season_name'].str.extract(r'^(\d{4})').astype(int)
            tabla_temporadas['anio_fin'] = tabla_temporadas['season_name'].str.extract(r'(\d{4})$')
            
            # Si solo hay un año (como 2018 o algo asi), el año de fin sera el mismo que el de inicio
            tabla_temporadas['anio_fin'] = tabla_temporadas['anio_fin'].fillna(tabla_temporadas['anio_inicio']).astype(int)
            
            # Eliminamos duplicados para procesar cada temporada una sola vez
            temporadas_limpias = tabla_temporadas[['season_id', 'anio_inicio', 'anio_fin']].drop_duplicates()
            
            for _, fila in temporadas_limpias.iterrows():
                instruccion_temporada = sqlalchemy.text("""
                    IF NOT EXISTS (SELECT 1 FROM temporada WHERE id_temporada = :id)
                    INSERT INTO temporada (id_temporada, anio_inicio, anio_fin) VALUES (:id, :ai, :af)
                """)
                
                conexion.execute(instruccion_temporada, {
                    "id": int(fila['season_id']), 
                    "ai": int(fila['anio_inicio']), 
                    "af": int(fila['anio_fin'])
                })                
                
                with open('carga_datos.sql', 'a', encoding='utf-8') as archivo_sql:
                    archivo_sql.write(f"IF NOT EXISTS (SELECT 1 FROM temporada WHERE id_temporada = {fila['season_id']}) "
                                      f"INSERT INTO temporada (id_temporada, anio_inicio, anio_fin) VALUES ({fila['season_id']}, {fila['anio_inicio']}, {fila['anio_fin']});\n")

            # Confirmamos todos los cambios en la base de datos
            conexion.commit()
            
            with open('carga_datos.sql', 'a', encoding='utf-8') as archivo_sql:
                archivo_sql.write("GO\n")
        
        print("Competencias y temporadas sincronizadas con exito!!! :D")

    except Exception as error:
        print(f"Ocurrio un error inesperado: {error}")

if __name__ == "__main__":
    cargar_competencias()