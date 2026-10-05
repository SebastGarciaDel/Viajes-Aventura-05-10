from datetime import date
from getpass import getpass

from database.conexion import crear_tablas

from models.cliente import Cliente
from models.destino import Destino
from models.paquete import Paquete

from services.cliente_service import ClienteService
from services.destino_service import DestinoService
from services.paquete_service import PaqueteService
from services.reserva_service import ReservaService


# --- Entradas del usuario, validadas antes de llegar a las clases ---------

# Pide un texto y no acepta que quede vacio
def pedir_texto(mensaje, obligatorio=True):
    valor = input(mensaje).strip()

    if obligatorio and not valor:
        raise ValueError("Ese dato es obligatorio.")

    return valor


# Pide un numero entero y avisa con un ejemplo si lo escrito no lo es
def pedir_entero(mensaje):
    texto = input(mensaje).strip()

    try:
        return int(texto)

    except ValueError as error:
        raise ValueError(
            f"'{texto}' no es un numero entero. Ejemplo: 3"
        ) from error


# Pide un numero decimal
def pedir_decimal(mensaje):
    texto = input(mensaje).strip()

    try:
        return float(texto)

    except ValueError as error:
        raise ValueError(
            f"'{texto}' no es un numero. Ejemplo: 120000"
        ) from error


# Pide una fecha y comprueba el formato antes de seguir
def pedir_fecha(mensaje):
    texto = input(mensaje).strip()

    try:
        date.fromisoformat(texto)

    except ValueError as error:
        raise ValueError(
            f"'{texto}' no es una fecha valida. Use AAAA-MM-DD, "
            "por ejemplo 2026-07-15"
        ) from error

    return texto


# --- Autenticacion --------------------------------------------------------

# Si la base esta vacia, se crea la cuenta del socio administrador
def asegurar_administrador(servicio_cliente):
    if servicio_cliente.contar_administradores() > 0:
        return

    print("\nNo hay cuentas de administrador en el sistema.")
    print("Cree la cuenta del socio que mantendra el catalogo.\n")

    while True:
        try:
            administrador = Cliente.registrar(
                nombre=pedir_texto("Nombre: "),
                rut=pedir_texto("RUT: "),
                correo=pedir_texto("Correo: "),
                telefono=pedir_texto("Telefono: "),
                contrasena=getpass("Contrasena (minimo 8, letras y numeros): "),
                rol="administrador"
            )

            servicio_cliente.crear_cliente(administrador)

            print("Cuenta de administrador creada. Ahora inicie sesion.\n")
            return

        except ValueError as error:
            print(f"No se pudo crear: {error}\n")


# Registro de un cliente nuevo. R9 y R10
def registrar_cliente(servicio_cliente):
    print("\n--- REGISTRO DE CLIENTE ---")

    cliente = Cliente.registrar(
        nombre=pedir_texto("Nombre completo: "),
        rut=pedir_texto("RUT: "),
        correo=pedir_texto("Correo: "),
        telefono=pedir_texto("Telefono: "),
        contrasena=getpass("Contrasena (minimo 8, letras y numeros): ")
    )

    servicio_cliente.crear_cliente(cliente)

    print(f"\nCuenta creada para {cliente.obtener_correo()}. Ya puede entrar.")


# Pide credenciales y devuelve la cuenta autenticada
def iniciar_sesion(servicio_cliente):
    intentos = 3

    while intentos > 0:
        print("\n--- INICIO DE SESION ---")

        correo = input("Correo: ")
        contrasena = getpass("Contrasena: ")

        cuenta = servicio_cliente.autenticar(correo, contrasena)

        if cuenta is not None:
            print(
                f"\nBienvenido/a {cuenta.obtener_nombre()} "
                f"· {cuenta.obtener_rol()}"
            )
            return cuenta

        intentos -= 1

        # No se dice si fallo el correo o la contrasena: eso le confirmaria
        # a quien prueba credenciales que una cuenta existe
        print(f"Credenciales incorrectas. Intentos restantes: {intentos}")

    print("Demasiados intentos fallidos.")
    return None


