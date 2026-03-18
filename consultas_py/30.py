import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca el promedio de goles por competicion en 2018
consulta_sql = """
SELECT
   c.nombre AS Competicion,
   COUNT(DISTINCT p.id_partido) AS TotalPartidos,
   AVG(CAST(p.goles_local + p.goles_visita AS FLOAT)) AS PromedioGoles
FROM competicion c
JOIN partido p ON c.id_competicion = p.id_competicion
WHERE YEAR(p.fecha) = 2018
GROUP BY c.nombre
ORDER BY PromedioGoles DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando promedios de goles por competicion en 2018...")
dataframe_goles = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_goles) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_goles.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de promedios de goles por competicion...")

# Crear una sola grafica de barras
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Promedio de goles por partido en 2018', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# BARRAS DE PROMEDIO DE GOLES
# --------------------------------------------------
lista_competiciones = dataframe_goles['Competicion'].tolist()
lista_promedios = dataframe_goles['PromedioGoles'].tolist()
lista_partidos = dataframe_goles['TotalPartidos'].tolist()
posiciones_x = range(len(lista_competiciones))

# Colores por competicion
colores = []
for comp in lista_competiciones:
    if 'Champions' in comp:
        colores.append('#1f77b4')  # azul
    elif 'World Cup' in comp:
        colores.append('#2ca02c')  # verde
    elif 'Liga' in comp:
        colores.append('#ff7f0e')  # naranja
    else:
        colores.append('#9467bd')  # morado

barras = grafica.bar(
    posiciones_x,
    lista_promedios,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Competicion')
grafica.set_ylabel('Promedio de goles por partido')
grafica.set_title('Comparacion de goles entre competiciones')
grafica.set_xticks(posiciones_x)
grafica.set_xticklabels(lista_competiciones, rotation=45, ha='right')
grafica.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, promedio, partidos) in enumerate(zip(barras, lista_promedios, lista_partidos)):
    altura = barra.get_height()
    grafica.text(
        barra.get_x() + barra.get_width()/2.,  # centro de la barra
        altura + 0.1,                           # un poco arriba
        f'{promedio:.2f}',                       # promedio con 2 decimales
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold'
    )
    
    # Informacion de cantidad de partidos en la base
    grafica.text(
        barra.get_x() + barra.get_width()/2.,
        0.1,
        f'n={partidos}',
        ha='center',
        va='bottom',
        fontsize=8,
        color='white',
        fontweight='bold'
    )

# Agregar linea con el promedio general
promedio_general = sum([p * t for p, t in zip(lista_promedios, lista_partidos)]) / sum(lista_partidos)
grafica.axhline(
    y=promedio_general,
    color='red',
    linestyle='--',
    linewidth=2,
    alpha=0.7,
    label=f'Promedio general: {promedio_general:.2f}'
)
grafica.legend()

# --------------------------------------------------
# TABLA DE DATOS
# --------------------------------------------------
# Crear una tabla pequeña con los datos
datos_tabla = []
for i, fila in dataframe_goles.iterrows():
    datos_tabla.append([
        fila['Competicion'],
        int(fila['TotalPartidos']),
        f"{fila['PromedioGoles']:.2f}"
    ])

# Crear texto de tabla
texto_tabla = "Competicion                    Partidos  Promedio\n"
texto_tabla += "-" * 45 + "\n"
for fila in datos_tabla:
    texto_tabla += f"{fila[0][:25]:25} {fila[1]:8}  {fila[2]:>6}\n"

# Posicionar tabla en la esquina superior derecha
grafica.text(
    0.98, 0.98,
    texto_tabla,
    transform=grafica.transAxes,
    fontsize=9,
    fontfamily='monospace',
    verticalalignment='top',
    horizontalalignment='right',
    bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.9)
)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '30.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")