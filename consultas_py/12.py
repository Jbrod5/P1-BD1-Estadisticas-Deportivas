import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los jugadores con mas asistencias en Mundiales
consulta_sql = """
SELECT TOP 10
    j.nombre AS jugador,
    COUNT(g.id_evento) AS total_asistencias,
    COUNT(DISTINCT p.id_partido) AS partidos_jugados,
    CAST(COUNT(g.id_evento) AS FLOAT) /
        NULLIF(COUNT(DISTINCT p.id_partido), 0) AS promedio_asistencias
FROM jugador j
JOIN gol g ON g.id_asistente = j.id_jugador
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
GROUP BY j.nombre
ORDER BY total_asistencias DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando jugadores con mas asistencias en Mundiales...")
dataframe_asistencias = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_asistencias) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_asistencias[['jugador', 'total_asistencias', 'partidos_jugados', 'promedio_asistencias']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de jugadores con mas asistencias...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_promedio) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Jugadores con mas asistencias en Copas del Mundo', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS DE ASISTENCIAS TOTALES
# --------------------------------------------------
lista_jugadores = dataframe_asistencias['jugador'].tolist()
lista_asistencias = dataframe_asistencias['total_asistencias'].tolist()
posiciones_x = range(len(lista_jugadores))

# Colores en tonos verdes (creatividad)
colores = ['#006400', '#228b22', '#32cd32', '#66cdaa', '#90ee90', 
           '#a0d6b4', '#b0e0e6', '#add8e6', '#b0c4de', '#c0c0c0']
colores = colores[:len(lista_jugadores)]

barras = grafica_barras.bar(
    posiciones_x,
    lista_asistencias,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica_barras.set_xlabel('Jugador')
grafica_barras.set_ylabel('Total de asistencias')
grafica_barras.set_title('Asistencias totales')
grafica_barras.set_xticks(posiciones_x)
grafica_barras.set_xticklabels(lista_jugadores, rotation=45, ha='right', fontsize=8)
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_asistencias)):
    altura = barra.get_height()
    grafica_barras.text(
        barra.get_x() + barra.get_width()/2.,  # centro de la barra
        altura + 0.1,                            # un poco arriba
        f'{int(valor)}',
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA DERECHA: BARRAS DE PROMEDIO POR PARTIDO
# --------------------------------------------------
lista_promedios = dataframe_asistencias['promedio_asistencias'].tolist()

barras_prom = grafica_promedio.bar(
    posiciones_x,
    lista_promedios,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica_promedio.set_xlabel('Jugador')
grafica_promedio.set_ylabel('Promedio de asistencias por partido')
grafica_promedio.set_title('Promedio de asistencias')
grafica_promedio.set_xticks(posiciones_x)
grafica_promedio.set_xticklabels(lista_jugadores, rotation=45, ha='right', fontsize=8)
grafica_promedio.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor, partidos) in enumerate(zip(barras_prom, lista_promedios, dataframe_asistencias['partidos_jugados'])):
    altura = barra.get_height()
    grafica_promedio.text(
        barra.get_x() + barra.get_width()/2.,  # centro de la barra
        altura + 0.02,                           # un poco arriba
        f'{valor:.2f}\n({partidos} partidos)',    # promedio y partidos jugados
        ha='center',
        va='bottom',
        fontsize=7,
        fontweight='bold'
    )

# --------------------------------------------------
# AGREGAR LINEA DE PROMEDIO GENERAL
# --------------------------------------------------
if len(lista_promedios) > 1:
    promedio_general = sum(lista_promedios) / len(lista_promedios)
    grafica_promedio.axhline(
        y=promedio_general,
        color='red',
        linestyle='--',
        linewidth=2,
        alpha=0.7,
        label=f'Promedio general: {promedio_general:.2f}'
    )
    grafica_promedio.legend()

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '12.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")