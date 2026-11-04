import os
import tomllib

from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from negocio import (
    Categoria,
    Compra,
    ErrorAlmacen,
    ErrorValidacion,
    Inventario,
    LineaCompra,
    Lote,
    ProductoNoPerecedero,
    ProductoPerecedero,
    Proveedor,
    StockInsuficiente,
    Usuario,
)


# ---------------------------------------------------------------------
# Conexión a MySQL y traducción de sus errores.
# ---------------------------------------------------------------------
class ErrorBaseDatos(ErrorAlmacen):
    """No hay conexión con MySQL u otro problema de la base."""


def traducir_error(error):
    """Convierte el error de MySQL en un mensaje que entiende el usuario."""
    codigo, mensaje = 0, str(error)
    if hasattr(error, "orig") and len(error.orig.args) >= 2:
        codigo, mensaje = error.orig.args[0], error.orig.args[1]

# ejemplo de error lanzado con SIGNAL
    if codigo == 1644:  # error lanzado con SIGNAL en un trigger o procedimiento
        if "stock" in mensaje.lower(): 
            return StockInsuficiente(mensaje)   
        return ErrorValidacion(mensaje)
    if codigo == 1062:
        return ErrorValidacion("Ya existe un registro con ese dato.")
    if codigo == 3819:  # no se cumple un CHECK de la tabla
        return ErrorValidacion("Hay un dato que no cumple las reglas de la base (por ejemplo, una cantidad negativa).")
    if codigo == 1451:
        return ErrorValidacion("No se puede eliminar porque otros registros lo usan.")
    if codigo in (1045, 1049, 2003):
        return ErrorBaseDatos("No se pudo conectar a MySQL. Revise que esté iniciado y el archivo config.toml.")
    return ErrorBaseDatos(f"Error de base de datos: {mensaje}")


class Conexion:
    def __init__(self, archivo_config):
        url = os.environ.get("ALMACEN_DB_URL")  # solo se usa para pruebas
        if not url:
            with open(archivo_config, encoding="utf-8-sig") as archivo:  # acepta cualquier forma de guardar en UTF-8
                datos = tomllib.loads(archivo.read())["base_datos"]
            url = URL.create("mysql+pymysql", username=datos["usuario"], password=datos["password"],
                             host=datos["host"], port=datos["puerto"], database=datos["nombre"])
        self.__motor = create_engine(url)

    def consultar(self, sql, parametros=None):
        """SELECT: devuelve una lista de filas (cada fila es un diccionario)."""
        try:
            with self.__motor.connect() as conexion:
                resultado = conexion.execute(text(sql), parametros or {})
                return [dict(fila._mapping) for fila in resultado]
        except SQLAlchemyError as error:
            raise traducir_error(error) from error

    def ejecutar(self, sql, parametros=None):
        """INSERT, UPDATE o DELETE. Devuelve el id generado."""
        try:
            with self.__motor.begin() as conexion:
                resultado = conexion.execute(text(sql), parametros or {})
                return resultado.lastrowid
        except SQLAlchemyError as error:
            raise traducir_error(error) from error

    def ejecutar_varios(self, sentencias):
        """TRANSACCIÓN: ejecuta varias sentencias juntas.
        Si una falla se deshacen todas (ROLLBACK); si no, se guardan todas (COMMIT).
        Cada sentencia es (sql, parametros); el id del primer INSERT se puede usar
        en las siguientes con el parámetro :id_nuevo."""
        try:
            with self.__motor.begin() as conexion:
                id_nuevo = None
                for sql, parametros in sentencias:
                    parametros = dict(parametros, id_nuevo=id_nuevo)
                    resultado = conexion.execute(text(sql), parametros)
                    if id_nuevo is None:
                        id_nuevo = resultado.lastrowid
                return id_nuevo
        except SQLAlchemyError as error:
            raise traducir_error(error) from error


# ---------------------------------------------------------------------
# Clase base de todos los DAO.
# ---------------------------------------------------------------------
class DAO:
    """Clase base: todos los DAO usan la misma conexión."""

    def __init__(self, conexion):
        self._conexion = conexion


