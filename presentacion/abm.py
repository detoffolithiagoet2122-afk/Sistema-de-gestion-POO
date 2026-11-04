from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QWidget,
)

from datos import CategoriaDAO, ProductoDAO, ProveedorDAO, SalidaDAO, StockDAO
from negocio import Categoria, ErrorAlmacen, ProductoNoPerecedero, ProductoPerecedero, Proveedor, Salida
from presentacion.util import (
    armar_pantalla,
    confirmar,
    crear_tabla,
    elegir_en_combo,
    filtrar_tabla,
    leer_numero,
    llenar_combo,
    llenar_tabla,
    mostrar_error,
)


# ---------------------------------------------------------------------
# ABM de Categorías.
# ---------------------------------------------------------------------
class FormCategorias(QWidget):
    def __init__(self, conexion):
        super().__init__()
        self.dao = CategoriaDAO(conexion)
        self.categorias = []
        self.seleccionada = None

        self.txt_nombre = QLineEdit()
        self.txt_descripcion = QLineEdit()
        self.chk_activo = QCheckBox("Activa")
        formulario = QFormLayout()
        formulario.addRow("Nombre *", self.txt_nombre)
        formulario.addRow("Descripción", self.txt_descripcion)
        formulario.addRow("", self.chk_activo)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar...")
        self.tabla = crear_tabla(["Nombre", "Descripción", "Activa"])
        armar_pantalla(self, "Categorías", self.tabla, self.txt_buscar, formulario)

        self.txt_buscar.textChanged.connect(self.buscar)
        self.tabla.cellClicked.connect(self.seleccionar)
        self.btn_nuevo.clicked.connect(self.nuevo)
        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_eliminar.clicked.connect(self.eliminar)
        self.nuevo()

    def cargar(self):
        """Trae los datos de la base y llena la grilla."""
        try:
            self.categorias = self.dao.listar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)
            return
        filas = [[c.nombre, c.descripcion, "Sí" if c.activo else "No"] for c in self.categorias]
        llenar_tabla(self.tabla, filas)
        self.buscar(self.txt_buscar.text())

    def buscar(self, texto):
        filtrar_tabla(self.tabla, texto)

    def seleccionar(self, fila, columna):
        self.seleccionada = self.categorias[fila]
        self.txt_nombre.setText(self.seleccionada.nombre)
        self.txt_descripcion.setText(self.seleccionada.descripcion)
        self.chk_activo.setChecked(self.seleccionada.activo)

    def nuevo(self):
        self.seleccionada = None
        self.txt_nombre.clear()
        self.txt_descripcion.clear()
        self.chk_activo.setChecked(True)

    def guardar(self):
        try:
            id_actual = self.seleccionada.id if self.seleccionada else None
            categoria = Categoria(self.txt_nombre.text(), self.txt_descripcion.text(),
                                  self.chk_activo.isChecked(), id_actual)
            self.dao.guardar(categoria)
            QMessageBox.information(self, "Listo", "Categoría guardada.")
            self.nuevo()
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)

    def eliminar(self):
        if self.seleccionada is None:
            QMessageBox.warning(self, "Atención", "Seleccione una categoría de la grilla.")
            return
        if not confirmar(self, f"¿Eliminar la categoría {self.seleccionada.nombre}? No se puede deshacer."):
            return
        try:
            self.dao.eliminar(self.seleccionada)
            self.nuevo()
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)


