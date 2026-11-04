"""Arranca el programa: python main.py"""

import sys

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from datos import Conexion
from negocio import ErrorAlmacen
from presentacion.util import aplicar_estilo
from presentacion.ventanas import Login, VentanaPrincipal

app = QApplication(sys.argv)
aplicar_estilo(app)

try:
    conexion = Conexion("config.toml")
    conexion.consultar("SELECT 1")  # prueba la conexión
except (ErrorAlmacen, FileNotFoundError) as error:
    QMessageBox.critical(None, "Sin conexión", str(error))
    sys.exit(1)
except ValueError as error:  # config.toml mal escrito
    QMessageBox.critical(None, "Error en config.toml", f"Revise el archivo config.toml: {error}")
    sys.exit(1)

login = Login(conexion)
if login.exec() != QDialog.DialogCode.Accepted:
    sys.exit(0)

ventana = VentanaPrincipal(conexion, login.usuario)
ventana.showMaximized()  # ocupa toda la pantalla, así no queda nada cortado
sys.exit(app.exec())
