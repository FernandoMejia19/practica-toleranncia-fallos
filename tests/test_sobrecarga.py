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

def send_request(req_id):
    url = f"{gateway}/reservations"
    data = json.dumps({
        "id_asiento": 6,
        "cliente": f"Carga {req_id}",
        "correo": f"carga{req_id}@test.com",
        "monto": 40.0
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
            with lock:
                results.append((req_id, response.status, elapsed))
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_time
        with lock:
            results.append((req_id, e.code, elapsed))
    except Exception as e:
        elapsed = time.time() - start_time
        with lock:
            results.append((req_id, 0, elapsed))

def test_scenario():
    print("=" * 60)
    print(" PRUEBA: EL DILUVIO DE PETICIONES (SOBRECARGA DE TRAFICO)")
    print("=" * 60)
    print("Este script enviara 10 peticiones de compra concurrentes.")
    print("Nginx tiene un limite configurado de 5 req/s.")
    print("Presione ENTER para comenzar...")
    input()

    threads = []
    print("Enviando 10 peticiones concurrentes...")
    for i in range(1, 11):
        t = threading.Thread(target=send_request, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("\nResultados de las peticiones:")
    print("ID Peticion | Codigo HTTP | Tiempo de Respuesta")
    print("-" * 45)
    
    with lock:
        results.sort(key=lambda x: x[0])
        for r_id, code, elap in results:
            status_text = "EXITO" if code == 200 else "BLOQUEADO (429)" if code == 429 else f"ERROR ({code})"
            print(f"   {r_id:7}  |     {code}     |      {elap:.3f}s ({status_text})")
            
    print("\nComprobacion:")
    print("Se debieron observar peticiones con codigo 429 (Too Many Requests).")
    print("Esto demuestra que el API Gateway rechazo la sobrecarga protegiendo al backend.")
    print("=" * 60)

if __name__ == "__main__":
    test_scenario()
