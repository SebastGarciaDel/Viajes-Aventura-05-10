from datetime import date


# Clase que representa un paquete turistico: varios destinos bajo un nombre
# comercial, con fechas, cupo y un precio que queda fijado al publicarse
class Paquete:

    # Limites de R3: un paquete combina entre dos y cinco destinos
    MINIMO_DESTINOS = 2
    MAXIMO_DESTINOS = 5

    def __init__(self, nombre, fecha_salida, fecha_regreso, cupo_maximo,
                 margen, destinos=None, precio_por_persona=None,
                 id_paquete=None):

        self.__id_paquete = id_paquete
        self.__nombre = nombre
        self.__fecha_salida = fecha_salida
        self.__fecha_regreso = fecha_regreso
        self.__cupo_maximo = cupo_maximo
        self.__margen = margen

        # Los destinos que combina el paquete, como objetos Destino
        self.__destinos = list(destinos) if destinos else []

        self.__validar()

        # R6 y R7: el precio se calcula una sola vez, al crear el paquete.
        # Cuando el paquete viene de la base ya trae el suyo y no se recalcula
        if precio_por_persona is None:
            self.__precio_por_persona = self.__calcular_precio()
        else:
            self.__precio_por_persona = precio_por_persona

    # R3, R5 y R6 del caso
    def __validar(self):
        if not self.__nombre or len(self.__nombre.strip()) < 3:
            raise ValueError("El nombre del paquete es obligatorio.")

        # R5: el cupo es mayor que cero
        if self.__cupo_maximo is None or self.__cupo_maximo < 1:
            raise ValueError("El cupo maximo debe ser de al menos una persona.")

        # R6: el margen nunca es negativo
        if self.__margen is None or self.__margen < 0:
            raise ValueError("El margen no puede ser negativo.")

        # R5: la fecha de regreso es posterior a la de salida
        salida = self.convertir_fecha(self.__fecha_salida, "salida")
        regreso = self.convertir_fecha(self.__fecha_regreso, "regreso")

        if regreso <= salida:
            raise ValueError(
                "La fecha de regreso debe ser posterior a la de salida."
            )

        self.__validar_destinos(self.__destinos)

    # R3: entre dos y cinco destinos, y ninguno se repite
    def __validar_destinos(self, destinos):
        cantidad = len(destinos)

        if cantidad < self.MINIMO_DESTINOS or cantidad > self.MAXIMO_DESTINOS:
            raise ValueError(
                f"Un paquete combina entre {self.MINIMO_DESTINOS} y "
                f"{self.MAXIMO_DESTINOS} destinos. Recibio {cantidad}."
            )

        identificadores = [d.obtener_id() for d in destinos]

        if len(set(identificadores)) != cantidad:
            raise ValueError(
                "Un destino no puede repetirse dentro del mismo paquete."
            )

    # Convierte el texto de una fecha y avisa con claridad si no sirve
    @staticmethod
    def convertir_fecha(texto, nombre_campo):
        try:
            return date.fromisoformat(str(texto))

        except (TypeError, ValueError) as error:
            raise ValueError(
                f"La fecha de {nombre_campo} debe tener el formato "
                "AAAA-MM-DD. Ejemplo: 2026-07-15"
            ) from error

    # R6: el precio por persona es la suma de los costos base de los destinos
    # incluidos, mas el margen de operacion
    def __calcular_precio(self):
        costo = sum(d.obtener_costo_base() for d in self.__destinos)

        return round(costo * (1 + self.__margen), 0)

    # --- Acceso controlado ------------------------------------------------

    def obtener_id(self):
        return self.__id_paquete

    def obtener_nombre(self):
        return self.__nombre

    def obtener_fecha_salida(self):
        return self.__fecha_salida

    def obtener_fecha_regreso(self):
        return self.__fecha_regreso

    def obtener_cupo_maximo(self):
        return self.__cupo_maximo

    def obtener_margen(self):
        return self.__margen

    def obtener_precio(self):
        return self.__precio_por_persona

    def obtener_destinos(self):
        # Se devuelve una copia para que nadie altere la lista interna
        return list(self.__destinos)

    def asignar_id(self, id_paquete):
        if self.__id_paquete is not None:
            raise ValueError("El paquete ya tiene un identificador asignado.")

        self.__id_paquete = id_paquete

    def cargar_destinos(self, destinos):
        # La usa el repositorio al reconstruir el paquete desde la base
        self.__destinos = list(destinos)

    # --- Comportamiento propio del paquete --------------------------------

    # R15: no se reserva un paquete cuya fecha de salida ya paso
    def salida_vencida(self, hoy=None):
        referencia = hoy if hoy else date.today()

        return self.convertir_fecha(self.__fecha_salida, "salida") < referencia

    # R14: el cupo disponible es el cupo maximo menos las personas ya
    # reservadas. El total de reservadas lo entrega el repositorio
    def cupo_disponible(self, personas_reservadas):
        return self.__cupo_maximo - personas_reservadas

    # R13: el total de una reserva es el precio del paquete por la cantidad
    # de personas. Se calcula aqui, con el precio congelado del paquete
    def calcular_total(self, cantidad_personas):
        if cantidad_personas is None or cantidad_personas < 1:
            raise ValueError("La reserva debe ser de al menos una persona.")

        return round(self.__precio_por_persona * cantidad_personas, 0)

    def __str__(self):
        nombres = ", ".join(d.obtener_nombre() for d in self.__destinos)

        return (
            f"[{self.__id_paquete}] {self.__nombre} · sale {self.__fecha_salida} "
            f"· cupo {self.__cupo_maximo} · ${self.__precio_por_persona:,.0f} "
            f"por persona\n    destinos: {nombres}"
        )
