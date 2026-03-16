import pandas as pd
import sqlalchemy as sa
import json

engine = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def cargar_competencias():
    try:
        with open('../datos/competitions.json', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.json_normalize(data)

        with open('carga_datos.sql', 'w', encoding='utf-8') as sql_file:
            sql_file.write("USE ProyectoFutbol;\nGO\n\n")

        # --- PROCESAMIENTO DINÁMICO ---
        with engine.connect() as conn:
            
            # 1. Competiciones
            print("Evaluando competiciones...")
            for _, row in df[['competition_id', 'competition_name']].drop_duplicates().iterrows():
                # Verificamos si existe, si no, lo agregamos
                query = sa.text("""
                    IF NOT EXISTS (SELECT 1 FROM competicion WHERE id_competicion = :id)
                    INSERT INTO competicion (id_competicion, nombre) VALUES (:id, :nom)
                """)
                conn.execute(query, {"id": row['competition_id'], "nom": row['competition_name']})
                
                with open('carga_datos.sql', 'a', encoding='utf-8') as f_sql:
                    f_sql.write(f"IF NOT EXISTS (SELECT 1 FROM competicion WHERE id_competicion = {row['competition_id']}) "
                                f"INSERT INTO competicion (id_competicion, nombre) VALUES ({row['competition_id']}, '{row['competition_name']}');\n")

            # 2. Temporadas
            print("Evaluando temporadas...")
            df_temp = df[['season_id', 'season_name']].copy()
            df_temp['anio_inicio'] = df_temp['season_name'].str.extract(r'^(\d{4})').astype(int)
            df_temp['anio_fin'] = df_temp['season_name'].str.extract(r'(\d{4})$')
            df_temp['anio_fin'] = df_temp['anio_fin'].fillna(df_temp['anio_inicio']).astype(int)
            
            for _, row in df_temp[['season_id', 'anio_inicio', 'anio_fin']].drop_duplicates().iterrows():
                query = sa.text("""
                    IF NOT EXISTS (SELECT 1 FROM temporada WHERE id_temporada = :id)
                    INSERT INTO temporada (id_temporada, anio_inicio, anio_fin) VALUES (:id, :ai, :af)
                """)
                conn.execute(query, {
                    "id": int(row['season_id']), 
                    "ai": int(row['anio_inicio']), 
                    "af": int(row['anio_fin'])
                })                
                with open('carga_datos.sql', 'a', encoding='utf-8') as f_sql:
                    f_sql.write(f"IF NOT EXISTS (SELECT 1 FROM temporada WHERE id_temporada = {row['season_id']}) "
                                f"INSERT INTO temporada (id_temporada, anio_inicio, anio_fin) VALUES ({row['season_id']}, {row['anio_inicio']}, {row['anio_fin']});\n")

            conn.commit()
            with open('carga_datos.sql', 'a', encoding='utf-8') as f_sql:
                f_sql.write("GO\n")
        
        print("¡Competencias y temporadas sincronizadas con éxito! :D")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cargar_competencias()