# Sistema de Gestión de Almacén (versión simple)

Programa de escritorio para manejar el depósito de un supermercado: categorías, proveedores, productos con lotes que vencen, compras y stock (consulta y descuento).

Trabajo Práctico Final de Programación Orientada a Objetos. La consigna está en `docs/consigna_TP_Final_POO.pdf`.

Hecho con **Python**, **PySide6** (formularios), **MySQL** y **SQLAlchemy** (conexión). Extras del grupo, en su forma más simple: login con contraseña cifrada (**bcrypt**), lector de códigos de barras USB y exportar el stock a Excel (**openpyxl**).

## Archivos

```
main.py                         arranca el programa

negocio.py                      CAPA DE NEGOCIO: todas las clases y las excepciones
                                (Producto, Lote, Compra, Salida, Usuario...)
datos.py                        CAPA DE DATOS: la conexión a MySQL y un DAO por tabla

presentacion/                   CAPA DE PRESENTACIÓN
    ventanas.py                 Login y menú principal
    abm.py                      Categorías, Proveedores y Productos
    operaciones.py              Compras y Stock (consulta, descontar y Excel)
    util.py                     grilla, buscador, mensajes y colores

script_bd.sql                   base de datos con datos de prueba
docs/                           diagramas (UML, DER), capturas y presentación
```

Dentro de cada archivo, cada clase tiene un título con guiones que la separa de la siguiente.

## Qué hace falta

- **Python 3.11** o más nuevo (al instalarlo, marcar "Add Python to PATH").
- **MySQL Server** y **MySQL Workbench**.

Para bajarlo: botón verde **Code** → **Download ZIP** y descomprimirlo. El paso a paso, con los errores más comunes, está en `COMO_INICIAR.txt`.

## Cómo ejecutarlo

