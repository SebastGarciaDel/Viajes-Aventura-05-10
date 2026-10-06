# Viajes Aventura · Sistema de Gestion

### Integrantes 

Marcela Sepulveda - Lider de proyecto
Sebastian Garcia

###


TI3V21 Programacion Orientada a Objeto Seguro · INACAP Valparaiso
Evaluacion Sumativa 4 · Unidad 4

Sistema en Python que gestiona el catalogo de destinos, los paquetes
turisticos y las reservas de clientes de la agencia Viajes Aventura, con
persistencia en SQLite y acceso autenticado por rol.

## Como se ejecuta

### Windows · simbolo del sistema (cmd)

```
py -m venv .venv
.venv\Scripts\activate.bat
py main.py
```

### Windows · PowerShell

```
py -m venv .venv
.venv\Scripts\Activate.ps1
py main.py
```

### macOS y Linux

```
python3 -m venv .venv
source .venv/bin/activate
python3 main.py
```

El sistema no tiene dependencias externas: usa solo la biblioteca estandar
de Python, asi que no hace falta instalar nada.

Conviene ejecutar desde la terminal y no con el boton de reproduccion del
editor: el inicio de sesion usa `getpass`, que necesita una terminal real
para ocultar la contrasena mientras se escribe.

### La primera ejecucion

Crea el archivo `viajes.db` y pide crear la cuenta del socio administrador.
La contrasena no se muestra mientras se escribe, y debe tener al menos 8
caracteres combinando letras y numeros. Despues se inicia sesion con ese
mismo correo y contrasena.

Para empezar de cero en cualquier momento se borra `viajes.db`: la base se
vuelve a crear vacia en la siguiente ejecucion.

## Estructura del proyecto

```
viajes_aventura/
  database/
    conexion.py                 conexion y creacion de las tablas
  models/                       las clases del diagrama UML
    destino.py
    paquete.py
    cliente.py
    reserva.py
  services/                     repositorios: aqui vive todo el SQL
    destino_service.py
    paquete_service.py
    cliente_service.py
    reserva_service.py
    seguridad.py                hash de contrasenas
  main.py                       registro, login, menu y flujo del sistema
  pruebas.py                    pruebas de las reglas de negocio
```

La separacion entre `models/` y `services/` es el patron repositorio: la
clase representa la cosa, el repositorio la lleva y la trae de la base.
Ninguna clase de dominio contiene SQL, y ningun repositorio contiene reglas
de negocio propias del dominio.

## Las cuatro entidades y sus relaciones

| Relacion | Multiplicidad | En la base de datos |
|---|---|---|
| Paquete — Destino | 2..5 a 0..* | Tabla `paquete_destino` con clave primaria compuesta |
| Cliente — Reserva | 1 a 0..* | FK `reserva.id_cliente` con `ON DELETE CASCADE` |
| Paquete — Reserva | 1 a 0..* | FK `reserva.id_paquete`, sin cascada |

Un paquete combina varios destinos y un destino participa en varios
paquetes: esa relacion muchos a muchos no cabe en una columna y necesita su
propia tabla. La clave primaria compuesta de `paquete_destino` es la que
impide que un destino se repita dentro del mismo paquete.

La reserva es composicion respecto del cliente —sin su cliente no significa
nada— y por eso lleva cascada. Respecto del paquete es asociacion: un
paquete no se elimina si tiene reservas, el repositorio lo impide antes.

## Los dos roles

| Rol | Que puede hacer |
|---|---|
| Administrador | Mantener el catalogo de destinos y armar los paquetes |
| Cliente | Ver los paquetes vigentes, reservar y consultar su historial |

El administrador es un rol, no una clase aparte: la misma persona con los
mismos datos de contacto. Lo que cambia es lo que puede hacer, no lo que
es. El menu se arma solo con las opciones que el rol permite, de modo que
las demas no aparecen en vez de aparecer y bloquearse.

## Seguridad aplicada

| Requisito | Como se implementa |
|---|---|
| Contrasenas protegidas | `hashlib.scrypt` con salt aleatorio por contrasena; se compara con `hmac.compare_digest`, en tiempo constante. Nunca se guarda el texto original |
| Acceso restringido | Sin sesion iniciada no se entra. `Cliente.tiene_permiso()` define los modulos por rol y el menu se arma con ellos |
| Aislamiento entre clientes | Las consultas de reservas filtran siempre por el cliente de la sesion, y el objeto `Reserva` responde por si mismo si pertenece a quien pregunta |
| Validacion de entradas | Validacion en los constructores de las clases de dominio y conversion controlada de lo que se escribe en el menu |
| Datos sensibles | El RUT y el telefono tienen metodos de acceso, pero ningun listado ni mensaje de error los usa |
| Prevencion de inyeccion SQL | Todas las consultas usan parametros `?`. No hay concatenacion ni f-strings con datos en ningun SQL |
| Restricciones en la base | `NOT NULL`, `UNIQUE` en nombre de destino, correo y RUT, `PRIMARY KEY` y `FOREIGN KEY` con `PRAGMA foreign_keys = ON` |
| Mensajes de error | El usuario recibe que paso y que hacer; el detalle tecnico queda encadenado con `raise ... from error` |

## Librerias utilizadas

Todas de la biblioteca estandar de Python, que es el repositorio oficial del
lenguaje:

| Modulo | Para que |
|---|---|
| `sqlite3` | Conexion y operaciones sobre la base de datos |
| `hashlib` | Hash de contrasenas con scrypt |
| `hmac` | Comparacion de hashes en tiempo constante |
| `os` | Generacion del salt aleatorio |
| `datetime` | Fechas de salida, regreso y emision |
| `getpass` | Lectura de contrasenas sin mostrarlas en pantalla |

## Pruebas

`py pruebas.py` ejecuta 26 casos que intentan violar las reglas del caso y
comprueban que el sistema las rechaza. Usa una base temporal: no toca `viajes.db`.

## Trazabilidad de las reglas de negocio

Las 17 reglas del caso estan implementadas y ubicadas en `DECISIONES.md`,
con el archivo y el metodo donde se aplica cada una.
