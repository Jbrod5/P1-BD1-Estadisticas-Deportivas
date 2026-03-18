import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca equipos con mejor diferencia de goles en los ultimos 10 minutos
consulta_sql = """
SELECT TOP 5
   e.nombre AS equipo,
   c.nombre AS competicion,
   SUM(CASE WHEN ev.id_equipo = e.id_equipo THEN 1 ELSE 0 END) AS goles_a_favor,
   SUM(CASE WHEN ev.id_equipo != e.id_equipo THEN 1 ELSE 0 END) AS goles_en_contra,
   SUM(CASE WHEN ev.id_equipo = e.id_equipo THEN 1 ELSE -1 END) AS diferencia_goles
FROM gol g
JOIN evento ev ON g.id_evento = ev.id_evento
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
JOIN equipo e ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
WHERE ev.minuto >= 80
 AND c.nombre IN ('Champions League', 'FIFA World Cup')
GROUP BY e.nombre, c.nombre
ORDER BY diferencia_goles DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando equipos con mejor diferencia en ultimos 10 minutos...")
dataframe_diferencia = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_diferencia) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_diferencia[['equipo', 'competicion', 'goles_a_favor', 'goles_en_contra', 'diferencia_goles']].to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de diferencia de goles...")

# Crear una sola grafica de barras
figura, grafica = matplotlib.pyplot.subplots(figsize=(12, 6))
figura.suptitle('Equipos con mejor diferencia de goles en los ultimos 10 minutos', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# PREPARAR DATOS
# --------------------------------------------------
# Crear etiquetas combinadas (equipo + competicion)
etiquetas = []
for i, fila in dataframe_diferencia.iterrows():
    comp = 'CL' if fila['competicion'] == 'Champions League' else 'WC'
    etiquetas.append(f"{fila['equipo']} ({comp})")

lista_favor = dataframe_diferencia['goles_a_favor'].tolist()
lista_contra = dataframe_diferencia['goles_en_contra'].tolist()
lista_diferencia = dataframe_diferencia['diferencia_goles'].tolist()
posiciones_x = range(len(etiquetas))

# --------------------------------------------------
# BARRAS APILADAS (goles a favor y en contra)
# --------------------------------------------------
ancho_barra = 0.6

# Barras de goles a favor (verde)
barras_favor = grafica.bar(
    posiciones_x,
    lista_favor,
    width=ancho_barra,
    label='Goles a favor',
    color='#2e8b57',
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

# Barras de goles en contra (rojo) - negativas para que se vean hacia abajo
barras_contra = grafica.bar(
    posiciones_x,
    [-c for c in lista_contra],
    width=ancho_barra,
    label='Goles en contra',
    color='#cd5c5c',
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Equipo')
grafica.set_ylabel('Goles')
grafica.set_title('Goles a favor y en contra en minutos finales')
grafica.set_xticks(posiciones_x)
grafica.set_xticklabels(etiquetas, rotation=45, ha='right')
grafica.axhline(y=0, color='black', linewidth=1)  # linea en cero
grafica.grid(axis='y', alpha=0.3, linestyle='--')
grafica.legend()

# Agregar la diferencia neta encima de las barras
for indice, (favor, contra, diferencia) in enumerate(zip(lista_favor, lista_contra, lista_diferencia)):
    # Texto de diferencia
    color_texto = 'green' if diferencia > 0 else 'red' if diferencia < 0 else 'black'
    grafica.text(
        indice,
        max(favor, contra) + 0.5,
        f'{diferencia:+d}',  # muestra + o - antes del numero
        ha='center',
        va='bottom',
        fontsize=11,
        fontweight='bold',
        color=color_texto
    )
    
    # Valores numericos dentro de las barras
    if favor > 0:
        grafica.text(
            indice,
            favor/2,
            str(int(favor)),
            ha='center',
            va='center',
            color='white',
            fontweight='bold'
        )
    if contra > 0:
        grafica.text(
            indice,
            -contra/2,
            str(int(contra)),
            ha='center',
            va='center',
            color='white',
            fontweight='bold'
        )

# Agregar una tabla pequeña con los datos
datos_tabla = []
for i, fila in dataframe_diferencia.iterrows():
    datos_tabla.append([
        f"{fila['equipo']}",
        fila['competicion'][:3],
        int(fila['goles_a_favor']),
        int(fila['goles_en_contra']),
        int(fila['diferencia_goles'])
    ])

# Crear tabla como texto en la esquina
texto_tabla = "Equipo          Comp   F   C   D\n"
texto_tabla += "-"*30 + "\n"
for fila in datos_tabla:
    texto_tabla += f"{fila[0][:15]:15} {fila[1]:4} {fila[2]:2} {fila[3]:2} {fila[4]:+3}\n"

grafica.text(
    0.02, 0.98,
    texto_tabla,
    transform=grafica.transAxes,
    fontsize=8,
    fontfamily='monospace',
    verticalalignment='top',
    bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.9)
)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '9.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")