# --- Gestion de destinos · solo administrador -----------------------------

def crear_destino(servicios, cuenta):
    destino = Destino(
        nombre=pedir_texto("Nombre del destino: "),
        zona=pedir_texto("Zona: "),
        descripcion=pedir_texto("Descripcion: ", obligatorio=False),
        duracion=pedir_entero("Duracion en dias: "),
        costo_base=pedir_decimal("Costo base por persona: ")
    )

    servicios["destino"].crear_destino(destino)

    print(f"Destino creado con el id {destino.obtener_id()}.")


def listar_destinos(servicios, cuenta):
    destinos = servicios["destino"].listar_destinos()

    if not destinos:
        print("El catalogo esta vacio.")
        return

    print("\n--- CATALOGO DE DESTINOS ---")

    for destino in destinos:
        print(destino)


def actualizar_destino(servicios, cuenta):
    destino = buscar_destino(servicios)

    if destino is None:
        return

    servicios["destino"].actualizar_destino(
        destino,
        pedir_texto("Nombre nuevo: "),
        pedir_texto("Zona nueva: "),
        pedir_texto("Descripcion nueva: ", obligatorio=False),
        pedir_entero("Duracion en dias: ")
    )

    print("Destino actualizado.")


def actualizar_costo(servicios, cuenta):
    destino = buscar_destino(servicios)

    if destino is None:
        return

    servicios["destino"].actualizar_costo(
        destino, pedir_decimal("Costo base nuevo: ")
    )

    # El aviso es parte de la regla R7: el cambio no se propaga hacia atras
    print(
        "Costo actualizado. Los paquetes ya publicados conservan el precio "
        "con que se vendieron."
    )


def retirar_destino(servicios, cuenta):
    destino = buscar_destino(servicios)

    if destino is None:
        return

    servicios["destino"].retirar_destino(destino)

    print(
        "Destino retirado de la oferta. Sigue visible en los paquetes que "
        "ya lo incluian."
    )


def eliminar_destino(servicios, cuenta):
    destino = buscar_destino(servicios)

    if destino is None:
        return

    servicios["destino"].eliminar_destino(destino)

    print("Destino eliminado del catalogo.")


# Busca el destino que piden varias opciones, para no repetir el mismo codigo
def buscar_destino(servicios):
    id_destino = pedir_entero("ID del destino: ")
    destino = servicios["destino"].buscar_por_id(id_destino)

    if destino is None:
        print("No existe un destino con ese id.")

    return destino


# --- Gestion de paquetes · solo administrador -----------------------------

def crear_paquete(servicios, cuenta):
    disponibles = servicios["destino"].listar_destinos(solo_disponibles=True)

    if len(disponibles) < Paquete.MINIMO_DESTINOS:
        print(
            f"Hacen falta al menos {Paquete.MINIMO_DESTINOS} destinos "
            "disponibles para armar un paquete."
        )
        return

    print("\nDestinos disponibles:")

    for destino in disponibles:
        print(f"  {destino}")

    nombre = pedir_texto("\nNombre comercial del paquete: ")
    salida = pedir_fecha("Fecha de salida (AAAA-MM-DD): ")
    regreso = pedir_fecha("Fecha de regreso (AAAA-MM-DD): ")
    cupo = pedir_entero("Cupo maximo de personas: ")

    margen = pedir_decimal(
        "Margen de operacion, por ejemplo 0.20 para un 20%: "
    )

    print(
        f"\nIndique entre {Paquete.MINIMO_DESTINOS} y "
        f"{Paquete.MAXIMO_DESTINOS} destinos, uno por linea. "
        "Escriba 0 para terminar."
    )

    elegidos = []

    while len(elegidos) < Paquete.MAXIMO_DESTINOS:
        id_destino = pedir_entero("ID del destino (0 para terminar): ")

        if id_destino == 0:
            break

        destino = servicios["destino"].buscar_por_id(id_destino)

        if destino is None:
            print("  No existe un destino con ese id.")
            continue

        if not destino.esta_disponible():
            print("  Ese destino esta retirado de la oferta.")
            continue

        elegidos.append(destino)
        print(f"  Agregado: {destino.obtener_nombre()}")

    # La clase Paquete valida la cantidad, que no se repitan y las fechas,
    # y calcula el precio. El menu no decide nada de eso
    paquete = Paquete(
        nombre=nombre,
        fecha_salida=salida,
        fecha_regreso=regreso,
        cupo_maximo=cupo,
        margen=margen,
        destinos=elegidos
    )

    servicios["paquete"].crear_paquete(paquete)

    print(
        f"\nPaquete creado con el id {paquete.obtener_id()}. "
        f"Precio por persona: ${paquete.obtener_precio():,.0f}"
    )


