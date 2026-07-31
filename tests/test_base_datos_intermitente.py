import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost").rstrip("/")
POSTGRES_WORKLOAD = os.getenv("POSTGRES_WORKLOAD", "deployment/postgres")
NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
DOWN_SECONDS = int(os.getenv("DB_DOWN_SECONDS", "6"))
UP_TIMEOUT = int(os.getenv("DB_UP_TIMEOUT", "90"))
CYCLES = int(os.getenv("DB_FLAP_CYCLES", "2"))
SEAT_IDS = [
    int(value.strip())
    for value in os.getenv("SEAT_IDS", "2,3,5,6").split(",")
    if value.strip()
]


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def run_kubectl(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    command = ["kubectl", "-n", NAMESPACE, *args]
    print(f"[{now()}] $ {' '.join(command)}")
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=True,
    )


def ensure_kubectl() -> None:
    try:
        result = run_kubectl("get", POSTGRES_WORKLOAD, check=False)
    except FileNotFoundError:
        print("ERROR: kubectl no está instalado o no está disponible en PATH.")
        sys.exit(1)

    if result.returncode != 0:
        print("ERROR: no se encontró el recurso de PostgreSQL.")
        print(result.stderr.strip())
        print(
            "Revise POSTGRES_WORKLOAD. Ejemplo: "
            '$env:POSTGRES_WORKLOAD="deployment/postgres"'
        )
        sys.exit(1)


def scale_postgres(replicas: int) -> bool:
    result = run_kubectl(
        "scale",
        POSTGRES_WORKLOAD,
        f"--replicas={replicas}",
        check=False,
    )
    if result.returncode != 0:
        print(f"ERROR al escalar PostgreSQL: {result.stderr.strip()}")
        return False
    print(result.stdout.strip())
    return True


