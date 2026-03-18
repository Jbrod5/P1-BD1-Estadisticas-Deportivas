import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
consulta_sql = """
SELECT TOP 5
    e.nombre AS equipo,
    AVG(ep.posesion) AS posesion_promedio,
    AVG(ep.tiros_a_puerta) AS tiros_promedio
FROM estadistica_partido ep
JOIN equipo e ON ep.id_equipo = e.id_equipo
JOIN partido p ON ep.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
  AND (
      (ep.id_equipo = p.id_equipo_local AND p.goles_local < p.goles_visita)
      OR
      (ep.id_equipo = p.id_equipo_visita AND p.goles_visita < p.goles_local)
  )
GROUP BY e.nombre
ORDER BY posesion_promedio DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando equipos que perdieron pero tuvieron alta posesion...")
dataframe_equipos = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_equipos) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print(f"Se encontraron {len(dataframe_equipos)} equipos")
print(dataframe_equipos.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de equipos que dominaron pero perdieron...")

# Crear figura con dos subgraficas una al lado de la otra
figura, (grafica_izquierda, grafica_derecha) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Equipos que perdieron en mundiales pero tuvieron mas posesion y tiros', 
                fontsize=14, fontweight='bold')

# Lista de equipos para el eje x
lista_equipos = dataframe_equipos['equipo'].tolist()
posiciones_x = range(len(lista_equipos))

# --------------------------------------------------
# GRAFICA IZQUIERDA: POSESION (barras)
# --------------------------------------------------
colores_posesion = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']

grafica_izquierda.bar(
    posiciones_x,
    dataframe_equipos['posesion_promedio'],
    color=colores_posesion,
    alpha=0.8
)

grafica_izquierda.set_xlabel('Equipo')
grafica_izquierda.set_ylabel('Posesion promedio %')
grafica_izquierda.set_title('Posesion de balon')
grafica_izquierda.set_xticks(posiciones_x)
grafica_izquierda.set_xticklabels(lista_equipos, rotation=45, ha='right')

# Agrega los valores encima de las barras
for indice, valor in enumerate(dataframe_equipos['posesion_promedio']):
    grafica_izquierda.text(
        indice,
        valor + 1,
        f"{valor:.1f}%",
        ha='center',
        fontsize=9,
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA DERECHA: TIROS A PUERTA (barras)
# --------------------------------------------------
colores_tiros = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']

grafica_derecha.bar(
    posiciones_x,
    dataframe_equipos['tiros_promedio'],
    color=colores_tiros,
    alpha=0.8
)

grafica_derecha.set_xlabel('Equipo')
grafica_derecha.set_ylabel('Tiros a puerta promedio')
grafica_derecha.set_title('Tiros a puerta')
grafica_derecha.set_xticks(posiciones_x)
grafica_derecha.set_xticklabels(lista_equipos, rotation=45, ha='right')

# Agrega los valores encima de las barras
for indice, valor in enumerate(dataframe_equipos['tiros_promedio']):
    grafica_derecha.text(
        indice,
        valor + 0.3,
        f"{valor:.1f}",
        ha='center',
        fontsize=9,
        fontweight='bold'
    )

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '17.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")