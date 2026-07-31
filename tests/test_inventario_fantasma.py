import os
import sys
import json
import time
import urllib.request
import urllib.error

gateway = os.getenv("GATEWAY_URL", "http://localhost")

def make_reservation(seat_id, cliente, correo, monto, tolerancia):
    url = f"{gateway}/reservations?tolerancia_activa={str(tolerancia).lower()}"
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

def test_scenario():
    print("=" * 60)
    print(" PRUEBA: EL INVENTARIO FANTASMA (CAIDA DE INVENTARIO)")
    print("=" * 60)
    print("Asegurese de que el servicio de inventario este APAGADO en la PC 2.")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("[Modo Automatico Activo]")
    else:
        print("Presione ENTER para comenzar...")
        input()

    print("\n--- PASO 1: Ejecutando CON Tolerancia a Fallos (Reintentos) ---")
    status, res, elapsed = make_reservation(2, "Test Retry", "retry@test.com", 35.0, True)
    print(f"Resultado HTTP: {status}")
    print(f"Tiempo Transcurrido: {elapsed:.2f} segundos")
    print(f"Respuesta del Servidor:\n{json.dumps(res, indent=2)}")

    print("\n--- PASO 2: Ejecutando SIN Tolerancia a Fallos (Falla Inmediata) ---")
    status_no, res_no, elapsed_no = make_reservation(2, "Test No Retry", "noretry@test.com", 35.0, False)
    print(f"Resultado HTTP: {status_no}")
    print(f"Tiempo Transcurrido: {elapsed_no:.2f} segundos")
    print(f"Respuesta del Servidor:\n{json.dumps(res_no, indent=2)}")
    print("=" * 60)

if __name__ == "__main__":
    test_scenario()
