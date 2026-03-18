import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca equipos con mas pases completados en los ultimos 10 minutos de La Liga
consulta_sql = """
SELECT TOP 5
   e.nombre AS equipo,
   COUNT(pa.id_evento) AS pases_completados_ultimos_10
FROM pase pa
JOIN evento ev ON pa.id_evento = ev.id_evento
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'La Liga'
 AND ev.minuto >= 80
 AND pa.completado = 1
GROUP BY e.nombre
ORDER BY pases_completados_ultimos_10 DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando equipos con mas pases en minutos finales de La Liga...")
dataframe_pases = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_pases) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_pases.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de pases en minutos finales...")

# Crear una sola grafica de barras
figura, grafica = matplotlib.pyplot.subplots(figsize=(12, 6))
figura.suptitle('Equipos con mas pases completados en los ultimos 10 minutos (La Liga)', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# BARRAS DE PASES
# --------------------------------------------------
lista_equipos = dataframe_pases['equipo'].tolist()
lista_pases = dataframe_pases['pases_completados_ultimos_10'].tolist()
posiciones_x = range(len(lista_equipos))

# Colores en tonos verdes (relacionado con posesion)
colores = ['#006400', '#228b22', '#32cd32', '#66cdaa', '#90ee90']

barras = grafica.bar(
    posiciones_x,
    lista_pases,
    color=colores[:len(lista_equipos)],
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Equipo')
grafica.set_ylabel('Cantidad de pases completados')
grafica.set_title('Top 5 equipos que mas pasan en los minutos finales')
grafica.set_xticks(posiciones_x)
grafica.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_pases)):
    altura = barra.get_height()
    grafica.text(
        barra.get_x() + barra.get_width()/2.,  # centro de la barra
        altura + 2,                              # un poco arriba
        f'{int(valor)}',                          # texto
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold'
    )

# Agregar linea con el promedio
promedio_pases = sum(lista_pases) / len(lista_pases)
grafica.axhline(
    y=promedio_pases,
    color='red',
    linestyle='--',
    linewidth=2,
    alpha=0.7,
    label=f'Promedio: {promedio_pases:.0f} pases'
)
grafica.legend()

# --------------------------------------------------
# TABLA CON DETALLES ADICIONALES (opcional)
# --------------------------------------------------
# Crear una tabla pequeña con los datos
datos_tabla = []
for i, fila in dataframe_pases.iterrows():
    datos_tabla.append([
        fila['equipo'],
        int(fila['pases_completados_ultimos_10'])
    ])

# Crear texto de tabla
texto_tabla = "Equipo                    Pases\n"
texto_tabla += "-" * 30 + "\n"
for fila in datos_tabla:
    texto_tabla += f"{fila[0][:20]:20} {fila[1]:6}\n"

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
nombre_archivo = '24.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")