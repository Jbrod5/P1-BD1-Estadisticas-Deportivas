import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los penales en finales de Champions por equipo
consulta_sql = """
SELECT
    e.nombre AS equipo,
    COUNT(pn.id_evento) AS penales_totales,
    SUM(CASE WHEN pn.resultado = 'Anotado' THEN 1 ELSE 0 END) AS penales_anotados,
    CAST(SUM(CASE WHEN pn.resultado = 'Anotado' THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(pn.id_evento), 0) * 100 AS efectividad_porcentaje
FROM penal pn
JOIN evento ev ON pn.id_evento = ev.id_evento
JOIN equipo e ON ev.id_equipo = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'Champions League'
  AND p.fase = 'Final'
GROUP BY e.nombre
ORDER BY efectividad_porcentaje DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando penales en finales de Champions...")
dataframe_penales = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_penales) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_penales[['equipo', 'penales_totales', 'penales_anotados', 'efectividad_porcentaje']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de penales en finales de Champions...")

# Crear figura con dos subgraficas
figura, (grafica_barras, grafica_porcentaje) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Penales en finales de Champions League', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: BARRAS DE PENALES (ANOTADOS VS TOTALES)
# --------------------------------------------------
lista_equipos = dataframe_penales['equipo'].tolist()
lista_totales = dataframe_penales['penales_totales'].tolist()
lista_anotados = dataframe_penales['penales_anotados'].tolist()
posiciones_x = range(len(lista_equipos))

ancho_barra = 0.35  # separacion entre barras

# Barras para penales totales (gris claro)
barras_totales = grafica_barras.bar(
    [i - ancho_barra/2 for i in posiciones_x],
    lista_totales,
    width=ancho_barra,
    label='Penales totales',
    color='#a9a9a9',
    alpha=0.7,
    edgecolor='black',
    linewidth=1
)

# Barras para penales anotados (verde)
barras_anotados = grafica_barras.bar(
    [i + ancho_barra/2 for i in posiciones_x],
    lista_anotados,
    width=ancho_barra,
    label='Penales anotados',
    color='#2e8b57',
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica_barras.set_xlabel('Equipo')
grafica_barras.set_ylabel('Cantidad de penales')
grafica_barras.set_title('Penales totales vs anotados')
grafica_barras.set_xticks(posiciones_x)
grafica_barras.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica_barras.legend()
grafica_barras.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar valores encima de las barras anotadas
for indice, (barra, valor) in enumerate(zip(barras_anotados, lista_anotados)):
    altura = barra.get_height()
    if altura > 0:
        grafica_barras.text(
            barra.get_x() + barra.get_width()/2.,
            altura + 0.2,
            f'{int(altura)}',
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold'
        )

# --------------------------------------------------
# GRAFICA DERECHA: PORCENTAJE DE EFECTIVIDAD
# --------------------------------------------------
lista_efectividad = dataframe_penales['efectividad_porcentaje'].tolist()

# Colores segun efectividad (verde intenso para mas de 80, amarillo para 50-80, rojo para menos de 50)
colores_efectividad = []
for efec in lista_efectividad:
    if efec >= 80:
        colores_efectividad.append('#006400')  # verde oscuro
    elif efec >= 50:
        colores_efectividad.append('#ffd700')  # dorado
    else:
        colores_efectividad.append('#8b0000')  # rojo oscuro

barras_efectividad = grafica_porcentaje.bar(
    posiciones_x,
    lista_efectividad,
    color=colores_efectividad,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica_porcentaje.set_xlabel('Equipo')
grafica_porcentaje.set_ylabel('Efectividad porcentaje')
grafica_porcentaje.set_title('Efectividad desde el punto penal')
grafica_porcentaje.set_xticks(posiciones_x)
grafica_porcentaje.set_xticklabels(lista_equipos, rotation=45, ha='right')
grafica_porcentaje.grid(axis='y', alpha=0.3, linestyle='--')
grafica_porcentaje.set_ylim(0, 105)  # dejar espacio para el texto

# Agregar el valor exacto encima de cada barra
for indice, (barra, valor, totales) in enumerate(zip(barras_efectividad, lista_efectividad, lista_totales)):
    altura = barra.get_height()
    grafica_porcentaje.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 2,
        f'{valor:.1f}%\n({int(lista_anotados[indice])}/{int(totales)})',
        ha='center',
        va='bottom',
        fontsize=8,
        fontweight='bold'
    )

# Agregar linea de 100% (perfeccion)
grafica_porcentaje.axhline(
    y=100,
    color='green',
    linestyle=':',
    linewidth=1.5,
    alpha=0.5,
    label='100% perfecto'
)

# Agregar linea de 50% (mitad)
grafica_porcentaje.axhline(
    y=50,
    color='orange',
    linestyle='--',
    linewidth=1.5,
    alpha=0.5,
    label='50% promedio'
)

grafica_porcentaje.legend()

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '13.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")