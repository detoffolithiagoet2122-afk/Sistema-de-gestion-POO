"""Login y pantalla principal (menú).
"""

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QWidget,
)

from datos import UsuarioDAO
from negocio import ErrorAlmacen
from presentacion.abm import FormCategorias, FormProductos, FormProveedores
from presentacion.operaciones import FormCompras, FormStock
from presentacion.util import mostrar_error


# ---------------------------------------------------------------------
# Ventana de inicio de sesión.
# ---------------------------------------------------------------------
class Login(QDialog):
    def __init__(self, conexion):
        super().__init__()
        self.dao = UsuarioDAO(conexion)
        self.usuario = None
        self.setWindowTitle("Iniciar sesión")

        self.txt_usuario = QLineEdit()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)  # muestra puntitos
        self.lbl_error = QLabel()
        btn_ingresar = QPushButton("Ingresar")

        formulario = QFormLayout(self)
        formulario.addRow("Usuario", self.txt_usuario)
        formulario.addRow("Contraseña", self.txt_password)
        formulario.addRow("", self.lbl_error)
        formulario.addRow("", btn_ingresar)

        btn_ingresar.clicked.connect(self.ingresar)
        self.txt_password.returnPressed.connect(self.ingresar)

    def ingresar(self):
        try:
            usuario = self.dao.buscar(self.txt_usuario.text())
        except ErrorAlmacen as error:
            mostrar_error(self, error)
            return
        if usuario is None or not usuario.verificar_password(self.txt_password.text()):
            self.lbl_error.setText("Usuario o contraseña incorrectos.")
            return
        self.usuario = usuario
        self.accept()


# ---------------------------------------------------------------------
# Ventana principal: el menú de la izquierda cambia la pantalla de la derecha.
# ---------------------------------------------------------------------
class VentanaPrincipal(QMainWindow):
    """El menú de la izquierda cambia la pantalla de la derecha."""

    def __init__(self, conexion, usuario):
        super().__init__()
        self.setWindowTitle(f"Gestión de Almacén - {usuario.nombre_completo}")
        self.resize(1200, 750)

        self.pantallas = [
            ("Stock", FormStock(conexion, usuario)),
            ("Compras", FormCompras(conexion, usuario)),
            ("Productos", FormProductos(conexion, usuario)),
            ("Categorías", FormCategorias(conexion)),
            ("Proveedores", FormProveedores(conexion)),
        ]
        self.menu = QListWidget()
        self.menu.setObjectName("menu")
        self.menu.setFixedWidth(180)
        self.paginas = QStackedWidget()
        for nombre, pantalla in self.pantallas:
            self.menu.addItem(nombre)
            self.paginas.addWidget(pantalla)

        central = QWidget()
        capa = QHBoxLayout(central)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.addWidget(self.menu)
        capa.addWidget(self.paginas)
        self.setCentralWidget(central)
        self.statusBar().showMessage(f"Usuario: {usuario.nombre_usuario} ({usuario.rol})")

        self.menu.currentRowChanged.connect(self.cambiar_pantalla)
        self.menu.setCurrentRow(0)

    def cambiar_pantalla(self, numero):
        self.paginas.setCurrentIndex(numero)
        nombre, pantalla = self.pantallas[numero]
        pantalla.cargar()  # cada vez que se entra, se leen los datos actualizados de la base
