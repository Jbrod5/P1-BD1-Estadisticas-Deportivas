import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca el jugador mas determinante en UCL 2010-2020
consulta_sql = """
SELECT TOP 5
    j.nombre AS jugador,
    COUNT(DISTINCT g.id_evento) AS goles,
    COUNT(DISTINCT g2.id_evento) AS asistencias,
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS pases_completados,
    COUNT(DISTINCT g.id_evento) * 10 +
    COUNT(DISTINCT g2.id_evento) * 7 +
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS score_total
FROM jugador j
JOIN evento ev ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
JOIN temporada t ON p.id_temporada = t.id_temporada
JOIN competicion c ON p.id_competicion = c.id_competicion
LEFT JOIN gol g ON g.id_evento = ev.id_evento
LEFT JOIN gol g2 ON g2.id_asistente = j.id_jugador
LEFT JOIN pase pa ON pa.id_evento = ev.id_evento
WHERE c.nombre = 'Champions League'
  AND t.anio_inicio BETWEEN 2010 AND 2020
GROUP BY j.nombre
ORDER BY score_total DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando jugador mas determinante en UCL 2010-2020...")
dataframe_jugadores = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_jugadores) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_jugadores[['jugador', 'goles', 'asistencias', 'pases_completados', 'score_total']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de jugador mas determinante...")

# Crear una sola grafica de barras horizontales
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Jugadores mas determinantes en Champions League (2010-2020)', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# PREPARAR DATOS PARA BARRAS APILADAS
# --------------------------------------------------
lista_jugadores = dataframe_jugadores['jugador'].tolist()
lista_goles = dataframe_jugadores['goles'].tolist()
lista_asistencias = dataframe_jugadores['asistencias'].tolist()
lista_pases = [p/100 for p in dataframe_jugadores['pases_completados'].tolist()]  # dividir para escala
lista_score = dataframe_jugadores['score_total'].tolist()

# Para barras apiladas horizontales, necesitamos posiciones en y
posiciones_y = range(len(lista_jugadores))

# Crear barras apiladas
barra_goles = grafica.barh(
    posiciones_y,
    [g*10 for g in lista_goles],  # goles ponderados
    color='#1f77b4',
    label='Goles (x10)'
)

barra_asistencias = grafica.barh(
    posiciones_y,
    [a*7 for a in lista_asistencias],  # asistencias ponderadas
    left=[g*10 for g in lista_goles],
    color='#ff7f0e',
    label='Asistencias (x7)'
)

barra_pases = grafica.barh(
    posiciones_y,
    lista_pases,
    left=[g*10 + a*7 for g, a in zip(lista_goles, lista_asistencias)],
    color='#2ca02c',
    label='Pases (/100)'
)

# Configurar la grafica
grafica.set_xlabel('Puntaje total')
grafica.set_ylabel('Jugador')
grafica.set_title('Top 5 jugadores mas determinantes (goles x10 + asistencias x7 + pases/100)')
grafica.set_yticks(posiciones_y)
grafica.set_yticklabels(lista_jugadores)
grafica.grid(axis='x', alpha=0.3, linestyle='--')
grafica.legend()

# Agregar el score total al final de cada barra
for indice, (barra, score) in enumerate(zip(barra_goles, lista_score)):
    # Calcular el final de la barra apilada
    final_x = barra.get_width()
    for barra_a in barra_asistencias:
        if barra_a.get_y() == barra.get_y():
            final_x += barra_a.get_width()
    for barra_p in barra_pases:
        if barra_p.get_y() == barra.get_y():
            final_x += barra_p.get_width()
    
    grafica.text(
        final_x + 5,
        barra.get_y() + barra.get_height()/2,
        f'Score: {int(score)}',
        va='center',
        fontsize=9,
        fontweight='bold'
    )

# Agregar etiquetas con los numeros dentro de las barras
for i, (goles, asis, pases) in enumerate(zip(lista_goles, lista_asistencias, lista_pases)):
    # Goles
    if goles > 0:
        grafica.text(
            goles*5, i,
            f'{int(goles)}',
            va='center',
            ha='center',
            color='white',
            fontweight='bold'
        )
    # Asistencias
    if asis > 0:
        grafica.text(
            goles*10 + asis*3.5, i,
            f'{int(asis)}',
            va='center',
            ha='center',
            color='white',
            fontweight='bold'
        )
    # Pases (en millones)
    if pases*100 > 0:
        grafica.text(
            goles*10 + asis*7 + pases/2, i,
            f'{int(pases*100)}k',
            va='center',
            ha='center',
            color='white',
            fontweight='bold',
            fontsize=8
        )

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '21.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")