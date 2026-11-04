"""CAPA DE NEGOCIO: las clases del supermercado.

No usan la base de datos ni la pantalla. Solo guardan los datos y
controlan que sean correctos.
"""

import re
from abc import ABC, abstractmethod
from datetime import date, datetime

import bcrypt


# ---------------------------------------------------------------------
# Las excepciones propias del sistema. Todas heredan de ErrorAlmacen.
# ---------------------------------------------------------------------
class ErrorAlmacen(Exception):
    """Error general del sistema. Las demás excepciones heredan de esta."""


class ErrorValidacion(ErrorAlmacen):
    """Un dato está vacío o mal escrito."""


class StockInsuficiente(ErrorAlmacen):
    """Se quiere sacar más mercadería de la que hay."""


def texto_obligatorio(valor, campo):
    valor = valor.strip()
    if valor == "":
        raise ErrorValidacion(f"El campo {campo} es obligatorio.")
    return valor


# ---------------------------------------------------------------------
# Clase base: todo lo que se guarda en una tabla tiene un id.
# ---------------------------------------------------------------------
class Entidad: """"Clase madre de la gran mayoria de clases (excento de 3 o 5, las cuales 3 son de errores)."""
    def __init__(self, id): """Constructor los cual tiene los parametros de id (identificador unico)"""
        self.__id = id """Guarda y compara el id de la entidad. Con __ se hace privado el id, para que no se pueda modificar desde afuera.""" 

    @property 
    """Se encarga de que el dato privado se pueda leer desde afuera, pero no se pueda modificar. Se hace con @property."""
    def id(self):
        return self.__id 
    """Obtiene el parametro privado id, lo cual hace que returne el id privado."""

    @id.setter
    """Deja que se pueda modificar los valores pero antes pasa una validacion/control tirando error en el dado caso de que no funcione"""
    def id(self, valor):
        self.__id = valor
    "Obtiene el parametro privado id, permitiendo moficicarlo"


# ---------------------------------------------------------------------
# Categoría de productos (Lácteos, Bebidas...).
# ---------------------------------------------------------------------
class Categoria(Entidad):
    def __init__(self, nombre, descripcion="", activo=True, id=None): """Constructor de la clase Categoria que esta heredada"""
        super().__init__(id) """Llama al constructor de la clase madre Entidad, obteniendo como parametro el id."""
        self.nombre = nombre """Atributo publico""" 
        self.__descripcion = descripcion """Atributo privado"""
        self.__activo = activo """Atributo privado"""

    @property
    def nombre(self):
        return self.__nombre
    """Returna el nombre pero en privado"""

    @nombre.setter
    """Permite modificar el nombre, valida si el texto es obligatorio, que no vengan vacio ni con nigun error"""
    def nombre(self, valor):
        self.__nombre = texto_obligatorio(valor, "Nombre") """Llama a la funcion texto_obligatorio, que valida todos los valores vacios en el texto"""

    @property
    def descripcion(self):
        return self.__descripcion
    """Returna lo que tenga guardado en descripcion, pero en privado"""
    @property
    def activo(self):
        return self.__activo
    """"Returna lo que tenga guardado en activo, pero en privado"""
    def __str__(self):
        return self.__nombre
    """Returna el nombre pero en privado, y str decide que es lo que se va a ver por pantalla, para que el texto no quede feo."""

# ---------------------------------------------------------------------
# Proveedor de mercadería.
# ---------------------------------------------------------------------
class Proveedor(Entidad):
    def __init__(self, razon_social, cuit, telefono, email, fecha_alta, activo=True, id=None):
        super().__init__(id)
        self.razon_social = razon_social
        self.cuit = cuit
        self.__telefono = telefono
        self.email = email
        self.fecha_alta = fecha_alta
        self.__activo = activo

    @property
    def razon_social(self):
        return self.__razon_social

    @razon_social.setter
    "permite modificar el atributo publico razon_social, pero antes pasa por la funcion texto_obligatorio, que valida que el texto no venga vacio ni con ningun error"
    def razon_social(self, valor):
        self.__razon_social = texto_obligatorio(valor, "Razón social")

    @property
    def cuit(self):
        return self.__cuit

    @cuit.setter
    """permite modificar el atributo privado cuit."""
    def cuit(self, valor):
        numeros = re.sub(r"\D", "", valor)  # deja solo los números
        if len(numeros) != 11:
            raise ErrorValidacion("El CUIT debe tener 11 números.")
        self.__cuit = f"{numeros[:2]}-{numeros[2:10]}-{numeros[10]}"

    @property
    def telefono(self):
        return self.__telefono

    @property
    def email(self):
        return self.__email

    @email.setter
    "Permite modificar el email."
    def email(self, valor):
        if valor and "@" not in valor: "email = thiagodetogmail.com ---> El email no es valido"
            raise ErrorValidacion("El email no es válido.")
        self.__email = valor

    @property
    def fecha_alta(self):
        return self.__fecha_alta

    @fecha_alta.setter
    def fecha_alta(self, valor):
        if valor > date.today():
            raise ErrorValidacion("La fecha de alta no puede ser futura.")
        self.__fecha_alta = valor

    @property
    def activo(self):
        return self.__activo

    def __str__(self):
        return self.__razon_social


