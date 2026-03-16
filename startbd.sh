#!/bin/bash

# Salir si algun comando falla
set -e

echo "Iniciando bd en SQL Server :D"
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'SS12345#' -i DDL.sql


# Usar venv
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Entorno virtual activado :3"
else
    echo "No se encontro la carpeta venv. Asegurate de estar en la raiz."
    exit 1
fi



cd pandas

echo "--------------------------------------"
echo "Cargando competiciones con pandas..."
python3 1-competitions.py

echo "--------------------------------------"
echo "Cargando partidos con pandas..."
python3 2-cargar_partidos.py

echo "--------------------------------------"
echo "Cargando alineaciones con pandas..."
python3 3-alineaciones.py

echo "--------------------------------------"
echo "Cargando eventos con pandas..."
python3 4-eventos.py

echo "--------------------------------------"
echo "Proceso terminado exitosamente!"