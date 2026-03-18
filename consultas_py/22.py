import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca estadísticas completas de equipos en Champions 2010-2020
consulta_sql = """
SELECT TOP 5
   e.nombre AS equipo,
   COUNT(DISTINCT p.id_partido) AS partidos_jugados,
   SUM(CASE
       WHEN p.id_equipo_local = e.id_equipo AND p.goles_local > p.goles_visita THEN 1
       WHEN p.id_equipo_visita = e.id_equipo AND p.goles_visita > p.goles_local THEN 1
       ELSE 0 END) AS victorias,
   SUM(CASE
       WHEN p.id_equipo_local = e.id_equipo THEN p.goles_local
       ELSE p.goles_visita END) AS goles_totales,
   AVG(ep.posesion) AS posesion_promedio,
   AVG(ep.tiros_a_puerta) AS tiros_promedio,
   AVG(ep.pases_completados) AS pases_promedio
FROM equipo e
JOIN partido p ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN temporada t ON p.id_temporada = t.id_temporada
LEFT JOIN estadistica_partido ep ON ep.id_partido = p.id_partido AND ep.id_equipo = e.id_equipo
WHERE c.nombre = 'Champions League'
 AND t.anio_inicio BETWEEN 2010 AND 2020
GROUP BY e.nombre
ORDER BY victorias DESC, goles_totales DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando estadísticas de equipos en Champions 2010-2020...")
dataframe_equipos = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_equipos) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_equipos[['equipo', 'partidos_jugados', 'victorias', 'goles_totales', 
                         'posesion_promedio', 'tiros_promedio', 'pases_promedio']].to_string(index=False))

# 4.5 MANEJAR VALORES NULOS
# Reemplazar None con 0 para las operaciones matematicas
dataframe_equipos['posesion_promedio'] = dataframe_equipos['posesion_promedio'].fillna(0)
dataframe_equipos['tiros_promedio'] = dataframe_equipos['tiros_promedio'].fillna(0)
dataframe_equipos['pases_promedio'] = dataframe_equipos['pases_promedio'].fillna(0)

print("\nDatos después de manejar nulos:")
print(dataframe_equipos[['equipo', 'partidos_jugados', 'victorias', 'goles_totales', 
                         'posesion_promedio', 'tiros_promedio', 'pases_promedio']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de equipos mas determinantes...")

# Crear figura con 2x2 subgraficas
figura = matplotlib.pyplot.figure(figsize=(14, 10))
figura.suptitle('Equipos mas determinantes en Champions League (2010-2020)', 
                fontsize=14, fontweight='bold')

# Crear las 4 subgraficas
grafica_victorias = figura.add_subplot(2, 2, 1)
grafica_goles = figura.add_subplot(2, 2, 2)
grafica_posesion = figura.add_subplot(2, 2, 3)
grafica_tiros = figura.add_subplot(2, 2, 4)

# Lista de equipos para los ejes
lista_equipos = dataframe_equipos['equipo'].tolist()
posiciones_x = range(len(lista_equipos))

# Colores degradados
colores = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6']

# --------------------------------------------------
# GRAFICA 1: VICTORIAS
# --------------------------------------------------
lista_victorias = dataframe_equipos['victorias'].tolist()

barras1 = grafica_victorias.bar(
    posiciones_x,
    lista_victorias,
    color=colores[:len(lista_equipos)],
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica_victorias.set_xlabel('Equipo')
grafica_victorias.set_ylabel('Victorias')
grafica_victorias.set_title('Victorias totales')
grafica_victorias.set_xticks(posiciones_x)
grafica_victorias.set_xticklabels(lista_equipos, rotation=45, ha='right', fontsize=9)
grafica_victorias.grid(axis='y', alpha=0.3, linestyle='--')

# Valores encima
for barra, valor in zip(barras1, lista_victorias):
    grafica_victorias.text(
        barra.get_x() + barra.get_width()/2.,
        barra.get_height() + 0.1,
        str(int(valor)),
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA 2: GOLES
# --------------------------------------------------
lista_goles = dataframe_equipos['goles_totales'].tolist()

barras2 = grafica_goles.bar(
    posiciones_x,
    lista_goles,
    color=colores[:len(lista_equipos)],
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica_goles.set_xlabel('Equipo')
grafica_goles.set_ylabel('Goles')
grafica_goles.set_title('Goles totales')
grafica_goles.set_xticks(posiciones_x)
grafica_goles.set_xticklabels(lista_equipos, rotation=45, ha='right', fontsize=9)
grafica_goles.grid(axis='y', alpha=0.3, linestyle='--')

# Valores encima
for barra, valor in zip(barras2, lista_goles):
    grafica_goles.text(
        barra.get_x() + barra.get_width()/2.,
        barra.get_height() + 0.3,
        str(int(valor)),
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='bold'
    )

# --------------------------------------------------
# GRAFICA 3: POSESION
# --------------------------------------------------
lista_posesion = dataframe_equipos['posesion_promedio'].tolist()

barras3 = grafica_posesion.bar(
    posiciones_x,
    lista_posesion,
    color=colores[:len(lista_equipos)],
    alpha=0.9,
    edgecolor='black',
    linewidth=1
)

grafica_posesion.set_xlabel('Equipo')
grafica_posesion.set_ylabel('Posesión promedio %')
grafica_posesion.set_title('Posesión de balón')
grafica_posesion.set_xticks(posiciones_x)
grafica_posesion.set_xticklabels(lista_equipos, rotation=45, ha='right', fontsize=9)
grafica_posesion.grid(axis='y', alpha=0.3, linestyle='--')

# Valores encima (solo si hay datos)
for barra, valor in zip(barras3, lista_posesion):
    if valor > 0:
        grafica_posesion.text(
            barra.get_x() + barra.get_width()/2.,
            barra.get_height() + 0.5,
            f'{valor:.1f}%',
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold'
        )
    else:
        grafica_posesion.text(
            barra.get_x() + barra.get_width()/2.,
            0.5,
            'Sin datos',
            ha='center',
            va='bottom',
            fontsize=8,
            color='gray'
        )

# --------------------------------------------------
# GRAFICA 4: TIROS Y PASES (doble barra)
# --------------------------------------------------
lista_tiros = dataframe_equipos['tiros_promedio'].tolist()
lista_pases = dataframe_equipos['pases_promedio'].tolist()

# Escalar pases para que se vean mejor (dividir entre 10)
lista_pases_escalados = [p/10 for p in lista_pases]

ancho_barra = 0.35

barras_tiros = grafica_tiros.bar(
    [i - ancho_barra/2 for i in posiciones_x],
    lista_tiros,
    width=ancho_barra,
    label='Tiros a puerta',
    color='#d62728',
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

barras_pases = grafica_tiros.bar(
    [i + ancho_barra/2 for i in posiciones_x],
    lista_pases_escalados,
    width=ancho_barra,
    label='Pases (/10)',
    color='#2ca02c',
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica_tiros.set_xlabel('Equipo')
grafica_tiros.set_ylabel('Promedio por partido')
grafica_tiros.set_title('Tiros a puerta y pases')
grafica_tiros.set_xticks(posiciones_x)
grafica_tiros.set_xticklabels(lista_equipos, rotation=45, ha='right', fontsize=9)
grafica_tiros.grid(axis='y', alpha=0.3, linestyle='--')
grafica_tiros.legend(loc='upper right', fontsize=8)

# Valores para tiros
for barra, valor in zip(barras_tiros, lista_tiros):
    if valor > 0:
        grafica_tiros.text(
            barra.get_x() + barra.get_width()/2.,
            barra.get_height() + 0.5,
            f'{valor:.1f}',
            ha='center',
            va='bottom',
            fontsize=8,
            fontweight='bold'
        )

# Valores para pases (mostrar el valor real, no el escalado)
for barra, valor, valor_escalado in zip(barras_pases, lista_pases, lista_pases_escalados):
    if valor > 0:
        grafica_tiros.text(
            barra.get_x() + barra.get_width()/2.,
            valor_escalado + 5,
            f'{valor:.0f}',
            ha='center',
            va='bottom',
            fontsize=8,
            fontweight='bold',
            color='#2ca02c'
        )

# --------------------------------------------------
# TABLA RESUMEN
# --------------------------------------------------
# Agregar una tabla con todos los datos
datos_tabla = []
for i, fila in dataframe_equipos.iterrows():
    datos_tabla.append([
        fila['equipo'],
        int(fila['partidos_jugados']),
        int(fila['victorias']),
        int(fila['goles_totales']),
        f"{fila['posesion_promedio']:.1f}" if fila['posesion_promedio'] > 0 else 'N/A',
        f"{fila['tiros_promedio']:.1f}" if fila['tiros_promedio'] > 0 else 'N/A',
        f"{fila['pases_promedio']:.0f}" if fila['pases_promedio'] > 0 else 'N/A'
    ])

# Crear tabla como texto
texto_tabla = "Equipo          Part  Vic  Gol  Pos   Tiros  Pases\n"
texto_tabla += "-" * 55 + "\n"
for fila in datos_tabla:
    texto_tabla += f"{fila[0][:12]:12} {fila[1]:4} {fila[2]:4} {fila[3]:4} {fila[4]:5} {fila[5]:6} {fila[6]:5}\n"

# Posicionar la tabla en la figura
figura.text(0.02, 0.02, texto_tabla, fontsize=8, fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.9))

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout(rect=[0, 0.05, 1, 0.95])

# 6. GUARDAR LA GRAFICA
nombre_archivo = '22.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")