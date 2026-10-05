import sqlite3


# Ruta por omision de la base de datos del sistema
RUTA_BASE = "viajes.db"


# Abre una conexion con SQLite y activa el control de claves foraneas
def conectar(ruta=RUTA_BASE):
    try:
        conexion = sqlite3.connect(ruta)

        # Sin este PRAGMA, SQLite ignora las claves foraneas y las cascadas
        conexion.execute("PRAGMA foreign_keys = ON")

        return conexion

    except sqlite3.Error as error:
        raise sqlite3.Error(
            "No fue posible conectar con la base de datos."
        ) from error


# Crea todas las tablas del sistema a partir del diagrama de clases
def crear_tablas(ruta=RUTA_BASE):
    conexion = None

    try:
        conexion = conectar(ruta)
        cursor = conexion.cursor()

        # destino · R1: el nombre no se repite en el catalogo
        # R8: no se borra si pertenece a un paquete, se marca no disponible,
        # por eso existe la columna disponible en vez de un DELETE directo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS destino (
                id_destino  INTEGER PRIMARY KEY,
                nombre      TEXT    NOT NULL UNIQUE,
                zona        TEXT    NOT NULL,
                descripcion TEXT,
                duracion    INTEGER NOT NULL,
                costo_base  REAL    NOT NULL,
                disponible  INTEGER NOT NULL DEFAULT 1
            )
        """)

        # paquete · R6 y R7: el precio se calcula una vez al crear el paquete
        # y queda guardado. Si despues cambia el costo de un destino, este
        # valor no se toca: es la correccion del problema que detecto el caso
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paquete (
                id_paquete        INTEGER PRIMARY KEY,
                nombre            TEXT    NOT NULL,
                fecha_salida      TEXT    NOT NULL,
                fecha_regreso     TEXT    NOT NULL,
                cupo_maximo       INTEGER NOT NULL,
                margen            REAL    NOT NULL,
                precio_por_persona REAL   NOT NULL
            )
        """)

        # paquete_destino · R4: un destino puede estar en varios paquetes y un
        # paquete combina varios destinos. La relacion muchos a muchos necesita
        # su propia tabla. La clave primaria compuesta aplica R3: un destino no
        # se repite dentro del mismo paquete
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paquete_destino (
                id_paquete INTEGER NOT NULL,
                id_destino INTEGER NOT NULL,
                PRIMARY KEY (id_paquete, id_destino),
                FOREIGN KEY (id_paquete)
                    REFERENCES paquete(id_paquete)
                    ON DELETE CASCADE,
                FOREIGN KEY (id_destino)
                    REFERENCES destino(id_destino)
            )
        """)

        # cliente · R9: el correo identifica al cliente y no se repite.
        # R10: se guarda el hash, nunca la contrasena escrita.
        # El rol distingue al administrador: es un rol, no una clase aparte
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cliente (
                id_cliente      INTEGER PRIMARY KEY,
                nombre          TEXT NOT NULL,
                rut             TEXT NOT NULL UNIQUE,
                correo          TEXT NOT NULL UNIQUE,
                telefono        TEXT NOT NULL,
                contrasena_hash TEXT NOT NULL,
                rol             TEXT NOT NULL DEFAULT 'cliente'
            )
        """)

        # reserva · R12 y R13: el total se calcula al reservar y queda guardado.
        # Es composicion respecto del cliente: una reserva sin su cliente no
        # significa nada, por eso la cascada
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reserva (
                id_reserva        INTEGER PRIMARY KEY,
                id_cliente        INTEGER NOT NULL,
                id_paquete        INTEGER NOT NULL,
                fecha_emision     TEXT    NOT NULL,
                cantidad_personas INTEGER NOT NULL,
                total             REAL    NOT NULL,
                FOREIGN KEY (id_cliente)
                    REFERENCES cliente(id_cliente)
                    ON DELETE CASCADE,
                FOREIGN KEY (id_paquete)
                    REFERENCES paquete(id_paquete)
            )
        """)

        conexion.commit()

    except sqlite3.Error as error:
        if conexion:
            conexion.rollback()

        raise sqlite3.Error(
            "No fue posible crear las tablas de la base de datos."
        ) from error

    finally:
        if conexion:
            conexion.close()
