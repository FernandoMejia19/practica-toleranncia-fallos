import os
import sys
import json
import urllib.request

gateway = os.getenv("GATEWAY_URL", "http://localhost")

def test_load_balancing():
    print("=" * 60)
    print(" PRUEBA: BALANCEO DE TRAFICO ENTRE LOS NODOS (PC 1 Y PC 2)")
    print("=" * 60)
    print("Este script realizara 10 peticiones secuenciales al endpoint /server.")
    print("Kubernetes deberia balancear el trafico entre las dos replicas.")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("[Modo Automatico Activo]")
    else:
        print("Presione ENTER para comenzar...")
        input()

    url = f"{gateway}/server"
    pods_seen = {}

    print("Enviando 10 peticiones...")
    for i in range(1, 11):
        try:
            with urllib.request.urlopen(url) as response:
                body = response.read().decode("utf-8")
                data = json.loads(body)
                pod_name = data.get("hostname", "unknown")
                pod_ip = data.get("ip", "unknown")
                
                pods_seen[pod_name] = pod_ip
                print(f"Peticion {i:2}: Atendida por el Pod [{pod_name}] con IP [{pod_ip}]")
        except Exception as e:
            print(f"Peticion {i:2}: Fallo - {str(e)}")

    print("\nResumen de Replicas Detectadas:")
    print("-" * 50)
    for pod, ip in pods_seen.items():
        print(f" - Pod: {pod:25} | IP interna: {ip}")
    
    if len(pods_seen) > 1:
        print("\nVerificacion: EXITOSA. Las peticiones fueron distribuidas entre multiples pods.")
        print("Esto demuestra que el balanceador de carga de Kubernetes (kube-proxy) funciona.")
    else:
        print("\nVerificacion: ADVERTENCIA. Solo se detecto una replica.")
        print("Asegurese de tener replicas activas en ambos nodos ('kubectl get pods -o wide').")
    print("=" * 60)

if __name__ == "__main__":
    test_load_balancing()
