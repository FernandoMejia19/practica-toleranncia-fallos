# Guía de Pruebas de Tolerancia a Fallos y Caos (Multi-PC con Minikube)

Esta guía detalla los pasos para habilitar la exposición de los servicios en red y realizar las pruebas de caos en la arquitectura distribuida utilizando **Minikube** (con el perfil aislado `ticket-chaos2`) y ejecutando los scripts de prueba en la consola (CMD/PowerShell) de la **PC 1**.

---

## 1. Exposición y Habilitación de Puertos (Ejecutar al inicio en cada PC)

Para conectar los dos clústeres Minikube a través de la red física local, debe ejecutar los siguientes reenvíos de puertos en terminales independientes en cada máquina. Esto habilitará que los servicios sean accesibles en la LAN usando las IPs físicas:

### En la PC 1 (IP: 100.119.203.121)
Abra dos terminales independientes y ejecute:
1. **Habilitar y Exponer Base de Datos (Postgres):**
   ```bash
   kubectl port-forward --address 0.0.0.0 service/postgres 30432:5432 -p ticket-chaos2
   ```
2. **Habilitar y Exponer el API Gateway:**
   ```bash
   kubectl port-forward --address 0.0.0.0 service/api-gateway 30080:80 -p ticket-chaos2
   ```

### En la PC 2 (IP: 100.125.114.25)
Abra tres terminales independientes y ejecute:
1. **Habilitar y Exponer Servicio de Inventario:**
   ```bash
   kubectl port-forward --address 0.0.0.0 service/inventario-service 32001:8000 -p ticket-chaos2
   ```
2. **Habilitar y Exponer Servicio de Pagos:**
   ```bash
   kubectl port-forward --address 0.0.0.0 service/pagos-service 32002:8000 -p ticket-chaos2
   ```
3. **Habilitar y Exponer Servicio de Notificaciones:**
   ```bash
   kubectl port-forward --address 0.0.0.0 service/notificaciones-service 32003:8000 -p ticket-chaos2
   ```

---

## 2. Configuración de la Terminal de Pruebas (En PC 1)

Antes de iniciar la ejecución de los scripts, abra una terminal (CMD o PowerShell) en la PC 1 en la raíz del proyecto y defina la dirección del Gateway:
- **Windows CMD**: `set GATEWAY_URL=http://localhost:30080`
- **PowerShell**: `$env:GATEWAY_URL="http://localhost:30080"`

---

## 3. Secuencia de Pruebas y Simulaciones de Caos

### Paso 1: Verificar el Balanceo de Tráfico Activo
Esta prueba demuestra que las solicitudes al Core se distribuyen entre las 2 réplicas que corren en el clúster de la PC 1.
- **Comando a ejecutar en PC 1:**
  ```bash
  python tests/test_balanceo.py --auto
  ```
- **Comportamiento Esperado:** El script envía 10 llamadas secuenciales y muestra en pantalla cómo el balanceador de carga interno de Kubernetes alterna y reparte el tráfico entre los dos nombres de pod activos del servicio de reservas.

---

### Paso 2: Simulación de Sobrecarga (El Diluvio de Peticiones)
Demuestra cómo el Gateway unificado protege al sistema de ráfagas masivas bloqueando el tráfico que supere el límite de 5 req/s.
- **Comando a ejecutar en PC 1:**
  ```bash
  python tests/test_sobrecarga.py --auto
  ```
- **Comportamiento Esperado:** Envía 10 solicitudes paralelas concurrentes. Nginx bloquea el tráfico excedente de forma instantánea devolviendo un código **`429 Too Many Requests`**. Las solicitudes que logran pasar a la cola del backend retornan 503 debido a que la PC 2 no está procesando compras en este instante de la prueba.

---

### Paso 3: Tolerancia a Caídas (El Inventario Fantasma)
Evalúa cómo el Core mitiga la indisponibilidad temporal del inventario mediante políticas de reintentos exponenciales.

- **Paso A (Inyectar el Fallo):**
  En la **PC 2**, detenga temporalmente el port-forward de inventario cerrando la terminal que ejecuta el `port-forward` del puerto 32001 (o apague el pod en PC 2 con `kubectl scale deployment inventario-service --replicas=0 -p ticket-chaos2`).
- **Paso B (Ejecutar Prueba en PC 1):**
  ```bash
  python tests/test_inventario_fantasma.py --auto
  ```
