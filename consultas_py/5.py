import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los jugadores con mejor promedio de goles en mundiales
consulta_sql = """
SELECT TOP 5
    j.nombre AS NombreJugador,
    COUNT(g.id_evento) AS Goles,
    COUNT(DISTINCT p.id_partido) AS PartidosJugados,
    (CAST(COUNT(g.id_evento) AS FLOAT) / NULLIF(COUNT(DISTINCT p.id_partido), 0)) AS PromedioGoles
FROM jugador j
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN gol g ON ev.id_evento = g.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
WHERE p.id_competicion = (SELECT id_competicion FROM competicion WHERE nombre = 'FIFA World Cup')
GROUP BY j.nombre
ORDER BY PromedioGoles DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando jugadores con mejor promedio de goles en mundiales...")
dataframe_goleadores = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_goleadores) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_goleadores[['NombreJugador', 'Goles', 'PartidosJugados', 'PromedioGoles']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de promedio de goles en mundiales...")

# Crear una sola grafica de barras horizontales
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Jugadores con mejor promedio de goles en Copas del Mundo', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# PREPARAR DATOS
# --------------------------------------------------
lista_jugadores = dataframe_goleadores['NombreJugador'].tolist()
lista_promedios = dataframe_goleadores['PromedioGoles'].tolist()
lista_goles = dataframe_goleadores['Goles'].tolist()
lista_partidos = dataframe_goleadores['PartidosJugados'].tolist()

# Invertir para que el mejor aparezca arriba
lista_jugadores.reverse()
lista_promedios.reverse()
lista_goles.reverse()
lista_partidos.reverse()

posiciones_y = range(len(lista_jugadores))

# --------------------------------------------------
# BARRAS HORIZONTALES
# --------------------------------------------------
# Colores basicos de matplotlib
colores = ['darkblue', 'blue', 'royalblue', 'cornflowerblue', 'lightblue']
colores.reverse()  # para que el mejor tenga el color mas oscuro

barras = grafica.barh(
    posiciones_y,
    lista_promedios,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Promedio de goles por partido')
grafica.set_ylabel('Jugador')
grafica.set_title('Top 5 goleadores mas efectivos en mundiales')
grafica.set_yticks(posiciones_y)
grafica.set_yticklabels(lista_jugadores)
grafica.grid(axis='x', alpha=0.3, linestyle='--')

# Agregar el valor exacto al final de cada barra
for i, (barra, promedio, goles, partidos) in enumerate(zip(barras, lista_promedios, lista_goles, lista_partidos)):
    ancho = barra.get_width()
    grafica.text(
        ancho + 0.05,
        i,
        f'{promedio:.2f}',
        va='center',
        fontsize=10,
        fontweight='bold'
    )
    
    # Informacion adicional dentro de la barra si hay espacio
    if ancho > 0.3:
        grafica.text(
            ancho/2,
            i,
            f'{int(goles)} gol/{int(partidos)} part',
            va='center',
            ha='center',
            color='white',
            fontweight='bold',
            fontsize=8
        )

# Agregar linea de referencia (1 gol por partido)
grafica.axvline(
    x=1.0,
    color='red',
    linestyle='--',
    linewidth=2,
    alpha=0.7,
    label='1 gol por partido'
)
grafica.legend()

# --------------------------------------------------
# TABLA DE DATOS
# --------------------------------------------------
# Crear texto de tabla
texto_tabla = "Jugador                    Goles  Part  Promedio\n"
texto_tabla += "-" * 45 + "\n"

# Usar datos originales (sin invertir) para la tabla
for i, fila in dataframe_goleadores.iterrows():
    texto_tabla += f"{fila['NombreJugador'][:25]:25} {int(fila['Goles']):5} {int(fila['PartidosJugados']):5} {fila['PromedioGoles']:8.2f}\n"

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
nombre_archivo = '5.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")