"""Pantallas de operación: Compras y Stock.
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from openpyxl import Workbook

from datos import CompraDAO, ProductoDAO, ProveedorDAO, SalidaDAO, StockDAO
from negocio import Compra, ErrorAlmacen, ErrorValidacion, LineaCompra, Salida
from presentacion.util import (
    crear_tabla,
    elegir_en_combo,
    filtrar_tabla,
    leer_numero,
    llenar_combo,
    llenar_tabla,
    mostrar_error,
    titulo,
)


# ---------------------------------------------------------------------
# Stock: consulta, descontar mercadería y exportar a Excel.
# ---------------------------------------------------------------------
class FormStock(QWidget):
    COLORES = {"Sin stock": "#e2e3e5", "Bajo mínimo": "#fff3cd", "OK": None}

    def __init__(self, conexion, usuario):
        super().__init__()
        self.usuario = usuario
        self.dao = SalidaDAO(conexion)
        self.producto_dao = ProductoDAO(conexion)
        self.stock_dao = StockDAO(conexion)
        self.inventario = None
        self.filas = []

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar...")
        btn_exportar = QPushButton("Exportar a Excel")
        self.tabla = crear_tabla(["Código", "Producto", "Categoría", "Disponible", "Mínimo", "Estado"])
        barra = QHBoxLayout()
        barra.addWidget(self.txt_buscar)
        barra.addWidget(btn_exportar)

        # Descontar: solo se pueden elegir productos que tienen stock.
        self.txt_lector = QLineEdit()
        self.txt_lector.setPlaceholderText("Escanee el código y presione Enter")
        self.cmb_producto = QComboBox()
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 10000)
        self.txt_motivo = QLineEdit("Venta")
        btn_descontar = QPushButton("Descontar")
        formulario = QFormLayout()
        formulario.addRow("Lector de códigos", self.txt_lector)
        formulario.addRow("Producto con stock *", self.cmb_producto)
        formulario.addRow("Cantidad *", self.spn_cantidad)
        formulario.addRow("Motivo *", self.txt_motivo)
        formulario.addRow("", btn_descontar)

        capa = QVBoxLayout(self)
        capa.addWidget(titulo("Stock"))
        capa.addLayout(barra)
        capa.addWidget(self.tabla)
        capa.addWidget(QLabel("Descontar del stock (se saca primero el lote que vence antes):"))
        capa.addLayout(formulario)

        self.txt_buscar.textChanged.connect(self.buscar)
        self.txt_lector.returnPressed.connect(self.leer_codigo)
        btn_exportar.clicked.connect(self.exportar)
        btn_descontar.clicked.connect(self.descontar)

    def cargar(self):
        anterior = self.cmb_producto.currentData()
        try:
            self.inventario = self.stock_dao.cargar_inventario()
            productos = self.producto_dao.listar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)
            return
        self.filas = []
        colores = []
        self.cmb_producto.clear()
        for p in productos:
            disponible = self.inventario.obtener_stock_total(p)
            estado = self.inventario.estado(p)
            self.filas.append([p.codigo, p.nombre, p.categoria.nombre, disponible, p.stock_minimo, estado])
            colores.append(self.COLORES[estado])
            if disponible > 0:
                self.cmb_producto.addItem(f"{p.nombre} ({disponible} disponibles)", p)
        llenar_tabla(self.tabla, self.filas, colores)
        self.buscar(self.txt_buscar.text())
        if anterior:
            elegir_en_combo(self.cmb_producto, anterior.id)

    def buscar(self, texto):
        filtrar_tabla(self.tabla, texto)

    def leer_codigo(self):
        """El lector USB escribe el código como un teclado y termina con Enter."""
        try:
            producto = self.producto_dao.buscar_por_codigo(self.txt_lector.text())
            if self.inventario.obtener_stock_total(producto) == 0:
                raise ErrorValidacion(f"{producto.nombre} no tiene stock.")
            elegir_en_combo(self.cmb_producto, producto.id)
        except ErrorAlmacen as error:
            mostrar_error(self, error)
        self.txt_lector.clear()

    def descontar(self):
        try:
            producto = self.cmb_producto.currentData()
            if producto is None:
                raise ErrorValidacion("No hay productos con stock para descontar.")
            salida = Salida(producto, self.spn_cantidad.value(), self.txt_motivo.text(), self.usuario)
            # Primero valida la capa de negocio; después el procedimiento descuenta en la base.
            self.inventario.verificar_stock(salida.producto, salida.cantidad)
            self.dao.descontar(salida)
            QMessageBox.information(self, "Listo", f"Se descontaron {salida.cantidad} unidades de {producto.nombre}.")
            self.spn_cantidad.setValue(1)
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)

    def exportar(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar", "stock.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        libro = Workbook()
        hoja = libro.active
        hoja.append(["Código", "Producto", "Categoría", "Disponible", "Mínimo", "Estado"])
        for fila in self.filas:
            hoja.append(fila)
        try:
            libro.save(ruta)
            QMessageBox.information(self, "Listo", f"Archivo guardado en {ruta}")
        except OSError:
            QMessageBox.warning(self, "Atención", "No se pudo guardar. ¿El archivo está abierto en Excel?")


# ---------------------------------------------------------------------
# Compras: se registra una compra con varios productos (transacción).
# ---------------------------------------------------------------------
class FormCompras(QWidget):
    def __init__(self, conexion, usuario):
        super().__init__()
        self.usuario = usuario
        self.dao = CompraDAO(conexion)
        self.producto_dao = ProductoDAO(conexion)
        self.proveedor_dao = ProveedorDAO(conexion)
        self.compra = None  # la compra que se está cargando

        self.cmb_proveedor = QComboBox()
        self.txt_observaciones = QLineEdit()
        self.txt_lector = QLineEdit()
        self.txt_lector.setPlaceholderText("Escanee el código y presione Enter")
        self.cmb_producto = QComboBox()
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 10000)
        self.txt_precio = QLineEdit()
        self.chk_vence = QCheckBox("Tiene vencimiento")
        self.fecha_vencimiento = QDateEdit(QDate.currentDate().addDays(30))
        self.fecha_vencimiento.setCalendarPopup(True)
        btn_agregar = QPushButton("Agregar producto")
        btn_guardar = QPushButton("Guardar compra")
        self.lbl_total = QLabel("Total: $ 0.00")

        formulario = QFormLayout()
        formulario.addRow("Proveedor *", self.cmb_proveedor)
        formulario.addRow("Observaciones", self.txt_observaciones)
        formulario.addRow("Lector de códigos", self.txt_lector)
        formulario.addRow("Producto *", self.cmb_producto)
        formulario.addRow("Cantidad *", self.spn_cantidad)
        formulario.addRow("Precio unitario *", self.txt_precio)
        formulario.addRow(self.chk_vence, self.fecha_vencimiento)
        formulario.addRow("", btn_agregar)

        self.tabla_lineas = crear_tabla(["Producto", "Cantidad", "Precio", "Vence", "Subtotal"])
        self.tabla_compras = crear_tabla(["N°", "Fecha", "Proveedor", "Productos", "Total"])

        pie = QHBoxLayout()
        pie.addWidget(self.lbl_total)
        pie.addStretch()
        pie.addWidget(btn_guardar)
        derecha = QVBoxLayout()
        derecha.addWidget(QLabel("Productos de esta compra:"))
        derecha.addWidget(self.tabla_lineas)
        derecha.addLayout(pie)
        arriba = QHBoxLayout()
        arriba.addLayout(formulario, 2)
        arriba.addLayout(derecha, 3)
        capa = QVBoxLayout(self)
        capa.addWidget(titulo("Compras a proveedores"))
        capa.addLayout(arriba)
        capa.addWidget(QLabel("Compras registradas:"))
        capa.addWidget(self.tabla_compras)

        self.txt_lector.returnPressed.connect(self.leer_codigo)
        self.cmb_producto.currentIndexChanged.connect(self.producto_elegido)
        self.chk_vence.toggled.connect(self.fecha_vencimiento.setEnabled)
        btn_agregar.clicked.connect(self.agregar_linea)
        btn_guardar.clicked.connect(self.guardar)

    def cargar(self):
        try:
            llenar_combo(self.cmb_proveedor, self.proveedor_dao.listar())
            llenar_combo(self.cmb_producto, self.producto_dao.listar())
            compras = self.dao.listar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)
            return
        filas = [[c.id, c.fecha.strftime("%d/%m/%Y %H:%M"), c.proveedor.razon_social, len(c.lineas),
                  f"$ {c.total():.2f}"] for c in compras]
        llenar_tabla(self.tabla_compras, filas)

    def leer_codigo(self):
        """El lector USB escribe el código como un teclado y termina con Enter."""
        try:
            producto = self.producto_dao.buscar_por_codigo(self.txt_lector.text())
            elegir_en_combo(self.cmb_producto, producto.id)
        except ErrorAlmacen as error:
            mostrar_error(self, error)
        self.txt_lector.clear()

    def producto_elegido(self):
        producto = self.cmb_producto.currentData()
        if producto is None:
            return
        # Polimorfismo: cada producto sabe si necesita fecha de vencimiento.
        self.chk_vence.setChecked(producto.requiere_vencimiento())
        self.fecha_vencimiento.setEnabled(producto.requiere_vencimiento())

    def agregar_linea(self):
        try:
            if self.compra is None:
                self.compra = Compra(self.cmb_proveedor.currentData(), self.usuario.id)
            vencimiento = self.fecha_vencimiento.date().toPython() if self.chk_vence.isChecked() else None
            precio = leer_numero(self.txt_precio.text(), "Precio unitario")
            linea = LineaCompra(self.cmb_producto.currentData(), self.spn_cantidad.value(), precio, vencimiento)
            self.compra.agregar_linea(linea)
            self.mostrar_lineas()
            self.txt_precio.clear()  # así el próximo producto no se carga con el precio de este
            self.spn_cantidad.setValue(1)
        except ErrorAlmacen as error:
            mostrar_error(self, error)

    def mostrar_lineas(self):
        lineas = self.compra.lineas if self.compra else []
        filas = []
        for linea in lineas:
            vence = linea.vencimiento.strftime("%d/%m/%Y") if linea.vencimiento else "-"
            filas.append([linea.producto.nombre, linea.cantidad, f"$ {linea.precio:.2f}", vence,
                          f"$ {linea.subtotal():.2f}"])
        llenar_tabla(self.tabla_lineas, filas)
        total = self.compra.total() if self.compra else 0
        self.lbl_total.setText(f"Total: $ {total:.2f}")

    def guardar(self):
        try:
            if self.compra is None:
                raise ErrorValidacion("Agregue al menos un producto.")
            self.compra.proveedor = self.cmb_proveedor.currentData()
            self.compra.observaciones = self.txt_observaciones.text()
            self.dao.guardar(self.compra)  # transacción: compra + todas sus líneas
            QMessageBox.information(self, "Listo", f"Compra N° {self.compra.id} guardada. Se crearon los lotes.")
            self.compra = None
            self.txt_observaciones.clear()
            self.txt_precio.clear()
            self.spn_cantidad.setValue(1)
            self.mostrar_lineas()
            self.cargar()
        except ErrorAlmacen as error:
            mostrar_error(self, error)
