import sqlite3

from database.conexion import conectar
from models.destino import Destino


# Repositorio de destinos: aqui vive todo el SQL de la tabla destino
class DestinoService:

    # Las columnas se nombran siempre, en el mismo orden que espera
    # __a_objeto. No se usa SELECT * para no arrastrar columnas de mas
    COLUMNAS = (
        "id_destino, nombre, zona, descripcion, duracion, "
        "costo_base, disponible"
    )

    def __init__(self, ruta=None):
        # La ruta llega por parametro para poder apuntar a otra base en pruebas
        self.__ruta = ruta

    def __conectar(self):
        if self.__ruta:
            return conectar(self.__ruta)

        return conectar()

    # Convierte una fila de la base en un objeto Destino
    def __a_objeto(self, fila):
        return Destino(
            id_destino=fila[0],
            nombre=fila[1],
            zona=fila[2],
            descripcion=fila[3],
            duracion=fila[4],
            costo_base=fila[5],
            disponible=bool(fila[6])
        )

    # C · Registra un destino y le devuelve el id que asigno la base
    def crear_destino(self, destino):
        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute("""
                INSERT INTO destino
                    (nombre, zona, descripcion, duracion, costo_base, disponible)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                destino.obtener_nombre(),
                destino.obtener_zona(),
                destino.obtener_descripcion(),
                destino.obtener_duracion(),
                destino.obtener_costo_base(),
                1 if destino.esta_disponible() else 0
            ))

            destino.asignar_id(cursor.lastrowid)
            conexion.commit()

            return destino

        except sqlite3.IntegrityError as error:
            if conexion:
                conexion.rollback()

            # R1: el nombre no se repite en el catalogo
            raise ValueError(
                "Ya existe un destino con ese nombre en el catalogo."
            ) from error

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo registrar el destino."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R · Devuelve todos los destinos como objetos, no como tuplas
    def listar_destinos(self, solo_disponibles=False):
        conexion = None

        try:
            conexion = self.__conectar()

            if solo_disponibles:
                filas = conexion.execute(
                    f"SELECT {self.COLUMNAS} FROM destino "
                    "WHERE disponible = 1 ORDER BY nombre"
                ).fetchall()
            else:
                filas = conexion.execute(
                    f"SELECT {self.COLUMNAS} FROM destino ORDER BY nombre"
                ).fetchall()

            return [self.__a_objeto(f) for f in filas]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudieron consultar los destinos."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R · Busca un destino por su identificador
    def buscar_por_id(self, id_destino):
        conexion = None

        try:
            conexion = self.__conectar()

            fila = conexion.execute(
                f"SELECT {self.COLUMNAS} FROM destino WHERE id_destino = ?",
                (id_destino,)
            ).fetchone()

            # Un id que no existe devuelve None y quien llama decide que hacer
            if fila is None:
                return None

            return self.__a_objeto(fila)

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo consultar el destino."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R · Los destinos que componen un paquete
    def listar_por_paquete(self, id_paquete):
        conexion = None

        try:
            conexion = self.__conectar()

            filas = conexion.execute(
                f"SELECT d.id_destino, d.nombre, d.zona, d.descripcion, "
                "d.duracion, d.costo_base, d.disponible "
                "FROM destino d "
                "INNER JOIN paquete_destino pd ON d.id_destino = pd.id_destino "
                "WHERE pd.id_paquete = ? ORDER BY d.nombre",
                (id_paquete,)
            ).fetchall()

            return [self.__a_objeto(f) for f in filas]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudieron consultar los destinos del paquete."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # Cuenta en cuantos paquetes participa un destino. R8 depende de esto
    def contar_paquetes(self, id_destino):
        conexion = None

        try:
            conexion = self.__conectar()

            fila = conexion.execute(
                "SELECT COUNT(*) FROM paquete_destino WHERE id_destino = ?",
                (id_destino,)
            ).fetchone()

            return fila[0]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo verificar el uso del destino."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # U · El objeto valida los datos nuevos antes de que se toque la base
    def actualizar_destino(self, destino, nombre, zona, descripcion, duracion):
        destino.actualizar_datos(nombre, zona, descripcion, duracion)

        return self.__guardar_cambios(destino)

    # U · Cambiar el costo no altera el precio de los paquetes ya publicados
    def actualizar_costo(self, destino, nuevo_costo):
        destino.actualizar_costo(nuevo_costo)

        return self.__guardar_cambios(destino)

    # Escribe en la base el estado actual del objeto
    def __guardar_cambios(self, destino):
        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute("""
                UPDATE destino
                SET nombre = ?, zona = ?, descripcion = ?,
                    duracion = ?, costo_base = ?, disponible = ?
                WHERE id_destino = ?
            """, (
                destino.obtener_nombre(),
                destino.obtener_zona(),
                destino.obtener_descripcion(),
                destino.obtener_duracion(),
                destino.obtener_costo_base(),
                1 if destino.esta_disponible() else 0,
                destino.obtener_id()
            ))

            # rowcount avisa si el UPDATE no encontro la fila
            if cursor.rowcount == 0:
                raise ValueError("El destino indicado no existe.")

            conexion.commit()

            return cursor.rowcount

        except sqlite3.IntegrityError as error:
            if conexion:
                conexion.rollback()

            raise ValueError(
                "Ya existe un destino con ese nombre en el catalogo."
            ) from error

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo actualizar el destino."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R8 · Retira el destino de la oferta sin borrarlo, para que los paquetes
    # ya vendidos conserven su contenido
    def retirar_destino(self, destino):
        destino.marcar_no_disponible()

        return self.__guardar_cambios(destino)

    # D · Solo elimina de verdad un destino que no pertenece a ningun paquete.
    # Es la otra mitad de R8, y la regla la decide el repositorio porque
    # necesita consultar la base para saberlo
    def eliminar_destino(self, destino):
        if self.contar_paquetes(destino.obtener_id()) > 0:
            raise ValueError(
                "Ese destino forma parte de un paquete, asi que no se elimina. "
                "Use la opcion de retirarlo de la oferta."
            )

        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute(
                "DELETE FROM destino WHERE id_destino = ?",
                (destino.obtener_id(),)
            )

            if cursor.rowcount == 0:
                raise ValueError("El destino indicado no existe.")

            conexion.commit()

            return cursor.rowcount

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo eliminar el destino."
            ) from error

        finally:
            if conexion:
                conexion.close()
