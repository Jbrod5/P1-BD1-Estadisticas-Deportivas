# P1-BD1-s-Deportivas
P1-BD1-Estadisticas-Deportivas con SQL Server

## Instalar SQL Server

Los pasos para la instalación de SQL Server están en el documento descriptivo de la base de datos y no son necesarios del todo aquí porque los entornos ya están preparados :D.



## Crear la base de datos
Para ejecutar el script DDL.sql:

```sh
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'SS12345#' -i DDL.sql
```


## Preparacion del entorno 


Por comodidad se utilizará venv por portabilidad entre computadoras. 
Debian no incluye pip ni venv por defecto. Instalarlas:

### 1.  Instalar y usar venv

```sh
sudo apt install python3-venv python3-pip
```

Para utilizar venv, ejecutar dentro de la carpeta del repo de git:

```sh
source venv/bin/activate
```

### 2. Instalar el driver para SQL Server

```sh
# Importar las llaves de Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc

# Añadir el repositorio de MS para Debian
# (Esto es para Debian 12 pero en debian 13 funciono bien xd)
curl https://packages.microsoft.com/config/debian/12/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

sudo apt update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools unixodbc-dev
```