def wait_postgres_ready() -> bool:
    result = run_kubectl(
        "rollout",
        "status",
        POSTGRES_WORKLOAD,
        f"--timeout={UP_TIMEOUT}s",
        check=False,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        print(f"PostgreSQL no quedó listo: {result.stderr.strip()}")
        return False
    return True


def request_json(method: str, path: str, payload: dict | None = None, timeout: int = 12):
    url = f"{GATEWAY_URL}{path}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            elapsed = time.time() - started
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body
            return response.status, parsed, elapsed
    except urllib.error.HTTPError as error:
        elapsed = time.time() - started
        body = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return error.code, parsed, elapsed
    except Exception as error:
        elapsed = time.time() - started
        return 0, str(error), elapsed


def print_result(label: str, status: int, body, elapsed: float) -> None:
    if status in (200, 201):
        category = "ÉXITO"
    elif status in (500, 502, 503, 504, 0):
        category = "FALLO DE CONECTIVIDAD/BD"
    elif status == 409:
        category = "ASIENTO NO DISPONIBLE"
    else:
        category = "RESPUESTA CONTROLADA"

    print(
        f"[{now()}] {label:<38} HTTP={status:<3} "
        f"tiempo={elapsed:>5.2f}s  {category}"
    )
    print(f"         Respuesta: {json.dumps(body, ensure_ascii=False)}")


def attempt_write(seat_id: int, label: str):
    payload = {
        "id_asiento": seat_id,
        "cliente": f"Prueba BD {label}",
        "correo": f"bd-{label.lower().replace(' ', '-')}@test.com",
        "monto": 35.0,
    }
    return request_json("POST", "/reservations", payload=payload)


def check_api() -> None:
    status, body, elapsed = request_json("GET", "/reservations", timeout=8)
    print_result("Comprobación inicial de la API", status, body, elapsed)
    if status not in (200, 201):
        print("ADVERTENCIA: la API no está respondiendo correctamente antes de iniciar.")


def main() -> None:
    print("=" * 72)
    print(" PRUEBA: BASE DE DATOS INTERMITENTE (FLAPPING DE POSTGRESQL)")
    print("=" * 72)
    #print(f"Gateway:             {GATEWAY_URL}")
    print(f"Recurso PostgreSQL:  {POSTGRES_WORKLOAD}")
    #print(f"Namespace:           {NAMESPACE}")
    print(f"Ciclos de caída:     {CYCLES}")
    print(f"Asientos de prueba:  {SEAT_IDS}")
    print()
    #print("El script hará lo siguiente:")
    #print("  1. Probar una escritura con PostgreSQL activo.")
    #print("  2. Escalar PostgreSQL a 0 réplicas.")
    #print("  3. Intentar una escritura durante la caída.")
    #print("  4. Restaurar PostgreSQL y esperar que quede Ready.")
    #print("  5. Intentar una nueva escritura para comprobar recuperación.")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("[Modo Automatico Activo]")
    else:
        input("Presione ENTER para comenzar o Ctrl+C para cancelar...")

    ensure_kubectl()
    check_api()

    results = []
    seat_index = 0

    def next_seat() -> int:
        nonlocal seat_index
        seat = SEAT_IDS[seat_index % len(SEAT_IDS)]
        seat_index += 1
        return seat

    try:
        seat = next_seat()
        result = attempt_write(seat, "BD activa inicial")
        results.append(("BD activa inicial", *result))
        print_result("Escritura con BD activa", *result)

        for cycle in range(1, CYCLES + 1):
            print("\n" + "-" * 72)
            print(f"CICLO {cycle}/{CYCLES}: PostgreSQL ABAJO")
            print("-" * 72)

            if not scale_postgres(0):
                raise RuntimeError("No fue posible detener PostgreSQL")

            time.sleep(DOWN_SECONDS)

            seat = next_seat()
            result = attempt_write(seat, f"ciclo {cycle} BD caída")
            results.append((f"Ciclo {cycle} BD caída", *result))
            print_result(f"Escritura durante caída {cycle}", *result)

            print("\nRestaurando PostgreSQL...")
            if not scale_postgres(1):
                raise RuntimeError("No fue posible restaurar PostgreSQL")
            if not wait_postgres_ready():
                raise RuntimeError("PostgreSQL no se recuperó dentro del tiempo esperado")

            # Da unos segundos a los servicios para abrir conexiones nuevas.
            time.sleep(3)

            seat = next_seat()
            result = attempt_write(seat, f"ciclo {cycle} recuperada")
            results.append((f"Ciclo {cycle} recuperada", *result))
            print_result(f"Escritura tras recuperación {cycle}", *result)

    except KeyboardInterrupt:
        print("\nPrueba cancelada por el usuario.")
    except Exception as error:
        print(f"\nERROR durante la prueba: {error}")
    finally:
        print("\nAsegurando que PostgreSQL quede activo...")
        scale_postgres(1)
        wait_postgres_ready()

    print("\n" + "=" * 72)
    print(" RESUMEN")
    print("=" * 72)
    for label, status, body, elapsed in results:
        print_result(label, status, body, elapsed)

    failures_down = [
        item for item in results
        if "BD caída" in item[0] and item[1] in (0, 500, 502, 503, 504)
    ]
    successes_after = [
        item for item in results
        if "recuperada" in item[0] and item[1] in (200, 201)
    ]

    print()
    if failures_down and successes_after:
        print("VERIFICACIÓN EXITOSA:")
        print("- Durante la caída, las escrituras fallaron de forma observable.")
        print("- Después de restaurar PostgreSQL, el sistema volvió a aceptar operaciones.")
        print("- Esto demuestra conectividad intermitente y capacidad de recuperación.")
    else:
        print("VERIFICACIÓN PARCIAL:")
        print("Revise los códigos HTTP y los logs de reserva-service/PostgreSQL.")
        print("Una respuesta 409 indica asiento ocupado, no necesariamente un fallo de BD.")

    print("=" * 72)


if __name__ == "__main__":
    if not SEAT_IDS:
        print("ERROR: SEAT_IDS no contiene asientos válidos.")
        sys.exit(1)
    main()
