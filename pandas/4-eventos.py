import sqlalchemy as sqlalchemy
import json
import os
import re

# Configuramos la conexion a nuestra base de datos en SQL Server
# Los datos de acceso son usuario sa y la contraseña SS12345#
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

def asegurar_jugador(conexion, datos_jugador):
    """
    Esta funcion verifica si un jugador ya existe en la base de datos
    Si no existe lo inserta y devuelve su id
    Si los datos del jugador no son validos devuelve None
    """
    if not datos_jugador:
        return None
    
    identificador_jugador = datos_jugador.get('id')
    nombre_jugador = datos_jugador.get('name')
    
    # Solo procesamos si el ID es un numero entero
    # Los UUIDs no los manejamos aqui porque la tabla jugador usa INT
    if identificador_jugador and isinstance(identificador_jugador, int):
        consulta_existencia = sqlalchemy.text("""
            IF NOT EXISTS (SELECT 1 FROM jugador WHERE id_jugador = :id)
            INSERT INTO jugador (id_jugador, nombre, id_nacionalidad) 
            VALUES (:id, :nom, NULL)
        """)
        
        conexion.execute(consulta_existencia, {
            "id": identificador_jugador, 
            "nom": nombre_jugador
        })
        
        return identificador_jugador
    
    return None


def asegurar_catalogo(conexion, nombre_tabla, nombre_columna_id, nombre_columna_nombre, valor_id, valor_nombre):
    """
    Funcion generica para insertar valores en tablas de catalogo
    Como tipo_evento, parte_cuerpo, etc.
    Solo inserta si el valor no existe previamente
    """
    if valor_id:
        consulta_catalogo = sqlalchemy.text(f"""
            IF NOT EXISTS (SELECT 1 FROM {nombre_tabla} WHERE {nombre_columna_id} = :id)
            INSERT INTO {nombre_tabla} ({nombre_columna_id}, {nombre_columna_nombre}) 
            VALUES (:id, :nom)
        """)
        
        conexion.execute(consulta_catalogo, {
            "id": valor_id, 
            "nom": valor_nombre
        })


