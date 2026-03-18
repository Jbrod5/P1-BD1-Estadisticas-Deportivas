import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca el jugador con mas goles en general
consulta_sql = """
SELECT TOP 5
   j.nombre AS Jugador,
   COUNT(g.id_evento) AS TotalGoles,
   c.nombre AS Competicion
FROM jugador j
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN gol g ON ev.id_evento = g.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
GROUP BY j.nombre, c.nombre
ORDER BY TotalGoles DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando jugadores con mas goles...")
dataframe_goleadores = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_goleadores) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_goleadores.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de maximo goleador...")

# Crear una sola grafica de barras
figura, grafica = matplotlib.pyplot.subplots(figsize=(12, 6))
figura.suptitle('Jugadores con mas goles', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# PREPARAR DATOS
# --------------------------------------------------
# Crear etiquetas combinadas (jugador + competicion)
etiquetas = []
for i, fila in dataframe_goleadores.iterrows():
    etiquetas.append(f"{fila['Jugador']}\n({fila['Competicion']})")

lista_goles = dataframe_goleadores['TotalGoles'].tolist()
posiciones_x = range(len(etiquetas))

# Colores por competicion
colores = []
for comp in dataframe_goleadores['Competicion']:
    if 'Champions' in comp:
        colores.append('#1f77b4')  # azul para Champions
    elif 'World Cup' in comp:
        colores.append('#2ca02c')  # verde para Mundial
    elif 'Liga' in comp:
        colores.append('#ff7f0e')  # naranja para La Liga
    else:
        colores.append('#9467bd')  # morado para otras

# Barras
barras = grafica.bar(
    posiciones_x,
    lista_goles,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Jugador')
grafica.set_ylabel('Total de goles')
grafica.set_title('Top 5 goleadores')
grafica.set_xticks(posiciones_x)
grafica.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=9)
grafica.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_goles)):
    altura = barra.get_height()
    grafica.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 0.3,
        f'{int(valor)}',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold'
    )

# Agregar leyenda manual
from matplotlib.patches import Patch
elementos_leyenda = [
    Patch(facecolor='#1f77b4', label='Champions League'),
    Patch(facecolor='#2ca02c', label='FIFA World Cup'),
    Patch(facecolor='#ff7f0e', label='La Liga'),
    Patch(facecolor='#9467bd', label='Otras')
]
grafica.legend(handles=elementos_leyenda, loc='upper right')

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '11.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")