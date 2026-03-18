import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los jugadores con mejor puntuacion en cuartos de final
consulta_sql = """
SELECT TOP 10
   j.nombre AS jugador,
   SUM(CASE WHEN g.id_evento IS NOT NULL THEN 10 ELSE 0 END) AS pts_goles,
   SUM(CASE WHEN g.id_asistente = j.id_jugador THEN 7 ELSE 0 END) AS pts_asistencias,
   SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END) AS pts_pases,
   (SUM(CASE WHEN g.id_evento IS NOT NULL THEN 10 ELSE 0 END) +
    SUM(CASE WHEN g.id_asistente = j.id_jugador THEN 7 ELSE 0 END) +
    SUM(CASE WHEN pa.completado = 1 THEN 1 ELSE 0 END)) AS puntuacion_total
FROM jugador j
JOIN evento ev ON ev.id_jugador = j.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
LEFT JOIN gol g ON g.id_evento = ev.id_evento
LEFT JOIN pase pa ON pa.id_evento = ev.id_evento
WHERE p.fase = 'Quarter-finals' 
GROUP BY j.nombre
ORDER BY puntuacion_total DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando jugadores mas determinantes en cuartos de final...")
dataframe_jugadores = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_jugadores) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_jugadores[['jugador', 'pts_goles', 'pts_asistencias', 'pts_pases', 'puntuacion_total']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de puntuacion de jugadores...")

# Crear una sola grafica de barras apiladas
figura, grafica = matplotlib.pyplot.subplots(figsize=(12, 7))
figura.suptitle('Top 10 jugadores mas determinantes en cuartos de final del Mundial', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# PREPARAR DATOS PARA BARRAS APILADAS
# --------------------------------------------------
lista_jugadores = dataframe_jugadores['jugador'].tolist()
lista_goles = dataframe_jugadores['pts_goles'].tolist()
lista_asistencias = dataframe_jugadores['pts_asistencias'].tolist()
lista_pases = dataframe_jugadores['pts_pases'].tolist()
lista_total = dataframe_jugadores['puntuacion_total'].tolist()

# Invertir listas para que el primero aparezca arriba
lista_jugadores.reverse()
lista_goles.reverse()
lista_asistencias.reverse()
lista_pases.reverse()
lista_total.reverse()

posiciones_y = range(len(lista_jugadores))

# Crear barras apiladas horizontales
barra_goles = grafica.barh(
    posiciones_y,
    lista_goles,
    color='red',
    label='Goles (10 pts)'
)

barra_asistencias = grafica.barh(
    posiciones_y,
    lista_asistencias,
    left=lista_goles,
    color='orange',
    label='Asistencias (7 pts)'
)

barra_pases = grafica.barh(
    posiciones_y,
    lista_pases,
    left=[g + a for g, a in zip(lista_goles, lista_asistencias)],
    color='blue',
    label='Pases (1 pt)'
)

grafica.set_xlabel('Puntuacion total')
grafica.set_ylabel('Jugador')
grafica.set_title('Puntuacion por jugador (goles*10 + asistencias*7 + pases)')
grafica.set_yticks(posiciones_y)
grafica.set_yticklabels(lista_jugadores)
grafica.grid(axis='x', alpha=0.3, linestyle='--')
grafica.legend(loc='lower right')

# Agregar el puntaje total al final de cada barra
for i, (goles, asis, pases, total) in enumerate(zip(lista_goles, lista_asistencias, lista_pases, lista_total)):
    # Posicion al final de la barra
    pos_x = goles + asis + pases
    grafica.text(
        pos_x + 5,
        i,
        f'{int(total)}',
        va='center',
        fontsize=9,
        fontweight='bold'
    )
    
    # Agregar los valores de cada componente dentro de las barras
    if goles > 0:
        grafica.text(
            goles/2,
            i,
            f'G:{int(goles/10)}',
            va='center',
            ha='center',
            color='white',
            fontweight='bold',
            fontsize=8
        )
    if asis > 0:
        grafica.text(
            goles + asis/2,
            i,
            f'A:{int(asis/7)}',
            va='center',
            ha='center',
            color='white',
            fontweight='bold',
            fontsize=8
        )
    if pases > 0:
        grafica.text(
            goles + asis + pases/2,
            i,
            f'P:{int(pases)}',
            va='center',
            ha='center',
            color='white',
            fontweight='bold',
            fontsize=7
        )

# --------------------------------------------------
# TABLA DE DETALLE
# --------------------------------------------------
# Crear una tabla pequeña con los datos originales (sin invertir)
datos_tabla = []
for i, fila in dataframe_jugadores.iterrows():
    datos_tabla.append([
        fila['jugador'][:15],
        int(fila['pts_goles']/10) if fila['pts_goles'] > 0 else 0,
        int(fila['pts_asistencias']/7) if fila['pts_asistencias'] > 0 else 0,
        int(fila['pts_pases']),
        int(fila['puntuacion_total'])
    ])

# Crear texto de tabla
texto_tabla = "Jugador           Goles  Asist  Pases  Total\n"
texto_tabla += "-" * 45 + "\n"
for fila in datos_tabla:
    texto_tabla += f"{fila[0][:15]:15} {fila[1]:5} {fila[2]:6} {fila[3]:6} {fila[4]:6}\n"

# Posicionar tabla en la esquina inferior derecha
grafica.text(
    0.98, 0.02,
    texto_tabla,
    transform=grafica.transAxes,
    fontsize=8,
    fontfamily='monospace',
    verticalalignment='bottom',
    horizontalalignment='right',
    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.9)
)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '10.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")