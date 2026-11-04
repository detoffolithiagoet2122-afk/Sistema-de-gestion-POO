-- =====================================================================
-- Sistema de Gestión de Almacén - versión simple
-- Base de datos MySQL. Ejecutar completo en MySQL Workbench (botón del rayo).
-- Usuarios de prueba: admin / admin123  y  operador / operador123
-- =====================================================================

DROP DATABASE IF EXISTS almacen_simple;
CREATE DATABASE almacen_simple CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE almacen_simple;

-- ---------------------------------------------------------------------
-- Tablas maestras
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
    id_usuario       INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario   VARCHAR(30) NOT NULL UNIQUE,
    nombre_completo  VARCHAR(100) NOT NULL,
    hash_password    VARCHAR(100) NOT NULL,      -- la contraseña guardada con bcrypt
    rol              ENUM('ADMIN', 'OPERADOR') NOT NULL
);

CREATE TABLE categoria (
    id_categoria  INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(60) NOT NULL UNIQUE,
    descripcion   VARCHAR(200),
    activo        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE proveedor (
    id_proveedor  INT AUTO_INCREMENT PRIMARY KEY,
    razon_social  VARCHAR(120) NOT NULL,
    cuit          CHAR(13) NOT NULL UNIQUE,
    telefono      VARCHAR(30),
    email         VARCHAR(120),
    fecha_alta    DATE NOT NULL,
    activo        BOOLEAN NOT NULL DEFAULT TRUE
);

-- "tipo" dice si en Python es ProductoPerecedero o ProductoNoPerecedero.
CREATE TABLE producto (
    id_producto   INT AUTO_INCREMENT PRIMARY KEY,
    codigo        VARCHAR(32) NOT NULL UNIQUE,
    nombre        VARCHAR(100) NOT NULL,
    tipo          ENUM('PERECEDERO', 'NO_PERECEDERO') NOT NULL,
    id_categoria  INT NOT NULL,
    id_proveedor  INT,
    precio        DECIMAL(12,2) NOT NULL CHECK (precio > 0),
    stock_minimo  INT NOT NULL DEFAULT 0,
    dias_alerta   INT,
    activo        BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (id_categoria) REFERENCES categoria (id_categoria),
    FOREIGN KEY (id_proveedor) REFERENCES proveedor (id_proveedor)
);

-- ---------------------------------------------------------------------
-- Compras: una compra tiene muchos productos y un producto está en
-- muchas compras (relación N a M a través de compra_detalle).
-- ---------------------------------------------------------------------
CREATE TABLE compra (
    id_compra      INT AUTO_INCREMENT PRIMARY KEY,
    id_proveedor   INT NOT NULL,
    id_usuario     INT NOT NULL,
    fecha          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones  VARCHAR(200),
    FOREIGN KEY (id_proveedor) REFERENCES proveedor (id_proveedor),
    FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
);

CREATE TABLE compra_detalle (
    id_detalle         INT AUTO_INCREMENT PRIMARY KEY,
    id_compra          INT NOT NULL,
    id_producto        INT NOT NULL,
    cantidad           INT NOT NULL CHECK (cantidad > 0),
    precio_unitario    DECIMAL(12,2) NOT NULL,
    fecha_vencimiento  DATE,
    FOREIGN KEY (id_compra) REFERENCES compra (id_compra),
    FOREIGN KEY (id_producto) REFERENCES producto (id_producto)
);

-- Un producto tiene muchos lotes (1 a N). Cada lote vence en una fecha.
CREATE TABLE lote (
    id_lote            INT AUTO_INCREMENT PRIMARY KEY,
    id_producto        INT NOT NULL,
    id_compra          INT,
    cantidad           INT NOT NULL,
    fecha_vencimiento  DATE,
    fecha_ingreso      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_producto) REFERENCES producto (id_producto),
    FOREIGN KEY (id_compra) REFERENCES compra (id_compra)
);

