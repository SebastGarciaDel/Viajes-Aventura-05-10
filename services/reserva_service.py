import sqlite3
from datetime import date

from database.conexion import conectar
from models.reserva import Reserva


# Repositorio de reservas. Aqui se concentran las reglas que el caso
# identifico como el origen de sus problemas: el cupo, la fecha vencida
# y el total congelado
class ReservaService:

    COLUMNAS = (
        "id_reserva, id_cliente, id_paquete, fecha_emision, "
        "cantidad_personas, total"
    )

    def __init__(self, servicio_paquete, ruta=None):
        self.__servicio_paquete = servicio_paquete
        self.__ruta = ruta

    def __conectar(self):
        if self.__ruta:
            return conectar(self.__ruta)

        return conectar()

    def __a_objeto(self, fila):
        return Reserva(
            id_reserva=fila[0],
            id_cliente=fila[1],
            id_paquete=fila[2],
            fecha_emision=fila[3],
            cantidad_personas=fila[4],
            total=fila[5]
        )

    # C · Reservar un paquete. Las tres reglas se comprueban antes de
    # escribir nada: fecha vigente, cupo suficiente y total calculado
    def reservar(self, cliente, paquete, cantidad_personas, hoy=None):
        referencia = hoy if hoy else date.today()

        # R16: al menos una persona. La validacion esta en el objeto Reserva,
        # pero se adelanta aqui para no calcular un total con un numero malo
        if cantidad_personas is None or cantidad_personas < 1:
            raise ValueError("La reserva debe ser de al menos una persona.")

        # R15: no se reserva un paquete cuya fecha de salida ya paso
        if paquete.salida_vencida(referencia):
            raise ValueError(
                f"El paquete '{paquete.obtener_nombre()}' salio el "
                f"{paquete.obtener_fecha_salida()} y ya no admite reservas."
            )

        # R14: el cupo disponible es el cupo maximo menos lo ya reservado
        disponible = self.__servicio_paquete.cupo_disponible(paquete)

        if cantidad_personas > disponible:
            raise ValueError(
                f"Quedan {disponible} cupo(s) en ese paquete y usted pidio "
                f"{cantidad_personas}."
            )

        # R13: el total se calcula con el precio vigente del paquete y queda
        # fijo. El objeto Paquete es quien sabe calcularlo
        total = paquete.calcular_total(cantidad_personas)

        reserva = Reserva(
            id_cliente=cliente.obtener_id(),
            id_paquete=paquete.obtener_id(),
            cantidad_personas=cantidad_personas,
            total=total,
            fecha_emision=referencia.isoformat()
        )

        conexion = None

        try:
            conexion = self.__conectar()

            cursor = conexion.execute("""
                INSERT INTO reserva
                    (id_cliente, id_paquete, fecha_emision,
                     cantidad_personas, total)
                VALUES (?, ?, ?, ?, ?)
            """, (
                reserva.obtener_id_cliente(),
                reserva.obtener_id_paquete(),
                reserva.obtener_fecha_emision(),
                reserva.obtener_cantidad_personas(),
                reserva.obtener_total()
            ))

            reserva.asignar_id(cursor.lastrowid)
            conexion.commit()

            return reserva

        except sqlite3.IntegrityError as error:
            if conexion:
                conexion.rollback()

            raise ValueError(
                "No se pudo registrar la reserva. Revise que el paquete "
                "siga publicado."
            ) from error

        except sqlite3.Error as error:
            if conexion:
                conexion.rollback()

            raise sqlite3.Error(
                "No se pudo registrar la reserva."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R11 · El historial de un cliente. La consulta filtra siempre por el
    # cliente de la sesion: no existe forma de pedir las reservas de otro
    def listar_por_cliente(self, id_cliente):
        conexion = None

        try:
            conexion = self.__conectar()

            filas = conexion.execute(
                f"SELECT {self.COLUMNAS} FROM reserva "
                "WHERE id_cliente = ? ORDER BY fecha_emision DESC",
                (id_cliente,)
            ).fetchall()

            return [self.__a_objeto(f) for f in filas]

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo consultar el historial de reservas."
            ) from error

        finally:
            if conexion:
                conexion.close()

    # R · Una reserva concreta, verificando que sea de quien la pide
    def buscar_de_cliente(self, id_reserva, id_cliente):
        conexion = None

        try:
            conexion = self.__conectar()

            fila = conexion.execute(
                f"SELECT {self.COLUMNAS} FROM reserva WHERE id_reserva = ?",
                (id_reserva,)
            ).fetchone()

            if fila is None:
                return None

            reserva = self.__a_objeto(fila)

            # R11: aunque alguien adivine el id de otra reserva, el objeto
            # responde que no le pertenece y el sistema la trata como
            # inexistente
            if not reserva.pertenece_a(id_cliente):
                return None

            return reserva

        except sqlite3.Error as error:
            raise sqlite3.Error(
                "No se pudo consultar la reserva."
            ) from error

        finally:
            if conexion:
                conexion.close()
