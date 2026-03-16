import sqlalchemy as sa
import json
import os

engine = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def asegurar_jugador(conn, player_data):
    if not player_data: return None
    p_id, p_nom = player_data.get('id'), player_data.get('name')
    if p_id:
        conn.execute(sa.text("""
            IF NOT EXISTS (SELECT 1 FROM jugador WHERE id_jugador = :id)
            INSERT INTO jugador (id_jugador, nombre, id_nacionalidad) VALUES (:id, :nom, NULL)
        """), {"id": p_id, "nom": p_nom})
    return p_id

def asegurar_catalogo(conn, tabla, id_col, nombre_col, val_id, val_nom):
    """Inserta en tablas de catálogo (posicion, parte_cuerpo, etc.) si no existen."""
    if val_id:
        query = sa.text(f"IF NOT EXISTS (SELECT 1 FROM {tabla} WHERE {id_col} = :id) "
                        f"INSERT INTO {tabla} ({id_col}, {nombre_col}) VALUES (:id, :nom)")
        conn.execute(query, {"id": val_id, "nom": val_nom})

def procesar_archivo_eventos(ruta, match_id):
    print(f"--- Procesando Eventos del Match: {match_id} ---")
    try:
        with open(ruta, encoding='utf-8') as f:
            data = json.load(f)
        
        with engine.connect() as conn:
            for ev in data:
                ev_id = ev['id']
                tipo = ev['type']
                id_jugador = asegurar_jugador(conn, ev.get('player'))
                id_equipo = ev['team']['id']
                
                # 1. Asegurar Tipo de Evento
                asegurar_catalogo(conn, 'tipo_evento', 'id_tipo', 'nombre', tipo['id'], tipo['name'])

                # 2. Insertar Evento Base
                loc = ev.get('location', [None, None])
                conn.execute(sa.text("""
                    INSERT INTO evento (id_evento, minuto, segundo, periodo, x_inicio, y_inicio, duracion, 
                                      id_equipo_posesion, id_partido, id_tipo, id_jugador, id_equipo)
                    VALUES (:id, :min, :seg, :per, :x, :y, :dur, :eqp, :part, :tipo, :jug, :eq)
                """), {
                    "id": ev_id, "min": ev.get('minute'), "seg": ev.get('second'), "per": ev.get('period'),
                    "x": loc[0], "y": loc[1], "dur": ev.get('duration', 0), "eqp": ev.get('possession_team', {}).get('id'),
                    "part": match_id, "tipo": tipo['id'], "jug": id_jugador, "eq": id_equipo
                })

                # 3. Especializaciones Dinámicas
                # --- PASES ---
                if tipo['name'] == 'Pass':
                    p = ev.get('pass', {})
                    id_rec = asegurar_jugador(conn, p.get('recipient'))
                    bp = p.get('body_part', {})
                    asegurar_catalogo(conn, 'parte_cuerpo', 'id_parte_cuerpo', 'nombre', bp.get('id'), bp.get('name'))
                    eloc = p.get('end_location', [None, None])
                    conn.execute(sa.text("""
                        INSERT INTO pase (id_evento, longitud, angulo, altura, completado, x_fin, y_fin, id_parte_cuerpo, id_receptor)
                        VALUES (:id, :lon, :ang, :alt, :comp, :xf, :yf, :bp, :rec)
                    """), {
                        "id": ev_id, "lon": p.get('length'), "ang": p.get('angle'), "alt": p.get('height', {}).get('name'),
                        "comp": 1 if 'outcome' not in p else 0, "xf": eloc[0], "yf": eloc[1], "bp": bp.get('id'), "rec": id_rec
                    })

                # --- DISPAROS ---
                elif tipo['name'] == 'Shot':
                    s = ev.get('shot', {})
                    bp = s.get('body_part', {})
                    asegurar_catalogo(conn, 'parte_cuerpo', 'id_parte_cuerpo', 'nombre', bp.get('id'), bp.get('name'))
                    eloc = s.get('end_location', [None, None])
                    conn.execute(sa.text("""
                        INSERT INTO disparo (id_evento, x_fin, y_fin, outcome, id_parte_cuerpo)
                        VALUES (:id, :xf, :yf, :out, :bp)
                    """), {"id": ev_id, "xf": eloc[0], "yf": eloc[1], "out": s.get('outcome', {}).get('name'), "bp": bp.get('id')})

                # --- CONDUCCIONES (Carries) ---
                elif tipo['name'] == 'Carry':
                    c = ev.get('carry', {})
                    eloc = c.get('end_location', [None, None])
                    conn.execute(sa.text("INSERT INTO conduccion (id_evento, x_fin, y_fin) VALUES (:id, :xf, :yf)"),
                                 {"id": ev_id, "xf": eloc[0], "yf": eloc[1]})

                # --- TARJETAS ---
                elif 'bad_behaviour' in ev or 'foul_committed' in ev:
                    card_data = ev.get('bad_behaviour') or ev.get('foul_committed')
                    if card_data and 'card' in card_data:
                        conn.execute(sa.text("INSERT INTO tarjeta (id_evento, color) VALUES (:id, :col)"),
                                     {"id": ev_id, "col": card_data['card']['name']})

                # --- SUSTITUCIONES ---
                elif tipo['name'] == 'Substitution':
                    sub = ev.get('substitution', {})
                    id_entra = asegurar_jugador(conn, sub.get('replacement'))
                    conn.execute(sa.text("INSERT INTO sustitucion (id_evento, id_jugador_sale, id_jugador_entra) VALUES (:id, :sale, :entra)"),
                                 {"id": ev_id, "sale": id_jugador, "entra": id_entra})

                conn.commit()
    except Exception as e:
        print(f"Error en {match_id}: {e}")



# Lista de archivos a procesar (puedes automatizar esto con os.walk)
archivos = [
    ('../datos/Champios/Eventos/22912 _ Eventos_FInal_UCL_2019.json', 22912),
    ('../datos/Champios/Eventos/Event_2015_18242.json', 18242),
    ('../datos/Copa del mundo/partidos/FIFA_W_C_1986/CuartosFinal_ARG_VS_ENG/EventosDelPartido.json', 3750191),
    ('../datos/LaLiga/events/3773386.json', 3773386),
    ('../datos/LaLiga/events/3773457.json', 3773457)
]

if __name__ == "__main__":
    for ruta, mid in archivos:
        if os.path.exists(ruta):
            procesar_archivo_eventos(ruta, mid)
    print("¡Carga de eventos finalizada!")