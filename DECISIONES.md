# Decisiones tecnicas y trazabilidad

Este documento conecta el caso con el codigo: donde esta implementada cada
regla de negocio, que decisiones se tomaron cuando el caso no alcanzaba, y
que se hizo con lo que sugirio la IA.

---

## 1. Las 17 reglas del caso, una por una

| Regla | Que exige | Donde esta |
|---|---|---|
| R1 | Datos del destino; el nombre no se repite | `models/destino.py` → `__validar()` · `UNIQUE` en la tabla `destino` |
| R2 | El costo base es mayor que cero | `models/destino.py` → `__validar()` y `actualizar_costo()` |
| R3 | Entre 2 y 5 destinos, sin repetir | `models/paquete.py` → `__validar_destinos()` · PK compuesta de `paquete_destino` |
| R4 | Un destino puede estar en varios paquetes | Tabla intermedia `paquete_destino` |
| R5 | Fechas y cupo del paquete; regreso posterior a salida | `models/paquete.py` → `__validar()` |
| R6 | Precio = suma de costos + margen; margen nunca negativo | `models/paquete.py` → `__calcular_precio()` |
| R7 | El precio queda fijado al publicar | Columna `precio_por_persona` almacenada; `__a_objeto()` la lee en vez de recalcular |
| R8 | Destino libre se elimina; destino en uso se retira | `services/destino_service.py` → `eliminar_destino()` y `retirar_destino()` |
| R9 | Datos del cliente; el correo no se repite | `models/cliente.py` → `__validar()` · `UNIQUE` en la tabla `cliente` |
| R10 | La contrasena nunca se almacena tal cual | `services/seguridad.py` → `generar_hash()` |
| R11 | Solo autenticado reserva, y ve unicamente lo suyo | `main.py` → el menu exige sesion · `reserva_service.py` → `listar_por_cliente()` y `buscar_de_cliente()` |
| R12 | La reserva registra fecha, personas y total | `models/reserva.py` → constructor |
| R13 | El total se calcula al reservar y no cambia | `models/paquete.py` → `calcular_total()` · columna `total` almacenada |
| R14 | No se acepta una reserva sobre el cupo disponible | `services/reserva_service.py` → `reservar()` · `paquete_service.personas_reservadas()` |
| R15 | No se reserva un paquete con salida vencida | `models/paquete.py` → `salida_vencida()` · `paquete_service.listar_vigentes()` |
| R16 | Al menos una persona por reserva | `models/reserva.py` → `__validar()` |
| R17 | RUT y telefono no se muestran en listados ni errores | `models/cliente.py` → `__str__()` los omite · mensajes de error genericos |

---

## 2. Como el sistema corrige cada problema medido en el caso

| Problema de la temporada | Cantidad | Como lo resuelve el sistema |
|---|---|---|
| Reservas duplicadas | 19 | El correo es `UNIQUE` y cada reserva se emite con su identificador: no hay dos formas de escribir al mismo cliente |
| Reservas por sobre el cupo | 6 | `cupo_disponible()` compara contra las personas ya reservadas antes de aceptar |
| Reservas sobre salidas vencidas | 3 | `salida_vencida()` compara la fecha de salida con la del dia |
| Paquetes cobrados a otro precio | 4 | El precio se congela al crear el paquete y no se recalcula nunca |
| Consultas revisando el cuaderno | 31 | `listar_por_cliente()` entrega el historial en una consulta |
| Destinos no operados aun visibles | 4 | La columna `disponible` los saca de la oferta sin borrarlos |

---

## 3. Las cuatro decisiones de diseno que hay que poder defender

### 3.1 El precio del paquete se guarda, no se calcula al leer

La alternativa era calcular el precio cada vez, sumando los costos de los
destinos. Se descarto porque R7 exige lo contrario: si manana sube el costo
del Salar de Surire, un paquete vendido en julio tiene que seguir valiendo
lo que valia en julio. Calcularlo al leer reproduce exactamente el problema
que el caso detecto: cuatro paquetes cobrados a un precio distinto del
publicado.

El costo es una columna mas en la tabla y un dato que queda desactualizado
respecto de sus destinos. Eso no es un defecto: es el requisito.

### 3.2 El destino en uso se retira, no se borra

La guia oficial dice "eliminar destinos existentes", pero R8 del caso lo
precisa: un destino que forma parte de un paquete no se elimina, se marca
como no disponible. Se siguio la regla del caso porque borrarlo dejaria sin
contenido a paquetes ya vendidos, que es justo lo que a la socia le impide
limpiar su planilla.

