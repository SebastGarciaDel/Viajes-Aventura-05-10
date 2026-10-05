import hashlib
import hmac
import os


# Parametros de scrypt. Se guardan como constantes para poder subirlos
# sin tocar el resto del codigo
COSTO_N = 16384
BLOQUE_R = 8
PARALELISMO_P = 1
LARGO_SALT = 16


# Genera el hash de una contrasena, con un salt aleatorio distinto cada vez.
# hashlib es parte de la biblioteca estandar de Python
def generar_hash(contrasena):
    if not contrasena:
        raise ValueError("La contrasena no puede estar vacia.")

    # El salt evita que dos contrasenas iguales produzcan el mismo hash
    salt = os.urandom(LARGO_SALT)

    hash_contrasena = hashlib.scrypt(
        contrasena.encode(),
        salt=salt,
        n=COSTO_N,
        r=BLOQUE_R,
        p=PARALELISMO_P
    )

    # Se guardan juntos porque el salt hace falta para verificar despues
    return salt.hex() + ":" + hash_contrasena.hex()


# Comprueba una contrasena contra el hash almacenado
def verificar_contrasena(contrasena, hash_guardado):
    try:
        salt_hex, hash_hex = hash_guardado.split(":")
        salt = bytes.fromhex(salt_hex)

        nuevo_hash = hashlib.scrypt(
            contrasena.encode(),
            salt=salt,
            n=COSTO_N,
            r=BLOQUE_R,
            p=PARALELISMO_P
        )

        # compare_digest compara en tiempo constante: no revela cuantos
        # caracteres coincidieron antes de fallar
        return hmac.compare_digest(nuevo_hash.hex(), hash_hex)

    except (ValueError, TypeError, AttributeError):
        # Un hash mal formado se trata como contrasena incorrecta, sin
        # mostrarle detalle tecnico al usuario
        return False
