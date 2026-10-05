import sqlite3

from database.conexion import conectar
from models.paquete import Paquete


# Repositorio de paquetes turisticos
class PaqueteService:

    COLUMNAS = (
        "id_paquete, nombre, fecha_salida, fecha_regreso, "
        "cupo_maximo, margen, precio_por_persona"
    )

    def __init__(self, servicio_destino, ruta=None):
        # Necesita el repositorio de destinos para poder reconstruir cada
        # paquete con los destinos que combina
        self.__servicio_destino = servicio_destino
        self.__ruta = ruta

    def __conectar(self):
        if self.__ruta:
            return conectar(self.__ruta)

        return conectar()

    # Convierte una fila en un objeto Paquete con sus destinos cargados.
    # El precio viaja desde la base: no se recalcula (R7)
    def __a_objeto(self, fila):
        paquete = Paquete(
            id_paquete=fila[0],
            nombre=fila[1],
            fecha_salida=fila[2],
            fecha_regreso=fila[3],
            cupo_maximo=fila[4],
            margen=fila[5],
            precio_por_persona=fila[6],
            destinos=self.__servicio_destino.listar_por_paquete(fila[0])
        )

        return paquete

    # C · Guarda el paquete y sus destinos en una sola transaccion
    def crear_paquete(self, paquete):
        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute("""
                INSERT INTO paquete
                    (nombre, fecha_salida, fecha_regreso, cupo_maximo,
                     margen, precio_por_persona)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                paquete.obtener_nombre(),
                paquete.obtener_fecha_salida(),
                paquete.obtener_fecha_regreso(),
                paquete.obtener_cupo_maximo(),
                paquete.obtener_margen(),
                paquete.obtener_precio()
            ))

            id_paquete = cursor.lastrowid
            paquete.asignar_id(id_paquete)

            # Los destinos del paquete se guardan en la tabla intermedia
            conexion.executemany(
                "INSERT INTO paquete_destino (id_paquete, id_destino) "
                "VALUES (?, ?)",
                [(id_paquete, d.obtener_id()) for d in paquete.obtener_destinos()]
            )

            # Un solo commit al final: o queda el paquete con sus destinos,
            # o no queda nada
            conexion.commit()

            return paquete

        except sqlite3.IntegrityError as error:
            if conexion:
                conexion.rollback()

            raise ValueError(
                "No se pudo crear el paquete. Revise que los destinos "
                "existan y que ninguno se repita."
            ) from error

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo crear el paquete."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R
    def listar_paquetes(self):
        conexion = None

        try:
            conexion = self.__conectar()

            filas = conexion.execute(
                f"SELECT {self.COLUMNAS} FROM paquete ORDER BY fecha_salida"
            ).fetchall()

            return [self.__a_objeto(f) for f in filas]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudieron consultar los paquetes."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R · Solo los paquetes que el cliente todavia puede reservar.
    # R15 se aplica en la consulta: no se ofrece lo que ya salio
    def listar_vigentes(self, hoy):
        conexion = None

        try:
            conexion = self.__conectar()

            filas = conexion.execute(
                f"SELECT {self.COLUMNAS} FROM paquete "
                "WHERE fecha_salida >= ? ORDER BY fecha_salida",
                (hoy,)
            ).fetchall()

            return [self.__a_objeto(f) for f in filas]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudieron consultar los paquetes vigentes."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R
    def buscar_por_id(self, id_paquete):
        conexion = None

        try:
            conexion = self.__conectar()

            fila = conexion.execute(
                f"SELECT {self.COLUMNAS} FROM paquete WHERE id_paquete = ?",
                (id_paquete,)
            ).fetchone()

            if fila is None:
                return None

            return self.__a_objeto(fila)

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo consultar el paquete."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R14 · Cuantas personas hay ya reservadas en un paquete
    def personas_reservadas(self, id_paquete):
        conexion = None

        try:
            conexion = self.__conectar()

            # COALESCE devuelve 0 cuando el paquete no tiene reservas, en vez
            # de un None que reventaria mas adelante
            fila = conexion.execute(
                "SELECT COALESCE(SUM(cantidad_personas), 0) "
                "FROM reserva WHERE id_paquete = ?",
                (id_paquete,)
            ).fetchone()

            return fila[0]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo calcular el cupo del paquete."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # Combina el cupo maximo del objeto con las reservas de la base
    def cupo_disponible(self, paquete):
        reservadas = self.personas_reservadas(paquete.obtener_id())

        return paquete.cupo_disponible(reservadas)

    # D · Un paquete con reservas no se elimina: borrarlo dejaria sin
    # respaldo a clientes que ya pagaron
    def eliminar_paquete(self, id_paquete):
        if self.personas_reservadas(id_paquete) > 0:
            raise ValueError(
                "Ese paquete tiene reservas, asi que no se elimina."
            )

        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute(
                "DELETE FROM paquete WHERE id_paquete = ?",
                (id_paquete,)
            )

            if cursor.rowcount == 0:
                raise ValueError("El paquete indicado no existe.")

            conexion.commit()

            return cursor.rowcount

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo eliminar el paquete."
            ) from error

        finally:
            if conexion:
                conexion.close()
