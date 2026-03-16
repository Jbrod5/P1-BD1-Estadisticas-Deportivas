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

def cargar_archivo_partidos(ruta):
    print(f"--- Procesando: {ruta} ---")
    try:
        with open(ruta, encoding='utf-8') as f:
            data = json.load(f)
        df = pd.json_normalize(data)
        df = df.replace({np.nan: None})

        with engine.connect() as conn:
            with open('carga_datos.sql', 'a', encoding='utf-8') as f_sql:
                
                # 1. NACIONALIDADES (Dinámico)
                paises = []
                if 'home_team.country.id' in df.columns:
                    paises.append(df[['home_team.country.id', 'home_team.country.name']].rename(columns={'home_team.country.id':'id', 'home_team.country.name':'n'}))
                if 'away_team.country.id' in df.columns:
                    paises.append(df[['away_team.country.id', 'away_team.country.name']].rename(columns={'away_team.country.id':'id', 'away_team.country.name':'n'}))
                if 'referee.country.id' in df.columns:
                    paises.append(df[['referee.country.id', 'referee.country.name']].rename(columns={'referee.country.id':'id', 'referee.country.name':'n'}))
                
                if paises:
                    df_nac = pd.concat(paises).dropna().drop_duplicates()
                    for _, row in df_nac.iterrows():
                        conn.execute(sa.text("IF NOT EXISTS (SELECT 1 FROM nacionalidad WHERE id_nacionalidad = :id) "
                                           "INSERT INTO nacionalidad (id_nacionalidad, nombre) VALUES (:id, :n)"), 
                                           {"id": row['id'], "n": row['n']})

                # 2. ESTADIOS (Con Ciudad arreglada)
                if 'stadium.id' in df.columns:
                    # Verificamos si existe la ciudad, si no, ponemos una por defecto
                    tiene_ciudad = 'stadium.city.name' in df.columns
                    cols = ['stadium.id', 'stadium.name', 'stadium.country.name']
                    if tiene_ciudad:
                        cols.append('stadium.city.name')
                    
                    df_est = df[cols].dropna(subset=['stadium.id']).drop_duplicates()
                    
                    for _, row in df_est.iterrows():
                        ciudad = row['stadium.city.name'] if tiene_ciudad else 'Desconocida'
                        conn.execute(sa.text("""
                            IF NOT EXISTS (SELECT 1 FROM estadio WHERE id_estadio = :id) 
                            INSERT INTO estadio (id_estadio, nombre, ciudad, pais) VALUES (:id, :n, :c, :p)
                        """), {"id": int(row['stadium.id']), "n": row['stadium.name'], "c": ciudad, "p": row['stadium.country.name']})
        
        
                # 3. ÁRBITROS
                if 'referee.id' in df.columns:
                    df_ref = df[['referee.id', 'referee.name', 'referee.country.id']].dropna(subset=['referee.id']).drop_duplicates()
                    for _, row in df_ref.iterrows():
                        conn.execute(sa.text("IF NOT EXISTS (SELECT 1 FROM arbitro WHERE id_arbitro = :id) "
                                           "INSERT INTO arbitro (id_arbitro, nombre, id_nacionalidad) VALUES (:id, :n, :nac)"), 
                                           {"id": row['referee.id'], "n": row['referee.name'], "nac": row['referee.country.id']})

                # 4. EQUIPOS
                df_eq_h = df[['home_team.home_team_id', 'home_team.home_team_name']].rename(columns={'home_team.home_team_id':'id', 'home_team.home_team_name':'n'})
                df_eq_a = df[['away_team.away_team_id', 'away_team.away_team_name']].rename(columns={'away_team.away_team_id':'id', 'away_team.away_team_name':'n'})
                df_equipos = pd.concat([df_eq_h, df_eq_a]).drop_duplicates()
                for _, row in df_equipos.iterrows():
                    conn.execute(sa.text("IF NOT EXISTS (SELECT 1 FROM equipo WHERE id_equipo = :id) "
                                       "INSERT INTO equipo (id_equipo, nombre) VALUES (:id, :n)"), 
                                       {"id": row['id'], "n": row['n']})

                # 5. PARTIDOS (Insert con validación de existencia)
                for _, row in df.iterrows():
                    try:
                        params = {
                            "id": int(row['match_id']), "f": str(row['match_date']), "k": str(row['kick_off']), 
                            "gl": int(row['home_score']), "gv": int(row['away_score']), 
                            "fa": str(row.get('competition_stage.name', 'Regular')), "jo": int(row.get('match_week', 0)),
                            "ic": int(row['competition.competition_id']), "it": int(row['season.season_id']),
                            "ie": int(row['stadium.id']) if row.get('stadium.id') else None, 
                            "el": int(row['home_team.home_team_id']), "ev": int(row['away_team.away_team_id']), 
                            "ar": int(row['referee.id']) if row.get('referee.id') else None
                        }

                        conn.execute(sa.text("""
                            IF NOT EXISTS (SELECT 1 FROM partido WHERE id_partido = :id)
                            INSERT INTO partido (id_partido, fecha, kick_off, goles_local, goles_visita, fase, jornada, 
                                               id_competicion, id_temporada, id_estadio, id_equipo_local, id_equipo_visita, id_arbitro)
                            VALUES (:id, :f, :k, :gl, :gv, :fa, :jo, :ic, :it, :ie, :el, :ev, :ar)
                        """), params)
                        
                        f_sql.write(f"IF NOT EXISTS (SELECT 1 FROM partido WHERE id_partido = {params['id']}) "
                                    f"INSERT INTO partido VALUES ({params['id']}, '{params['f']}', '{params['k']}', {params['gl']}, {params['gv']}, '{params['fa']}', {params['jo']}, {params['ic']}, {params['it']}, {sql_val(params['ie'])}, {params['el']}, {params['ev']}, {sql_val(params['ar'])});\n")

                    except Exception as e:
                        print(f"Error al insertar partido {row['match_id']}: {e}")
                
                conn.commit()
                f_sql.write("GO\n")

    except Exception as e:
        print(f"Error procesando archivo {ruta}: {e}")

        
        
        

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