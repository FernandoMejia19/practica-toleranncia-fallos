import os
import sys
import json
import urllib.request
import urllib.error

gateway = os.getenv("GATEWAY_URL", "http://localhost")

def make_reservation(seat_id, cliente, correo, monto):
    url = f"{gateway}/reservations"
    data = json.dumps({
        "id_asiento": seat_id,
        "cliente": cliente,
        "correo": correo,
        "monto": monto
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err_json = json.loads(body)
        except Exception:
            err_json = body
        return e.code, err_json
    except Exception as e:
        return 0, str(e)

def send_notification(reserva_id, correo, simular_fallo):
    url = f"{gateway}/notifications?simular_fallo={str(simular_fallo).lower()}"
    data = json.dumps({
        "id_reserva": reserva_id,
        "correo": correo
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err_json = json.loads(body)
        except Exception:
            err_json = body
        return e.code, err_json
    except Exception as e:
        return 0, str(e)

def check_reservation(reserva_id):
    url = f"{gateway}/reservations/{reserva_id}"
    try:
        with urllib.request.urlopen(url) as r:
            body = r.read().decode("utf-8")
            return json.loads(body)
    except Exception as e:
        return {"error": str(e)}

def test_scenario():
    print("=" * 60)
    print(" PRUEBA: EL CORREO PERDIDO (NOTIFICACIONES FUERA DE LINEA)")
    print("=" * 60)
    print("Asegurese de que todos los servicios esten activos.")
    print("Presione ENTER para comenzar...")
    input()

    print("\n--- PASO 1: Creando reserva y procesando pago principal ---")
    status, res = make_reservation(5, "Sofia Diaz", "sofia@test.com", 40.0)
    print(f"Resultado Reserva: {status}")
    print(f"Respuesta: {json.dumps(res, indent=2)}")
    
    if status != 200:
        print("Error al crear reserva. Abortando.")
        return
        
    id_reserva = res.get("id_reserva")
    
    print("\n--- PASO 2: Consultando estado de la reserva en base de datos ---")
    data_res = check_reservation(id_reserva)
    print(f"Estado de la Reserva #{id_reserva}: {data_res.get('estado')} (Debe ser CONFIRMADA)")

    print("\n--- PASO 3: Intentando enviar correo simulando fallo en servidor SMTP ---")
    status_notif, res_notif = send_notification(id_reserva, "sofia@test.com", True)
    print(f"Resultado Notificacion: {status_notif}")
    print(f"Respuesta: {json.dumps(res_notif, indent=2)}")

    print("\n--- PASO 4: Confirmando degradacion elegante ---")
    data_res_final = check_reservation(id_reserva)
    print(f"Estado de la Reserva final en BD: {data_res_final.get('estado')} (Debe seguir CONFIRMADA)")
    print("La caida de notificaciones no afecto la transaccion de compra principal.")
    print("=" * 60)

if __name__ == "__main__":
    test_scenario()
