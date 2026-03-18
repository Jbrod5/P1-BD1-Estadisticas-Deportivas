import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy
from mplsoccer import Pitch

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca todos los pases en finales de Champions
consulta_sql = """
SELECT TOP 200
   j.nombre AS Jugador,
   ev.minuto,
   ev.segundo,
   ev.x_inicio,
   ev.y_inicio,
   pa.x_fin,
   pa.y_fin
FROM evento ev
JOIN pase pa ON ev.id_evento = pa.id_evento
JOIN jugador j ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League'
 AND p.fase = 'Final' 
ORDER BY ev.minuto, ev.segundo;
"""

# 3. EJECUTAR CONSULTA
print("Buscando pases en finales de Champions...")
dataframe_pases = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_pases) == 0:
    print("No se encontraron pases para esta consulta")
    exit()

print(f"Se encontraron {len(dataframe_pases)} pases")
print("\nPrimeros 5 pases:")
print(dataframe_pases.head().to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando mapa de pases de finales de Champions...")

# Configurar la cancha
cancha = Pitch(pitch_type='statsbomb', pitch_color='lightgray', line_color='black', linewidth=1.5)
figura, eje = cancha.draw(figsize=(14, 8))
figura.suptitle('Pases en finales de Champions League', 
                fontsize=16, fontweight='bold')

# --------------------------------------------------
# DIBUJAR TODOS LOS PASES
# --------------------------------------------------
# Colores básicos de matplotlib
colores = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

# Asignar un color a cada jugador unico
jugadores_unicos = dataframe_pases['Jugador'].unique()
color_por_jugador = {}
for i, jugador in enumerate(jugadores_unicos):
    color_por_jugador[jugador] = colores[i % len(colores)]

# Contador para la leyenda (solo mostrar algunos)
jugadores_mostrados = set()

for _, pase in dataframe_pases.iterrows():
    color = color_por_jugador[pase['Jugador']]
    
    # Dibujar flecha del pase
    cancha.arrows(
        pase['x_inicio'], pase['y_inicio'],
        pase['x_fin'], pase['y_fin'],
        ax=eje,
        width=1.5,
        headwidth=4,
        headlength=4,
        color=color,
        alpha=0.6,
        label=pase['Jugador'] if pase['Jugador'] not in jugadores_mostrados else ""
    )
    jugadores_mostrados.add(pase['Jugador'])
    
    # Marcar punto de inicio
    cancha.scatter(
        pase['x_inicio'], pase['y_inicio'],
        ax=eje,
        s=20,
        color=color,
        edgecolor='black',
        linewidth=0.5,
        alpha=0.8
    )

# Configurar leyenda
eje.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, title='Jugadores')

# --------------------------------------------------
# GRAFICA ADICIONAL: FRECUENCIA DE PASES POR MINUTO
# --------------------------------------------------
figura2, grafica2 = matplotlib.pyplot.subplots(figsize=(12, 4))
figura2.suptitle('Frecuencia de pases por minuto en finales de Champions', 
                 fontsize=14, fontweight='bold')

# Agrupar pases por minuto
pases_por_minuto = dataframe_pases.groupby('minuto').size().reset_index(name='cantidad')

grafica2.bar(
    pases_por_minuto['minuto'],
    pases_por_minuto['cantidad'],
    color='blue',
    alpha=0.7,
    edgecolor='black',
    linewidth=1
)

grafica2.set_xlabel('Minuto del partido')
grafica2.set_ylabel('Cantidad de pases')
grafica2.set_title('Distribucion de pases en el tiempo')
grafica2.grid(axis='y', alpha=0.3, linestyle='--')

# --------------------------------------------------
# ESTADISTICAS BASICAS
# --------------------------------------------------
print("\nEstadisticas de pases:")
print(f"Total de pases: {len(dataframe_pases)}")
print(f"Jugadores distintos: {len(jugadores_unicos)}")
print(f"Rango de minutos: {dataframe_pases['minuto'].min()} - {dataframe_pases['minuto'].max()}")

# Minutos con mas pases
top_minutos = pases_por_minuto.nlargest(3, 'cantidad')
print("\nMinutos con mas pases:")
for _, fila in top_minutos.iterrows():
    print(f"  Minuto {int(fila['minuto'])}: {int(fila['cantidad'])} pases")

# --------------------------------------------------
# GUARDAR GRAFICAS
# --------------------------------------------------
nombre_archivo1 = '27_pases_finales.png'
matplotlib.pyplot.figure(1)
matplotlib.pyplot.savefig(nombre_archivo1, dpi=300, bbox_inches='tight')
print(f"\nGrafica de pases guardada como: {nombre_archivo1}")

nombre_archivo2 = '27_frecuencia_pases.png'
matplotlib.pyplot.figure(2)
matplotlib.pyplot.savefig(nombre_archivo2, dpi=300, bbox_inches='tight')
print(f"Grafica de frecuencia guardada como: {nombre_archivo2}")

# Mostrar graficas
matplotlib.pyplot.show()
print("Listo!")