1. Iniciar el servicio de MySQL.
2. Abrir `script_bd.sql` en MySQL Workbench y ejecutarlo completo (botón del rayo). Crea la base `almacen_simple`.
3. Copiar `config.example.toml` con el nombre `config.toml` y escribir la contraseña de MySQL entre las comillas de `password = ""`. Ese archivo no está en el repositorio a propósito: cada uno pone la suya.
4. Instalar las librerías (solo la primera vez):
   ```
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
5. Ejecutar:
   ```
   .venv\Scripts\python main.py
   ```

Usuarios: `admin` / `admin123` y `operador` / `operador123`.

## Qué pide la consigna y dónde está

| Requisito | Dónde |
|---|---|
| 3 capas | `presentacion/`, `negocio.py`, `datos.py` |
| Encapsulamiento | Atributos privados con `__` y acceso con `@property` en todas las clases de `negocio.py` |
| Herencia | `Producto` → `ProductoPerecedero` y `ProductoNoPerecedero`. Las clases que se guardan con su propio id heredan de `Entidad`. Las excepciones heredan de `ErrorAlmacen` |
| Polimorfismo | `tipo()` y `requiere_vencimiento()` responden distinto en cada producto |
| Excepciones | Conexión: `traducir_error()` en `datos.py`. Conversión de números: `leer_numero()` en `util.py`. Validaciones: `ErrorValidacion` en los setters |
| ≥ 3 tablas con PK y FK, relación 1‑N y N‑M | 8 tablas. 1‑N: producto → lote. N‑M: compra ↔ producto con `compra_detalle` |
| Stored procedure | `sp_descontar` |
| Trigger | `trg_compra_crea_lote` y `trg_lote_sin_negativos` |
| Transacciones | `sp_descontar` (START TRANSACTION / COMMIT / ROLLBACK), guardar una compra y crear un producto con su stock inicial (`Conexion.ejecutar_varios`) |
| Menú principal | `VentanaPrincipal` en `ventanas.py` |
| ABM con texto, fecha y checkbox, con validaciones | `abm.py`: Categorías, Proveedores y Productos. Proveedores tiene la fecha de alta con calendario |
| Grilla actualizada | Se recarga cada vez que se entra a la pantalla y después de guardar |
| ComboBox desde la base | Categoría y Proveedor en Productos; Proveedor y Producto en Compras; productos con stock en Stock |
| ABM de ≥ 2 entidades | Categorías, Proveedores y Productos |
| Mapeo manual a objetos | Cada DAO arma los objetos a partir de las filas |
| Buscador en tiempo real | Campo "Buscar..." en cada grilla (`filtrar_tabla`) |
| Módulo transaccional | Compras (registro con varios productos) y Descontar en Stock |
| Script SQL | `script_bd.sql` |
| UML y DER | `docs/diagramas.drawio` (se abre en draw.io; tiene 4 pestañas: Arquitectura, Diagrama de clases, DER y Flujo para descontar) |
| Presentación | `docs/presentacion.pptx` |

## Guía para la defensa

**¿Dónde está el encapsulamiento?**
En `negocio.py`. Por ejemplo, en la clase `Producto` el precio es `self.__precio`: con doble guion bajo no se puede usar desde afuera. Se lee con la propiedad `precio`, y el setter controla que sea mayor a cero.

**¿Dónde está la herencia?**
`ProductoPerecedero` y `ProductoNoPerecedero` heredan de `Producto`. El perecedero llama a `super().__init__(...)` y agrega `dias_alerta`. El no perecedero no agrega atributos, así que usa directamente el constructor de `Producto`.

**¿Dónde está el polimorfismo?**
`Producto` tiene dos métodos abstractos, `tipo()` y `requiere_vencimiento()`, y cada hija los responde distinto. En Compras, la pantalla llama a `producto.requiere_vencimiento()` sin saber qué tipo es, y según la respuesta habilita la fecha de vencimiento.

**¿Por qué `Producto` es abstracta?**
Porque no existe un producto "genérico": siempre es perecedero o no perecedero. Si se intenta crear un `Producto` directamente, Python da error.

**¿Qué es un DAO?**
Una clase que se encarga de una tabla: escribe el SQL, lo ejecuta y convierte cada fila en un objeto. Así la pantalla nunca trabaja con filas de la base, solo con objetos.

**¿Cómo manejan los errores?**
Cada botón tiene un `try / except ErrorAlmacen` y muestra el mensaje. Hay tres casos:
- **Falla MySQL:** `traducir_error()` lo convierte en un mensaje claro (sin conexión, dato repetido, registro en uso).
- **Se escribe texto donde va un número:** `leer_numero()` atrapa el `ValueError`.
- **Falta un dato o está mal:** los setters lanzan `ErrorValidacion`.

**¿Dónde hay transacciones?**
- **Al guardar una compra:** la cabecera y todos sus productos se guardan juntos con `ejecutar_varios`. Si uno falla, no se guarda nada.
- **Al crear un producto:** el producto y su primer lote (el stock inicial) se guardan juntos con `ejecutar_varios`.
- **En el procedimiento `sp_descontar`:** usa `START TRANSACTION`, `COMMIT` y, si hay error, `ROLLBACK`.

**¿Qué hacen los triggers?**
- `trg_compra_crea_lote`: cada producto que se compra crea su lote solo.
- `trg_lote_sin_negativos`: impide que un lote quede con cantidad negativa.

**¿Qué hace el procedimiento?**
Lo usa el botón **Descontar** de la pantalla Stock. `sp_descontar` revisa que haya stock y descuenta empezando por el lote que vence antes; los lotes vencidos no se usan. Después registra la salida en la tabla `salida`.

**¿Cómo se conectan Productos y Stock?**
Productos es el catálogo y Stock muestra cuánto hay de cada uno. Un producto nuevo se crea con su **stock inicial**, así no existe un producto que no esté en el depósito. Después el stock sube con **Compras** y baja con **Descontar**, que solo deja elegir productos que tienen stock.

**¿Cómo se modifica un producto?**
Se elige en la grilla y se ve bloqueado. Recién al tocar **Editar producto** se puede cambiar el nombre, el precio o el stock. Si el stock sube, se agrega un lote; si baja, se descuenta con `sp_descontar`, igual que en Stock. El mismo botón pasa a decir **Cancelar edición** para salir sin guardar.

**¿Cómo funciona el lector de códigos?**
El lector USB funciona como un teclado: escribe el código y presiona Enter. El campo "Lector de códigos" detecta ese Enter y busca el producto.
