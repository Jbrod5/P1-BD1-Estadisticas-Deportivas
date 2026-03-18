import pandas
import matplotlib.pyplot
import sqlalchemy
from mplsoccer import Pitch

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
consulta_sql = """
SELECT
    j.nombre AS jugador,
    ev.x_inicio AS x_posicion,
    ev.y_inicio AS y_posicion,
    g.x_fin AS x_destino,
    g.y_fin AS y_destino,
    g.tipo_gol,
    ev.minuto,
    p.fecha
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN jugador j ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
WHERE j.nombre LIKE '%Maradona%'
ORDER BY p.fecha, ev.minuto;
"""

# 3. EJECUTAR CONSULTA
print("Buscando goles de Maradona en la base de datos...")
dataframe_goles = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_goles) == 0:
    print("No se encontraron goles de Maradona")
    exit()

print(f"Se encontraron {len(dataframe_goles)} goles de Maradona")
print("Mostrando los primeros 3 goles encontrados:")
print(dataframe_goles[['jugador', 'minuto', 'tipo_gol', 'x_posicion', 'y_posicion']].head(3).to_string(index=False))

# 5. CREAR LA CANCHA DE FUTBOL
print("Dibujando cancha y goles de Maradona...")
cancha = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white', stripe=True)
figura, eje = cancha.draw(figsize=(14, 8))

# 6. DIBUJAR CADA GOL EN LA CANCHA
for indice, fila in dataframe_goles.iterrows():
    
    # Dibuja una linea desde donde disparo hasta donde entro el gol
    cancha.lines(
        fila.x_posicion, fila.y_posicion,      # punto de inicio del disparo
        fila.x_destino, fila.y_destino,        # punto donde entro el gol
        ax=eje,
        color='red',               # color rojo para la trayectoria
        linewidth=2,               # grosor de la linea
        alpha=0.6,                 # transparencia para ver varias lineas
        comet=True                 # efecto de estela al inicio
    )
    
    # Marca el punto de donde disparo con un circulo azul
    cancha.scatter(
        fila.x_posicion, fila.y_posicion,
        ax=eje,
        s=50,                    # tamaño del circulo
        color='blue',            # color azul
        edgecolor='black',       # borde negro
        alpha=0.7                # un poco transparente
    )
    
    # Marca el punto del gol con una estrella dorada
    cancha.scatter(
        fila.x_destino, fila.y_destino,
        ax=eje,
        s=100,                 # tamaño mas grande que el circulo
        color='gold',          # color dorado
        edgecolor='red',       # borde rojo
        marker='*',            # estrella (caracter valido)
        alpha=0.9              # casi sin transparencia
    )

# 7. TITULO Y LEYENDA
eje.set_title(f'Mapa de goles de Lionel Maradona - {len(dataframe_goles)} goles analizados', 
              fontsize=16, fontweight='bold')

# Explicacion de los simbolos en la grafica
eje.text(10, 5, '● Punto de disparo', color='blue', fontsize=10,
        bbox=dict(facecolor='white', alpha=0.7))

eje.text(10, 0, '★ Gol', color='gold', fontsize=10,
        bbox=dict(facecolor='white', alpha=0.7))

eje.text(10, -5, 'Linea roja: trayectoria del disparo', color='red', fontsize=10,
        bbox=dict(facecolor='white', alpha=0.7))

# 8. GUARDAR LA GRAFICA
nombre_archivo = '19.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")