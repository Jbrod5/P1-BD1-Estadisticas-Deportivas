from mplsoccer import Pitch
import pandas as pd
import matplotlib.pyplot as plt
import sqlalchemy as sa

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_bd = sa.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Esta consulta trae todas las coordenadas de los eventos de Messi
# Solo trae eventos que tienen coordenadas (x_inicio no es nulo)

consulta_sql = """
SELECT
    j.nombre AS jugador,
    te.nombre AS tipo_evento,
    ev.x_inicio,
    ev.y_inicio,
    ev.minuto,
    p.fecha
FROM evento ev
JOIN jugador j ON ev.id_jugador = j.id_jugador
JOIN tipo_evento te ON ev.id_tipo = te.id_tipo
JOIN partido p ON ev.id_partido = p.id_partido
WHERE j.nombre LIKE '%Messi%'
  AND ev.x_inicio IS NOT NULL
ORDER BY p.fecha, ev.minuto;
"""

# 3. EJECUTAR LA CONSULTA Y CARGAR LOS DATOS
print("Ejecutando consulta para obtener eventos de Messi...")
df = pd.read_sql(consulta_sql, motor_bd)

print(f"Se encontraron {len(df)} eventos de Messi con coordenadas")

# 4. VERIFICAR QUE HAYA DATOS
if len(df) == 0:
    print("No se encontraron datos para Messi")
    exit()

# 5. CREAR LA GRAFICA DEL MAPA DE CALOR
print("Dibujando mapa de calor...")

# Configura la cancha con cesped y lineas blancas
pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white', stripe=True)
fig, ax = pitch.draw(figsize=(14, 8))

# Dibuja el mapa de calor con los puntos de los eventos
pitch.kdeplot(
    df.x_inicio, df.y_inicio,
    ax=ax,
    cmap='hot',          # usa colores calientes (negro, rojo, amarillo)
    fill=True,           # rellena las areas del mapa
    levels=100,          # cantidad de divisiones de color
    alpha=0.7,           # transparencia para ver la cancha de fondo
    shade=True           # suaviza los bordes
)

# 6. PERSONALIZAR LA GRAFICA
ax.set_title('Mapa de calor de Lionel Messi - Zonas de participacion', fontsize=16, fontweight='bold')

# Agrega un recuadro con la cantidad total de eventos
ax.text(10, 5, f'Total de eventos analizados: {len(df)}', fontsize=10, color='white',
        bbox=dict(facecolor='black', alpha=0.6))

# 7. GUARDAR LA GRAFICA
nombre_archivo = '28.png'
plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

# Muestra la grafica en pantalla
plt.show()

print("Proceso completado con exito!")