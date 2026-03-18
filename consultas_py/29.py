import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los paises con mas goles en 2018
consulta_sql = """
SELECT TOP 10
   n.nombre AS Pais,
   COUNT(DISTINCT p.id_partido) AS PartidosTotales,
   COUNT(g.id_evento) AS GolesPorNacionalidad
FROM nacionalidad n
JOIN jugador j ON n.id_nacionalidad = j.id_nacionalidad
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
LEFT JOIN gol g ON ev.id_evento = g.id_evento
WHERE YEAR(p.fecha) = 2018
GROUP BY n.nombre
HAVING COUNT(g.id_evento) > 0
ORDER BY GolesPorNacionalidad DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando paises con mas goles en 2018...")
dataframe_paises = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_paises) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_paises.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de paises con mas goles en 2018...")

# Crear una sola grafica de barras horizontales
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Paises con mas goles en 2018', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# PREPARAR DATOS
# --------------------------------------------------
lista_paises = dataframe_paises['Pais'].tolist()
lista_goles = dataframe_paises['GolesPorNacionalidad'].tolist()
lista_partidos = dataframe_paises['PartidosTotales'].tolist()

# Invertir para que el primero aparezca arriba
lista_paises.reverse()
lista_goles.reverse()
lista_partidos.reverse()

posiciones_y = range(len(lista_paises))

# --------------------------------------------------
# BARRAS HORIZONTALES
# --------------------------------------------------
# Colores por rango de goles
colores = []
for goles in lista_goles:
    if goles >= 100:
        colores.append('darkred')
    elif goles >= 50:
        colores.append('red')
    elif goles >= 20:
        colores.append('orange')
    elif goles >= 10:
        colores.append('gold')
    else:
        colores.append('lightblue')

barras = grafica.barh(
    posiciones_y,
    lista_goles,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Cantidad de goles')
grafica.set_ylabel('Pais')
grafica.set_title('Top 10 paises goleadores en 2018')
grafica.set_yticks(posiciones_y)
grafica.set_yticklabels(lista_paises)
grafica.grid(axis='x', alpha=0.3, linestyle='--')

# Agregar el valor exacto al final de cada barra
for i, (barra, goles, partidos) in enumerate(zip(barras, lista_goles, lista_partidos)):
    ancho = barra.get_width()
    grafica.text(
        ancho + 1,
        i,
        f'{int(goles)} goles',
        va='center',
        fontsize=9,
        fontweight='bold'
    )
    
    # Informacion de partidos dentro de la barra si hay espacio
    if ancho > 20:
        grafica.text(
            ancho/2,
            i,
            f'{int(partidos)} part',
            va='center',
            ha='center',
            color='white',
            fontweight='bold',
            fontsize=8
        )

# --------------------------------------------------
# CALCULAR EFECTIVIDAD (goles por partido)
# --------------------------------------------------
dataframe_paises['GolesPorPartido'] = dataframe_paises['GolesPorNacionalidad'] / dataframe_paises['PartidosTotales']

# Agregar segunda grafica de efectividad
figura2, grafica2 = matplotlib.pyplot.subplots(figsize=(10, 4))
figura2.suptitle('Efectividad goleadora por pais (goles por partido) - 2018', 
                 fontsize=14, fontweight='bold')

lista_paises_efec = dataframe_paises['Pais'].tolist()
lista_efectividad = dataframe_paises['GolesPorPartido'].tolist()
posiciones_x = range(len(lista_paises_efec))

barras2 = grafica2.bar(
    posiciones_x,
    lista_efectividad,
    color='green',
    alpha=0.7,
    edgecolor='black',
    linewidth=1
)

grafica2.set_xlabel('Pais')
grafica2.set_ylabel('Goles por partido')
grafica2.set_title('Efectividad goleadora')
grafica2.set_xticks(posiciones_x)
grafica2.set_xticklabels(lista_paises_efec, rotation=45, ha='right')
grafica2.grid(axis='y', alpha=0.3, linestyle='--')

# Valores encima de barras
for barra, valor in zip(barras2, lista_efectividad):
    altura = barra.get_height()
    grafica2.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 0.1,
        f'{valor:.2f}',
        ha='center',
        va='bottom',
        fontsize=8,
        fontweight='bold'
    )

# --------------------------------------------------
# TABLA DE DATOS
# --------------------------------------------------
# Crear texto de tabla
texto_tabla = "Pais                    Goles  Partidos  Efectividad\n"
texto_tabla += "-" * 55 + "\n"

for i, fila in dataframe_paises.iterrows():
    texto_tabla += f"{fila['Pais'][:20]:20} {int(fila['GolesPorNacionalidad']):6} {int(fila['PartidosTotales']):8} {fila['GolesPorPartido']:11.2f}\n"

figura.text(
    0.02, 0.02,
    texto_tabla,
    fontsize=8,
    fontfamily='monospace',
    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.9)
)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LAS GRAFICAS
nombre_archivo1 = '29_goles.png'
matplotlib.pyplot.figure(1)
matplotlib.pyplot.savefig(nombre_archivo1, dpi=300, bbox_inches='tight')
print(f"Grafica de goles guardada como: {nombre_archivo1}")

nombre_archivo2 = '29_efectividad.png'
matplotlib.pyplot.figure(2)
matplotlib.pyplot.savefig(nombre_archivo2, dpi=300, bbox_inches='tight')
print(f"Grafica de efectividad guardada como: {nombre_archivo2}")

matplotlib.pyplot.show()
print("Listo!")