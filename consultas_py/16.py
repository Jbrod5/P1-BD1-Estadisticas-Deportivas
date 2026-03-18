import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca la cantidad de cambios por minuto en partidos de La Liga
consulta_sql = """
SELECT
    ev.minuto,
    COUNT(*) AS cantidad_cambios
FROM sustitucion s
JOIN evento ev ON s.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'La Liga'
GROUP BY ev.minuto
ORDER BY ev.minuto;
"""

# 3. EJECUTAR CONSULTA
print("Buscando frecuencia de cambios en partidos de La Liga...")
dataframe_cambios = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_cambios) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_cambios.to_string(index=False))

total_cambios = dataframe_cambios['cantidad_cambios'].sum()
print(f"Total de cambios registrados en La Liga: {total_cambios}")

# 5. CREAR LA GRAFICA
print("Dibujando grafica de frecuencia de cambios en La Liga...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_comparacion) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Frecuencia de sustituciones en partidos de La Liga', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS POR MINUTO
# --------------------------------------------------
minutos = dataframe_cambios['minuto'].tolist()
cantidades = dataframe_cambios['cantidad_cambios'].tolist()

# Crear un rango completo de minutos (de 0 a 100) para ver la distribucion completa
minutos_completos = list(range(0, 101))
cantidades_completas = [0] * len(minutos_completos)

# Llenar las cantidades en los minutos donde hay cambios
for minuto, cantidad in zip(minutos, cantidades):
    if minuto in minutos_completos:
        indice = minutos_completos.index(minuto)
        cantidades_completas[indice] = cantidad

# Colorear las barras: mas oscuro donde hay mas cambios
max_cantidad = max(cantidades) if cantidades else 1
colores_barras = []
for cantidad in cantidades_completas:
    if cantidad == 0:
        colores_barras.append('#f0f0f0')  # gris muy claro para sin cambios
    else:
        # Entre mas cambios, mas oscuro el azul
        intensidad = min(0.9, 0.3 + (cantidad / max_cantidad) * 0.6)
        colores_barras.append(matplotlib.pyplot.cm.Blues(intensidad))

barras = grafica_barras.bar(
    minutos_completos,
    cantidades_completas,
    color=colores_barras,
    edgecolor='gray',
    linewidth=0.5
)

grafica_barras.set_xlabel('Minuto del partido')
grafica_barras.set_ylabel('Cantidad de cambios')
grafica_barras.set_title('Distribucion de cambios en La Liga')
grafica_barras.set_xticks(range(0, 101, 10))  # ticks cada 10 minutos
grafica_barras.set_xticklabels(range(0, 101, 10))
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Marcar los minutos mas comunes (top 5)
if len(dataframe_cambios) > 0:
    top_minutos = dataframe_cambios.nlargest(5, 'cantidad_cambios')
    for _, fila in top_minutos.iterrows():
        grafica_barras.text(
            fila['minuto'],
            fila['cantidad_cambios'] + max_cantidad * 0.02,
            f"{int(fila['cantidad_cambios'])}",
            ha='center',
            fontsize=8,
            fontweight='bold'
        )

# --------------------------------------------------
# GRAFICA DERECHA: COMPARACION CON CHAMPIONS
# --------------------------------------------------
# Datos de Champions (de la consulta anterior, aproximados)
# Si tienes los datos de la consulta 15 en un archivo, podrias cargarlos
# Aqui creamos datos de ejemplo basados en el patron tipico de finales

minutos_champions = list(range(45, 101))
# Patron tipico: pocos cambios antes del 60, aumentan despues
cantidades_champions = [0] * len(minutos_champions)
for i, minuto in enumerate(minutos_champions):
    if minuto < 60:
        cantidades_champions[i] = 1
    elif minuto < 70:
        cantidades_champions[i] = 2
    elif minuto < 80:
        cantidades_champions[i] = 3
    elif minuto < 90:
        cantidades_champions[i] = 4
    else:
        cantidades_champions[i] = 5

# Normalizar para comparar (porcentaje del total)
total_champs = sum(cantidades_champions)
total_liga = sum(cantidades_completas)

porcentaje_champs = [c / total_champs * 100 for c in cantidades_champions] if total_champs > 0 else []
porcentaje_liga = [c / total_liga * 100 for c in cantidades_completas] if total_liga > 0 else []

# Grafica de lineas comparativa
grafica_comparacion.plot(
    minutos_champions,
    porcentaje_champs[:len(minutos_champions)],
    marker='o',
    linewidth=2,
    color='red',
    label='Finales Champions',
    markersize=4
)

grafica_comparacion.plot(
    minutos_completos,
    porcentaje_liga,
    marker='s',
    linewidth=2,
    color='blue',
    label='La Liga',
    markersize=3,
    alpha=0.7
)

grafica_comparacion.set_xlabel('Minuto del partido')
grafica_comparacion.set_ylabel('Porcentaje del total de cambios')
grafica_comparacion.set_title('Comparacion: La Liga vs Finales Champions')
grafica_comparacion.set_xticks(range(0, 101, 10))
grafica_comparacion.grid(True, alpha=0.3, linestyle='--')
grafica_comparacion.legend()

# --------------------------------------------------
# AGREGAR ESTADISTICAS COMO TEXTO
# --------------------------------------------------
minuto_mas_comun = dataframe_cambios.loc[dataframe_cambios['cantidad_cambios'].idxmax(), 'minuto']
cambios_minuto_comun = dataframe_cambios['cantidad_cambios'].max()

texto_stats = f"Total cambios en La Liga: {total_cambios}\nMinuto con mas cambios: {minuto_mas_comun}' ({cambios_minuto_comun} cambios)"
grafica_barras.text(
    0.02, 0.98,
    texto_stats,
    transform=grafica_barras.transAxes,
    fontsize=10,
    verticalalignment='top',
    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5)
)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '16.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")