-- Cada salida de mercadería del depósito.
CREATE TABLE salida (
    id_salida    INT AUTO_INCREMENT PRIMARY KEY,
    id_producto  INT NOT NULL,
    id_usuario   INT NOT NULL,
    cantidad     INT NOT NULL,
    motivo       VARCHAR(100) NOT NULL,
    fecha        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_producto) REFERENCES producto (id_producto),
    FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
);

DELIMITER $$

-- ---------------------------------------------------------------------
-- TRIGGER 1: cada renglón de una compra crea su lote automáticamente.
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_compra_crea_lote
AFTER INSERT ON compra_detalle
FOR EACH ROW
BEGIN
    INSERT INTO lote (id_producto, id_compra, cantidad, fecha_vencimiento)
    VALUES (NEW.id_producto, NEW.id_compra, NEW.cantidad, NEW.fecha_vencimiento);
END$$

-- ---------------------------------------------------------------------
-- TRIGGER 2: un lote nunca puede quedar con cantidad negativa.
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_lote_sin_negativos
BEFORE UPDATE ON lote
FOR EACH ROW
BEGIN
    IF NEW.cantidad < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock insuficiente: el lote quedaría negativo.';
    END IF;
END$$

-- ---------------------------------------------------------------------
-- STORED PROCEDURE con TRANSACCIÓN: descuenta mercadería.
-- Saca primero del lote que vence antes y no usa lotes vencidos.
-- Si algo falla, ROLLBACK: no queda nada a medias.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_descontar(
    IN p_id_producto INT, IN p_cantidad INT, IN p_id_usuario INT, IN p_motivo VARCHAR(100)
)
BEGIN
    DECLARE v_disponible INT;
    DECLARE v_falta INT;
    DECLARE v_id_lote INT;
    DECLARE v_cantidad_lote INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT COALESCE(SUM(cantidad), 0) INTO v_disponible
      FROM lote
     WHERE id_producto = p_id_producto AND cantidad > 0
       AND (fecha_vencimiento IS NULL OR fecha_vencimiento >= CURDATE());

    IF v_disponible < p_cantidad THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock insuficiente para descontar.';
    END IF;

    SET v_falta = p_cantidad;
    WHILE v_falta > 0 DO
        -- el lote con stock que vence antes
        SELECT id_lote, cantidad INTO v_id_lote, v_cantidad_lote
          FROM lote
         WHERE id_producto = p_id_producto AND cantidad > 0
           AND (fecha_vencimiento IS NULL OR fecha_vencimiento >= CURDATE())
         ORDER BY fecha_vencimiento IS NULL, fecha_vencimiento
         LIMIT 1;

        SET v_cantidad_lote = LEAST(v_cantidad_lote, v_falta);
        UPDATE lote SET cantidad = cantidad - v_cantidad_lote WHERE id_lote = v_id_lote;
        SET v_falta = v_falta - v_cantidad_lote;
    END WHILE;

    INSERT INTO salida (id_producto, id_usuario, cantidad, motivo)
    VALUES (p_id_producto, p_id_usuario, p_cantidad, p_motivo);

    COMMIT;
END$$

DELIMITER ;

-- =====================================================================
-- Datos de prueba
-- =====================================================================
INSERT INTO usuario (nombre_usuario, nombre_completo, hash_password, rol) VALUES
    ('admin',    'Administrador',        '$2b$12$CsSqPyYCYi/h3LFH6FbbW.4e64Jp7RqX7f/euGfqdDWQ4peCZVPum', 'ADMIN'),
    ('operador', 'Operador de depósito', '$2b$12$nJo7jOEzzB1DwsL9DzWgkeHtyD.f07RtpW0bSb4MGwtahDoe1IWoq', 'OPERADOR');

