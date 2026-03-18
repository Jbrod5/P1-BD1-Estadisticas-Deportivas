import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca el equipo con más goles en Champions entre 2010 y 2019
consulta_sql = """
SELECT TOP 1
    e.nombre AS equipo,
    COUNT(g.id_evento) AS total_goles
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN temporada t ON p.id_temporada = t.id_temporada
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League'
  AND t.anio_inicio BETWEEN 2010 AND 2019
GROUP BY e.nombre
ORDER BY total_goles DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando al equipo con mas goles en Champions 2010-2019...")
dataframe_goles = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_goles) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_goles.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica del equipo mas goleador...")

# Crear figura con una sola grafica
figura, grafica = matplotlib.pyplot.subplots(figsize=(8, 6))

# Extraer los valores
nombre_equipo = dataframe_goles['equipo'].iloc[0]
cantidad_goles = dataframe_goles['total_goles'].iloc[0]

# Crear una sola barra para el equipo ganador
colores = ['#1f77b4']  # azul
barras = grafica.bar([nombre_equipo], [cantidad_goles], color=colores, alpha=0.8)

# Agregar el valor exacto encima de la barra
for barra in barras:
    altura = barra.get_height()
    grafica.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 0.5,
        f'{int(altura)} goles',
        ha='center',
        va='bottom',
        fontsize=12,
        fontweight='bold'
    )

# Configurar la grafica
grafica.set_xlabel('Equipo')
grafica.set_ylabel('Total de goles')
grafica.set_title('Equipo con mas goles en Champions League (2010-2019)', 
                  fontsize=14, fontweight='bold')
grafica.grid(axis='y', alpha=0.3, linestyle='--')

# Ajustar limites del eje y para que se vea mejor
grafica.set_ylim(0, cantidad_goles + 5)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '1.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")