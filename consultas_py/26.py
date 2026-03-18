from mplsoccer import Pitch
import pandas as pd
import matplotlib.pyplot as plt
import sqlalchemy as sa

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_bd = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL CORREGIDA - AHORA CON x_fin Y y_fin
# Busca todos los pases de Argentina en cuartos de final del Mundial 1986
# e incluye las coordenadas de destino del pase

consulta_sql = """
SELECT 
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
WHERE p.fase = 'Quarter-finals' 
  AND ev.id_equipo = (SELECT id_equipo FROM equipo WHERE nombre = 'Argentina')
ORDER BY ev.minuto, ev.segundo;
"""

# 3. EJECUTAR LA CONSULTA
print("Buscando pases de Argentina en cuartos de final del Mundial 1986...")
df = pd.read_sql(consulta_sql, motor_bd)

# 4. VERIFICAR DATOS
if len(df) == 0:
    print("No se encontraron pases para Argentina en ese partido")
    exit()

print(f"Se encontraron {len(df)} pases")
print(f"Mostrando los primeros 3 pases como ejemplo:")
print(df[['Jugador', 'minuto', 'segundo', 'x_inicio', 'y_inicio', 'x_fin', 'y_fin']].head(3))

# 5. CREAR LA GRAFICA
print("Dibujando la sucesion de pases...")

# Cancha con fondo oscuro para que resalten las lineas de colores
pitch = Pitch(pitch_type='statsbomb', pitch_color='#0a1a2a', line_color='white', linewidth=1.5)
fig, ax = pitch.draw(figsize=(14, 8))

# Lista de colores para diferenciar jugadores
colores = ['#ff3333', '#33ff33', '#3333ff', '#ffff33', '#ff33ff', '#33ffff']

# 6. DIBUJAR CADA PASE
for i, (idx, row) in enumerate(df.iterrows()):
    color_actual = colores[i % len(colores)]
    
    # Dibuja la flecha del pase desde inicio hasta fin
    pitch.arrows(
        row.x_inicio, row.y_inicio,
        row.x_fin, row.y_fin,
        ax=ax,
        width=2,
        headwidth=5,
        headlength=5,
        color=color_actual,
        alpha=0.7
    )
    
    # Marca el punto de inicio con el nombre del jugador (solo el apellido)
    nombre_corto = row.Jugador.split()[-1]  # toma el ultimo apellido
    ax.annotate(
        nombre_corto,
        (row.x_inicio, row.y_inicio),
        color='white',
        fontsize=7,
        weight='bold',
        bbox=dict(facecolor='black', alpha=0.5, boxstyle='round,pad=0.2')
    )
    
    # Agrega el minuto del pase cerca del destino
    ax.annotate(
        f"{row.minuto}'",
        (row.x_fin, row.y_fin),
        color='lightgray',
        fontsize=6,
        alpha=0.6,
        ha='center'
    )

# 7. TITULO Y LEYENDA
ax.set_title('Sucesion de pases de Argentina - Cuartos de final Mundial 1986', 
             fontsize=16, color='white', fontweight='bold', pad=20)

# Nota sobre la jugada historica
nota = (
    "Partido Argentina vs Inglaterra\n"
    "Incluye el Gol del Siglo de Maradona\n"
    f"Total de pases mostrados: {len(df)}"
)
ax.text(60, 5, nota, color='white', fontsize=10, ha='center',
        bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.5'))

# 8. GUARDAR LA GRAFICA
nombre_archivo = '26.png'
plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight', facecolor='#0a1a2a')
print(f"Grafica guardada como: {nombre_archivo}")

# Muestra la grafica
plt.show()
print("Listo!")