def listar_paquetes(servicios, cuenta):
    paquetes = servicios["paquete"].listar_paquetes()

    if not paquetes:
        print("No hay paquetes publicados.")
        return

    print("\n--- PAQUETES PUBLICADOS ---")

    for paquete in paquetes:
        disponible = servicios["paquete"].cupo_disponible(paquete)

        print(paquete)
        print(f"    cupo disponible: {disponible}")


def eliminar_paquete(servicios, cuenta):
    id_paquete = pedir_entero("ID del paquete: ")

    servicios["paquete"].eliminar_paquete(id_paquete)

    print("Paquete eliminado.")


# --- Operaciones del cliente ----------------------------------------------

# R15: el catalogo que ve el cliente solo trae paquetes vigentes
def ver_catalogo(servicios, cuenta):
    hoy = date.today().isoformat()
    paquetes = servicios["paquete"].listar_vigentes(hoy)

    if not paquetes:
        print("No hay paquetes disponibles en este momento.")
        return

    print("\n--- PAQUETES DISPONIBLES ---")

    for paquete in paquetes:
        disponible = servicios["paquete"].cupo_disponible(paquete)

        if disponible < 1:
            continue

        print(paquete)
        print(f"    cupos disponibles: {disponible}")


def reservar_paquete(servicios, cuenta):
    id_paquete = pedir_entero("ID del paquete que desea reservar: ")
    paquete = servicios["paquete"].buscar_por_id(id_paquete)

    if paquete is None:
        print("No existe un paquete con ese id.")
        return

    personas = pedir_entero("Cantidad de personas: ")

    # El repositorio comprueba fecha, cupo y total antes de escribir nada
    reserva = servicios["reserva"].reservar(cuenta, paquete, personas)

    print(
        f"\nReserva {reserva.obtener_id()} confirmada para "
        f"{paquete.obtener_nombre()}."
    )
    print(f"Total a pagar: ${reserva.obtener_total():,.0f}")


# R11: cada cliente ve unicamente sus reservas
def ver_mis_reservas(servicios, cuenta):
    reservas = servicios["reserva"].listar_por_cliente(cuenta.obtener_id())

    if not reservas:
        print("Todavia no tiene reservas registradas.")
        return

    print(f"\n--- RESERVAS DE {cuenta.obtener_nombre().upper()} ---")

    for reserva in reservas:
        paquete = servicios["paquete"].buscar_por_id(
            reserva.obtener_id_paquete()
        )

        nombre = paquete.obtener_nombre() if paquete else "paquete retirado"

        print(f"{reserva}\n    paquete: {nombre}")


# --- Cuenta · disponible para los dos roles -------------------------------

def cambiar_contrasena(servicios, cuenta):
    actual = getpass("Contrasena actual: ")

    # Se comprueba la contrasena vigente antes de permitir el cambio
    if not cuenta.autenticar(actual):
        print("La contrasena actual no es correcta.")
        return

    servicios["cliente"].cambiar_contrasena(
        cuenta, getpass("Contrasena nueva: ")
    )

    print("Contrasena actualizada.")


# --- Menu -----------------------------------------------------------------

