import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los equipos con mas goles en los primeros 10 minutos
consulta_sql = """
SELECT TOP 5
    e.nombre AS equipo,
    c.nombre AS competicion,
    COUNT(g.id_evento) AS goles_primeros_10,
    COUNT(DISTINCT p.id_partido) AS partidos_jugados,
    CAST(COUNT(g.id_evento) AS FLOAT) /
        NULLIF(COUNT(DISTINCT p.id_partido), 0) AS promedio_goles_inicio
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE ev.minuto <= 10
  AND c.nombre IN ('La Liga', 'Champions League')
GROUP BY e.nombre, c.nombre
ORDER BY promedio_goles_inicio DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando equipos con mas goles en los primeros 10 minutos...")
dataframe_goles_tempranos = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_goles_tempranos) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_goles_tempranos[['equipo', 'competicion', 'goles_primeros_10', 'partidos_jugados', 'promedio_goles_inicio']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de goles en los primeros 10 minutos...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_tabla) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Equipos con mas goles en los primeros 10 minutos', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS DE PROMEDIO POR COMPETICION
# --------------------------------------------------
# Separar datos por competicion para mejor visualizacion
dataframe_laliga = dataframe_goles_tempranos[dataframe_goles_tempranos['competicion'] == 'La Liga'].head(3)
dataframe_champions = dataframe_goles_tempranos[dataframe_goles_tempranos['competicion'] == 'Champions League'].head(3)

# Combinar para la grafica (maximo 3 de cada una)
lista_equipos = dataframe_laliga['equipo'].tolist() + dataframe_champions['equipo'].tolist()
lista_promedios = dataframe_laliga['promedio_goles_inicio'].tolist() + dataframe_champions['promedio_goles_inicio'].tolist()
lista_competicion = ['La Liga'] * len(dataframe_laliga) + ['Champions'] * len(dataframe_champions)
lista_goles = dataframe_laliga['goles_primeros_10'].tolist() + dataframe_champions['goles_primeros_10'].tolist()
lista_partidos = dataframe_laliga['partidos_jugados'].tolist() + dataframe_champions['partidos_jugados'].tolist()

posiciones_x = range(len(lista_equipos))

# Colores: azul para La Liga, rojo para Champions
colores_barras = []
for comp in lista_competicion:
    if comp == 'La Liga':
        colores_barras.append('#1f77b4')  # azul
    else:
        colores_barras.append('#d62728')  # rojo

barras = grafica_barras.bar(
    posiciones_x,
    lista_promedios,
    color=colores_barras,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica_barras.set_xlabel('Equipo')
grafica_barras.set_ylabel('Promedio de goles por partido')
grafica_barras.set_title('Promedio de goles en primeros 10 minutos')
grafica_barras.set_xticks(posiciones_x)
grafica_barras.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar los valores y detalles en las barras
for indice, (barra, promedio, goles, partidos, comp) in enumerate(zip(barras, lista_promedios, lista_goles, lista_partidos, lista_competicion)):
    altura = barra.get_height()
    
    # Valor del promedio
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 0.02,
        f'{promedio:.2f}',
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='bold'
    )
    
    # Detalle de goles y partidos (mas pequeño)
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,
        altura - 0.05,
        f'({int(goles)}/{int(partidos)})',
        ha='center',
        va='top',
        fontsize=7,
        color='white',
        fontweight='bold'
    )

# Crear una leyenda manual
from matplotlib.patches import Patch
elementos_leyenda = [
    Patch(facecolor='#1f77b4', label='La Liga'),
    Patch(facecolor='#d62728', label='Champions League')
]
grafica_barras.legend(handles=elementos_leyenda, loc='upper right')

# --------------------------------------------------
# GRAFICA DERECHA: TABLA DE DATOS
# --------------------------------------------------
grafica_tabla.axis('off')
grafica_tabla.set_title('Detalle de goles tempranos', fontsize=12, fontweight='bold')

# Preparar datos para la tabla
datos_tabla = []
for i, fila in dataframe_goles_tempranos.iterrows():
    datos_tabla.append([
        fila['equipo'],
        fila['competicion'],
        int(fila['goles_primeros_10']),
        int(fila['partidos_jugados']),
        f"{fila['promedio_goles_inicio']:.3f}"
    ])

# Crear la tabla
tabla = grafica_tabla.table(
    cellText=datos_tabla,
    colLabels=['Equipo', 'Competicion', 'Goles', 'Partidos', 'Promedio'],
    loc='center',
    cellLoc='center',
    colWidths=[0.25, 0.2, 0.15, 0.15, 0.15]
)

# Dar formato a la tabla
tabla.auto_set_font_size(False)
tabla.set_fontsize(9)
tabla.scale(1.2, 1.5)

# Colorear filas por competicion
for i in range(len(datos_tabla)):
    if datos_tabla[i][1] == 'La Liga':
        for j in range(len(datos_tabla[0])):
            tabla[(i+1, j)].set_facecolor('#e6f0fa')  # azul clarito
    else:
        for j in range(len(datos_tabla[0])):
            tabla[(i+1, j)].set_facecolor('#fae6e6')  # rojo clarito

# Resaltar el primer lugar
for j in range(len(datos_tabla[0])):
    tabla[(1, j)].set_facecolor('#ffffcc')  # amarillo claro
    tabla[(1, j)].set_text_props(weight='bold')

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '32.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")