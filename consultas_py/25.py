import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los equipos con mejor rendimiento en Copas del Mundo
consulta_sql = """
SELECT TOP 5
   e.nombre AS equipo,
   COUNT(DISTINCT p.id_partido) AS partidos,
   SUM(CASE
       WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
       WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
       ELSE 0 END) AS victorias,
   SUM(CASE
       WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
       ELSE p.goles_visita END) AS goles_anotados
FROM equipo e
JOIN partido p ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
GROUP BY e.nombre
ORDER BY victorias DESC, goles_anotados DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando equipos con mejor rendimiento en Mundiales...")
dataframe_mundial = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_mundial) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_mundial[['equipo', 'partidos', 'victorias', 'goles_anotados']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de equipos mas determinantes en Mundiales...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_tabla) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Equipos mas determinantes en Copas del Mundo', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS DOBLES (Victorias y Goles)
# --------------------------------------------------
lista_equipos = dataframe_mundial['equipo'].tolist()
lista_victorias = dataframe_mundial['victorias'].tolist()
lista_goles = dataframe_mundial['goles_anotados'].tolist()
posiciones_x = range(len(lista_equipos))

ancho_barra = 0.35

# Barras para victorias (azul)
barras_victorias = grafica_barras.bar(
    [i - ancho_barra/2 for i in posiciones_x],
    lista_victorias,
    width=ancho_barra,
    label='Victorias',
    color='#1f77b4',
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

# Barras para goles (naranja)
barras_goles = grafica_barras.bar(
    [i + ancho_barra/2 for i in posiciones_x],
    lista_goles,
    width=ancho_barra,
    label='Goles anotados',
    color='#ff7f0e',
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica_barras.set_xlabel('Equipo')
grafica_barras.set_ylabel('Cantidad')
grafica_barras.set_title('Victorias y goles por equipo')
grafica_barras.set_xticks(posiciones_x)
grafica_barras.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')
grafica_barras.legend()

# Agregar valores encima de las barras
for barra, valor in zip(barras_victorias, lista_victorias):
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,
        barra.get_height() + 0.5,
        str(int(valor)),
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='bold'
    )

for barra, valor in zip(barras_goles, lista_goles):
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,
        barra.get_height() + 0.5,
        str(int(valor)),
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA DERECHA: TABLA DE RENDIMIENTO
# --------------------------------------------------
grafica_tabla.axis('off')
grafica_tabla.set_title('Estadisticas detalladas', fontsize=12, fontweight='bold')

# Calcular promedio de goles por partido
dataframe_mundial['goles_por_partido'] = dataframe_mundial['goles_anotados'] / dataframe_mundial['partidos']
dataframe_mundial['victorias_por_partido'] = dataframe_mundial['victorias'] / dataframe_mundial['partidos']

# Preparar datos para tabla
datos_tabla = []
for i, fila in dataframe_mundial.iterrows():
    datos_tabla.append([
        fila['equipo'][:15],
        int(fila['partidos']),
        int(fila['victorias']),
        int(fila['goles_anotados']),
        f"{fila['victorias_por_partido']:.2f}",
        f"{fila['goles_por_partido']:.2f}"
    ])

# Crear la tabla
tabla = grafica_tabla.table(
    cellText=datos_tabla,
    colLabels=['Equipo', 'Partidos', 'Victorias', 'Goles', 'Vic/Part', 'Gol/Part'],
    loc='center',
    cellLoc='center',
    colWidths=[0.25, 0.15, 0.15, 0.15, 0.15, 0.15]
)

# Dar formato a la tabla
tabla.auto_set_font_size(False)
tabla.set_fontsize(9)
tabla.scale(1.2, 1.5)

# Colorear la fila del primer lugar
for j in range(len(datos_tabla[0])):
    tabla[(1, j)].set_facecolor('#ffffcc')  # amarillo claro
    tabla[(1, j)].set_text_props(weight='bold')

# Colorear filas alternadas
for i in range(2, len(datos_tabla) + 1):
    if i % 2 == 0:
        for j in range(len(datos_tabla[0])):
            tabla[(i, j)].set_facecolor('#f0f0f0')

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '25.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")