# Guía Completa de Instalación y Pruebas - PC 1 (Servidor Principal)

La **PC 1 (IP: 100.119.203.121)** alojará la Base de Datos PostgreSQL, el API Gateway, el microservicio Core de Reservas y coordinará el clúster local Minikube utilizando el perfil aislado `ticket-chaos2`.

---

## 1. Requisitos Previos en PC 1
Asegúrese de tener instalado en su sistema operativo:
- **Git** (para clonar el repositorio).
- **Docker Desktop** (o Docker Engine).
- **Minikube** (instalado y configurado en el PATH).
- **Python 3.x** (para ejecutar los scripts de prueba).

---

## 2. Preparación y Clonación del Proyecto en PC 1

1. Abra una terminal (CMD o PowerShell) en la PC 1.
2. Clone el repositorio del proyecto:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd pratica-toleracia-fallos
   ```

---

## 3. Despliegue en Minikube (PC 1 - Perfil ticket-chaos2)

1. **Iniciar Minikube con Perfil Aislado:**
   Inicie su clúster local utilizando el perfil `ticket-chaos2`:
   ```bash
   minikube start -p ticket-chaos2 --driver=docker
   ```

2. **Construir Imágenes Locales:**
   Construya las imágenes correspondientes a los servicios de la PC 1:
   ```bash
   docker build -t reserva-service:latest -f BackEnd/reserva-servicio/Dockerfile BackEnd/reserva-servicio
   docker build -t api-gateway:latest -f gateway/Dockerfile .
   ```

3. **Cargar Imágenes en Minikube (Solución a ErrImagePull):**
   Cargue las imágenes locales de su Docker host directamente dentro del entorno de Minikube:
   ```bash
   minikube image load reserva-service:latest -p ticket-chaos2
   minikube image load api-gateway:latest -p ticket-chaos2
   ```

4. **Desplegar los Manifiestos de Kubernetes:**
   Aplique la configuración específica para la PC 1:
   ```bash
   kubectl apply -f K8S/pc-distribuido/pc1/
   ```

5. **Exponer los Servicios al Exterior (Para que PC 2 pueda conectarse):**
   Para conectar las dos Minikube entre las PCs físicas por red, redirija los puertos escuchando en todas las interfaces de red (`0.0.0.0`):
   - **Exponer Base de Datos PostgreSQL:**
     ```bash
     kubectl port-forward --address 0.0.0.0 service/postgres 30432:5432
     ```
     *(Mantenga esta terminal abierta o ejecute en segundo plano)*.
   - **Exponer el API Gateway (En otra terminal):**
     ```bash
     kubectl port-forward --address 0.0.0.0 service/api-gateway 30080:80
     ```
     *(Mantenga esta terminal abierta)*.

---

## 4. Secuencia de Ejecución de Pruebas (Desde la consola de PC 1)

Abra otra terminal en la PC 1 en la carpeta raíz del proyecto y configure la variable de entorno del gateway apuntando al puerto redireccionado `30080`:
- **Windows CMD**: `set GATEWAY_URL=http://localhost:30080`
- **PowerShell**: `$env:GATEWAY_URL="http://localhost:30080"`

### Paso 1: Verificar el Balanceo de Tráfico Activo
```bash
python tests/test_balanceo.py
```
*Salida esperada: El script llamará 10 veces al endpoint `/server`. Mostrará cómo las llamadas se reparten entre las réplicas del Core en PC 1, alternando sus nombres de pod e IPs.*

### Paso 2: Simulación de Sobrecarga
```bash
python tests/test_sobrecarga.py
```
*Salida esperada: Envío de 10 peticiones rápidas, donde las excedentes a 5 req/s son inmediatamente bloqueadas con HTTP 429.*

### Paso 3: Tolerancia a Caídas (El Inventario Fantasma)
1. Detenga el inventario en la **PC 2** (apague su port-forward de inventario o escale a 0 en la PC 2: `kubectl scale deployment inventario-service --replicas=0`).
2. Ejecute la prueba en **PC 1**:
   ```bash
   python tests/test_inventario_fantasma.py
   ```
3. Observe los reintentos automáticos en la consola y logs:
   ```bash
   kubectl logs -f -l app=reserva-service --tail=20
   ```
4. Restaure el servicio en **PC 2** (vuelva a iniciar el port-forward o escale en PC 2: `kubectl scale deployment inventario-service --replicas=2`).

### Paso 4: Latencia y Circuit Breaker (La Pasarela Lenta)
```bash
python tests/test_pasarela_lenta.py
```
*Salida esperada: 2 peticiones lentas que toman 3s cada una y ejecutan compensación SAGA (asiento liberado). La 3ª petición falla instantáneamente con error de Circuit Breaker. Al esperar 10s y reintentar, el circuito recupera y procesa con éxito.*

### Paso 5: Degradación Elegante (El Correo Perdido)
1. Detenga notificaciones en **PC 2** (apague su port-forward de notificaciones o escale a 0: `kubectl scale deployment notificaciones-service --replicas=0`).
2. Ejecute la prueba:
   ```bash
   python tests/test_correo_perdido.py
   ```
3. Verifique que la compra finalice con éxito (HTTP 200) a pesar de la caída del correo.
4. Restaure el servicio en **PC 2**.
