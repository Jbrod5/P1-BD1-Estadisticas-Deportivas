import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Calcula un puntaje para cada equipo basado en su historial en mundiales
# victorias peso 3, goles peso 2, posesion peso 1
consulta_sql = """
SELECT TOP 5
    e.nombre AS equipo,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
        WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
        ELSE 0 END) AS victorias,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
        ELSE p.goles_visita END) AS goles,
    AVG(ep.posesion) AS posesion_promedio,
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
        WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
        ELSE 0 END) * 3 +
    SUM(CASE
        WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
        ELSE p.goles_visita END) * 2 +
    ISNULL(AVG(ep.posesion), 0) AS score_mundial_2026
FROM equipo e
JOIN partido p ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
LEFT JOIN estadistica_partido ep ON ep.id_partido = p.id_partido AND ep.id_equipo = e.id_equipo
WHERE c.nombre = 'FIFA World Cup'
GROUP BY e.nombre
ORDER BY score_mundial_2026 DESC;
"""

# 3. EJECUTAR CONSULTA
print("Calculando probabilidades para el Mundial 2026...")
dataframe_prediccion = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_prediccion) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_prediccion[['equipo', 'victorias', 'goles', 'posesion_promedio', 'score_mundial_2026']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de prediccion para el Mundial 2026...")

# Crear figura con dos subgraficas una al lado de la otra
figura, (grafica_barras, grafica_tabla) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Prediccion: Equipos con mas probabilidades de ganar el Mundial 2026', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS DEL PUNTAJE
# --------------------------------------------------
lista_equipos = dataframe_prediccion['equipo'].tolist()
lista_puntajes = dataframe_prediccion['score_mundial_2026'].tolist()
posiciones_x = range(len(lista_equipos))

# Colores degradados (el primero mas oscuro)
colores = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6']

barras = grafica_barras.bar(
    posiciones_x,
    lista_puntajes,
    color=colores,
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica_barras.set_xlabel('Equipo')
grafica_barras.set_ylabel('Puntaje total')
grafica_barras.set_title('Puntaje basado en historial mundialista')
grafica_barras.set_xticks(posiciones_x)
grafica_barras.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_puntajes)):
    altura = barra.get_height()
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 2,
        f'{valor:.1f}',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA DERECHA: TABLA CON DETALLES
# --------------------------------------------------
# Ocultar los ejes de la tabla
grafica_tabla.axis('off')
grafica_tabla.set_title('Detalle de estadisticas', fontsize=12, fontweight='bold')

# Crear datos para la tabla
datos_tabla = []
for indice, fila in dataframe_prediccion.iterrows():
    datos_tabla.append([
        fila['equipo'],
        int(fila['victorias']),
        int(fila['goles']),
        f"{fila['posesion_promedio']:.1f}%",
        f"{fila['score_mundial_2026']:.1f}"
    ])

# Crear la tabla
tabla = grafica_tabla.table(
    cellText=datos_tabla,
    colLabels=['Equipo', 'Victorias', 'Goles', 'Posesion', 'Puntaje'],
    loc='center',
    cellLoc='center',
    colWidths=[0.2, 0.15, 0.15, 0.15, 0.15]
)

# Dar formato a la tabla
tabla.auto_set_font_size(False)
tabla.set_fontsize(10)
tabla.scale(1.2, 1.5)

# Colorear la fila del primer lugar
for j in range(len(datos_tabla[0])):
    tabla[(1, j)].set_facecolor('#ffffcc')  # amarillo claro para el primero

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '31.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")