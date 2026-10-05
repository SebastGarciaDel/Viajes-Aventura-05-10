# Clase que representa un destino del catalogo de Viajes Aventura
class Destino:

    # El id llega en None cuando el destino todavia no se guarda,
    # porque lo asigna la base de datos
    def __init__(self, nombre, zona, descripcion, duracion, costo_base,
                 id_destino=None, disponible=True):

        # Atributos privados: es el signo - del diagrama de clases
        self.__id_destino = id_destino
        self.__nombre = nombre
        self.__zona = zona
        self.__descripcion = descripcion
        self.__duracion = duracion
        self.__costo_base = costo_base
        self.__disponible = disponible

        # La validacion va en el constructor: asi es imposible que exista
        # un destino con datos invalidos
        self.__validar()

    # R1 y R2 del caso: datos obligatorios y costo mayor que cero
    def __validar(self):
        if not self.__nombre or len(self.__nombre.strip()) < 3:
            raise ValueError("El nombre del destino es obligatorio.")

        if not self.__zona or not self.__zona.strip():
            raise ValueError("La zona del destino es obligatoria.")

        if self.__duracion is None or self.__duracion < 1:
            raise ValueError("La duracion debe ser de al menos un dia.")

        # R2: el costo base es siempre mayor que cero
        if self.__costo_base is None or self.__costo_base <= 0:
            raise ValueError("El costo base debe ser mayor que cero.")

    # --- Acceso controlado a los atributos privados -----------------------

    def obtener_id(self):
        return self.__id_destino

    def obtener_nombre(self):
        return self.__nombre

    def obtener_zona(self):
        return self.__zona

    def obtener_descripcion(self):
        return self.__descripcion

    def obtener_duracion(self):
        return self.__duracion

    def obtener_costo_base(self):
        return self.__costo_base

    def esta_disponible(self):
        return self.__disponible

    # El repositorio usa esto despues del INSERT para entregarle al objeto
    # el identificador que asigno la base
    def asignar_id(self, id_destino):
        if self.__id_destino is not None:
            raise ValueError("El destino ya tiene un identificador asignado.")

        self.__id_destino = id_destino

    # --- Comportamiento propio del destino --------------------------------

    # Cambia el costo base validando antes de asignar.
    # R7: esto NO afecta a los paquetes ya publicados, porque ellos guardan
    # su propio precio en vez de recalcularlo
    def actualizar_costo(self, nuevo_costo):
        if nuevo_costo is None or nuevo_costo <= 0:
            raise ValueError("El costo base debe ser mayor que cero.")

        self.__costo_base = nuevo_costo

    def actualizar_datos(self, nombre, zona, descripcion, duracion):
        if not nombre or len(nombre.strip()) < 3:
            raise ValueError("El nombre del destino es obligatorio.")

        if duracion is None or duracion < 1:
            raise ValueError("La duracion debe ser de al menos un dia.")

        self.__nombre = nombre
        self.__zona = zona
        self.__descripcion = descripcion
        self.__duracion = duracion

    # R8: un destino que pertenece a un paquete no se elimina, se retira de
    # la oferta. Asi los paquetes ya vendidos conservan su contenido
    def marcar_no_disponible(self):
        if not self.__disponible:
            raise ValueError("El destino ya estaba fuera de la oferta.")

        self.__disponible = False

    def marcar_disponible(self):
        self.__disponible = True

    # Representacion legible para los listados del menu
    def __str__(self):
        estado = "" if self.__disponible else "  [no disponible]"

        return (
            f"[{self.__id_destino}] {self.__nombre} · {self.__zona} · "
            f"{self.__duracion} dias · ${self.__costo_base:,.0f}{estado}"
        )