# ---------------------------------------------------------------------
# Producto: clase ABSTRACTA. Solo se crean perecederos o no perecederos.
# ---------------------------------------------------------------------
class Producto(Entidad, ABC):
    def __init__(self, codigo, nombre, categoria, proveedor, precio, stock_minimo, activo=True, id=None):
        super().__init__(id)
        self.codigo = codigo
        self.nombre = nombre
        self.categoria = categoria
        self.__proveedor = proveedor
        self.precio = precio
        self.stock_minimo = stock_minimo
        self.__activo = activo

    @property
    def codigo(self):
        return self.__codigo

    @codigo.setter
    def codigo(self, valor):
        self.__codigo = texto_obligatorio(valor, "Código")

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        self.__nombre = texto_obligatorio(valor, "Nombre")

    @property
    def categoria(self):
        return self.__categoria

    @categoria.setter
    def categoria(self, valor):
        if valor is None:
            raise ErrorValidacion("Debe elegir una categoría.")
        self.__categoria = valor

    @property
    def proveedor(self):
        return self.__proveedor

    @property
    def precio(self):
        return self.__precio

    @precio.setter
    def precio(self, valor):
        if valor <= 0:
            raise ErrorValidacion("El precio debe ser mayor a cero.")
        self.__precio = valor

    @property
    def stock_minimo(self):
        return self.__stock_minimo

    @stock_minimo.setter
    def stock_minimo(self, valor):
        if valor < 0:
            raise ErrorValidacion("El stock mínimo no puede ser negativo.")
        self.__stock_minimo = valor

    @property
    def activo(self):
        return self.__activo

    # Cada subclase responde estos métodos a su manera (polimorfismo).
    @abstractmethod
    def tipo(self):
        pass
    """la respuesta la da las clases hija, si es perecedero o no, y si requiere vencimiento o no"""
    @abstractmethod
    def requiere_vencimiento(self):
        pass
     """la respuesta la da las clases hija, si es perecedero o no, y si requiere vencimiento o no"""

    def validar_vencimiento(self, fecha):
        if self.requiere_vencimiento() and fecha is None:
            raise ErrorValidacion(f"{self.nombre} es perecedero: falta la fecha de vencimiento.")

    def __str__(self):
        return f"{self.__nombre} ({self.__codigo})"


# ---------------------------------------------------------------------
# Producto que vence: HERENCIA y POLIMORFISMO.
# ---------------------------------------------------------------------
class ProductoPerecedero(Producto):
    def __init__(self, codigo, nombre, categoria, proveedor, precio, stock_minimo, dias_alerta,
                 activo=True, id=None):
        super().__init__(codigo, nombre, categoria, proveedor, precio, stock_minimo, activo, id)
        self.__dias_alerta = dias_alerta  # atributo que solo tiene esta subclase

    @property
    def dias_alerta(self):
        return self.__dias_alerta

    def tipo(self):
        return "PERECEDERO"

    def requiere_vencimiento(self):
        return True


# ---------------------------------------------------------------------
# Producto que no vence: HERENCIA y POLIMORFISMO.
# ---------------------------------------------------------------------
class ProductoNoPerecedero(Producto):
    def tipo(self):
        return "NO_PERECEDERO"

    def requiere_vencimiento(self):
        return False


# ---------------------------------------------------------------------
# Lote: una cantidad de un producto con su fecha de vencimiento.
# ---------------------------------------------------------------------
class Lote(Entidad):
    def __init__(self, producto, cantidad, fecha_vencimiento, id=None):
        super().__init__(id)
        self.__producto = producto
        self.__cantidad = cantidad
        self.__fecha_vencimiento = fecha_vencimiento

    @property
    def producto(self):
        return self.__producto

    @property
    def cantidad(self):
        return self.__cantidad

    @property
    def fecha_vencimiento(self):
        return self.__fecha_vencimiento

    def esta_vencido(self):
        return self.__fecha_vencimiento is not None and self.__fecha_vencimiento < date.today()


