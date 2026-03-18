import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca la cantidad de cambios por minuto en finales de Champions
consulta_sql = """
SELECT
    ev.minuto,
    COUNT(*) AS cantidad_cambios
FROM sustitucion s
JOIN evento ev ON s.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League'
  AND p.fase = 'Final'
GROUP BY ev.minuto
ORDER BY ev.minuto;
"""

# 3. EJECUTAR CONSULTA
print("Buscando frecuencia de cambios en finales de Champions...")
dataframe_cambios = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_cambios) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_cambios.to_string(index=False))

print(f"Total de cambios registrados: {dataframe_cambios['cantidad_cambios'].sum()}")

# 5. CREAR LA GRAFICA
print("Dibujando grafica de frecuencia de cambios...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_pastel) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Frecuencia de sustituciones en finales de Champions League', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS POR MINUTO
# --------------------------------------------------
minutos = dataframe_cambios['minuto'].tolist()
cantidades = dataframe_cambios['cantidad_cambios'].tolist()

# Crear un rango completo de minutos (de 45 a 120) para que se vea la distribucion completa
minutos_completos = list(range(45, 121))
cantidades_completas = [0] * len(minutos_completos)

# Llenar las cantidades en los minutos donde hay cambios
for minuto, cantidad in zip(minutos, cantidades):
    if minuto in minutos_completos:
        indice = minutos_completos.index(minuto)
        cantidades_completas[indice] = cantidad

# Colorear las barras: mas oscuro donde hay mas cambios
colores_barras = []
for cantidad in cantidades_completas:
    if cantidad == 0:
        colores_barras.append('#f0f0f0')  # gris muy claro para sin cambios
    else:
        # Entre mas cambios, mas oscuro el azul
        intensidad = min(0.9, 0.3 + (cantidad / max(cantidades)) * 0.6)
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
grafica_barras.set_title('Distribucion de cambios por minuto')
grafica_barras.set_xticks(range(45, 121, 5))  # ticks cada 5 minutos
grafica_barras.set_xticklabels(range(45, 121, 5), rotation=45)
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Marcar los minutos mas comunes (top 3)
if len(dataframe_cambios) > 0:
    top_minutos = dataframe_cambios.nlargest(3, 'cantidad_cambios')
    for _, fila in top_minutos.iterrows():
        grafica_barras.text(
            fila['minuto'],
            fila['cantidad_cambios'] + 0.2,
            f"{int(fila['cantidad_cambios'])}",
            ha='center',
            fontsize=9,
            fontweight='bold'
        )

# --------------------------------------------------
# GRAFICA DERECHA: PASTEL CON RANGOS DE MINUTOS
# --------------------------------------------------
# Agrupar por rangos de minutos
rangos = {
    '45-60': 0,
    '61-75': 0,
    '76-85': 0,
    '86-90': 0,
    '91-105': 0,
    '106-120': 0
}

for minuto, cantidad in zip(minutos, cantidades):
    if minuto <= 60:
        rangos['45-60'] += cantidad
    elif minuto <= 75:
        rangos['61-75'] += cantidad
    elif minuto <= 85:
        rangos['76-85'] += cantidad
    elif minuto <= 90:
        rangos['86-90'] += cantidad
    elif minuto <= 105:
        rangos['91-105'] += cantidad
    else:
        rangos['106-120'] += cantidad

# Filtrar rangos con cambios
etiquetas_pastel = [rango for rango, valor in rangos.items() if valor > 0]
valores_pastel = [valor for valor in rangos.values() if valor > 0]
colores_pastel = matplotlib.pyplot.cm.Set3(range(len(valores_pastel)))

# Crear el grafico de pastel
if valores_pastel:
    parches, textos, porcentajes = grafica_pastel.pie(
        valores_pastel,
        labels=etiquetas_pastel,
        autopct='%1.1f%%',
        colors=colores_pastel,
        startangle=90
    )
    grafica_pastel.set_title('Porcentaje de cambios por rango de minutos')
else:
    grafica_pastel.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
    grafica_pastel.set_title('Porcentaje de cambios por rango de minutos')

# --------------------------------------------------
# AGREGAR ESTADISTICAS COMO TEXTO
# --------------------------------------------------
total_cambios = dataframe_cambios['cantidad_cambios'].sum()
minuto_mas_comun = dataframe_cambios.loc[dataframe_cambios['cantidad_cambios'].idxmax(), 'minuto']
cambios_minuto_comun = dataframe_cambios['cantidad_cambios'].max()

texto_stats = f"Total de cambios: {total_cambios}\nMinuto con mas cambios: {minuto_mas_comun}' ({cambios_minuto_comun} cambios)"
grafica_barras.text(
    0.02, 0.98,
    texto_stats,
    transform=grafica_barras.transAxes,
    fontsize=10,
    verticalalignment='top',
    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '15.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")