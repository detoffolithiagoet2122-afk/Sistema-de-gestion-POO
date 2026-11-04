"""Funciones que usan todos los formularios."""

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from datos import ErrorBaseDatos
from negocio import ErrorValidacion

ESTILO = """
QLabel#titulo { font-size: 16pt; font-weight: bold; color: #1f3a5f; }
QListWidget#menu { background: #1f3a5f; color: white; font-size: 11pt; border: none; }
QListWidget#menu::item { padding: 10px; }
QListWidget#menu::item:selected { background: #2f5597; }
QPushButton { padding: 6px 14px; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #7a8794; background: white; }
QCheckBox::indicator:checked { background: #2f5597; }
QHeaderView::section { background: #e9eef5; padding: 5px; font-weight: bold; border: none; }
"""


def aplicar_estilo(app):
    """Colores claros fijos, así se ve bien aunque Windows esté en modo oscuro."""
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    paleta = QPalette(QColor("#f4f6f9"), QColor("#f7f9fc"))
    paleta.setColor(QPalette.ColorRole.Text, QColor("#1d232b"))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor("#1d232b"))
    paleta.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor("#2f5597"))
    app.setPalette(paleta)
    app.setStyleSheet(ESTILO)


def mostrar_error(ventana, error):
    if isinstance(error, ErrorBaseDatos):
        QMessageBox.critical(ventana, "Error de base de datos", str(error))
    else:
        QMessageBox.warning(ventana, "Atención", str(error))


def confirmar(ventana, pregunta):
    """Pregunta antes de una acción importante. Devuelve True si el usuario acepta."""
    caja = QMessageBox(QMessageBox.Icon.Question, "Confirmar", pregunta, parent=ventana)
    btn_si = caja.addButton("Sí", QMessageBox.ButtonRole.AcceptRole)
    btn_no = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    caja.setDefaultButton(btn_no)  # si se aprieta Enter sin querer, no pasa nada
    caja.exec()
    return caja.clickedButton() == btn_si


def leer_numero(texto, campo):
    """Convierte un texto en número. Si no se puede, avisa qué campo está mal."""
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        raise ErrorValidacion(f"El campo {campo} debe ser un número.") from None


def crear_tabla(encabezados):
    tabla = QTableWidget(0, len(encabezados))
    tabla.setHorizontalHeaderLabels(encabezados)
    tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setStretchLastSection(True)
    return tabla


def llenar_tabla(tabla, filas, colores=None):
    """filas es una lista de listas de textos. colores (opcional) dice el color de cada fila."""
    tabla.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            celda = QTableWidgetItem(str(valor))
            if colores and colores[i]:
                celda.setBackground(QColor(colores[i]))
            tabla.setItem(i, j, celda)
    tabla.resizeColumnsToContents()


def filtrar_tabla(tabla, texto):
    """Buscador en tiempo real: oculta las filas que no contienen el texto."""
    texto = texto.lower()
    for fila in range(tabla.rowCount()):
        contenido = " ".join(tabla.item(fila, col).text().lower() for col in range(tabla.columnCount()))
        tabla.setRowHidden(fila, texto not in contenido)


def llenar_combo(combo, objetos, opcion_vacia=None):
    """Carga objetos traídos de la base en un ComboBox."""
    combo.clear()
    if opcion_vacia:
        combo.addItem(opcion_vacia, None)
    for objeto in objetos:
        combo.addItem(str(objeto), objeto)


def elegir_en_combo(combo, id_buscado):
    for i in range(combo.count()):
        objeto = combo.itemData(i)
        if objeto is not None and objeto.id == id_buscado:
            combo.setCurrentIndex(i)
            return
    combo.setCurrentIndex(0)


def titulo(texto):
    etiqueta = QLabel(texto)
    etiqueta.setObjectName("titulo")
    return etiqueta


def armar_pantalla(ventana, titulo, tabla, buscador, formulario):
    """Ubica los elementos: título arriba, grilla a la izquierda y campos con botones a la derecha."""
    ventana.btn_nuevo = QPushButton("Nuevo")
    ventana.btn_guardar = QPushButton("Guardar")
    ventana.btn_eliminar = QPushButton("Eliminar")
    botones = QHBoxLayout()
    botones.addWidget(ventana.btn_nuevo)
    botones.addWidget(ventana.btn_eliminar)
    botones.addWidget(ventana.btn_guardar)

    izquierda = QVBoxLayout()
    izquierda.addWidget(buscador)
    izquierda.addWidget(tabla)
    derecha = QVBoxLayout()
    derecha.addLayout(formulario)
    derecha.addStretch()
    derecha.addLayout(botones)

    cuerpo = QHBoxLayout()
    cuerpo.addLayout(izquierda, 3)
    cuerpo.addLayout(derecha, 2)
    etiqueta = QLabel(titulo)
    etiqueta.setObjectName("titulo")
    capa = QVBoxLayout(ventana)
    capa.addWidget(etiqueta)
    capa.addLayout(cuerpo)
