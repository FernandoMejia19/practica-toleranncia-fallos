-- ===========================================
-- CREAR TABLAS
-- ===========================================

CREATE TABLE eventos (
    id_evento SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    lugar VARCHAR(100) NOT NULL
);

CREATE TABLE asientos (
    id_asiento SERIAL PRIMARY KEY,
    id_evento INT NOT NULL,
    numero VARCHAR(10) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'DISPONIBLE'
	CHECK (estado IN ('DISPONIBLE','RESERVADO','VENDIDO')),

    CONSTRAINT fk_evento
        FOREIGN KEY(id_evento)
        REFERENCES eventos(id_evento)
        ON DELETE CASCADE
);

CREATE TABLE reservas (
    id_reserva SERIAL PRIMARY KEY,
    id_asiento INT NOT NULL,
    cliente VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_asiento
        FOREIGN KEY(id_asiento)
        REFERENCES asientos(id_asiento)
);

CREATE TABLE pagos (
    id_pago SERIAL PRIMARY KEY,
    id_reserva INT NOT NULL,
    monto NUMERIC(8,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reserva_pago
        FOREIGN KEY(id_reserva)
        REFERENCES reservas(id_reserva)
);

CREATE TABLE notificaciones (
    id_notificacion SERIAL PRIMARY KEY,
    id_reserva INT NOT NULL,
    correo VARCHAR(100) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reserva_notificacion
        FOREIGN KEY(id_reserva)
        REFERENCES reservas(id_reserva)
);

-- ===========================================
-- INSERTAR EVENTOS
-- ===========================================

INSERT INTO eventos(nombre,fecha,lugar)
VALUES
('Concierto de Rock','2026-08-20','Quito'),
('Festival de Jazz','2026-09-15','Guayaquil');

-- ===========================================
-- INSERTAR ASIENTOS
-- ===========================================

INSERT INTO asientos(id_evento,numero,estado)
VALUES
(1,'A1','DISPONIBLE'),
(1,'A2','DISPONIBLE'),
(1,'A3','DISPONIBLE'),
(2,'B1','DISPONIBLE'),
(2,'B2','DISPONIBLE'),
(2,'B3','DISPONIBLE');

-- ===========================================
-- INSERTAR RESERVAS
-- ===========================================

INSERT INTO reservas(id_asiento,cliente,correo,estado)
VALUES
(1,'Juan Perez','juan@email.com','CONFIRMADA'),
(4,'Maria Lopez','maria@email.com','PENDIENTE');

-- ===========================================
-- INSERTAR PAGOS
-- ===========================================

INSERT INTO pagos(id_reserva,monto,estado)
VALUES
(1,35.00,'EXITOSO'),
(2,40.00,'PENDIENTE');

-- ===========================================
-- INSERTAR NOTIFICACIONES
-- ===========================================

INSERT INTO notificaciones(id_reserva,correo,estado)
VALUES
(1,'juan@email.com','ENVIADO'),
(2,'maria@email.com','PENDIENTE');


SELECT * FROM RESERVAS;