# ---------------------------------------------------------------------
# ABM de Proveedores.
# ---------------------------------------------------------------------
class FormProveedores(QWidget):
    def __init__(self, conexion):
        super().__init__()
        self.dao = ProveedorDAO(conexion)
        self.proveedores = []
        self.seleccionado = None

        self.txt_razon = QLineEdit()
        self.txt_cuit = QLineEdit()
        self.txt_cuit.setInputMask("99-99999999-9")  # obliga el formato del CUIT
        self.txt_telefono = QLineEdit()
        self.txt_email = QLineEdit()
        self.fecha_alta = QDateEdit()
        self.fecha_alta.setCalendarPopup(True)  # muestra un calendario para elegir la fecha
        self.chk_activo = QCheckBox("Activo")
        formulario = QFormLayout()
        formulario.addRow("Razón social *", self.txt_razon)
        formulario.addRow("CUIT *", self.txt_cuit)
        formulario.addRow("Teléfono", self.txt_telefono)
        formulario.addRow("Email", self.txt_email)
        formulario.addRow("Fecha de alta", self.fecha_alta)
        formulario.addRow("", self.chk_activo)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar...")
        self.tabla = crear_tabla(["Razón social", "CUIT", "Teléfono", "Email", "Alta", "Activo"])
        armar_pantalla(self, "Proveedores", self.tabla, self.txt_buscar, formulario)

        self.txt_buscar.textChanged.connect(self.buscar)
        self.tabla.cellClicked.connect(self.seleccionar)
        self.btn_nuevo.clicked.connect(self.nuevo)
        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_eliminar.clicked.connect(self.eliminar)
        self.nuevo()

    def cargar(self):
        try:
            self.proveedores = self.dao.listar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)
            return
        filas = [[p.razon_social, p.cuit, p.telefono, p.email, p.fecha_alta.strftime("%d/%m/%Y"),
                  "Sí" if p.activo else "No"] for p in self.proveedores]
        llenar_tabla(self.tabla, filas)
        self.buscar(self.txt_buscar.text())

    def buscar(self, texto):
        filtrar_tabla(self.tabla, texto)

    def seleccionar(self, fila, columna):
        p = self.proveedores[fila]
        self.seleccionado = p
        self.txt_razon.setText(p.razon_social)
        self.txt_cuit.setText(p.cuit)
        self.txt_telefono.setText(p.telefono)
        self.txt_email.setText(p.email)
        self.fecha_alta.setDate(QDate(p.fecha_alta.year, p.fecha_alta.month, p.fecha_alta.day))
        self.chk_activo.setChecked(p.activo)

    def nuevo(self):
        self.seleccionado = None
        for campo in (self.txt_razon, self.txt_cuit, self.txt_telefono, self.txt_email):
            campo.clear()
        self.fecha_alta.setDate(QDate.currentDate())
        self.chk_activo.setChecked(True)

    def guardar(self):
        try:
            id_actual = self.seleccionado.id if self.seleccionado else None
            proveedor = Proveedor(self.txt_razon.text(), self.txt_cuit.text(), self.txt_telefono.text(),
                                  self.txt_email.text(), self.fecha_alta.date().toPython(),
                                  self.chk_activo.isChecked(), id_actual)
            self.dao.guardar(proveedor)
            QMessageBox.information(self, "Listo", "Proveedor guardado.")
            self.nuevo()
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)

    def eliminar(self):
        if self.seleccionado is None:
            QMessageBox.warning(self, "Atención", "Seleccione un proveedor de la grilla.")
            return
        if not confirmar(self, f"¿Dar de baja al proveedor {self.seleccionado.razon_social}? Quedará inactivo."):
            return
        try:
            self.dao.eliminar(self.seleccionado)
            self.nuevo()
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)


