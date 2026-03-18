import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca las finales con mas goles en Mundiales y Champions
consulta_sql = """
SELECT TOP 5
    el.nombre AS equipo_local,
    ev2.nombre AS equipo_visita,
    p.goles_local,
    p.goles_visita,
    (p.goles_local + p.goles_visita) AS total_goles,
    c.nombre AS competicion,
    t.anio_inicio AS temporada
FROM partido p
JOIN equipo el ON p.id_equipo_local = el.id_equipo
JOIN equipo ev2 ON p.id_equipo_visita = ev2.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN temporada t ON p.id_temporada = t.id_temporada
WHERE p.fase = 'Final'
  AND c.nombre IN ('FIFA World Cup', 'Champions League')
ORDER BY total_goles DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando finales con mas goles...")
dataframe_finales = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_finales) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_finales[['equipo_local', 'equipo_visita', 'total_goles', 'competicion', 'temporada']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de finales con mas goles...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_tabla) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Finales con mas goles en la historia', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS DE GOLES TOTALES
# --------------------------------------------------
# Crear etiquetas para las barras (local vs visitante)
etiquetas = []
for i, fila in dataframe_finales.iterrows():
    etiqueta = f"{fila['equipo_local']}\nvs\n{fila['equipo_visita']}\n{fila['temporada']}"
    etiquetas.append(etiqueta)

lista_goles_local = dataframe_finales['goles_local'].tolist()
lista_goles_visit = dataframe_finales['goles_visita'].tolist()
lista_total = dataframe_finales['total_goles'].tolist()
posiciones_x = range(len(etiquetas))

# Ancho de las barras
ancho_barra = 0.35

# Barras para goles locales
barras_local = grafica_barras.bar(
    [i - ancho_barra/2 for i in posiciones_x],
    lista_goles_local,
    width=ancho_barra,
    label='Goles local',
    color='#1f77b4',
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

# Barras para goles visitantes
barras_visit = grafica_barras.bar(
    [i + ancho_barra/2 for i in posiciones_x],
    lista_goles_visit,
    width=ancho_barra,
    label='Goles visitante',
    color='#ff7f0e',
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica_barras.set_xlabel('Final')
grafica_barras.set_ylabel('Goles')
grafica_barras.set_title('Goles por equipo en cada final')
grafica_barras.set_xticks(posiciones_x)
grafica_barras.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=9)
grafica_barras.legend()
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el total de goles encima de las barras apiladas
for i, total in enumerate(lista_total):
    grafica_barras.text(
        i,
        total + 0.3,
        f'Total: {total}',
        ha='center',
        fontsize=9,
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA DERECHA: TABLA CON DETALLES
# --------------------------------------------------
grafica_tabla.axis('off')
grafica_tabla.set_title('Detalle de las finales', fontsize=12, fontweight='bold')

# Crear datos para la tabla
datos_tabla = []
for i, fila in dataframe_finales.iterrows():
    marcador = f"{int(fila['goles_local'])} - {int(fila['goles_visita'])}"
    datos_tabla.append([
        f"{fila['equipo_local']} vs {fila['equipo_visita']}",
        fila['competicion'],
        fila['temporada'],
        marcador,
        int(fila['total_goles'])
    ])

# Crear la tabla
tabla = grafica_tabla.table(
    cellText=datos_tabla,
    colLabels=['Partido', 'Competicion', 'Año', 'Marcador', 'Total'],
    loc='center',
    cellLoc='center',
    colWidths=[0.3, 0.2, 0.1, 0.15, 0.1]
)

# Dar formato a la tabla
tabla.auto_set_font_size(False)
tabla.set_fontsize(9)
tabla.scale(1.2, 1.5)

# Colorear la fila del primer lugar (mas goles)
for j in range(len(datos_tabla[0])):
    celda = tabla[(1, j)]
    celda.set_facecolor('#ffffcc')  # amarillo claro
    celda.set_text_props(weight='bold')

# Colorear las filas alternadas para mejor lectura
for i in range(2, len(datos_tabla) + 1):
    if i % 2 == 0:  # filas pares
        for j in range(len(datos_tabla[0])):
            tabla[(i, j)].set_facecolor('#f5f5f5')

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '6.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")