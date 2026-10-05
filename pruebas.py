"""Pruebas de las reglas de negocio. Cada caso intenta violar una regla y
comprueba que el sistema la rechaza (o, en los casos felices, que la acepta).
Ejecutar:  py pruebas.py   (usa una base temporal, no toca viajes.db)"""
import os
import sqlite3
import tempfile
from datetime import date, timedelta

from database.conexion import crear_tablas, conectar
from models.destino import Destino
from models.paquete import Paquete
from models.cliente import Cliente
from services.destino_service import DestinoService
from services.paquete_service import PaqueteService
from services.cliente_service import ClienteService
from services.reserva_service import ReservaService

RUTA = os.path.join(tempfile.mkdtemp(), "prueba.db")
crear_tablas(RUTA)
ds = DestinoService(RUTA)
ps = PaqueteService(ds, RUTA)
cs = ClienteService(RUTA)
rs = ReservaService(ps, RUTA)

resultados = []


def caso(regla, descripcion, funcion, debe_fallar):
    try:
        funcion()
        ok = not debe_fallar
    except (ValueError, sqlite3.Error):
        ok = debe_fallar
    resultados.append((regla, descripcion, ok))
    print(f"{'OK   ' if ok else 'FALLA'} {regla:<4} {descripcion}")


def destino(nombre, costo=100000):
    d = Destino(nombre, "Norte", "Descripcion del destino", 2, costo)
    ds.crear_destino(d)
    return d


def paquete(nombre, ds_, salida=30, cupo=10, margen=0.2):
    hoy = date.today()
    p = Paquete(nombre, (hoy + timedelta(days=salida)).isoformat(),
                (hoy + timedelta(days=salida + 5)).isoformat(), cupo, margen, ds_)
    ps.crear_paquete(p)
    return p


def cliente(correo, rut, rol="cliente"):
    c = Cliente.registrar("Persona Prueba", rut, correo, "912345678", "clave1234", rol)
    cs.crear_cliente(c)
    return c


# --- datos base ---
a, b, c3, c4, c5, c6 = (destino(f"Destino {i}", 100000 * i) for i in range(1, 7))
cl = cliente("uno@correo.cl", "11111111-1")
otro = cliente("dos@correo.cl", "22222222-2")

# R1 / R2
caso("R1", "Nombre de destino repetido se rechaza", lambda: destino("Destino 1"), True)
caso("R2", "Costo base cero se rechaza", lambda: Destino("X Valido", "Z", "Descripcion", 1, 0), True)
# R3 / R4
caso("R3", "Paquete con 1 destino se rechaza", lambda: paquete("P-uno", [a]), True)
caso("R3", "Paquete con 6 destinos se rechaza", lambda: paquete("P-seis", [a, b, c3, c4, c5, c6]), True)
caso("R3", "Paquete con destino repetido se rechaza", lambda: paquete("P-rep", [a, a]), True)
p1 = paquete("Norte Grande", [a, b])
caso("R4", "Un destino puede estar en varios paquetes", lambda: paquete("Norte Clasico", [a, c3]), False)
# R5 / R6
caso("R5", "Regreso anterior a la salida se rechaza",
     lambda: Paquete("Mal", date.today().isoformat(),
                     (date.today() - timedelta(days=1)).isoformat(), 5, 0, [a, b]), True)
caso("R6", "Margen negativo se rechaza",
     lambda: Paquete("Mal2", (date.today() + timedelta(days=9)).isoformat(),
                     (date.today() + timedelta(days=12)).isoformat(), 5, -1, [a, b]), True)
caso("R6", "Precio = suma de costos x (1 + margen)",
     lambda: (_ for _ in ()).throw(ValueError()) if p1.obtener_precio() != round(300000 * 1.2) else None, False)
# R7
ds.actualizar_costo(a, 999999)
caso("R7", "Subir el costo de un destino no cambia el precio publicado",
     lambda: (_ for _ in ()).throw(ValueError())
     if ps.buscar_por_id(p1.obtener_id()).obtener_precio() != 360000 else None, False)
# R8
caso("R8", "Destino en un paquete no se elimina", lambda: ds.eliminar_destino(a), True)
caso("R8", "Destino en un paquete se retira (queda no disponible)", lambda: ds.retirar_destino(a), False)
caso("R8", "Destino sin uso se elimina", lambda: ds.eliminar_destino(c6), False)
# R9 / R10
caso("R9", "Correo repetido se rechaza", lambda: cliente("uno@correo.cl", "33333333-3"), True)
caso("R9", "Contrasena sin numeros se rechaza",
     lambda: Cliente.registrar("Persona X", "44444444-4", "x@c.cl", "912345678", "sololetras"), True)
def _hash_no_claro():
    fila = conectar(RUTA).execute("SELECT contrasena_hash FROM cliente WHERE correo=?", ("uno@correo.cl",)).fetchone()
    if "clave1234" in fila[0]:
        raise ValueError()
caso("R10", "La contrasena no se guarda en claro", _hash_no_claro, False)
caso("R10", "Contrasena correcta autentica", lambda: None if cs.autenticar("uno@correo.cl", "clave1234") else (_ for _ in ()).throw(ValueError()), False)
caso("R10", "Contrasena incorrecta no autentica", lambda: None if not cs.autenticar("uno@correo.cl", "otraclave1") else (_ for _ in ()).throw(ValueError()), False)
# R11
r1 = rs.reservar(cl, p1, 2)
caso("R11", "Un cliente no ve la reserva de otro",
     lambda: None if rs.buscar_de_cliente(r1.obtener_id(), otro.obtener_id()) is None else (_ for _ in ()).throw(ValueError()), False)
# R12 / R13
caso("R13", "Total = precio x personas",
     lambda: None if r1.obtener_total() == 360000 * 2 else (_ for _ in ()).throw(ValueError()), False)
# R14
p2 = paquete("Cupo Chico", [b, c3], cupo=3)
rs.reservar(cl, p2, 2)
caso("R14", "Reserva sobre el cupo disponible se rechaza", lambda: rs.reservar(otro, p2, 2), True)
caso("R14", "Reserva dentro del cupo se acepta", lambda: rs.reservar(otro, p2, 1), False)
# R15
caso("R15", "Paquete con salida vencida no admite reservas",
     lambda: rs.reservar(cl, p1, 1, hoy=date.today() + timedelta(days=60)), True)
# R16
caso("R16", "Reserva de 0 personas se rechaza", lambda: rs.reservar(cl, p1, 0), True)
# R17
caso("R17", "str(cliente) no muestra RUT ni telefono",
     lambda: (_ for _ in ()).throw(ValueError())
     if ("11111111" in str(cl) or "912345678" in str(cl)) else None, False)
# Inyeccion SQL
caso("SQL", "Correo con inyeccion SQL no rompe ni autentica",
     lambda: None if not cs.autenticar("' OR '1'='1", "x") else (_ for _ in ()).throw(ValueError()), False)

ok = sum(1 for r in resultados if r[2])
print(f"\n{ok}/{len(resultados)} pruebas correctas")
raise SystemExit(0 if ok == len(resultados) else 1)