- **Paso C (Comportamiento Esperado):**
  1. **Con Tolerancia:** El Core intentará conectarse 3 veces esperando `0.5s`, `1s` y `2s`. Si durante ese tiempo reactiva el servicio, la compra se completará. De lo contrario, reportará un HTTP 503 controlado. Puede observar los logs en PC 1 con:
     ```bash
     kubectl logs -f -l app=reserva-service
     ```
  2. **Sin Tolerancia:** El sistema falla de inmediato en el primer intento (0s transcurridos), sin reintentar.
- **Paso D (Restauración):**
  Restaure el servicio en la **PC 2** (iniciando el port-forward de nuevo o escalando a 2 réplicas).

---

### Paso 4: Latencia y Circuit Breaker (La Pasarela Lenta)
Demuestra cómo los timeouts evitan que las conexiones del servidor queden colgadas y cómo el Circuit Breaker entra en estado OPEN para rechazar tráfico ante fallos recurrentes.

- **Comando a ejecutar en PC 1:**
  ```bash
  python tests/test_pasarela_lenta.py --auto
  ```
- **Comportamiento Esperado:**
  1. **Petición 1 y 2 (CB Cerrado):** Se simula una demora de pagos de 15 segundos. Al superar el timeout límite de 3.0s, el Core cancela la transacción, ejecuta la compensación SAGA liberando el asiento retenido en el inventario y devuelve 503.
  2. **Petición 3 (CB Abierto):** Habiendo acumulado 2 fallos seguidos, el Circuit Breaker de reservas cambia a estado **`OPEN`**. Al enviar una compra normal inmediata, esta se rechaza instantáneamente (milisegundos) con mensaje `"Circuito de Pagos abierto"` sin sobrecargar la red.
  3. **Petición 4 (CB Recuperado):** El script espera 10 segundos (tiempo de recuperación). Al enviar la compra, el circuito cambia a `HALF-OPEN` y se cierra (`CLOSED`) tras completarse exitosamente (HTTP 200).
  4. **Petición 5 (Sin Tolerancia):** Se inyecta latencia sin resiliencia. La llamada se queda colgada durante 15 segundos bloqueando los hilos de ejecución. Al fallar, NO se ejecuta compensación, dejando el asiento bloqueado permanentemente en la base de datos (inconsistencia de datos).

---

### Paso 5: Fallo del Correo (El Correo Perdido)
Verifica que las caídas de servicios secundarios/notificaciones no interrumpan ni impidan la compra de boletos del cliente.

- **Paso A (Inyectar el Fallo):**
  En la **PC 2**, cierre la terminal del port-forward de notificaciones (puerto 32003) (o scale a 0 replicas en PC 2).
- **Paso B (Ejecutar Prueba en PC 1):**
  ```bash
  python tests/test_correo_perdido.py --auto
  ```
- **Paso C (Comportamiento Esperado):** La compra finaliza con éxito en la base de datos (estado `CONFIRMADA` y pago `EXITOSO`). El envío de la notificación falla de forma aislada sin comprometer el flujo crítico del negocio.
- **Paso D (Restauración):**
  Restaure la exposición del servicio en la **PC 2**.

---

### Paso 6: Consistencia de Asientos (Condición de Carrera)
Verifica la consistencia transaccional cuando dos usuarios compran concurrentemente el mismo asiento libre.
- **Comando a ejecutar en PC 1:**
  ```bash
  python tests/test_condicion_carrera.py --auto
  ```
- **Comportamiento Esperado:** Envía 2 solicitudes de compra en paralelo para el mismo Asiento 3. Un cliente recibirá éxito (HTTP 200) y el segundo cliente recibirá conflicto (HTTP 409) debido al control de estado transaccional en el inventario.

---

### Paso 7: Base de Datos Intermitente (Flapping de Postgres)
Verifica la respuesta del sistema cuando la base de datos centralizada sufre caídas intermitentes durante operaciones de escritura.
- **Comando a ejecutar en PC 1:**
  ```bash
  python tests/test_base_datos_intermitente.py --auto
  ```
- **Comportamiento Esperado:** 
  1. Realiza una escritura inicial exitosa.
  2. Apaga (escala a 0) PostgreSQL en el clúster usando `kubectl`.
  3. Intenta realizar una compra, la cual falla de forma visible (HTTP 500/503) debido a la caída de conectividad de BD.
  4. Restaura PostgreSQL a 1 réplica y espera que los pods estén listos (`rollout status`).
  5. Envía una nueva compra, la cual se procesa y finaliza con éxito (HTTP 200), demostrando auto-recuperación sin pérdidas ni corrupción.

