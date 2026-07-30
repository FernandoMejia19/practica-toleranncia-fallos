from .database import get_connection

def crear_pago(id_reserva: int, monto: float, estado: str = 'EXITOSO'):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_reserva FROM reservas WHERE id_reserva = %s;", (id_reserva,))
        if cursor.fetchone() is None:
            raise ValueError("Reserva no encontrada")
        query = """
            INSERT INTO pagos (id_reserva, monto, estado)
            VALUES (%s, %s, %s)
            RETURNING id_pago, id_reserva, monto, estado, fecha;
        """
        cursor.execute(query, (id_reserva, monto, estado))
        pago = cursor.fetchone()
        if estado == 'EXITOSO':
            cursor.execute(
                "UPDATE reservas SET estado = 'CONFIRMADA' WHERE id_reserva = %s;",
                (id_reserva,)
            )
        conn.commit()
        return {
            "id_pago": pago[0],
            "id_reserva": pago[1],
            "monto": float(pago[2]),
            "estado": pago[3],
            "fecha": pago[4]
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def obtener_pagos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_pago, id_reserva, monto, estado, fecha
        FROM pagos
        ORDER BY id_pago;
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {
            "id_pago": row[0],
            "id_reserva": row[1],
            "monto": float(row[2]),
            "estado": row[3],
            "fecha": row[4]
        } for row in rows
    ]

def obtener_pago(id_pago: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_pago, id_reserva, monto, estado, fecha
        FROM pagos
        WHERE id_pago = %s;
    """, (id_pago,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "id_pago": row[0],
            "id_reserva": row[1],
            "monto": float(row[2]),
            "estado": row[3],
            "fecha": row[4]
        }
    return None

def obtener_pagos_por_reserva(id_reserva: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_pago, id_reserva, monto, estado, fecha
        FROM pagos
        WHERE id_reserva = %s
        ORDER BY id_pago;
    """, (id_reserva,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {
            "id_pago": row[0],
            "id_reserva": row[1],
            "monto": float(row[2]),
            "estado": row[3],
            "fecha": row[4]
        } for row in rows
    ]