# ---------------------------------------------------------------------
# SQL de la tabla categoria.
# ---------------------------------------------------------------------
class CategoriaDAO(DAO):
    def listar(self):
        filas = self._conexion.consultar("SELECT * FROM categoria ORDER BY nombre")
        return [Categoria(f["nombre"], f["descripcion"] or "", bool(f["activo"]), f["id_categoria"]) for f in filas]

    def guardar(self, c):
        datos = {"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion, "activo": c.activo}
        if c.id is None:
            self._conexion.ejecutar(
                "INSERT INTO categoria (nombre, descripcion, activo) VALUES (:nombre, :descripcion, :activo)", datos)
        else:
            self._conexion.ejecutar(
                "UPDATE categoria SET nombre=:nombre, descripcion=:descripcion, activo=:activo "
                "WHERE id_categoria=:id", datos)

    def eliminar(self, c):
        # Baja física. Si la categoría tiene productos, MySQL no lo permite (clave foránea).
        self._conexion.ejecutar("DELETE FROM categoria WHERE id_categoria=:id", {"id": c.id})


# ---------------------------------------------------------------------
# SQL de la tabla proveedor.
# ---------------------------------------------------------------------
class ProveedorDAO(DAO):
    def listar(self):
        filas = self._conexion.consultar("SELECT * FROM proveedor ORDER BY razon_social")
        return [self.crear_proveedor(f) for f in filas]

    @staticmethod
    def crear_proveedor(f):
        return Proveedor(f["razon_social"], f["cuit"], f["telefono"] or "", f["email"] or "",
                         f["fecha_alta"], bool(f["activo"]), f["id_proveedor"])

    def guardar(self, p):
        datos = {"id": p.id, "razon": p.razon_social, "cuit": p.cuit, "tel": p.telefono, "email": p.email,
                 "alta": p.fecha_alta, "activo": p.activo}
        if p.id is None:
            self._conexion.ejecutar(
                "INSERT INTO proveedor (razon_social, cuit, telefono, email, fecha_alta, activo) "
                "VALUES (:razon, :cuit, :tel, :email, :alta, :activo)", datos)
        else:
            self._conexion.ejecutar(
                "UPDATE proveedor SET razon_social=:razon, cuit=:cuit, telefono=:tel, email=:email, "
                "fecha_alta=:alta, activo=:activo WHERE id_proveedor=:id", datos)

    def eliminar(self, p):
        # Baja lógica: queda inactivo pero se conservan sus compras.
        self._conexion.ejecutar("UPDATE proveedor SET activo=0 WHERE id_proveedor=:id", {"id": p.id})


# ---------------------------------------------------------------------
# SQL de la tabla producto.
# ---------------------------------------------------------------------
class ProductoDAO(DAO):
    def listar(self):
        filas = self._conexion.consultar("SELECT * FROM producto ORDER BY nombre")
        categorias = {c.id: c for c in CategoriaDAO(self._conexion).listar()}
        proveedores = {p.id: p for p in ProveedorDAO(self._conexion).listar()}
        productos = []
        for f in filas:
            categoria = categorias[f["id_categoria"]]
            proveedor = proveedores.get(f["id_proveedor"])
            precio = float(f["precio"])
            # Según la columna "tipo" se crea un objeto de una subclase o de la otra.
            if f["tipo"] == "PERECEDERO":
                producto = ProductoPerecedero(f["codigo"], f["nombre"], categoria, proveedor, precio,
                                              f["stock_minimo"], f["dias_alerta"], bool(f["activo"]), f["id_producto"])
            else:
                producto = ProductoNoPerecedero(f["codigo"], f["nombre"], categoria, proveedor, precio,
                                                f["stock_minimo"], bool(f["activo"]), f["id_producto"])
            productos.append(producto)
        return productos

    def buscar_por_codigo(self, codigo):
        for producto in self.listar():
            if producto.codigo == codigo.strip():
                return producto
        raise ErrorValidacion(f"No existe un producto con el código {codigo}.")

    def guardar(self, p, stock_inicial=0, vencimiento=None):
        """Un producto nuevo se guarda junto con su primer lote, en una transacción."""
        datos = {"id": p.id, "codigo": p.codigo, "nombre": p.nombre, "tipo": p.tipo(),
                 "categoria": p.categoria.id, "proveedor": p.proveedor.id if p.proveedor else None,
                 "precio": p.precio, "minimo": p.stock_minimo, "activo": p.activo,
                 "alerta": p.dias_alerta if isinstance(p, ProductoPerecedero) else None}
        if p.id is None:
            sentencias = [(
                "INSERT INTO producto (codigo, nombre, tipo, id_categoria, id_proveedor, precio, stock_minimo, "
                "dias_alerta, activo) VALUES (:codigo, :nombre, :tipo, :categoria, :proveedor, :precio, :minimo, "
                ":alerta, :activo)", datos)]
            if stock_inicial > 0:
                sentencias.append(("INSERT INTO lote (id_producto, cantidad, fecha_vencimiento) "
                                   "VALUES (:id_nuevo, :cantidad, :vence)",
                                   {"cantidad": stock_inicial, "vence": vencimiento}))
            p.id = self._conexion.ejecutar_varios(sentencias)
        else:
            self._conexion.ejecutar(
                "UPDATE producto SET codigo=:codigo, nombre=:nombre, tipo=:tipo, id_categoria=:categoria, "
                "id_proveedor=:proveedor, precio=:precio, stock_minimo=:minimo, dias_alerta=:alerta, "
                "activo=:activo WHERE id_producto=:id", datos)

    def eliminar(self, p):
        self._conexion.ejecutar("UPDATE producto SET activo=0 WHERE id_producto=:id", {"id": p.id})


# ---------------------------------------------------------------------
# SQL de la tabla usuario.
# ---------------------------------------------------------------------
class UsuarioDAO(DAO):
    def listar(self):
        filas = self._conexion.consultar("SELECT * FROM usuario")
        return [Usuario(f["nombre_usuario"], f["nombre_completo"], f["rol"], f["hash_password"], f["id_usuario"])
                for f in filas]

    def buscar(self, nombre_usuario):
        for usuario in self.listar():
            if usuario.nombre_usuario == nombre_usuario.strip().lower():
                return usuario
        return None


# ---------------------------------------------------------------------
# Lee los lotes y arma el Inventario.
# ---------------------------------------------------------------------
class StockDAO(DAO):
    def cargar_inventario(self):
        productos = {p.id: p for p in ProductoDAO(self._conexion).listar()}
        inventario = Inventario()
        for f in self._conexion.consultar("SELECT * FROM lote WHERE cantidad > 0"):
            inventario.agregar_lote(Lote(productos[f["id_producto"]], f["cantidad"], f["fecha_vencimiento"],
                                         f["id_lote"]))
        return inventario

    def agregar_lote(self, producto, cantidad, vencimiento):
        """Suma stock a mano (al editar un producto). Las compras crean sus lotes con el trigger."""
        self._conexion.ejecutar("INSERT INTO lote (id_producto, cantidad, fecha_vencimiento) "
                                "VALUES (:producto, :cantidad, :vence)",
                                {"producto": producto.id, "cantidad": cantidad, "vence": vencimiento})


# ---------------------------------------------------------------------
# Guarda una compra con sus líneas (transacción).
# ---------------------------------------------------------------------
class CompraDAO(DAO):
    def listar(self):
        proveedores = {p.id: p for p in ProveedorDAO(self._conexion).listar()}
        productos = {p.id: p for p in ProductoDAO(self._conexion).listar()}
        compras = []
        for f in self._conexion.consultar("SELECT * FROM compra ORDER BY fecha DESC"):
            compra = Compra(proveedores[f["id_proveedor"]], f["id_usuario"], f["fecha"], f["observaciones"] or "",
                            f["id_compra"])
            detalle = self._conexion.consultar("SELECT * FROM compra_detalle WHERE id_compra=:id",
                                               {"id": compra.id})
            for d in detalle:
                compra.agregar_linea(LineaCompra(productos[d["id_producto"]], d["cantidad"],
                                                 float(d["precio_unitario"]), d["fecha_vencimiento"]))
            compras.append(compra)
        return compras

    def guardar(self, compra):
        """Guarda la compra y sus líneas en UNA transacción.
        El trigger trg_compra_crea_lote crea un lote por cada línea."""
        compra.validar()
        sentencias = [("INSERT INTO compra (id_proveedor, id_usuario, observaciones) "
                       "VALUES (:proveedor, :usuario, :obs)",
                       {"proveedor": compra.proveedor.id, "usuario": compra.id_usuario, "obs": compra.observaciones})]
        for linea in compra.lineas:
            sentencias.append(("INSERT INTO compra_detalle (id_compra, id_producto, cantidad, precio_unitario, "
                               "fecha_vencimiento) VALUES (:id_nuevo, :producto, :cantidad, :precio, :vence)",
                               {"producto": linea.producto.id, "cantidad": linea.cantidad,
                                "precio": linea.precio, "vence": linea.vencimiento}))
        compra.id = self._conexion.ejecutar_varios(sentencias)


# ---------------------------------------------------------------------
# Descuenta stock con el procedimiento sp_descontar.
# ---------------------------------------------------------------------
class SalidaDAO(DAO):
    """Descuenta stock. Cada salida queda registrada en la tabla salida."""

    def descontar(self, salida):
        # El procedimiento tiene su propia transacción (START TRANSACTION / COMMIT / ROLLBACK).
        self._conexion.ejecutar("CALL sp_descontar(:producto, :cantidad, :usuario, :motivo)",
                                {"producto": salida.producto.id, "cantidad": salida.cantidad,
                                 "usuario": salida.usuario.id, "motivo": salida.motivo})
