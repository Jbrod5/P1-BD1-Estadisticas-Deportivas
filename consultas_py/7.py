import pandas
import matplotlib.pyplot
import sqlalchemy
import numpy

# 1. CONEXION A LA BASE DE DATOS
print("Conectando a la base de datos...")
motor_base_datos = sqlalchemy.create_engine("mssql+pyodbc://sa:SS12345#@localhost/ProyectoFutbol?driver=ODBC+Driver+17+for+SQL+Server")

# 2. CONSULTA SQL
# Busca los jugadores con mas tarjetas amarillas
consulta_sql = """
SELECT TOP 5
    j.nombre AS NombreJugador,
    COUNT(t.id_evento) AS CantidadAmarillas
FROM tarjeta t
JOIN evento ev ON t.id_evento = ev.id_evento
JOIN jugador j ON ev.id_jugador = j.id_jugador
WHERE t.color LIKE '%Amarilla%' OR t.color LIKE '%Yellow%'
GROUP BY j.nombre
ORDER BY CantidadAmarillas DESC;
"""

# 3. EJECUTAR CONSULTA
print("Buscando jugadores con mas tarjetas amarillas...")
dataframe_tarjetas = pandas.read_sql(consulta_sql, motor_base_datos)

# 4. VERIFICAR QUE HAYA DATOS
if len(dataframe_tarjetas) == 0:
    print("No se encontraron datos para esta consulta")
    exit()

print("Datos obtenidos:")
print(dataframe_tarjetas.to_string(index=False))

# 5. CREAR LA GRAFICA
print("Dibujando grafica de jugadores con mas tarjetas amarillas...")

# Crear figura
figura, grafica = matplotlib.pyplot.subplots(figsize=(10, 6))
figura.suptitle('Jugadores con mas tarjetas amarillas en Mundiales y Champions', 
                fontsize=14, fontweight='bold')

# --------------------------------------------------
# BARRAS HORIZONTALES (para nombres largos)
# --------------------------------------------------
lista_jugadores = dataframe_tarjetas['NombreJugador'].tolist()
lista_amarillas = dataframe_tarjetas['CantidadAmarillas'].tolist()
posiciones_y = range(len(lista_jugadores))

# Colores en tonos amarillos (mas oscuro el que tiene mas tarjetas)
colores = ['#b8860b', '#cd9b1d', '#dbb42c', '#e0b642', '#e6c35c']
colores = colores[:len(lista_jugadores)]  # solo los que necesitamos

# Barras horizontales
barras = grafica.barh(
    posiciones_y,
    lista_amarillas,
    color=colores,
    alpha=0.8,
    edgecolor='black',
    linewidth=1
)

grafica.set_xlabel('Cantidad de tarjetas amarillas')
grafica.set_ylabel('Jugador')
grafica.set_title('Top 5 jugadores mas amonestados')
grafica.set_yticks(posiciones_y)
grafica.set_yticklabels(lista_jugadores)
grafica.grid(axis='x', alpha=0.3, linestyle='--')

# Agregar el valor exacto al final de cada barra
for indice, (barra, valor) in enumerate(zip(barras, lista_amarillas)):
    ancho = barra.get_width()
    grafica.text(
        ancho + 0.2,           # posicion x (al final de la barra)
        barra.get_y() + barra.get_height()/2.,  # centro de la barra
        f'{int(valor)} tarjetas',  # texto
        va='center',            # centrado vertical
        fontsize=10,
        fontweight='bold'
    )

# Agregar linea vertical con el promedio
if len(lista_amarillas) > 1:
    promedio_amarillas = sum(lista_amarillas) / len(lista_amarillas)
    grafica.axvline(
        x=promedio_amarillas,
        color='red',
        linestyle='--',
        linewidth=2,
        alpha=0.7,
        label=f'Promedio top 5: {promedio_amarillas:.1f} tarjetas'
    )
    grafica.legend()

# --------------------------------------------------
# AJUSTES FINALES
# --------------------------------------------------
matplotlib.pyplot.tight_layout()

# 6. GUARDAR LA GRAFICA
nombre_archivo = '7.png'
matplotlib.pyplot.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
print(f"Grafica guardada como: {nombre_archivo}")

matplotlib.pyplot.show()
print("Listo!")