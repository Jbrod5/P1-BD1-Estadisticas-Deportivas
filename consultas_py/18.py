import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy
import os

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Obtiene todas las coordenadas de eventos en Mundiales
consulta_sql = """
SELECT
   e.nombre AS equipo,
   ev.x_inicio,
   ev.y_inicio,
   COUNT(*) AS eventos_en_zona
FROM evento ev
JOIN equipo e ON ev.id_equipo_posesion = e.id_equipo
JOIN partido p ON ev.id_partido = p.id_partido
JOIN competicion c ON p.id_competicion = c.id_competicion
WHERE c.nombre = 'FIFA World Cup'
 AND ev.x_inicio IS NOT NULL
 AND ev.y_inicio IS NOT NULL
GROUP BY e.nombre, ev.x_inicio, ev.y_inicio
ORDER BY e.nombre, eventos_en_zona DESC;
"""

# 3. EJECUTAR CONSULTA
print("Obteniendo datos para mapa de calor de posesion en Mundiales...")
dataframe_calor = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_calor) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print(f"Se encontraron {len(dataframe_calor)} puntos de eventos")
print("\nResumen por equipo:")
resumen = dataframe_calor.groupby('equipo').agg({
    'eventos_en_zona': ['sum', 'count']
}).round(0)
resumen.columns = ['Total eventos', 'Puntos unicos']
print(resumen.to_string())

# 5. GUARDAR DATOS PARA USAR EN MAPAS DE CALOR
print("\nGuardando datos para analisis...")

# Guardar todos los datos en un CSV
archivo_csv = 'datos_calor_mundial.csv'
dataframe_calor.to_csv(archivo_csv, index=False)
print(f"Datos guardados en: {archivo_csv}")

# Tambien guardar por equipo para mapas individuales
carpeta_mapas = 'mapas_calor'
if not os.path.exists(carpeta_mapas):
    os.makedirs(carpeta_mapas)

equipos_unicos = dataframe_calor['equipo'].unique()
for equipo in equipos_unicos[:5]:  # solo primeros 5 equipos para no saturar
    df_equipo = dataframe_calor[dataframe_calor['equipo'] == equipo]
    archivo_equipo = f"{carpeta_mapas}/calor_{equipo.replace(' ', '_')}.csv"
    df_equipo.to_csv(archivo_equipo, index=False)
    print(f"  Datos de {equipo} guardados en: {archivo_equipo}")

# 6. MOSTRAR EJEMPLO DE MAPA DE CALOR PARA UN EQUIPO
print("\nGenerando ejemplo de mapa de calor para el primer equipo...")

# Tomar el primer equipo con mas datos
equipo_ejemplo = resumen.index[0]
df_ejemplo = dataframe_calor[dataframe_calor['equipo'] == equipo_ejemplo]

# Si hay muchos puntos, tomar una muestra para el grafico
if len(df_ejemplo) > 1000:
    # Para el mapa de calor usamos los puntos con mas eventos
    df_ejemplo = df_ejemplo.nlargest(500, 'eventos_en_zona')

print(f"Generando mapa para {equipo_ejemplo} con {len(df_ejemplo)} puntos")

# Crear mapa de calor de ejemplo
try:
    from mplsoccer import Pitch
    
    # Crear cancha
    cancha = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white', stripe=True)
    figura, eje = cancha.draw(figsize=(12, 8))
    
    # Expandir los puntos segun su frecuencia para el mapa de calor
    puntos_x = []
    puntos_y = []
    for _, fila in df_ejemplo.iterrows():
        # Repetir cada punto segun su frecuencia
        puntos_x.extend([fila['x_inicio']] * int(fila['eventos_en_zona']))
        puntos_y.extend([fila['y_inicio']] * int(fila['eventos_en_zona']))
    
    # Dibujar mapa de calor
    cancha.kdeplot(
        puntos_x, puntos_y,
        ax=eje,
        cmap='hot',
        fill=True,
        levels=50,
        alpha=0.7,
        shade=True
    )
    
    eje.set_title(f'Mapa de calor de posesion - {equipo_ejemplo}', 
                  fontsize=16, fontweight='bold')
    
    # Guardar ejemplo
    archivo_ejemplo = f"{carpeta_mapas}/ejemplo_calor_{equipo_ejemplo.replace(' ', '_')}.png"
    matplotlib.pyplot.savefig(archivo_ejemplo, dpi=300, bbox_inches='tight')
    print(f"Mapa de ejemplo guardado en: {archivo_ejemplo}")
    
    matplotlib.pyplot.show()
    
except ImportError:
    print("Nota: Para generar mapas de calor necesitas instalar mplsoccer")
    print("Los datos CSV estan listos para usar con mplsoccer")

# 7. MOSTRAR ESTADISTICAS BASICAS
print("\nEstadisticas basicas de posesion por equipo:")

# Calcular zona mas activa para cada equipo
for equipo in equipos_unicos[:5]:
    df_equipo = dataframe_calor[dataframe_calor['equipo'] == equipo]
    zona_top = df_equipo.nlargest(1, 'eventos_en_zona').iloc[0]
    print(f"\n{equipo}:")
    print(f"  Total eventos: {df_equipo['eventos_en_zona'].sum():.0f}")
    print(f"  Zona mas activa: x={zona_top['x_inicio']:.1f}, y={zona_top['y_inicio']:.1f}")
    print(f"  Eventos en esa zona: {zona_top['eventos_en_zona']:.0f}")

# --------------------------------------------------
# GRAFICA RESUMEN DE ZONAS POR EQUIPO (opcional)
# --------------------------------------------------
print("\nDibujando grafica resumen de zonas de posesion...")

# Tomar top 10 zonas mas activas en general
top_zonas = dataframe_calor.nlargest(10, 'eventos_en_zona')

figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Zonas del campo con mas actividad de posesion en Mundiales', 
                fontsize=14, fontweight='bold')

# Crear etiquetas para las zonas
etiquetas = [f"{row['equipo']}\n({row['x_inicio']:.0f}, {row['y_inicio']:.0f})" 
             for _, row in top_zonas.iterrows()]

barras = grafica.bar(
    range(len(top_zonas)),
    top_zonas['eventos_en_zona'].tolist(),
    color='#ff8c00',
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Equipo y coordenada')
grafica.set_ylabel('Cantidad de eventos')
grafica.set_title('Top 10 zonas con mas actividad')
grafica.set_xticks(range(len(top_zonas)))
grafica.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=8)
grafica.grid(axis='y', alpha=0.3, linestyle='--')

# Agregar valores
for barra, valor in zip(barras, top_zonas['eventos_en_zona']):
    altura = barra.get_height()
    grafica.text(
        barra.get_x() + barra.get_width()/2.,
        altura + 5,
        f'{int(altura)}',
        ha='center',
        va='bottom',
        fontsize=8,
        fontweight='bold'
    )

matplotlib.pyplot.tight_layout()
archivo_resumen = '18.png'
matplotlib.pyplot.savefig(archivo_resumen, dpi=300, bbox_inches='tight')
print(f"Grafica resumen guardada como: {archivo_resumen}")

matplotlib.pyplot.show()
print("\nListo! Los datos estan listos para analisis de mapas de calor")