
-- Crear la base de datos por separado:
-- CREATE DATABASE gestion_articulos;

-- Ejecutar las siguientes instrucciones
-- conectado a gestion_articulos.

CREATE TABLE usuarios (
    id_usuario INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE articulos (
    id_articulo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_comercial VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio_unitario NUMERIC(10,2) NOT NULL,
    stock INTEGER NOT NULL
);

INSERT INTO articulos
(nombre_comercial, descripcion, precio_unitario, stock)
VALUES
('Teclado Logitech', 'Teclado USB', 25.50, 15),
('Ratón óptico', 'Ratón inalámbrico', 18.90, 30),
('Monitor Samsung', 'Monitor LED 24 pulgadas', 149.99, 8);
