# Guía Completa de Instalación y Monitoreo - PC 2 (Nodo Secundario)

La **PC 2 (IP: 100.125.114.25)** alojará los microservicios de Inventario, Pagos y Notificaciones en un clúster local Minikube independiente utilizando el perfil aislado `ticket-chaos2`, conectándose a la base de datos de la PC 1.

---

## 1. Requisitos Previos en PC 2
Asegúrese de tener instalado en su sistema operativo:
- **Git** (para clonar el repositorio).
- **Docker Desktop** (o Docker Engine).
- **Minikube** (instalado y configurado en el PATH).

---

## 2. Preparación y Clonación del Proyecto en PC 2

1. Abra una terminal en la PC 2.
2. Clone el repositorio del proyecto:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd string-del-proyecto
   ```

---

## 3. Despliegue en Minikube (PC 2 - Perfil ticket-chaos2)

1. **Iniciar Minikube con Perfil Aislado:**
   Inicie su clúster local utilizando el perfil `ticket-chaos2`:
   ```bash
   minikube start -p ticket-chaos2 --driver=docker
   ```

2. **Construir Imágenes Locales:**
   Construya las imágenes correspondientes a los servicios de la PC 2:
   ```bash
   docker build -t inventario-service:latest -f BackEnd/inventario-servicio/Dockerfile BackEnd/inventario-servicio
   docker build -t pagos-service:latest -f BackEnd/pagos-servicio/Dockerfile BackEnd/pagos-servicio
   docker build -t notificaciones-service:latest -f BackEnd/notificaciones-servicio/Dockerfile BackEnd/notificaciones-servicio
   ```

3. **Cargar Imágenes en Minikube (Solución a ErrImagePull):**
   Cargue las imágenes locales de su Docker host directamente dentro del entorno de Minikube:
   ```bash
   minikube image load inventario-service:latest -p ticket-chaos2
   minikube image load pagos-service:latest -p ticket-chaos2
   minikube image load notificaciones-service:latest -p ticket-chaos2
   ```

4. **Desplegar los Manifiestos de Kubernetes:**
   Aplique la configuración específica para la PC 2:
   ```bash
   kubectl apply -f K8S/pc-distribuido/pc2/
   ```

5. **Exponer los Servicios al Exterior (Para que PC 1 pueda conectarse):**
   Abra terminales independientes en la PC 2 para mapear y exponer los servicios en todas las interfaces de red (`0.0.0.0`) hacia la red LAN utilizando los puertos válidos de Kubernetes NodePort (`30000-32767`):
   - **Exponer Servicio de Inventario:**
     ```bash
     kubectl port-forward --address 0.0.0.0 service/inventario-service 32001:8000
     ```
   - **Exponer Servicio de Pagos (En otra terminal):**
     ```bash
     kubectl port-forward --address 0.0.0.0 service/pagos-service 32002:8000
     ```
   - **Exponer Servicio de Notificaciones (En otra terminal):**
     ```bash
     kubectl port-forward --address 0.0.0.0 service/notificaciones-service 32003:8000
     ```

---

## 4. Monitoreo y Observabilidad (Durante las Pruebas)

Mientras la PC 1 ejecuta los scripts de caos, puede ver en la PC 2 qué ocurre internamente ejecutando:

### Monitoreo del Inventario (Caídas de Red y Bloqueos de Asientos)
```bash
kubectl logs -f -l app=inventario-service --tail=20
```

### Monitoreo del Procesamiento de Pagos (Simulador de Latencia)
```bash
kubectl logs -f -l app=pagos-service --tail=20
```

### Monitoreo de Notificaciones (Simulador de Fallos de Envío)
```bash
kubectl logs -f -l app=notificaciones-service --tail=20
```
