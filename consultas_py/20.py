import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
consulta_sql = """
SELECT
    p.fase,
    p.fecha,
    er.nombre AS rival,
    p.goles_local AS goles_arg,
    p.goles_visita AS goles_rival,
    ep.posesion,
    ep.pases_completados,
    ep.tiros_a_puerta,
    CAST(ep.pases_completados AS FLOAT) /
        NULLIF(ep.pases_totales, 0) * 100 AS eficiencia_pases
FROM partido p
JOIN equipo ea ON ea.nombre = 'Argentina'
JOIN equipo er ON er.id_equipo = p.id_equipo_visita
JOIN estadistica_partido ep ON ep.id_partido = p.id_partido AND ep.id_equipo = ea.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN temporada t ON p.id_temporada = t.id_temporada
WHERE c.nombre = 'FIFA World Cup'
  AND t.anio_inicio = 2022
  AND p.id_equipo_local = ea.id_equipo
ORDER BY p.fecha;
"""

# 3. EJECUTAR CONSULTA
print("Buscando datos de Argentina en el Mundial 2022...")
dataframe_partidos = pandas.read_sql(consulta_sql, motor_base_datos)

if len(dataframe_partidos) == 0:
    print("No se encontraron datos para Argentina en el Mundial 2022")
    exit()

print(f"Se encontraron {len(dataframe_partidos)} partidos")
print(dataframe_partidos[['fase', 'rival', 'goles_arg', 'goles_rival', 'posesion']].to_string(index=False))

# 4. CREAR LA FIGURA CON TRES GRAFICAS
# subplots(3,1) crea tres graficas apiladas verticalmente
figura, (grafica_uno, grafica_dos, grafica_tres) = matplotlib.pyplot.subplots(3, 1, figsize=(10, 12))
figura.suptitle('Camino de Argentina hacia el titulo - Mundial 2022', fontsize=14, fontweight='bold')

# Lista de fases para el eje x
lista_fases = dataframe_partidos['fase'].tolist()
posiciones_x = range(len(lista_fases))

# --------------------------------------------------
# GRAFICA 1: GOLES (barras)
# --------------------------------------------------
ancho_de_barra = 0.35  # separacion entre barras de Argentina y rival

# Barras para goles de Argentina (azul)
grafica_uno.bar(
    [i - ancho_de_barra/2 for i in posiciones_x], 
    dataframe_partidos['goles_arg'], 
    width=ancho_de_barra, 
    label='Argentina', 
    color='#6a9fb5'
)

# Barras para goles del rival (rojo)
grafica_uno.bar(
    [i + ancho_de_barra/2 for i in posiciones_x], 
    dataframe_partidos['goles_rival'], 
    width=ancho_de_barra, 
    label='Rival', 
    color='#e9896a'
)

grafica_uno.set_ylabel('Goles')
grafica_uno.set_title('Goles marcados y recibidos por partido')
grafica_uno.set_xticks(posiciones_x)
grafica_uno.set_xticklabels(lista_fases, rotation=45, ha='right')  # rotacion para que se lean mejor :D
grafica_uno.legend()
grafica_uno.grid(True, alpha=0.3, linestyle='--')  # lineas de cuadricula suaves

# Agrega el resultado como texto encima de las barras
for indice, fila in dataframe_partidos.iterrows():
    resultado = f"{fila['goles_arg']}-{fila['goles_rival']}"
    valor_maximo = max(fila['goles_arg'], fila['goles_rival'])
    grafica_uno.text(
        indice, 
        valor_maximo + 0.1, 
        resultado, 
        ha='center', 
        fontsize=9, 
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA 2: POSESION (linea)
# --------------------------------------------------
grafica_dos.plot(
    posiciones_x, 
    dataframe_partidos['posesion'], 
    marker='o',          # circulos en cada punto :3
    linewidth=2, 
    color='#2e8b57', 
    markersize=8
)

grafica_dos.set_ylabel('Posesion %')
grafica_dos.set_title('Posesion de balon por partido')
grafica_dos.set_xticks(posiciones_x)
grafica_dos.set_xticklabels(lista_fases, rotation=45, ha='right')
grafica_dos.grid(True, alpha=0.3, linestyle='--')

# Agrega los valores en los puntos
for indice, posesion in enumerate(dataframe_partidos['posesion']):
    grafica_dos.annotate(
        f"{posesion:.0f}%", 
        (indice, posesion), 
        textcoords="offset points", 
        xytext=(0, 10),    # desplaza el texto 10 puntos arriba :3
        ha='center', 
        fontsize=9
    )

# --------------------------------------------------
# GRAFICA 3: EFICIENCIA Y TIROS (lineas dobles)
# --------------------------------------------------
# Linea de eficiencia en pases (color naranja)
grafica_tres.plot(
    posiciones_x, 
    dataframe_partidos['eficiencia_pases'], 
    marker='s',          # marcador cuadrado
    linewidth=2, 
    color='#b8860b', 
    label='Eficiencia pases %', 
    markersize=8
)

# Linea de tiros a puerta (color rojo oscuro)
grafica_tres.plot(
    posiciones_x, 
    dataframe_partidos['tiros_a_puerta'], 
    marker='^',          # marcador triangulo
    linewidth=2, 
    color='#8b1a1a', 
    label='Tiros a puerta', 
    markersize=8
)

grafica_tres.set_ylabel('Porcentaje / Cantidad')
grafica_tres.set_title('Eficiencia en pases y tiros a puerta')
grafica_tres.set_xticks(posiciones_x)
grafica_tres.set_xticklabels(lista_fases, rotation=45, ha='right')
grafica_tres.legend()
grafica_tres.grid(True, alpha=0.3, linestyle='--')

# --------------------------------------------------
# Ajustes finales
# --------------------------------------------------
matplotlib.pyplot.tight_layout()  # ajusta espacios para que no se sobrepongan supongo xd

# 5. GUARDAR LA GRAFICA
nombre_archivo = '20.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

print("Listo!")