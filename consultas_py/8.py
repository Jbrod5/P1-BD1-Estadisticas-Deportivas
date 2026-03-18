import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca el promedio de goles por equipo en cada competicion
consulta_sql = """
SELECT
   e.nombre AS Equipo,
   c.nombre AS Competicion,
   AVG(CAST(p.goles_local + p.goles_visita AS FLOAT)) AS PromedioGolesPartido
FROM partido p
JOIN equipo e ON e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visita
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre IN ('Champions League', 'FIFA World Cup', 'La Liga')
GROUP BY e.nombre, c.nombre
ORDER BY PromedioGolesPartido DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando promedios de goles por equipo y competicion...")
dataframe_promedios = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_promedios) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print(f"Se encontraron {len(dataframe_promedios)} registros")
print("\nPrimeros 10 registros:")
print(dataframe_promedios.head(10).to_string(index=False))

# 5. CALCULAR EL PROMEDIO DE LA LIGA
promedio_liga = dataframe_promedios[dataframe_promedios['Competicion'] == 'La Liga']['PromedioGolesPartido'].mean()
print(f"\nPromedio general de La Liga: {promedio_liga:.2f} goles por partido")

# 6. FILTRAR EQUIPOS QUE SUPERAN EL PROMEDIO DE LA LIGA EN OTRAS COMPETICIONES
equipos_destacados = dataframe_promedios[
    (dataframe_promedios['Competicion'] != 'La Liga') & 
    (dataframe_promedios['PromedioGolesPartido'] > promedio_liga)
].copy()

print(f"\nEquipos que superan el promedio de La Liga en otras competiciones:")
print(equipos_destacados.to_string(index=False))

# 7. CREAR LA GRAFICA
print("\nDibujando grafica de promedios de goles...")

# Crear figura
figura, (grafica_superiores, grafica_todos) = matplotlib.pyplot.subplots(1, 2, figsize=(14, 6))
figura.suptitle('Promedio de goles por partido - Comparacion con La Liga', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# GRAFICA IZQUIERDA: EQUIPOS QUE SUPERAN EL PROMEDIO
# --------------------------------------------------
if len(equipos_destacados) > 0:
    # Preparar datos
    etiquetas = [f"{fila['Equipo']}\n({fila['Competicion'][:3]})" 
                 for _, fila in equipos_destacados.iterrows()]
    valores = equipos_destacados['PromedioGolesPartido'].tolist()
    posiciones_x = range(len(etiquetas))
    
    # Colores por competicion
    colores = []
    for comp in equipos_destacados['Competicion']:
        if 'Champions' in comp:
            colores.append('blue')
        elif 'World Cup' in comp:
            colores.append('green')
        else:
            colores.append('orange')
    
    barras = grafica_superiores.bar(
        posiciones_x,
        valores,
        color=colores,
        alpha=0.8,
        edgecolor='black',
        linewidth=1
    )
    
    grafica_superiores.set_xlabel('Equipo')
    grafica_superiores.set_ylabel('Promedio de goles por partido')
    grafica_superiores.set_title('Equipos que superan el promedio de La Liga')
    grafica_superiores.set_xticks(posiciones_x)
    grafica_superiores.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=8)
    grafica_superiores.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Linea del promedio de La Liga
    grafica_superiores.axhline(
        y=promedio_liga,
        color='red',
        linestyle='--',
        linewidth=2,
        alpha=0.7,
        label=f'Promedio La Liga: {promedio_liga:.2f}'
    )
    grafica_superiores.legend()
    
    # Valores encima de barras
    for barra, valor in zip(barras, valores):
        altura = barra.get_height()
        grafica_superiores.text(
            barra.get_x() + barra.get_width()/2.,
            altura + 0.1,
            f'{valor:.2f}',
            ha='center',
            va='bottom',
            fontsize=8,
            fontweight='bold'
        )
else:
    grafica_superiores.text(0.5, 0.5, 'No hay equipos que superen el promedio', 
                           ha='center', va='center', transform=grafica_superiores.transAxes)

# --------------------------------------------------
# GRAFICA DERECHA: TOP 10 GENERAL
# --------------------------------------------------
top_10 = dataframe_promedios.nlargest(10, 'PromedioGolesPartido')

etiquetas_top = [f"{fila['Equipo'][:15]}\n({fila['Competicion'][:3]})" 
                 for _, fila in top_10.iterrows()]
valores_top = top_10['PromedioGolesPartido'].tolist()
posiciones_top = range(len(etiquetas_top))

# Colores por competicion para top 10
colores_top = []
for comp in top_10['Competicion']:
    if 'Champions' in comp:
        colores_top.append('blue')
    elif 'World Cup' in comp:
        colores_top.append('green')
    elif 'Liga' in comp:
        colores_top.append('orange')
    else:
        colores_top.append('purple')

barras_top = grafica_todos.bar(
    posiciones_top,
    valores_top,
    color=colores_top,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica_todos.set_xlabel('Equipo')
grafica_todos.set_ylabel('Promedio de goles por partido')
grafica_todos.set_title('Top 10 equipos con mayor promedio')
grafica_todos.set_xticks(posiciones_top)
grafica_todos.set_xticklabels(etiquetas_top, rotation=45, ha='right', fontsize=7)
grafica_todos.grid(axis='y', alpha=0.3, linestyle='--')

# Valores encima de barras
for barra, valor in zip(barras_top, valores_top):
    altura = barra.get_height()
    grafica_todos.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 0.1,
        f'{valor:.2f}',
        ha='center',
        va='bottom',
        fontsize=7,
        fontweight='bold'
    )

# --------------------------------------------------
# LEYENDA
# --------------------------------------------------
from matplotlib.patches import Patch
elementos_leyenda = [
    Patch(facecolor='blue', label='Champions League'),
    Patch(facecolor='green', label='FIFA World Cup'),
    Patch(facecolor='orange', label='La Liga')
]
grafica_todos.legend(handles=elementos_leyenda, loc='upper right', fontsize=8)

# --------------------------------------------------
# TABLA RESUMEN
# --------------------------------------------------
# Crear texto con los equipos que superan el promedio
texto_resumen = f"Promedio La Liga: {promedio_liga:.2f}\n\n"
texto_resumen += "Equipos que lo superan:\n"
if len(equipos_destacados) > 0:
    for _, fila in equipos_destacados.iterrows():
        comp_short = 'CL' if 'Champions' in fila['Competicion'] else 'WC' if 'World' in fila['Competicion'] else fila['Competicion'][:3]
        texto_resumen += f"{fila['Equipo'][:15]:15} {comp_short}: {fila['PromedioGolesPartido']:.2f}\n"
else:
    texto_resumen += "Ninguno"

figura.text(
    0.02, 0.02,
    texto_resumen,
    fontsize=9,
    fontfamily='monospace',
    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.9)
)

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 8. GUARDAR LA GRAFICA
nombre_archivo = '8.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")