# Cada opcion declara el modulo que necesita. El menu se arma solo con las
# que el rol de la cuenta tiene permitidas
OPCIONES = [
    ("destinos", "Registrar destino", crear_destino),
    ("destinos", "Ver catalogo de destinos", listar_destinos),
    ("destinos", "Modificar datos de un destino", actualizar_destino),
    ("destinos", "Cambiar el costo de un destino", actualizar_costo),
    ("destinos", "Retirar un destino de la oferta", retirar_destino),
    ("destinos", "Eliminar un destino", eliminar_destino),
    ("paquetes", "Crear paquete turistico", crear_paquete),
    ("paquetes", "Ver paquetes publicados", listar_paquetes),
    ("paquetes", "Eliminar paquete", eliminar_paquete),
    ("catalogo", "Ver paquetes disponibles", ver_catalogo),
    ("reservar", "Reservar un paquete", reservar_paquete),
    ("mis_reservas", "Ver mis reservas", ver_mis_reservas),
    ("cuenta", "Cambiar mi contrasena", cambiar_contrasena)
]


# Devuelve solo las opciones que el rol de la cuenta puede usar
def opciones_permitidas(cuenta):
    return [
        (titulo, accion)
        for permiso, titulo, accion in OPCIONES
        if cuenta.tiene_permiso(permiso)
    ]


def mostrar_menu(cuenta, disponibles):
    print("\n========================================")
    print("            VIAJES AVENTURA")
    print("        Sistema de Gestion Interna")
    print(f"  {cuenta.obtener_nombre()} · {cuenta.obtener_rol()}")
    print("========================================")

    for numero, (titulo, _) in enumerate(disponibles, start=1):
        print(f"{numero:>2}. {titulo}")

    print(f"{len(disponibles) + 1:>2}. Cerrar sesion")


# Menu de trabajo, ya con la sesion iniciada
def menu_principal(servicios, cuenta):
    import sqlite3

    disponibles = opciones_permitidas(cuenta)

    while True:
        mostrar_menu(cuenta, disponibles)

        opcion = input("\nSeleccione una opcion: ").strip()

        if opcion == str(len(disponibles) + 1):
            print(f"Sesion cerrada. Hasta pronto, {cuenta.obtener_nombre()}.")
            return

        try:
            indice = int(opcion)

            if indice < 1 or indice > len(disponibles):
                print("Opcion no valida.")
                continue

        except ValueError:
            print("Opcion no valida.")
            continue

        titulo, accion = disponibles[indice - 1]

        try:
            accion(servicios, cuenta)

        # Primero los errores concretos, con un mensaje para el usuario
        except ValueError as error:
            print(f"No se pudo completar: {error}")

        except sqlite3.Error as error:
            print(f"Error de base de datos: {error}")


# --- Programa principal ---------------------------------------------------

def main():
    import sqlite3

    crear_tablas()

    servicio_cliente = ClienteService()
    servicio_destino = DestinoService()
    servicio_paquete = PaqueteService(servicio_destino)

    servicios = {
        "cliente": servicio_cliente,
        "destino": servicio_destino,
        "paquete": servicio_paquete,
        "reserva": ReservaService(servicio_paquete)
    }

    asegurar_administrador(servicio_cliente)

    while True:
        print("\n========================================")
        print("            VIAJES AVENTURA")
        print("========================================")
        print(" 1. Iniciar sesion")
        print(" 2. Registrarme como cliente")
        print(" 3. Salir")

        opcion = input("\nSeleccione una opcion: ").strip()

        if opcion == "1":
            cuenta = iniciar_sesion(servicio_cliente)

            # R11: sin sesion iniciada no se entra al sistema
            if cuenta is not None:
                menu_principal(servicios, cuenta)

        elif opcion == "2":
            try:
                registrar_cliente(servicio_cliente)

            except ValueError as error:
                print(f"No se pudo registrar: {error}")

            except sqlite3.Error as error:
                print(f"Error de base de datos: {error}")

        elif opcion == "3":
            print("Sistema finalizado.")
            break

        else:
            print("Opcion no valida.")


if __name__ == "__main__":
    try:
        main()

    # Si el usuario corta con Ctrl+C o se acaba la entrada, el programa
    # termina con un mensaje y no con una traza de error
    except (KeyboardInterrupt, EOFError):
        print("\n\nSistema interrumpido por el usuario.")
