# Guía de Pruebas de Tolerancia a Fallos y Caos (Multi-PC)

Esta guía detalla los pasos para realizar el despliegue distribuido en dos computadoras físicas (PC 1 y PC 2) y ejecutar los scripts de prueba de caos desde la consola, tanto para **Docker Compose** como para **Kubernetes**.

---

## Información de Red
- **PC 1 (IP: 100.119.203.121)**: Nodo principal / Servidor A.
- **PC 2 (IP: 100.125.114.25)**: Nodo secundario / Servidor B.

---

## OPCION A: Despliegue y Pruebas en Kubernetes (Clúster Multi-Nodo)

En un entorno Kubernetes multi-nodo (donde la PC 1 actúa como plano de control y la PC 2 está unida como nodo de cómputo), Kubernetes gestiona la red interna (overlay) de forma transparente. Las réplicas se comunican usando los nombres de servicio DNS del clúster (e.g., `http://inventario-service:8000`).

### 1. Despliegue en el Clúster
1. Asegúrese de que la PC 2 esté unida al clúster de la PC 1 (usando `kubeadm join` o la herramienta del clúster como K3s/MicroK8s).
2. Construya las imágenes Docker en ambas máquinas (o cárguelas al registro local de Kubernetes):
   ```bash
   # En cada PC, construya las imágenes:
   docker build -t reserva-service:latest -f BackEnd/reserva-servicio/Dockerfile BackEnd/reserva-servicio
   docker build -t inventario-service:latest -f BackEnd/inventario-servicio/Dockerfile BackEnd/inventario-servicio
   docker build -t pagos-service:latest -f BackEnd/pagos-servicio/Dockerfile BackEnd/pagos-servicio
   docker build -t notificaciones-service:latest -f BackEnd/notificaciones-servicio/Dockerfile BackEnd/notificaciones-servicio
   docker build -t api-gateway:latest -f gateway/Dockerfile .
   ```
3. Desde la **PC 1**, aplique los manifiestos de Kubernetes:
   ```bash
   kubectl apply -f K8S/
   ```
4. Verifique la distribución de los Pods entre los dos nodos:
   ```bash
   kubectl get pods -o wide
   ```
   *(Observará que las 2 réplicas de `reserva-service` e `inventario-service` están repartidas entre la PC 1 y la PC 2 debido a las reglas de `podAntiAffinity`).*

### 2. Acceso y Dirección del Gateway
El API Gateway se expone mediante un servicio tipo `NodePort` en el puerto `30080` (definido en `K8S/gateway.yaml`). Puede acceder a la aplicación desde el navegador de **cualquier PC** escribiendo:
- `http://100.119.203.121:30080` (o `http://100.125.114.25:30080`)

Para las pruebas desde consola, defina la variable `GATEWAY_URL` apuntando al NodePort en su terminal:
- **Windows CMD**: `set GATEWAY_URL=http://100.119.203.121:30080`
- **PowerShell**: `$env:GATEWAY_URL="http://100.119.203.121:30080"`

### 3. Ejecución de Pruebas e Inyección de Caos (Desde PC 1)

#### Escenario 1: El Inventario Fantasma (Caída de Pod)
- **Inyección de Caos:** Detenga el servicio de inventario en el clúster escalando sus réplicas a 0:
  ```bash
  kubectl scale deployment inventario-service --replicas=0
  ```
- **Comando de Prueba:** `python tests/test_inventario_fantasma.py`
- **Monitoreo de Logs:** En otra terminal de la PC 1, observe los reintentos:
  ```bash
  kubectl logs -f -l app=reserva-service --tail=20
  ```
- **Restauración:**
  ```bash
  kubectl scale deployment inventario-service --replicas=2
  ```

#### Escenario 2: La Pasarela Lenta (Latencia y Circuit Breaker)
- **Comando de Prueba:** `python tests/test_pasarela_lenta.py`
- **Monitoreo de Logs:** Observe los logs de reservas para presenciar el disparo del Circuit Breaker (`OPEN`) y la compensación SAGA:
  ```bash
  kubectl logs -f -l app=reserva-service --tail=20
  ```

#### Escenario 3: El Correo Perdido (Notificación fuera de línea)
- **Inyección de Caos:** Escale a 0 el deployment de notificaciones:
  ```bash
  kubectl scale deployment notificaciones-service --replicas=0
  ```
- **Comando de Prueba:** `python tests/test_correo_perdido.py`
- **Restauración:**
  ```bash
  kubectl scale deployment notificaciones-service --replicas=1
  ```

#### Escenario 4: Sobrecarga (El Diluvio de Peticiones)
- **Comando de Prueba:** `python tests/test_sobrecarga.py`
- **Verificación:** Nginx (dentro del pod del gateway) rechazará las peticiones excedentes con HTTP 429.

#### Escenario 5: Condición de Carrera
- **Comando de Prueba:** `python tests/test_condicion_carrera.py`

---

## OPCION B: Despliegue y Pruebas en Docker Compose

Si no dispone de un clúster Kubernetes configurado en el momento, puede usar la simulación distribuida mediante Docker Compose:

### 1. Despliegue

#### En la PC 1 (IP: 100.119.203.121)
```bash
docker-compose -f docker-compose-pc1.yml up --build -d
```

#### En la PC 2 (IP: 100.125.114.25)
```bash
docker-compose -f docker-compose-pc2.yml up --build -d
```

### 2. Dirección del Gateway
El gateway se expone en el puerto `80` de la PC 1. Configure en la consola de PC 1:
- **Windows CMD**: `set GATEWAY_URL=http://localhost`

### 3. Ejecución de Pruebas e Inyección de Caos (Desde PC 1)

- **Inventario Fantasma:**
  - Apagar en PC 2: `docker stop inventario-service`
  - Ejecutar en PC 1: `python tests/test_inventario_fantasma.py`
  - Restaurar en PC 2: `docker start inventario-service`

- **Pasarela Lenta:**
  - Ejecutar en PC 1: `python tests/test_pasarela_lenta.py`
  - Monitorear logs en PC 1: `docker logs -f reserva-service`

- **Correo Perdido:**
  - Apagar en PC 2: `docker stop notificaciones-service`
  - Ejecutar en PC 1: `python tests/test_correo_perdido.py`
  - Restaurar en PC 2: `docker start notificaciones-service`

- **Sobrecarga:**
  - Ejecutar en PC 1: `python tests/test_sobrecarga.py`

- **Condición de Carrera:**
  - Ejecutar en PC 1: `python tests/test_condicion_carrera.py`
