import os
import sys
import json
import time
import urllib.request
import urllib.error

gateway = os.getenv("GATEWAY_URL", "http://localhost")

def make_reservation(seat_id, cliente, correo, monto, delay, fail, tolerancia):
    url = f"{gateway}/reservations?simular_demora_pago={delay}&simular_fallo_pago={str(fail).lower()}&tolerancia_activa={str(tolerancia).lower()}"
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
    start_time = time.time()
    try:
        with urllib.request.urlopen(req) as response:
            elapsed = time.time() - start_time
            body = response.read().decode("utf-8")
            return response.status, json.loads(body), elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_time
        body = e.read().decode("utf-8")
        try:
            err_json = json.loads(body)
        except Exception:
            err_json = body
        return e.code, err_json, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        return 0, str(e), elapsed

def check_seat(seat_id):
    url = f"{gateway}/inventory/seats/{seat_id}"
    try:
        with urllib.request.urlopen(url) as r:
            body = r.read().decode("utf-8")
            return json.loads(body).get("estado")
    except Exception as e:
        return f"Error: {str(e)}"

def test_scenario():
    print("=" * 60)
    print(" PRUEBA: LA PASARELA LENTA (LATENCIA Y CIRCUIT BREAKER)")
    print("=" * 60)
    print("Asegurese de que todos los servicios esten activos.")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("[Modo Automatico Activo]")
    else:
        print("Presione ENTER para comenzar...")
        input()

    print("\n--- PARTE I: PROBANDO CON TOLERANCIA A FALLOS ---")
    
    print("\n[Peticion 1] Enviando compra con latencia de 15s...")
    s1, r1, e1 = make_reservation(2, "User A", "a@test.com", 35.0, 15, False, True)
    print(f"Resultado HTTP: {s1} | Tiempo tomado: {e1:.2f}s")
    print(f"Respuesta: {json.dumps(r1)}")
    print(f"Estado del Asiento 2 en Inventario: {check_seat(2)} (Debe ser DISPONIBLE por compensacion SAGA)")

    print("\n[Peticion 2] Enviando compra con latencia de 15s...")
    s2, r2, e2 = make_reservation(2, "User B", "b@test.com", 35.0, 15, False, True)
    print(f"Resultado HTTP: {s2} | Tiempo tomado: {e2:.2f}s")
    print(f"Respuesta: {json.dumps(r2)}")
    print("Circuit Breaker deberia estar abierto (OPEN).")

    print("\n[Peticion 3] Enviando compra normal inmediata...")
    s3, r3, e3 = make_reservation(2, "User C", "c@test.com", 35.0, 0, False, True)
    print(f"Resultado HTTP: {s3} | Tiempo tomado: {e3:.2f}s (Falla inmediata por Circuit Breaker Abierto)")
    print(f"Respuesta: {json.dumps(r3)}")

    print("\nEsperando 10 segundos para que expire el recovery_timeout...")
    time.sleep(10)

    print("\n[Peticion 4] Enviando compra normal inmediata...")
    s4, r4, e4 = make_reservation(2, "User D", "d@test.com", 35.0, 0, False, True)
    print(f"Resultado HTTP: {s4} | Tiempo tomado: {e4:.2f}s (Circuito se cerro y la compra fue exitosa!)")
    print(f"Respuesta: {json.dumps(r4)}")

    print("\n--- PARTE II: PROBANDO SIN TOLERANCIA A FALLOS ---")
    print("\n[Peticion 5] Enviando compra con latencia de 15s (SIN resiliencia)...")
    print("Esta peticion va a quedar colgada por 15 segundos...")
    s5, r5, e5 = make_reservation(3, "User E", "e@test.com", 35.0, 15, False, False)
    print(f"Resultado HTTP: {s5} | Tiempo tomado: {e5:.2f}s")
    print(f"Respuesta: {json.dumps(r5)}")
    print(f"Estado del Asiento 3 en Inventario: {check_seat(3)} (Debe quedar bloqueado RESERVADO por falta de compensacion SAGA)")
    print("=" * 60)

if __name__ == "__main__":
    test_scenario()
