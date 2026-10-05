import sqlite3

from database.conexion import conectar
from models.cliente import Cliente


# Repositorio de clientes y punto de entrada de la autenticacion
class ClienteService:

    COLUMNAS = (
        "id_cliente, nombre, rut, correo, telefono, contrasena_hash, rol"
    )

    def __init__(self, ruta=None):
        self.__ruta = ruta

    def __conectar(self):
        if self.__ruta:
            return conectar(self.__ruta)

        return conectar()

    # C · Guarda el hash, nunca la contrasena en claro (R10)
    def crear_cliente(self, cliente):
        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute("""
                INSERT INTO cliente
                    (nombre, rut, correo, telefono, contrasena_hash, rol)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cliente.obtener_nombre(),
                cliente.obtener_rut(),
                cliente.obtener_correo(),
                cliente.obtener_telefono(),
                cliente.obtener_contrasena_hash(),
                cliente.obtener_rol()
            ))

            cliente.asignar_id(cursor.lastrowid)
            conexion.commit()

            return cliente

        except sqlite3.IntegrityError as error:
            if conexion:
                conexion.rollback()

            # R9: el correo identifica al cliente y no se repite. El mensaje
            # no revela cual de los dos datos choco, porque el RUT es sensible
            raise ValueError(
                "Ya existe una cuenta registrada con esos datos."
            ) from error

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo registrar el cliente."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R · Devuelve un objeto Cliente, no una tupla
    def buscar_por_correo(self, correo):
        conexion = None

        try:
            conexion = self.__conectar()

            fila = conexion.execute(
                f"SELECT {self.COLUMNAS} FROM cliente WHERE correo = ?",
                (Cliente.normalizar_correo(correo),)
            ).fetchone()

            if fila is None:
                return None

            return Cliente.desde_fila(fila)

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo consultar la cuenta."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # Cuenta los administradores: sirve para saber si hay que crear el
    # primero al arrancar el sistema
    def contar_administradores(self):
        conexion = None

        try:
            conexion = self.__conectar()

            fila = conexion.execute(
                "SELECT COUNT(*) FROM cliente WHERE rol = 'administrador'"
            ).fetchone()

            return fila[0]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo verificar las cuentas del sistema."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # U
    def cambiar_contrasena(self, cliente, nueva_contrasena):
        # El objeto valida la politica de contrasenas y genera el hash
        cliente.cambiar_contrasena(nueva_contrasena)

        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute(
                "UPDATE cliente SET contrasena_hash = ? WHERE id_cliente = ?",
                (cliente.obtener_contrasena_hash(), cliente.obtener_id())
            )

            if cursor.rowcount == 0:
                raise ValueError("La cuenta indicada no existe.")

            conexion.commit()

            return cursor.rowcount

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo cambiar la contrasena."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # Autenticacion: devuelve el cliente si las credenciales calzan
    def autenticar(self, correo, contrasena):
        if not correo or not contrasena:
            return None

        cliente = self.buscar_por_correo(correo)

        # Se responde lo mismo si el correo no existe o si la contrasena esta
        # mala: no se le confirma a nadie que una cuenta esta registrada
        if cliente is None:
            return None

        if not cliente.autenticar(contrasena):
            return None

        return cliente
