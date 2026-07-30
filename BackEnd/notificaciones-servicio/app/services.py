from .database import get_connection

def crear_notificacion(id_reserva: int, correo: str, estado: str = 'PENDIENTE'):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_reserva FROM reservas WHERE id_reserva = %s;", (id_reserva,))
        if cursor.fetchone() is None:
            raise ValueError("Reserva no encontrada")
        query = """
            INSERT INTO notificaciones (id_reserva, correo, estado)
            VALUES (%s, %s, %s)
            RETURNING id_notificacion, id_reserva, correo, estado, fecha_envio;
        """
        cursor.execute(query, (id_reserva, correo, estado))
        notif = cursor.fetchone()
        conn.commit()
        return {
            "id_notificacion": notif[0],
            "id_reserva": notif[1],
            "correo": notif[2],
            "estado": notif[3],
            "fecha_envio": notif[4]
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def obtener_notificaciones():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_notificacion, id_reserva, correo, estado, fecha_envio
        FROM notificaciones
        ORDER BY id_notificacion;
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {
            "id_notificacion": row[0],
            "id_reserva": row[1],
            "correo": row[2],
            "estado": row[3],
            "fecha_envio": row[4]
        } for row in rows
    ]

def obtener_notificacion(id_notificacion: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_notificacion, id_reserva, correo, estado, fecha_envio
        FROM notificaciones
        WHERE id_notificacion = %s;
    """, (id_notificacion,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "id_notificacion": row[0],
            "id_reserva": row[1],
            "correo": row[2],
            "estado": row[3],
            "fecha_envio": row[4]
        }
    return None

def obtener_notificaciones_por_reserva(id_reserva: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_notificacion, id_reserva, correo, estado, fecha_envio
        FROM notificaciones
        WHERE id_reserva = %s
        ORDER BY id_notificacion;
    """, (id_reserva,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {
            "id_notificacion": row[0],
            "id_reserva": row[1],
            "correo": row[2],
            "estado": row[3],
            "fecha_envio": row[4]
        } for row in rows
    ]
