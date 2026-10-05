from datetime import date


# Clase que representa la reserva de un paquete por parte de un cliente
class Reserva:

    def __init__(self, id_cliente, id_paquete, cantidad_personas, total,
                 fecha_emision=None, id_reserva=None):

        self.__id_reserva = id_reserva
        self.__id_cliente = id_cliente
        self.__id_paquete = id_paquete
        self.__cantidad_personas = cantidad_personas

        # R13: el total llega ya calculado por el paquete, con el precio que
        # estaba vigente al reservar, y no vuelve a cambiar
        self.__total = total

        # R12: la reserva registra la fecha en que se emitio
        if fecha_emision:
            self.__fecha_emision = fecha_emision
        else:
            self.__fecha_emision = date.today().isoformat()

        self.__validar()

    # R12 y R16 del caso
    def __validar(self):
        if self.__id_cliente is None:
            raise ValueError("La reserva debe corresponder a un cliente.")

        if self.__id_paquete is None:
            raise ValueError("La reserva debe corresponder a un paquete.")

        # R16: la cantidad de personas es al menos uno
        if self.__cantidad_personas is None or self.__cantidad_personas < 1:
            raise ValueError("La reserva debe ser de al menos una persona.")

        if self.__total is None or self.__total <= 0:
            raise ValueError("El total de la reserva debe ser mayor que cero.")

    # --- Acceso controlado ------------------------------------------------

    def obtener_id(self):
        return self.__id_reserva

    def obtener_id_cliente(self):
        return self.__id_cliente

    def obtener_id_paquete(self):
        return self.__id_paquete

    def obtener_fecha_emision(self):
        return self.__fecha_emision

    def obtener_cantidad_personas(self):
        return self.__cantidad_personas

    def obtener_total(self):
        return self.__total

    def asignar_id(self, id_reserva):
        if self.__id_reserva is not None:
            raise ValueError("La reserva ya tiene un identificador asignado.")

        self.__id_reserva = id_reserva

    # R11: cada cliente ve unicamente sus reservas. El objeto puede responder
    # por si mismo si pertenece a quien pregunta
    def pertenece_a(self, id_cliente):
        return self.__id_cliente == id_cliente

    def __str__(self):
        return (
            f"[{self.__id_reserva}] emitida {self.__fecha_emision} · "
            f"{self.__cantidad_personas} persona(s) · "
            f"total ${self.__total:,.0f}"
        )
