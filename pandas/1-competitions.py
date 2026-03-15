import pandas as pd
import sqlalchemy as sa
import json

engine = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def cargar_competencias():
    try:
        with open('../datos/competitions.json', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.json_normalize(data)

        # Preparamos el archivo SQL de inserts :3
        with open('carga_datos.sql', 'w', encoding='utf-8') as sql_file:
            sql_file.write("USE ProyectoFutbol;\nGO\n\n")

        # --- LIMPIEZA DE COMPETICIONES ---
        df_comp = df[['competition_id', 'competition_name']].drop_duplicates()
        df_comp.columns = ['id_competicion', 'nombre']

        # --- LIMPIEZA DE TEMPORADAS ---
        df_temp = df[['season_id', 'season_name']].copy()
        df_temp['anio_inicio'] = df_temp['season_name'].str.extract(r'^(\d{4})').astype(int)
        df_temp['anio_fin'] = df_temp['season_name'].str.extract(r'(\d{4})$')
        df_temp['anio_fin'] = df_temp['anio_fin'].fillna(df_temp['anio_inicio']).astype(int)
        df_temp = df_temp[['season_id', 'anio_inicio', 'anio_fin']].drop_duplicates()
        df_temp.columns = ['id_temporada', 'anio_inicio', 'anio_fin']

        # --- CARGA A SQL Y GENERACION DE SCRIPT ---
        print("Cargando competiciones :3")
        df_comp.to_sql('competicion', engine, if_exists='append', index=False)
        
        # Generar inserts para el archivo .sql
        with open('carga_datos.sql', 'a', encoding='utf-8') as f:
            for _, r in df_comp.iterrows():
                f.write(f"INSERT INTO competicion (id_competicion, nombre) VALUES ({r['id_competicion']}, '{r['nombre']}');\n")
            f.write("GO\n\n")

        print("Cargando temporadas :3")
        df_temp.to_sql('temporada', engine, if_exists='append', index=False)
        
        with open('carga_datos.sql', 'a', encoding='utf-8') as f:
            for _, r in df_temp.iterrows():
                f.write(f"INSERT INTO temporada (id_temporada, anio_inicio, anio_fin) VALUES ({r['id_temporada']}, {r['anio_inicio']}, {r['anio_fin']});\n")
            f.write("GO\n\n")
        
        print("Carga de competencias y temporadas lista :D")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cargar_competencias()