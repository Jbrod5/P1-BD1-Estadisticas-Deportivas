import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca el equipo con mayor promedio de posesion en 2018
consulta_sql = """
SELECT TOP 5
    e.nombre AS NombreEquipo,
    AVG(ep.posesion) AS PromedioPosesion
FROM equipo e
JOIN estadistica_partido ep ON e.id_equipo = ep.id_equipo
JOIN partido p ON ep.id_partido = p.id_partido
JOIN temporada t ON p.id_temporada = t.id_temporada
WHERE t.anio_inicio = 2018 
   OR t.anio_inicio = 2017
GROUP BY e.nombre
ORDER BY PromedioPosesion DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando equipos con mayor posesion en 2018...")
dataframe_posesion = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_posesion) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_posesion.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de posesion...")

# Crear una sola grafica de barras
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Equipos con mayor posesion de balon - Temporada 2018', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# BARRAS DE POSESION
# --------------------------------------------------
lista_equipos = dataframe_posesion['NombreEquipo'].tolist()
lista_posesion = dataframe_posesion['PromedioPosesion'].tolist()
posiciones_x = range(len(lista_equipos))

# Colores degradados (el primero mas oscuro)
colores = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6']

barras = grafica.bar(
    posiciones_x,
    lista_posesion,
    color=colores[:len(lista_equipos)],
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Equipo')
grafica.set_ylabel('Posesion promedio %')
grafica.set_title('Top 5 equipos con mas posesion')
grafica.set_xticks(posiciones_x)
grafica.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_posesion)):
    altura = barra.get_height()
    grafica.text(
        barra.get_x() + barra.get_width()/2.,  # centro de la barra
        altura + 0.5,                           # un poco arriba de la barra
        f'{valor:.1f}%',                         # texto con un decimal
        ha='center',                              # centrado horizontal
        va='bottom',                               # alineado abajo
        fontsize=10,                                # tamaño de letra
        fontweight='bold'                            # negritas
    )

# Agregar una linea horizontal en el promedio general
if len(lista_posesion) > 1:
    promedio_general = sum(lista_posesion) / len(lista_posesion)
    grafica.axhline(
        y=promedio_general,
        color='red',
        linestyle='--',
        linewidth=2,
        alpha=0.7,
        label=f'Promedio top 5: {promedio_general:.1f}%'
    )
    grafica.legend()

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '3.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")