# ---------------------------------------------------------------------
# ABM de Productos (con Editar producto y stock).
# ---------------------------------------------------------------------
class FormProductos(QWidget):
    def __init__(self, conexion, usuario):
        super().__init__()
        self.usuario = usuario
        self.dao = ProductoDAO(conexion)
        self.categoria_dao = CategoriaDAO(conexion)
        self.proveedor_dao = ProveedorDAO(conexion)
        self.stock_dao = StockDAO(conexion)
        self.salida_dao = SalidaDAO(conexion)
        self.productos = []
        self.inventario = None
        self.seleccionado = None
        self.editando = False  # un producto de la grilla solo se modifica después de tocar Editar producto

        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Escanee el código o escríbalo")
        self.txt_nombre = QLineEdit()
        self.cmb_categoria = QComboBox()
        self.cmb_proveedor = QComboBox()
        self.txt_precio = QLineEdit()
        self.spn_minimo = QSpinBox()
        self.spn_minimo.setMaximum(10000)
        self.chk_perecedero = QCheckBox("Es perecedero")
        self.spn_alerta = QSpinBox()
        self.spn_alerta.setRange(1, 365)
        self.chk_activo = QCheckBox("Activo")
        # Un producto nuevo nace con stock: así no quedan productos que no existen en el depósito.
        self.spn_stock = QSpinBox()
        self.spn_stock.setRange(1, 10000)
        self.fecha_vence = QDateEdit(QDate.currentDate().addDays(30))
        self.fecha_vence.setCalendarPopup(True)
        formulario = QFormLayout()
        formulario.addRow("Código de barras *", self.txt_codigo)
        formulario.addRow("Nombre *", self.txt_nombre)
        formulario.addRow("Categoría *", self.cmb_categoria)
        formulario.addRow("Proveedor", self.cmb_proveedor)
        formulario.addRow("Precio *", self.txt_precio)
        formulario.addRow("Stock mínimo", self.spn_minimo)
        formulario.addRow("", self.chk_perecedero)
        formulario.addRow("Días de alerta", self.spn_alerta)
        formulario.addRow("", self.chk_activo)
        formulario.addRow("Stock *", self.spn_stock)
        formulario.addRow("Vence (si es perecedero)", self.fecha_vence)
        self.campos = [self.txt_codigo, self.txt_nombre, self.cmb_categoria, self.cmb_proveedor, self.txt_precio,
                       self.spn_minimo, self.chk_perecedero, self.chk_activo, self.spn_stock]

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar...")
        self.tabla = crear_tabla(["Código", "Nombre", "Disponible", "Categoría", "Tipo", "Proveedor", "Precio",
                                  "Activo"])
        armar_pantalla(self, "Productos", self.tabla, self.txt_buscar, formulario)
        self.btn_editar = self.btn_nuevo  # en Productos, el primer botón es Editar producto

        self.txt_codigo.returnPressed.connect(self.txt_nombre.setFocus)
        self.chk_perecedero.toggled.connect(self.actualizar_campos_perecedero)
        self.txt_buscar.textChanged.connect(self.buscar)
        self.tabla.cellClicked.connect(self.seleccionar)
        self.btn_editar.clicked.connect(self.editar)
        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_eliminar.clicked.connect(self.eliminar)
        self.nuevo()

    def cargar(self):
        try:
            # Los ComboBox se llenan con datos de la base (claves foráneas).
            llenar_combo(self.cmb_categoria, self.categoria_dao.listar())
            llenar_combo(self.cmb_proveedor, self.proveedor_dao.listar(), "(sin proveedor)")
            self.productos = self.dao.listar()
            self.inventario = self.stock_dao.cargar_inventario()
        except ErrorAlmacen as error:
            mostrar_error(self, error)
            return
        filas = []
        for p in self.productos:
            tipo = "Perecedero" if p.requiere_vencimiento() else "No perecedero"
            proveedor = p.proveedor.razon_social if p.proveedor else "-"
            filas.append([p.codigo, p.nombre, self.inventario.obtener_stock_total(p), p.categoria.nombre, tipo,
                          proveedor, f"$ {p.precio:.2f}", "Sí" if p.activo else "No"])
        llenar_tabla(self.tabla, filas)
        self.buscar(self.txt_buscar.text())

    def buscar(self, texto):
        filtrar_tabla(self.tabla, texto)

    def habilitar_campos(self, si):
        for campo in self.campos:
            campo.setEnabled(si)
        self.actualizar_campos_perecedero(self.chk_perecedero.isChecked())

    def actualizar_campos_perecedero(self, perecedero):
        se_puede = self.seleccionado is None or self.editando
        self.spn_alerta.setEnabled(perecedero and se_puede)
        self.fecha_vence.setEnabled(perecedero and se_puede)

    def seleccionar(self, fila, columna):
        p = self.productos[fila]
        self.seleccionado = p
        self.editando = False
        self.txt_codigo.setText(p.codigo)
        self.txt_nombre.setText(p.nombre)
        elegir_en_combo(self.cmb_categoria, p.categoria.id)
        elegir_en_combo(self.cmb_proveedor, p.proveedor.id if p.proveedor else None)
        self.txt_precio.setText(f"{p.precio:.2f}")
        self.spn_minimo.setValue(p.stock_minimo)
        self.chk_perecedero.setChecked(p.requiere_vencimiento())
        if p.requiere_vencimiento():
            self.spn_alerta.setValue(p.dias_alerta)
        self.chk_activo.setChecked(p.activo)
        self.spn_stock.setMinimum(0)
        self.spn_stock.setValue(self.inventario.obtener_stock_total(p))
        self.habilitar_campos(False)  # se ve, pero no se toca hasta tocar Editar producto
        self.btn_editar.setText("Editar producto")

    def editar(self):
        if self.seleccionado is None:
            QMessageBox.warning(self, "Atención", "Seleccione un producto de la grilla para editarlo.")
            return
        if self.editando:  # el mismo botón sirve para cancelar
            self.nuevo()
            return
        self.editando = True
        self.habilitar_campos(True)
        self.btn_editar.setText("Cancelar edición")
        self.txt_nombre.setFocus()

    def nuevo(self):
        self.seleccionado = None
        self.editando = False
        for campo in (self.txt_codigo, self.txt_nombre, self.txt_precio):
            campo.clear()
        self.spn_minimo.setValue(0)
        self.chk_perecedero.setChecked(False)
        self.spn_alerta.setValue(7)
        self.chk_activo.setChecked(True)
        self.spn_stock.setMinimum(1)
        self.spn_stock.setValue(1)
        self.fecha_vence.setDate(QDate.currentDate().addDays(30))
        self.habilitar_campos(True)
        self.btn_editar.setText("Editar producto")
        self.tabla.clearSelection()

    def guardar(self):
        if self.seleccionado is not None and not self.editando:
            QMessageBox.warning(self, "Atención", "Toque Editar producto para poder modificarlo.")
            return
        try:
            id_actual = self.seleccionado.id if self.seleccionado else None
            precio = leer_numero(self.txt_precio.text(), "Precio")
            # Según el checkbox se crea un objeto de una subclase o de la otra.
            if self.chk_perecedero.isChecked():
                producto = ProductoPerecedero(self.txt_codigo.text(), self.txt_nombre.text(),
                                              self.cmb_categoria.currentData(), self.cmb_proveedor.currentData(),
                                              precio, self.spn_minimo.value(), self.spn_alerta.value(),
                                              self.chk_activo.isChecked(), id_actual)
            else:
                producto = ProductoNoPerecedero(self.txt_codigo.text(), self.txt_nombre.text(),
                                                self.cmb_categoria.currentData(), self.cmb_proveedor.currentData(),
                                                precio, self.spn_minimo.value(), self.chk_activo.isChecked(),
                                                id_actual)
            vencimiento = self.fecha_vence.date().toPython() if producto.requiere_vencimiento() else None
            mensaje = "Producto guardado."
            if id_actual is None:
                producto.validar_vencimiento(vencimiento)
                self.dao.guardar(producto, self.spn_stock.value(), vencimiento)  # producto + primer lote
            else:
                antes = self.inventario.obtener_stock_total(self.seleccionado)
                diferencia = self.spn_stock.value() - antes
                if diferencia > 0:  # entra mercadería: se valida la fecha antes de guardar nada
                    producto.validar_vencimiento(vencimiento)
                self.dao.guardar(producto)
                if diferencia > 0:
                    self.stock_dao.agregar_lote(producto, diferencia, vencimiento)
                elif diferencia < 0:  # sale mercadería: lo descuenta el procedimiento, igual que en Stock
                    self.salida_dao.descontar(Salida(producto, -diferencia, "Ajuste desde Productos",
                                                         self.usuario))
                if diferencia:
                    mensaje += f" El stock pasó de {antes} a {self.spn_stock.value()}."
            QMessageBox.information(self, "Listo", mensaje)
            self.nuevo()
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)

    def eliminar(self):
        if self.seleccionado is None:
            QMessageBox.warning(self, "Atención", "Seleccione un producto de la grilla.")
            return
        if not confirmar(self, f"¿Dar de baja el producto {self.seleccionado.nombre}? Quedará inactivo."):
            return
        try:
            self.dao.eliminar(self.seleccionado)
            self.nuevo()
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)
