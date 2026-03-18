import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los 5 equipos con mas victorias jugando como visitante
consulta_sql = """
SELECT TOP 5
    e.nombre AS equipo,
    COUNT(*) AS partidos_ganados_visitante
FROM partido p
JOIN equipo e ON p.id_equipo_visita = e.id_equipo
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre IN ('Champions League', 'La Liga', 'FIFA World Cup')
  AND p.goles_visita > p.goles_local
GROUP BY e.nombre
ORDER BY partidos_ganados_visitante DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando los 5 equipos con mas victorias como visitante...")
dataframe_victorias = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_victorias) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_victorias.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de equipos con mas victorias como visitante...")

# Crear figura
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))

# Lista de equipos y victorias
lista_equipos = dataframe_victorias['equipo'].tolist()
lista_victorias = dataframe_victorias['partidos_ganados_visitante'].tolist()
posiciones_x = range(len(lista_equipos))

# Colores degradados del mas oscuro al mas claro
# El que tiene mas victorias tiene el color mas oscuro
colores = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6']

# Dibujar barras
barras = grafica.bar(
    posiciones_x,
    lista_victorias,
    color=colores,
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_victorias)):
    altura = barra.get_height()
    grafica.text(
        barra.get_x() + barra.get_width()/2.,  # posicion X (centro de la barra)
        altura + 0.5,                           # posicion Y (encima de la barra)
        f'{int(valor)} victorias',               # texto a mostrar
        ha='center',                              # alineacion horizontal centrada
        va='bottom',                               # alineacion vertical abajo
        fontsize=10,                                # tamaño de letra
        fontweight='bold'                            # negritas
    )

# Configurar la grafica
grafica.set_xlabel('Equipo')
grafica.set_ylabel('Cantidad de victorias como visitante')
grafica.set_title('Top 5 equipos con mas victorias jugando fuera de casa', 
                  fontsize=14, fontweight='bold')
grafica.set_xticks(posiciones_x)
grafica.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica.grid(axis='y', alpha=0.3, linestyle='--')

# Ajustar limite superior del eje y para que quepa el texto
grafica.set_ylim(0, max(lista_victorias) + 5)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '2.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

# Muestra la grafica
matplotlib.pyplot.show()
print("Listo!")