def procesar_archivo_eventos(ruta_archivo, id_partido_manual):
    """
    Esta funcion procesa un archivo JSON de eventos
    Lee cada evento y lo inserta en las tablas correspondientes
    Tambien maneja las especializaciones como disparos pases tarjetas etc.
    """
    
    # Extraemos el nombre base del archivo para identificar el partido
    nombre_base = os.path.basename(ruta_archivo)
    
    # Buscamos numeros en el nombre del archivo usando expresiones regulares
    numeros_encontrados = re.findall(r'\d+', nombre_base)
    
    # Determinamos el ID del partido
    # Si recibimos un valor manual lo usamos si no tomamos el primer numero del nombre
    if id_partido_manual:
        id_partido = id_partido_manual
    elif numeros_encontrados:
        id_partido = numeros_encontrados[0]
    else:
        id_partido = 0
        print(f"Advertencia: No se pudo determinar el ID del partido para {nombre_base}")

    print(f"--- Cargando Eventos del Partido: {id_partido} ---")
    
    try:
        # Abrimos y leemos el archivo JSON
        with open(ruta_archivo, encoding='utf-8') as archivo:
            datos_eventos = json.load(archivo)
        
        print(f"  Se encontraron {len(datos_eventos)} eventos en el archivo")
        
        # 1. PREPARACION: Construimos un diccionario rapido para relacionar pases con asistentes
        # Esto nos ayudara a resolver el problema de convertir UUIDs a IDs numericos
        pases_a_jugadores = {}
        
        for evento in datos_eventos:
            tipo_evento = evento.get('type', {}).get('name')
            if tipo_evento == 'Pass' and 'player' in evento:
                id_evento_actual = evento.get('id')
                id_jugador_actual = evento.get('player', {}).get('id')
                
                # Solo guardamos si ambos IDs existen y el del jugador es numerico
                if id_evento_actual and id_jugador_actual and isinstance(id_jugador_actual, int):
                    pases_a_jugadores[id_evento_actual] = id_jugador_actual
        
        print(f"  Se prepararon {len(pases_a_jugadores)} relaciones de pases para buscar asistencias")
        
        # 2. PROCESAMIENTO: Recorremos cada evento y lo insertamos en la base de datos
        with motor_base_datos.connect() as conexion:
            
            contador_eventos = 0
            contador_goles = 0
            contador_pases = 0
            contador_disparos = 0
            contador_tarjetas = 0
            contador_sustituciones = 0
            
            for evento in datos_eventos:
                
                # Obtenemos los datos basicos del evento
                id_evento = evento.get('id')
                tipo_evento = evento.get('type', {})
                
                # Aseguramos que el jugador exista en la base de datos
                id_jugador = asegurar_jugador(conexion, evento.get('player'))
                
                # Obtenemos el equipo del evento
                id_equipo = evento.get('team', {}).get('id')
                
                # 2.1 REGISTRO BASE EN TABLA EVENTO
                
                # Aseguramos que el tipo de evento exista en el catalogo
                asegurar_catalogo(
                    conexion, 
                    'tipo_evento', 
                    'id_tipo', 
                    'nombre', 
                    tipo_evento.get('id'), 
                    tipo_evento.get('name')
                )
                
                # Obtenemos las coordenadas del evento
                coordenadas = evento.get('location', [None, None])
                x_inicio = coordenadas[0] if len(coordenadas) > 0 else None
                y_inicio = coordenadas[1] if len(coordenadas) > 1 else None
                
                # Insertamos el evento principal
                consulta_evento = sqlalchemy.text("""
                    INSERT INTO evento (
                        id_evento, minuto, segundo, periodo, 
                        x_inicio, y_inicio, duracion,
                        id_equipo_posesion, id_partido, id_tipo, 
                        id_jugador, id_equipo
                    ) VALUES (
                        :id, :min, :seg, :per, 
                        :x, :y, :dur, 
                        :eq_pos, :part, :tipo, 
                        :jug, :eq
                    )
                """)
                
                parametros_evento = {
                    "id": id_evento,
                    "min": evento.get('minute'),
                    "seg": evento.get('second'),
                    "per": evento.get('period'),
                    "x": x_inicio,
                    "y": y_inicio,
                    "dur": evento.get('duration', 0),
                    "eq_pos": evento.get('possession_team', {}).get('id'),
                    "part": int(id_partido),
                    "tipo": tipo_evento.get('id'),
                    "jug": id_jugador,
                    "eq": id_equipo
                }
                
                conexion.execute(consulta_evento, parametros_evento)
                contador_eventos += 1
                
                # 2.2 ESPECIALIZACION: DISPARO
                if tipo_evento.get('name') == 'Shot':
                    
                    datos_disparo = evento.get('shot', {})
                    resultado_disparo = datos_disparo.get('outcome', {}).get('name')
                    tipo_disparo = datos_disparo.get('type', {}).get('name')
                    
                    # Procesamos la parte del cuerpo usada
                    parte_cuerpo = datos_disparo.get('body_part', {})
                    asegurar_catalogo(
                        conexion, 
                        'parte_cuerpo', 
                        'id_parte_cuerpo', 
                        'nombre', 
                        parte_cuerpo.get('id'), 
                        parte_cuerpo.get('name')
                    )
                    
                    # Coordenadas finales del disparo
                    coordenadas_finales = datos_disparo.get('end_location', [None, None])
                    x_fin = coordenadas_finales[0] if len(coordenadas_finales) > 0 else None
                    y_fin = coordenadas_finales[1] if len(coordenadas_finales) > 1 else None
                    
                    # Insertamos en la tabla disparo
                    consulta_disparo = sqlalchemy.text("""
                        INSERT INTO disparo (
                            id_evento, x_fin, y_fin, outcome, id_parte_cuerpo
                        ) VALUES (
                            :id, :xf, :yf, :out, :bp
                        )
                    """)
                    
                    conexion.execute(consulta_disparo, {
                        "id": id_evento,
                        "xf": x_fin,
                        "yf": y_fin,
                        "out": resultado_disparo,
                        "bp": parte_cuerpo.get('id')
                    })
                    
                    contador_disparos += 1
                    
                    # 2.2.1 SUBESPECIALIZACION: GOL (si el disparo termino en gol)
                    if resultado_disparo == 'Goal':
                        
                        # Buscamos la asistencia
                        # El ID del pase que genero el gol puede ser un UUID
                        uuid_asistencia = datos_disparo.get('key_pass_id')
                        
                        # Convertimos el UUID del pase al ID numerico del jugador que hizo el pase
                        id_asistente_real = pases_a_jugadores.get(uuid_asistencia)
                        
                        if id_asistente_real:
                            print(f"    Gol asistido por jugador {id_asistente_real}")
                        
                        # Insertamos en la tabla gol
                        consulta_gol = sqlalchemy.text("""
                            INSERT INTO gol (
                                id_evento, tipo_gol, x_fin, y_fin, 
                                id_parte_cuerpo, id_asistente
                            ) VALUES (
                                :id, :tipo, :xf, :yf, :bp, :asist
                            )
                        """)
                        
                        conexion.execute(consulta_gol, {
                            "id": id_evento,
                            "tipo": tipo_disparo,
                            "xf": x_fin,
                            "yf": y_fin,
                            "bp": parte_cuerpo.get('id'),
                            "asist": id_asistente_real
                        })
                        
                        contador_goles += 1
                    
                    # 2.2.2 SUBESPECIALIZACION: PENAL
                    # Detectamos si fue penal por el tipo de disparo o por el periodo
                    if tipo_disparo == 'Penalty' or evento.get('period') == 5:
                        
                        resultado_penal = 'Anotado' if resultado_disparo == 'Goal' else 'Fallado'
                        
                        consulta_penal = sqlalchemy.text("""
                            INSERT INTO penal (id_evento, resultado) 
                            VALUES (:id, :res)
                        """)
                        
                        conexion.execute(consulta_penal, {
                            "id": id_evento,
                            "res": resultado_penal
                        })
                
                # 2.3 ESPECIALIZACION: PASE
                elif tipo_evento.get('name') == 'Pass':
                    
                    datos_pase = evento.get('pass', {})
                    
                    # Procesamos la parte del cuerpo usada
                    parte_cuerpo = datos_pase.get('body_part', {})
                    asegurar_catalogo(
                        conexion, 
                        'parte_cuerpo', 
                        'id_parte_cuerpo', 
                        'nombre', 
                        parte_cuerpo.get('id'), 
                        parte_cuerpo.get('name')
                    )
                    
                    # Aseguramos que el receptor del pase exista
                    id_receptor = asegurar_jugador(conexion, datos_pase.get('recipient'))
                    
                    # Determinamos si el pase fue completado
                    # Si tiene campo outcome significa que fue fallido
                    pase_completado = 1 if 'outcome' not in datos_pase else 0
                    
                    # Coordenadas finales del pase
                    coordenadas_finales = datos_pase.get('end_location', [None, None])
                    x_fin = coordenadas_finales[0] if len(coordenadas_finales) > 0 else None
                    y_fin = coordenadas_finales[1] if len(coordenadas_finales) > 1 else None
                    
                    # Insertamos en la tabla pase
                    consulta_pase = sqlalchemy.text("""
                        INSERT INTO pase (
                            id_evento, longitud, angulo, altura, completado,
                            x_fin, y_fin, id_parte_cuerpo, id_receptor
                        ) VALUES (
                            :id, :lon, :ang, :alt, :comp,
                            :xf, :yf, :bp, :rec
                        )
                    """)
                    
                    conexion.execute(consulta_pase, {
                        "id": id_evento,
                        "lon": datos_pase.get('length'),
                        "ang": datos_pase.get('angle'),
                        "alt": datos_pase.get('height', {}).get('name'),
                        "comp": pase_completado,
                        "xf": x_fin,
                        "yf": y_fin,
                        "bp": parte_cuerpo.get('id'),
                        "rec": id_receptor
                    })
                    
                    contador_pases += 1
                
                # 2.4 ESPECIALIZACION: CONDUCCION
                elif tipo_evento.get('name') == 'Carry':
                    
                    datos_conduccion = evento.get('carry', {})
                    
                    # Coordenadas finales de la conduccion
                    coordenadas_finales = datos_conduccion.get('end_location', [None, None])
                    x_fin = coordenadas_finales[0] if len(coordenadas_finales) > 0 else None
                    y_fin = coordenadas_finales[1] if len(coordenadas_finales) > 1 else None
                    
                    consulta_conduccion = sqlalchemy.text("""
                        INSERT INTO conduccion (id_evento, x_fin, y_fin) 
                        VALUES (:id, :xf, :yf)
                    """)
                    
                    conexion.execute(consulta_conduccion, {
                        "id": id_evento,
                        "xf": x_fin,
                        "yf": y_fin
                    })
                
                # 2.5 ESPECIALIZACION: TARJETA
                elif 'bad_behaviour' in evento or 'foul_committed' in evento:
                    
                    datos_tarjeta = evento.get('bad_behaviour') or evento.get('foul_committed')
                    
                    if datos_tarjeta and 'card' in datos_tarjeta:
                        
                        color_tarjeta = datos_tarjeta['card']['name']
                        
                        consulta_tarjeta = sqlalchemy.text("""
                            INSERT INTO tarjeta (id_evento, color) 
                            VALUES (:id, :color)
                        """)
                        
                        conexion.execute(consulta_tarjeta, {
                            "id": id_evento,
                            "color": color_tarjeta
                        })
                        
                        contador_tarjetas += 1
                
                # 2.6 ESPECIALIZACION: SUSTITUCION
                elif tipo_evento.get('name') == 'Substitution':
                    
                    datos_sustitucion = evento.get('substitution', {})
                    
                    # Aseguramos que el jugador que entra exista
                    id_jugador_entra = asegurar_jugador(conexion, datos_sustitucion.get('replacement'))
                    
                    consulta_sustitucion = sqlalchemy.text("""
                        INSERT INTO sustitucion (
                            id_evento, id_jugador_sale, id_jugador_entra
                        ) VALUES (
                            :id, :sale, :entra
                        )
                    """)
                    
                    conexion.execute(consulta_sustitucion, {
                        "id": id_evento,
                        "sale": id_jugador,
                        "entra": id_jugador_entra
                    })
                    
                    contador_sustituciones += 1
                
                # Confirmamos cada evento individualmente
                conexion.commit()
            
            # Mostramos un resumen de lo que se cargo
            print(f"  Resumen de carga para partido {id_partido}")
            print(f"    Eventos base: {contador_eventos}")
            print(f"    Disparos: {contador_disparos}")
            print(f"    Goles: {contador_goles}")
            print(f"    Pases: {contador_pases}")
            print(f"    Tarjetas: {contador_tarjetas}")
            print(f"    Sustituciones: {contador_sustituciones}")
        
        print(f"  Carga completada para partido {id_partido}")
        
    except Exception as error:
        print(f"  Error procesando archivo {id_partido}: {error}")
        print(f"  Tipo de error: {type(error).__name__}")


