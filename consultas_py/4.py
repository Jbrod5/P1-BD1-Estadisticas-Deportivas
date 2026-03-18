import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los porteros con mas partidos sin recibir goles
consulta_sql = """
SELECT TOP 5
    j.nombre AS NombrePortero,
    COUNT(DISTINCT p.id_partido) AS PorteriasACero
FROM jugador j
JOIN evento ev ON j.id_jugador = ev.id_jugador
JOIN partido p ON ev.id_partido = p.id_partido
JOIN equipo e ON ev.id_equipo = e.id_equipo
WHERE (p.id_equipo_local = e.id_equipo AND p.goles_visita = 0)
   OR (p.id_equipo_visita = e.id_equipo AND p.goles_local = 0)
GROUP BY j.nombre
ORDER BY PorteriasACero DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando porteros con mas porterias a cero...")
dataframe_porteros = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_porteros) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_porteros.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de porteros con mas porterias a cero...")

# Crear figura
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Porteros con mas partidos sin recibir goles', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# BARRAS HORIZONTALES (para que los nombres largos se lean mejor)
# --------------------------------------------------
lista_porteros = dataframe_porteros['NombrePortero'].tolist()
lista_porterias = dataframe_porteros['PorteriasACero'].tolist()
posiciones_y = range(len(lista_porteros))

# Colores en tonos azules (mas oscuro el que tiene mas porterias)
colores = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6']
colores = colores[:len(lista_porteros)]  # solo los que necesitamos

# Barras horizontales
barras = grafica.barh(
    posiciones_y,
    lista_porterias,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Cantidad de porterias a cero')
grafica.set_ylabel('Portero')
grafica.set_title('Top 5 porteros con mas partidos sin recibir goles')
grafica.set_yticks(posiciones_y)
grafica.set_yticklabels(lista_porteros)
grafica.grid(axis='x', alpha=0.3, linestyle='--')

# Agregar el valor exacto al final de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_porterias)):
    ancho = barra.get_width()
    grafica.text(
        ancho + 0.5,           # posicion x (al final de la barra)
        barra.get_y() + barra.get_height()/2.,  # centro de la barra
        f'{int(valor)} partidos',  # texto
        va='center',            # centrado vertical
        fontsize=10,
        fontweight='bold'
    )

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '4.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")