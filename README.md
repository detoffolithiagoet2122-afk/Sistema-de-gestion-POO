Sistema de Gestión de Inventario

Aplicación de escritorio desarrollada en Python para la gestión de productos, lotes e inventario, utilizando Programación Orientada a Objetos (POO), una interfaz gráfica y una arquitectura en capas.

Tecnologías utilizadas

* Python: lenguaje principal.
* PySide6: desarrollo de la interfaz gráfica (GUI).
* SQLAlchemy 2.x: ORM para el acceso a datos.
* SQLite: base de datos inicial.
* Alembic: gestión de migraciones de la base de datos.
* bcrypt: hash seguro de contraseñas.
* openpyxl: exportación de reportes a Excel.
* ReportLab: generación de reportes y documentos PDF.
* python-barcode: generación de códigos de barras.
* pytest y pytest-qt: pruebas del sistema y de la interfaz.
* Ruff y mypy: análisis de código y verificación de tipos.
* PyInstaller: empaquetado de la aplicación como ejecutable.

Características previstas

* Gestión de productos, lotes e inventario.
* Inicio de sesión con contraseñas protegidas mediante hash.
* Interfaz gráfica de escritorio intuitiva.
* Persistencia de datos mediante una base de datos relacional.
* Exportación de reportes a Excel y PDF.
* Generación de etiquetas con códigos de barras.
* Compatibilidad con lectores de códigos de barras USB.
* Pruebas automatizadas y validación del código.

Arquitectura

El proyecto utiliza una arquitectura por capas para separar las responsabilidades:

* Dominio: clases Python independientes de la interfaz y la base de datos, como Producto, Lote e Inventario.
* Presentación: interfaz gráfica desarrollada con PySide6.
* Acceso a datos: repositorios implementados con SQLAlchemy.
* Migraciones: control de cambios en el esquema mediante Alembic.

Esta separación facilita el mantenimiento, las pruebas y la evolución del sistema.

Base de datos

Se utiliza SQLite como base de datos inicial. La integración mediante SQLAlchemy permite contemplar una futura migración a PostgreSQL sin acoplar las clases del dominio a un motor específico.

Requisitos

* Python 3.11 o superior, según las versiones de las dependencias.
* pip para instalar las dependencias.
* Sistema operativo compatible con PySide6.

Estado del proyecto

En desarrollo.

