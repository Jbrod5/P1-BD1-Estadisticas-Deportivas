import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL CORREGIDA
# Busca jugadores con mejor promedio de goles en Mundiales (mínimo 500 minutos)
consulta_sql = """
SELECT TOP 5
    j.nombre AS NombreJugador,
    COUNT(g.id_evento) AS Goles,
    SUM(aj.minuto_fin - aj.minuto_inicio) AS MinutosJugados,
    (CAST(COUNT(g.id_evento) AS FLOAT) / 
        NULLIF(SUM(aj.minuto_fin - aj.minuto_inicio), 0) * 90) AS GolesPor90Minutos
FROM jugador j
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN gol g ON ev.id_evento = g.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN alineacion a ON p.id_partido = a.id_partido AND a.id_equipo = ev.id_equipo
JOIN alineacion_jugador aj ON a.id_alineacion = aj.id_alineacion AND aj.id_jugador = j.id_jugador
WHERE c.nombre = 'FIFA World Cup'
GROUP BY j.nombre
HAVING SUM(aj.minuto_fin - aj.minuto_inicio) >= 500
ORDER BY GolesPor90Minutos DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando jugadores con mejor promedio de goles en Mundiales...")
dataframe_goleadores = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_goleadores) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_goleadores[['NombreJugador', 'Goles', 'MinutosJugados', 'GolesPor90Minutos']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de eficiencia goleadora...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_tabla) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Jugadores con mejor promedio de goles en Mundiales (minimo 500 minutos)', 
                fontsize=12, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS DE GOLES POR 90 MINUTOS
# --------------------------------------------------
lista_jugadores = dataframe_goleadores['NombreJugador'].tolist()
lista_promedios = dataframe_goleadores['GolesPor90Minutos'].tolist()
lista_goles = dataframe_goleadores['Goles'].tolist()
lista_minutos = dataframe_goleadores['MinutosJugados'].tolist()
posiciones_x = range(len(lista_jugadores))

# Colores degradados (mas oscuro el que tiene mejor promedio)
colores = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6']

barras = grafica_barras.bar(
    posiciones_x,
    lista_promedios,
    color=colores[:len(lista_jugadores)],
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica_barras.set_xlabel('Jugador')
grafica_barras.set_ylabel('Goles por cada 90 minutos')
grafica_barras.set_title('Eficiencia goleadora')
grafica_barras.set_xticks(posiciones_x)
grafica_barras.set_xticklabels(lista_jugadores, rotation=45, ha='right', fontsize=9)
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor, goles, minutos) in enumerate(zip(barras, lista_promedios, lista_goles, lista_minutos)):
    altura = barra.get_height()
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,  # centro de la barra
        altura + 0.05,                          # un poco arriba
        f'{valor:.2f}',                          # promedio con 2 decimales
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='bold'
    )
    
    # Informacion adicional en la base de la barra
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,
        0.1,
        f'{int(goles)} goles\n{int(minutos)} min',
        ha='center',
        va='bottom',
        fontsize=7,
        color='white',
        fontweight='bold'
    )

# Agregar linea de referencia (1 gol por partido = 1.0)
grafica_barras.axhline(
    y=1.0,
    color='red',
    linestyle='--',
    linewidth=1.5,
    alpha=0.7,
    label='1 gol por partido'
)
grafica_barras.legend()

# --------------------------------------------------
# GRAFICA DERECHA: TABLA DE DATOS
# --------------------------------------------------
grafica_tabla.axis('off')
grafica_tabla.set_title('Detalle de eficiencia', fontsize=12, fontweight='bold')

# Preparar datos para la tabla
datos_tabla = []
for i, fila in dataframe_goleadores.iterrows():
    datos_tabla.append([
        fila['NombreJugador'],
        int(fila['Goles']),
        int(fila['MinutosJugados']),
        f"{fila['MinutosJugados']/90:.1f}",
        f"{fila['GolesPor90Minutos']:.3f}"
    ])

# Crear la tabla
tabla = grafica_tabla.table(
    cellText=datos_tabla,
    colLabels=['Jugador', 'Goles', 'Minutos', 'Partidos\nequival', 'G/90\'\''],
    loc='center',
    cellLoc='center',
    colWidths=[0.3, 0.15, 0.15, 0.15, 0.15]
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
nombre_archivo = '5.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")