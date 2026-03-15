import sqlalchemy as sa

#  usuario SA y la IP (localhost)
SERVER = 'localhost'
DATABASE = 'ProyectoFutbol'
USERNAME = 'sa'
PASSWORD = 'SS12345#' 

connection_string = (
    f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}?"
    "driver=ODBC+Driver+17+for+SQL+Server"
)

try:
    engine = sa.create_engine(connection_string)
    with engine.connect() as conn:
        print("Conectado a SQL Server desde Debian :D")
except Exception as e:
    print(f"Error :c: {e}")