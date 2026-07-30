import os
import sys
import json
import time
import threading
import urllib.request
import urllib.error

gateway = os.getenv("GATEWAY_URL", "http://localhost")

results = []
lock = threading.Lock()

def send_request(client_name, email):
    url = f"{gateway}/reservations"
    data = json.dumps({
        "id_asiento": 3,
        "cliente": client_name,
        "correo": email,
        "monto": 35.0
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
            with lock:
                results.append((client_name, response.status, json.loads(body)))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err_json = json.loads(body)
        except Exception:
            err_json = body
        with lock:
            results.append((client_name, e.code, err_json))
    except Exception as e:
        with lock:
            results.append((client_name, 0, str(e)))

def check_seat(seat_id):
    url = f"{gateway}/inventory/seats/{seat_id}"
    try:
        with urllib.request.urlopen(url) as r:
            body = r.read().decode("utf-8")
            return json.loads(body)
    except Exception as e:
        return {"error": str(e)}

def test_scenario():
    print("=" * 60)
    print(" PRUEBA: CONDICION DE CARRERA (SOBREVENTA CONCURRENTE)")
    print("=" * 60)
    print("Este script enviara 2 peticiones de compra simultaneas para el ASIENTO 3.")
    print("Presione ENTER para comenzar...")
    input()

    print("Comprobando estado inicial del Asiento 3...")
    asiento_info = check_seat(3)
    print(f"Estado inicial Asiento 3: {asiento_info.get('estado')}")
    if asiento_info.get("estado") != "DISPONIBLE":
        print("ADVERTENCIA: El Asiento 3 no esta DISPONIBLE. La prueba podria fallar.")
        print("¿Desea continuar de todos modos? (S/N): ")
        if input().strip().lower() == "n":
            return

    t1 = threading.Thread(target=send_request, args=("Cliente A", "a@test.com"))
    t2 = threading.Thread(target=send_request, args=("Cliente B", "b@test.com"))

    print("Enviando peticiones concurrentes...")
    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\nResultados:")
    with lock:
        for name, code, body in results:
            print(f"Cliente: {name} | HTTP Status: {code}")
            print(f"Respuesta: {json.dumps(body, indent=2)}")
            print("-" * 45)

    print("\nComprobando estado final del Asiento 3 en Inventario...")
    asiento_final = check_seat(3)
    print(f"Estado final: {asiento_final.get('estado')} (Debe ser VENDIDO o RESERVADO, nunca duplicado)")
    print("=" * 60)

if __name__ == "__main__":
    test_scenario()