# Lista de archivos a procesar con sus IDs de partido correspondientes
# Cada entrada es una tupla con la ruta del archivo y el ID del partido
archivos_a_procesar = [
    ('../datos/Champios/Eventos/22912 _ Eventos_FInal_UCL_2019.json', 22912),
    ('../datos/Champios/Eventos/Event_2015_18242.json', 18242),
    ('../datos/Copa del mundo/partidos/FIFA_W_C_1986/CuartosFinal_ARG_VS_ENG/EventosDelPartido.json', 3750191),
    ('../datos/LaLiga/events/3773386.json', 3773386),
    ('../datos/LaLiga/events/3773457.json', 3773457)
]


if __name__ == "__main__":
    
    print("Iniciando carga de eventos")
    print("=" * 60)
    
    contador_archivos_procesados = 0
    
    for ruta_archivo, id_partido in archivos_a_procesar:
        
        if os.path.exists(ruta_archivo):
            procesar_archivo_eventos(ruta_archivo, id_partido)
            contador_archivos_procesados += 1
        else:
            print(f"Archivo no encontrado: {ruta_archivo}")
    
    print("=" * 60)
    print(f"Proceso completado. Se procesaron {contador_archivos_procesados} archivos")
    print("--- CARGA COMPLETADA!!!!! ---")