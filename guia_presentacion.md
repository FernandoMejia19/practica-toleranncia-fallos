# Guía de Presentación de Tolerancia a Fallos (Live Demo)

Esta guía detalla el orden de la presentación, qué comandos ejecutar, qué ocurre internamente en cada caso y cómo demostrar el contraste entre tener la tolerancia activada y desactivada.

---

## 1. Verificación Inicial de Infraestructura (Antes de iniciar)

Ejecute en la terminal de la **PC 1** para mostrar que los servicios están listos y distribuidos:
```bash
kubectl get pods -o wide
```
- **Qué significa:** Muestra que la Base de Datos, el Nginx Gateway y las 2 réplicas del Core (`reserva-service`) están corriendo. Las réplicas del Core deben mostrar IPs internas distintas, lo que prueba que están balanceadas.

---

## 2. Pruebas con Solo PC 1 Activa (PC 2 Apagada/Desconectada)

Si la PC 2 aún no está encendida o está desconectada, puede realizar estas pruebas para iniciar la exposición:

### Prueba A: Balanceo de Tráfico Local
Demuestra que Kubernetes balancea las peticiones dinámicamente entre múltiples pods del Core en la PC 1.
- **Comando (en PC 1):**
  ```bash
  python tests/test_balanceo.py --auto
  ```
- **Qué muestra la pantalla:** Una lista de 10 peticiones secuenciales donde la IP interna y el Hostname del pod alternan de manera equitativa.
- **Qué ocurre internamente:** El Gateway Nginx envía la solicitud a `http://reserva-service:8000`. El balanceador de carga interno de Kubernetes (`kube-proxy`) intercepta el tráfico y lo redirige en Round-Robin entre las réplicas activas.
- **Qué significa la respuesta:** Prueba que la pérdida de una réplica individual no tumba el sistema, ya que el tráfico se redirigirá al pod restante de forma transparente.

### Prueba B: Protección ante Sobrecarga (Rate Limiting)
Demuestra cómo el Gateway bloquea ataques o picos de tráfico antes de que saturen los servidores.
- **Comando (en PC 1):**
  ```bash
  python tests/test_sobrecarga.py --auto
  ```
- **Qué muestra la pantalla:**
  - 7 peticiones retornan instantáneamente con código **`429`** (BLOQUEADO).
  - 3 peticiones consiguen pasar al backend pero devuelven **`503`** tras unos segundos de reintentos (porque la PC 2 está apagada).
- **Qué ocurre internamente:** Nginx tiene una zona de memoria que rastrea las IPs clientes. Si superan el límite de 5 req/s, responde de inmediato con HTTP 429 sin enviar la petición al microservicio Core.
- **Qué significa la respuesta:** Evita que el servidor colapse por denegación de servicio (DoS) o sobrecarga accidental.

### Prueba C: Contraste de Reintentos (Inventario Fantasma con PC 2 Caída)
Demuestra la diferencia entre tener resiliencia (reintentos con retraso) y no tenerla.
- **Comando (en PC 1):**
  ```bash
  python tests/test_inventario_fantasma.py --auto
  ```
- **Qué muestra la pantalla:**
  - **Paso 1 (Con Tolerancia):** Demora aproximadamente 3.5 segundos en responder y devuelve un error **`503`** detallado.
  - **Paso 2 (Sin Tolerancia):** Falla instantáneamente (0.01 segundos) con un error de conexión genérico.
- **Qué ocurre internamente:** 
  - Con tolerancia activa, el Core intenta conectarse al puerto 32001 de la PC 2. Al fallar, espera 0.5s, luego 1.0s y finalmente 2.0s antes de darse por vencido.
  - Sin tolerancia, el Core hace una sola llamada directa y ante el fallo aborta la ejecución de inmediato.
- **Cómo se muestra la corrección:** Si la PC 2 se encendiera durante el intervalo de los reintentos (3.5s), la transacción del Paso 1 habría finalizado con éxito (HTTP 200) sin que el usuario final notara la caída temporal.

---

## 3. Pruebas con Ambas PCs Activas (PC 1 + PC 2 Conectadas)

Una vez que la PC 2 esté encendida y sus puertos expuestos (`32001`, `32002` y `32003`), ejecute estas pruebas para demostrar la tolerancia a fallos completa:

### Prueba D: Latencia y Circuit Breaker (La Pasarela Lenta)
Muestra cómo el sistema se defiende de servicios extremadamente lentos (cuellos de botella) y cómo mantiene la consistencia de base de datos.
- **Comando (en PC 1):**
  ```bash
  python tests/test_pasarela_lenta.py --auto
  ```
