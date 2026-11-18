-- ########## TABLAS DE PERSONAS ###########

CREATE TABLE IF NOT EXISTS Proveedores (
    id_proveedor SERIAL PRIMARY KEY,
    razon_social VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Usuarios (
    id_usuario SERIAL PRIMARY KEY,
    perfil VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Clientes (
    id_cliente SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    rfc VARCHAR(13),
    correo VARCHAR(100),
    fecha_nacimiento DATE,
    puntos_acumulados INT DEFAULT 0,
    ciudad VARCHAR(100),
    estado VARCHAR(100)
);

-- ########### TABLAS DE COMPRAS/VENTAS ############

CREATE TABLE IF NOT EXISTS Productos (
    id_producto SERIAL PRIMARY KEY,
    id_proveedor INT REFERENCES Proveedores(id_proveedor) ON DELETE SET NULL,
    folio VARCHAR(20),
    nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50),
    precio_compra DECIMAL(10,2) NOT NULL,
    precio_venta DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    es_controlado BOOLEAN DEFAULT FALSE,
    es_alcohol BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS Compras (
    id_compra SERIAL PRIMARY KEY,
    id_proveedor INT REFERENCES Proveedores(id_proveedor) ON DELETE RESTRICT,
    id_usuario INT REFERENCES Usuarios(id_usuario) ON DELETE RESTRICT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado_pedido VARCHAR(50),
    total_compra DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS Ventas (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES Clientes(id_cliente) ON DELETE SET NULL,
    id_usuario INT REFERENCES Usuarios(id_usuario) ON DELETE RESTRICT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(50),
    efectivo_recibido DECIMAL(10,2),
    cambio_entregado DECIMAL(10,2),
    descuento_aplicado BOOLEAN DEFAULT FALSE,
    total_venta DECIMAL(10,2)
);

-- ############ TABLAS POST-COMPRAS/VENTAS ###############

CREATE TABLE IF NOT EXISTS Detalle_Compras (
    id_detalle_compra SERIAL PRIMARY KEY,
    id_compra INT REFERENCES Compras(id_compra) ON DELETE CASCADE,
    id_producto INT REFERENCES Productos(id_producto) ON DELETE RESTRICT,
    cantidad INT NOT NULL,
    precio_compra_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS Detalle_Ventas (
    id_detalle_venta SERIAL PRIMARY KEY,
    id_venta INT REFERENCES Ventas(id_venta) ON DELETE CASCADE,
    id_producto INT REFERENCES Productos(id_producto) ON DELETE RESTRICT,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS Facturas (
    id_factura SERIAL PRIMARY KEY,
    id_venta INT REFERENCES Ventas(id_venta) ON DELETE CASCADE,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rfc_receptor VARCHAR(13),
    ruta_archivo_pdf VARCHAR(255)
);
