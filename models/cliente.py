from services.seguridad import generar_hash, verificar_contrasena


# Modulos a los que accede cada rol. El administrador mantiene el catalogo;
# el cliente reserva y consulta lo suyo
PERMISOS_POR_ROL = {
    "administrador": ["destinos", "paquetes", "cuenta"],
    "cliente": ["catalogo", "reservar", "mis_reservas", "cuenta"]
}


# Clase que representa a una persona registrada en el sistema.
# El administrador es un rol, no una clase aparte: la misma persona con los
# mismos datos de contacto, lo que cambia es lo que puede hacer
class Cliente:

    LARGO_MINIMO_CONTRASENA = 8

    # El constructor recibe el hash, nunca la contrasena en claro. Asi un
    # cliente que viene de la base no vuelve a hashear lo que ya es un hash
    def __init__(self, nombre, rut, correo, telefono, contrasena_hash,
                 rol="cliente", id_cliente=None):

        self.__id_cliente = id_cliente
        self.__nombre = nombre
        self.__rut = rut
        self.__correo = correo
        self.__telefono = telefono
        self.__contrasena_hash = contrasena_hash
        self.__rol = rol

        self.__validar()

    # R9 del caso, mas la validacion de rol
    def __validar(self):
        if not self.__nombre or len(self.__nombre.strip()) < 3:
            raise ValueError("El nombre del cliente es obligatorio.")

        if not self.__rut or len(self.__rut.strip()) < 8:
            raise ValueError("El RUT no es valido.")

        if not self.__correo or "@" not in self.__correo:
            raise ValueError("El correo electronico no es valido.")

        if not self.__telefono or len(self.__telefono.strip()) < 8:
            raise ValueError("El telefono no es valido.")

        if self.__rol not in PERMISOS_POR_ROL:
            raise ValueError("El rol debe ser administrador o cliente.")

    # Crea un cliente nuevo a partir de una contrasena en claro. Es el unico
    # punto del sistema donde se genera un hash (R10)
    @classmethod
    def registrar(cls, nombre, rut, correo, telefono, contrasena,
                  rol="cliente"):
        cls.validar_contrasena(contrasena)

        return cls(
            nombre=nombre,
            rut=cls.normalizar_rut(rut),
            correo=cls.normalizar_correo(correo),
            telefono=telefono,
            contrasena_hash=generar_hash(contrasena),
            rol=rol
        )

    # Reconstruye el objeto a partir de una fila de la tabla cliente
    @classmethod
    def desde_fila(cls, fila):
        return cls(
            id_cliente=fila[0],
            nombre=fila[1],
            rut=fila[2],
            correo=fila[3],
            telefono=fila[4],
            contrasena_hash=fila[5],
            rol=fila[6]
        )

    # Politica minima de contrasenas del sistema
    @classmethod
    def validar_contrasena(cls, contrasena):
        if not contrasena or len(contrasena) < cls.LARGO_MINIMO_CONTRASENA:
            raise ValueError(
                f"La contrasena debe tener al menos "
                f"{cls.LARGO_MINIMO_CONTRASENA} caracteres."
            )

        if contrasena.isdigit() or contrasena.isalpha():
            raise ValueError(
                "La contrasena debe combinar letras y numeros."
            )

    # Saneamiento: el correo identifica al cliente, asi que dos formas de
    # escribirlo no pueden dar dos cuentas distintas
    @staticmethod
    def normalizar_correo(correo):
        if not correo:
            raise ValueError("El correo electronico es obligatorio.")

        return correo.strip().lower()

    # El RUT se guarda sin puntos y con el digito verificador en minuscula
    @staticmethod
    def normalizar_rut(rut):
        if not rut:
            raise ValueError("El RUT es obligatorio.")

        return rut.strip().replace(".", "").replace(" ", "").lower()

    # --- Comportamiento propio del cliente --------------------------------

    # Compara la contrasena ingresada con el hash almacenado
    def autenticar(self, contrasena):
        if not contrasena:
            return False

        return verificar_contrasena(contrasena, self.__contrasena_hash)

    def cambiar_contrasena(self, nueva_contrasena):
        Cliente.validar_contrasena(nueva_contrasena)

        self.__contrasena_hash = generar_hash(nueva_contrasena)

    # Responde si el rol alcanza para usar un modulo del sistema
    def tiene_permiso(self, permiso):
        return permiso in PERMISOS_POR_ROL.get(self.__rol, [])

    # --- Acceso controlado ------------------------------------------------

    def obtener_id(self):
        return self.__id_cliente

    def obtener_nombre(self):
        return self.__nombre

    def obtener_correo(self):
        return self.__correo

    def obtener_rol(self):
        return self.__rol

    # R17: el RUT y el telefono son datos sensibles. Existen estos metodos
    # porque el propio cliente puede ver sus datos, pero ningun listado del
    # sistema los usa
    def obtener_rut(self):
        return self.__rut

    def obtener_telefono(self):
        return self.__telefono

    # El hash se entrega solo al repositorio, para poder guardarlo
    def obtener_contrasena_hash(self):
        return self.__contrasena_hash

    def asignar_id(self, id_cliente):
        if self.__id_cliente is not None:
            raise ValueError("El cliente ya tiene un identificador asignado.")

        self.__id_cliente = id_cliente

    # R17: la representacion por omision no muestra RUT ni telefono, porque
    # es la que terminaria en un listado o en un mensaje de error
    def __str__(self):
        return f"[{self.__id_cliente}] {self.__nombre} · {self.__correo}"