- **Qué muestra la pantalla:**
  - **Petición 1 y 2:** Demoran exactamente 3 segundos y retornan un error **`503`**. El asiento 2 se reporta como **`DISPONIBLE`**.
  - **Petición 3:** Falla de inmediato (milisegundos) indicando que el Circuit Breaker está **`OPEN`**.
  - **Petición 4:** Tras esperar 10 segundos, la compra se realiza con éxito (**`HTTP 200`**).
  - **Petición 5 (Sin resiliencia):** Se cuelga por 15 segundos y al fallar, el asiento 3 queda bloqueado como **`RESERVADO`** de forma permanente.
- **Qué ocurre internamente:**
  - **Con Tolerancia:** El Core corta la llamada a Pagos a los 3s (timeout). Como falló, se ejecuta la compensación SAGA que libera el asiento en el Inventario (evita inconsistencia). Tras 2 fallos consecutivos, el Circuit Breaker se abre para no saturar el servidor de pagos. Tras 10s, se prueba una llamada (Half-Open) y al tener éxito, el circuito se cierra.
  - **Sin Tolerancia:** No hay timeout (la conexión queda colgada 15s). Al fallar el pago, no se ejecuta la lógica de liberación del asiento, por lo que el asiento queda "huérfano" en estado RESERVADO y nadie más lo puede comprar (inconsistencia).

### Prueba E: Degradación Elegante (El Correo Perdido)
Demuestra que fallas en servicios secundarios no impiden que el cliente compre su entrada.
- **Preparación:** En la **PC 2**, cierre la terminal del port-forward de notificaciones (puerto 32003) para simular la caída del servicio de correos.
- **Comando (en PC 1):**
  ```bash
  python tests/test_correo_perdido.py --auto
  ```
- **Qué muestra la pantalla:** La reserva y el pago finalizan con éxito (**`HTTP 200`**). La base de datos muestra la reserva como **`CONFIRMADA`**, a pesar de que el envío del correo de notificación falló.
- **Qué ocurre internamente:** El Core intenta enviar la notificación al servicio de correos. Al detectar la caída, captura la excepción de red, registra el fallo en los logs y devuelve una respuesta exitosa al cliente.
- **Qué significa la respuesta:** El negocio sigue operando y facturando aunque los servicios de soporte no esenciales estén caídos.

### Prueba F: Condición de Carrera (Doble Reserva Concurrentes)
Demuestra la consistencia transaccional cuando dos personas intentan comprar el mismo asiento al mismo milisegundo.
- **Comando (en PC 1):**
  ```bash
  python tests/test_condicion_carrera.py --auto
  ```
- **Qué muestra la pantalla:**
  - Un cliente obtiene éxito (**`HTTP 200`** - Reserva Confirmada).
  - El otro cliente obtiene conflicto (**`HTTP 409`** - Asiento ya vendido o reservado).
- **Qué ocurre internamente:** La base de datos ejecuta una consulta atómica de actualización (`UPDATE ... WHERE estado = 'DISPONIBLE'`). El primer hilo de ejecución bloquea la fila y cambia el estado. Cuando el segundo hilo intenta hacer el update, la condición `WHERE` ya no se cumple, retornando 0 filas afectadas y abortando la compra del segundo cliente con seguridad.
- **Qué significa la respuesta:** Evita el problema de la sobreventa (vender una entrada a dos personas distintas).

### Prueba G: Base de Datos Intermitente (Flapping de Postgres)
Demuestra la robustez y capacidad de recuperación del sistema completo ante pérdidas y restauraciones intermitentes de la base de datos centralizada.
- **Comando (en PC 1):**
  ```bash
  python tests/test_base_datos_intermitente.py --auto
  ```
- **Qué muestra la pantalla:**
  - Escritura con BD activa: Éxito (HTTP 200/201).
  - Escritura durante la caída (ciclo): Fallo observable (HTTP 500/503/502).
  - Escritura tras la recuperación (ciclo): Éxito de nuevo (HTTP 200/201), validando la restauración automática del sistema.
- **Qué ocurre internamente:** El script interactúa directamente con la API de Kubernetes en el nodo Master (PC 1) reduciendo las réplicas del deployment de PostgreSQL a 0 (simulando una falla de hardware o pérdida total de disco). Los microservicios quedan desconectados de su persistencia. Luego, el script restaura el pod de Postgres a 1 réplica y espera a que el servicio esté completamente listo antes de enviar tráfico exitosamente de nuevo.