El sistema hace las dos cosas segun corresponda: `eliminar_destino()`
consulta primero en cuantos paquetes participa, y si participa en alguno,
rechaza la operacion y sugiere retirarlo.

### 3.3 El administrador es un rol, no una subclase

La alternativa era una clase `Administrador` que heredara de `Cliente`. Se
descarto porque un socio puede dejar de administrar el catalogo sin dejar de
ser una persona registrada, y con herencia habria que destruir el objeto y
crear otro. El rol es una columna, y los permisos se resuelven con
`tiene_permiso()`.

### 3.4 El total de la reserva lo calcula el paquete

`Paquete.calcular_total()` es un metodo del paquete, no del repositorio ni
del menu. El paquete es quien conoce su precio, asi que es quien sabe cuanto
cuesta reservarlo para N personas. El repositorio solo persiste el resultado.

---

## 4. Supuestos declarados

El caso advierte que no entrega toda la informacion y pide declarar los
supuestos. Estos son los que se adoptaron:

| Vacio del caso | Supuesto adoptado | Fundamento |
|---|---|---|
| Que ocurre si un cliente desiste de una reserva | No se implementa anulacion en esta version | Anular libera cupo y obliga a definir devoluciones, que estan fuera del alcance acordado |
| Como se comporta un paquete cuando su temporada termina | Deja de aparecer en el catalogo del cliente, pero se conserva en la base | Las reservas ya emitidas tienen que seguir siendo consultables |
| Quien puede modificar el catalogo | Solo el rol administrador | El caso dice que el administrador "mantiene el catalogo"; ningun cliente tiene ese permiso |
| Si un destino no disponible debe seguir visible para el cliente | No aparece al armar paquetes nuevos, pero si dentro de los paquetes que ya lo incluian | Es la lectura literal de R8 |
| Formato del RUT | Se normaliza sin puntos y con el digito verificador en minuscula | Evita que el mismo RUT entre dos veces escrito distinto |
| Cuanta historia migrar del cuaderno | No se migra: el sistema parte vacio | La migracion de datos no esta en el alcance de la primera version |

---

## 5. Analisis del codigo generado con apoyo de IA

> Completar con los prompts textuales que uso cada integrante.

| Aspecto revisado | Problema detectado | Decision | Fundamento tecnico |
|---|---|---|---|
| Calculo del precio del paquete | La propuesta calculaba el precio en cada consulta, sumando los costos de los destinos | Modificar | Contradice R7: un cambio de costo alteraria los paquetes ya vendidos. Se guarda el precio en la tabla |
| Eliminacion de destinos | Se propuso un `DELETE` directo | Modificar | R8 exige conservar el destino si pertenece a un paquete. Se agrego la columna `disponible` y la verificacion previa |
| Hash de contrasenas | Se propuso `hashlib.sha256` simple | Descartar | Sin salt es vulnerable a tablas precalculadas. Se uso `scrypt` con salt aleatorio por contrasena |
| Comparacion de hashes | Se comparaba con `==` | Modificar | Permite un ataque por tiempo de respuesta. Se uso `hmac.compare_digest` |
| Consulta del cupo | Se proponia contar reservas en vez de sumar personas | Modificar | Una reserva de cuatro personas ocupa cuatro cupos, no uno. Se uso `SUM(cantidad_personas)` |
| Listado de clientes | Mostraba RUT y telefono | Modificar | R17 los declara sensibles. El `__str__` los omite y existen metodos de acceso aparte |
| Construccion de consultas | Se armaba el SQL concatenando los datos | Descartar | Habilita inyeccion SQL. Todas las consultas usan parametros `?` |
| Manejo de errores | Un unico `except Exception` | Modificar | Oculta la causa. Se separaron `ValueError` y `sqlite3.Error`, del mas concreto al mas general |

---

## 6. Lo que falta para la entrega

El codigo es una de las dos evidencias. El informe tecnico grupal necesita
ademas:

- Catalogo de requerimientos funcionales y no funcionales, numerado y
  priorizado
- Diagrama de casos de uso con sus fichas
- Diagrama BPMN del proceso de reserva
- Diagrama de clases UML
- Planificacion agil: roles, Product Backlog y Sprint Backlog
- Los prompts reales usados con la IA