# ---------------------------------------------------------------------
# Inventario: todos los lotes del depósito. Calcula el stock.
# ---------------------------------------------------------------------
class Inventario:
    """Todos los lotes del depósito."""

    def __init__(self):
        self.__lotes = []

    def agregar_lote(self, lote):
        self.__lotes.append(lote)

    def obtener_stock_total(self, producto):
        """Suma los lotes del producto que no están vencidos."""
        total = 0
        for lote in self.__lotes:
            if lote.producto.id == producto.id and not lote.esta_vencido():
                total += lote.cantidad
        return total

    def verificar_stock(self, producto, cantidad):
        disponible = self.obtener_stock_total(producto)
        if cantidad > disponible:
            raise StockInsuficiente(f"Solo hay {disponible} unidades de {producto.nombre}.")

    def estado(self, producto):
        total = self.obtener_stock_total(producto)
        if total == 0:
            return "Sin stock"
        if total < producto.stock_minimo:
            return "Bajo mínimo"
        return "OK"


# ---------------------------------------------------------------------
# Línea (renglón) de una compra.
# ---------------------------------------------------------------------
class LineaCompra:
    def __init__(self, producto, cantidad, precio, vencimiento):
        if cantidad <= 0:
            raise ErrorValidacion("La cantidad debe ser mayor a cero.")
        producto.validar_vencimiento(vencimiento)
        self.__producto = producto
        self.__cantidad = cantidad
        self.__precio = precio
        self.__vencimiento = vencimiento

    @property
    def producto(self):
        return self.__producto

    @property
    def cantidad(self):
        return self.__cantidad

    @property
    def precio(self):
        return self.__precio

    @property
    def vencimiento(self):
        return self.__vencimiento

    def subtotal(self):
        return self.__cantidad * self.__precio


# ---------------------------------------------------------------------
# Compra a un proveedor: tiene varias líneas.
# ---------------------------------------------------------------------
class Compra(Entidad):
    def __init__(self, proveedor, id_usuario, fecha=None, observaciones="", id=None):
        super().__init__(id)
        self.proveedor = proveedor
        self.__id_usuario = id_usuario
        self.__fecha = fecha or datetime.now()
        self.__observaciones = observaciones
        self.__lineas = []

    @property
    def proveedor(self):
        return self.__proveedor

    @proveedor.setter
    def proveedor(self, valor):
        if valor is None:
            raise ErrorValidacion("Debe elegir un proveedor.")
        self.__proveedor = valor

    @property
    def id_usuario(self):
        return self.__id_usuario

    @property
    def fecha(self):
        return self.__fecha

    @property
    def observaciones(self):
        return self.__observaciones

    @observaciones.setter
    def observaciones(self, valor):
        self.__observaciones = valor.strip()

    @property
    def lineas(self):
        return list(self.__lineas)  # una copia, para que nadie cambie la lista de afuera

    def agregar_linea(self, linea):
        self.__lineas.append(linea)

    def total(self):
        return sum(linea.subtotal() for linea in self.__lineas) 

    def validar(self):
        if len(self.__lineas) == 0:
            raise ErrorValidacion("La compra no tiene productos.") 


# ---------------------------------------------------------------------
# Salida: cada vez que se descuenta stock (lo usa Descontar).
# ---------------------------------------------------------------------
class Salida(Entidad):
    def __init__(self, producto, cantidad, motivo, usuario, fecha=None, id=None):
        super().__init__(id)
        if cantidad <= 0:
            raise ErrorValidacion("La cantidad debe ser mayor a cero.")
        self.__producto = producto
        self.__cantidad = cantidad
        self.__motivo = texto_obligatorio(motivo, "Motivo")
        self.__usuario = usuario
        self.__fecha = fecha or datetime.now()

    @property
    def producto(self):
        return self.__producto

    @property
    def cantidad(self):
        return self.__cantidad

    @property
    def motivo(self):
        return self.__motivo

    @property
    def usuario(self):
        return self.__usuario

    @property
    def fecha(self):
        return self.__fecha


# ---------------------------------------------------------------------
# Usuario del sistema. La contraseña se guarda con bcrypt.
# ---------------------------------------------------------------------
class Usuario(Entidad):
    def __init__(self, nombre_usuario, nombre_completo, rol, hash_password, id=None):
        super().__init__(id)
        self.__nombre_usuario = nombre_usuario
        self.__nombre_completo = nombre_completo
        self.__rol = rol
        self.__hash_password = hash_password

    @property
    def nombre_usuario(self):
        return self.__nombre_usuario

    @property
    def nombre_completo(self):
        return self.__nombre_completo

    @property
    def rol(self):
        return self.__rol

    def verificar_password(self, password):
        return bcrypt.checkpw(password.encode(), self.__hash_password.encode()) """repaso"""