INSERT INTO categoria (nombre, descripcion) VALUES
    ('Lácteos',     'Leches, yogures y quesos'),
    ('Almacén',     'Arroz, fideos, aceites, yerba'),
    ('Bebidas',     'Aguas, gaseosas y jugos'),
    ('Limpieza',    'Artículos de limpieza'),
    ('Panificados', 'Pan y facturas');

INSERT INTO proveedor (razon_social, cuit, telefono, email, fecha_alta) VALUES
    ('Lácteos del Sur S.A.',               '30-71234567-1', '011 4555-1200', 'ventas@lacteosdelsur.com.ar', '2024-03-01'),
    ('Distribuidora Almacén Norte S.R.L.', '30-70345678-9', '011 4789-3300', 'pedidos@almacennorte.com.ar', '2024-05-15'),
    ('Bebidas Andinas S.A.',               '30-50012345-8', '0261 420-9900', 'comercial@bebidasandinas.com', '2025-01-10'),
    ('Higiene Total S.A.',                 '30-71987654-0', '011 4222-8800', NULL,                           '2025-06-20');

INSERT INTO producto (codigo, nombre, tipo, id_categoria, id_proveedor, precio, stock_minimo, dias_alerta) VALUES
    ('7791000000017', 'Leche entera 1 L',             'PERECEDERO',    1, 1,    1400, 24, 5),
    ('7791000000024', 'Yogur bebible frutilla 900 g', 'PERECEDERO',    1, 1,    2100, 12, 5),
    ('7791000000031', 'Queso cremoso 500 g',          'PERECEDERO',    1, 1,    4800,  6, 10),
    ('7791000000055', 'Arroz largo fino 1 kg',        'NO_PERECEDERO', 2, 2,    1500, 20, NULL),
    ('7791000000062', 'Fideos spaghetti 500 g',       'NO_PERECEDERO', 2, 2,    1100, 30, NULL),
    ('7791000000086', 'Yerba mate 1 kg',              'NO_PERECEDERO', 2, 2,    4500, 15, NULL),
    ('7791000000093', 'Agua mineral 2 L',             'NO_PERECEDERO', 3, 3,     900, 24, NULL),
    ('7791000000116', 'Jugo de naranja 1 L',          'PERECEDERO',    3, 3,    1900, 12, 10),
    ('7791000000123', 'Lavandina 1 L',                'NO_PERECEDERO', 4, 4,     950, 12, NULL),
    ('7791000000147', 'Pan lactal blanco 550 g',      'PERECEDERO',    5, NULL, 2500, 10, 3);

-- Compras de prueba: el trigger trg_compra_crea_lote crea los lotes solo.
INSERT INTO compra (id_proveedor, id_usuario, fecha, observaciones) VALUES
    (1, 1, NOW() - INTERVAL 9 DAY, 'Pedido semanal de lácteos'),
    (2, 1, NOW() - INTERVAL 7 DAY, 'Reposición de secos'),
    (3, 2, NOW() - INTERVAL 5 DAY, NULL);

INSERT INTO compra_detalle (id_compra, id_producto, cantidad, precio_unitario, fecha_vencimiento) VALUES
    (1, 1, 48,  980, CURDATE() + INTERVAL 3 DAY),
    (1, 2, 24, 1500, CURDATE() + INTERVAL 20 DAY),
    (1, 3, 10, 3500, CURDATE() + INTERVAL 30 DAY),
    (2, 4, 40, 1050, NULL),
    (2, 5, 60,  750, NULL),
    (2, 6, 10, 3300, NULL),
    (3, 7, 48,  550, NULL),
    (3, 8, 20, 1300, CURDATE() + INTERVAL 8 DAY);

-- Un lote ya vencido de leche (no cuenta como stock disponible).
INSERT INTO lote (id_producto, cantidad, fecha_vencimiento) VALUES (1, 12, CURDATE() - INTERVAL 2 DAY);

-- Salidas de prueba usando el procedimiento.
CALL sp_descontar(1, 10, 2, 'Reposición de góndola');
CALL sp_descontar(5, 15, 2, 'Venta mayorista');
