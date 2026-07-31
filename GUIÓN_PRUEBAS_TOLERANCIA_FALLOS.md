# Guion de presentación de pruebas de tolerancia a fallos

## 1. Introducción

En esta demostración se ejecutarán seis pruebas automatizadas sobre una arquitectura de microservicios desplegada en Kubernetes.

Los componentes principales del proyecto son:

- API Gateway con Nginx.
- Servicio de Reservas.
- Servicio de Inventario.
- Servicio de Pagos.
- Servicio de Notificaciones.
- PostgreSQL.
- Kubernetes y Minikube.

Todas las solicitudes de prueba ingresan por el API Gateway y luego son dirigidas al microservicio correspondiente.

Los seis escenarios que se presentarán son:

1. Inventario Fantasma.
2. Pasarela Lenta.
3. Diluvio de Peticiones.
4. Base de Datos Intermitente.
5. Correo Perdido.
6. Condición de Carrera.

Además, el proyecto contiene una prueba adicional de balanceo de carga:

```text
test_balanceo.py
```

---

# 2. Preparación general

## 2.1 Abrir PowerShell en la carpeta del proyecto

```powershell
cd "C:\Users\Cyborg 15\practica-tolerancia-fallos"
```

### ¿Qué hace el comando?

`cd` significa `Change Directory`.

Este comando cambia la carpeta de trabajo actual de PowerShell hacia la raíz del proyecto.

Internamente, PowerShell actualiza la ruta desde la que se buscarán:

- los scripts de Python;
- los manifiestos de Kubernetes;
- los archivos de configuración;
- las rutas relativas como `.\tests\`.

---

## 2.2 Configurar la dirección del API Gateway

```powershell
$env:GATEWAY_URL="http://10.131.1.128:8080"
```

### ¿Qué hace el comando?

Crea una variable de entorno llamada:

```text
GATEWAY_URL
```

Los scripts de Python pueden leer esta variable mediante:

```python
os.getenv("GATEWAY_URL")
```

Esto permite cambiar la dirección del Gateway sin modificar directamente el código fuente.

### Explicación para la presentación

> Todos los scripts envían sus solicitudes al API Gateway. El Gateway funciona como punto de entrada del sistema y redirige cada petición al microservicio correspondiente.

---

## 2.3 Verificar el contexto de Kubernetes

```powershell
kubectl config current-context
```

### ¿Qué hace el comando?

Muestra el contexto de Kubernetes que se encuentra activo.

Internamente, `kubectl` consulta el archivo:

```text
C:\Users\TU_USUARIO\.kube\config
```

El contexto contiene:

- el clúster activo;
- las credenciales;
- el namespace predeterminado.

### Resultado esperado

```text
minikube
```

### Explicación para la presentación

> Primero verifico que kubectl esté conectado al clúster correcto. Esto evita ejecutar las pruebas accidentalmente en otro entorno.

---

## 2.4 Verificar los pods del sistema

```powershell
kubectl get pods
```

### ¿Qué hace el comando?

Consulta la API de Kubernetes y solicita la lista de pods del namespace actual.

Internamente ocurre lo siguiente:

```text
kubectl
   ↓
Kubernetes API Server
   ↓
Consulta objetos Pod
   ↓
Devuelve nombre, estado, reinicios y antigüedad
```

### Resultado esperado

Los servicios deberían aparecer en estado:

```text
Running
```

Ejemplo:

```text
api-gateway
reserva-service
inventario-service
pagos-service
notificaciones-service
postgres
```

### Explicación para la presentación

> Antes de provocar los fallos, verifico que todos los componentes estén funcionando. De esta forma puedo demostrar que los errores posteriores fueron causados por las pruebas y no por un problema previo.

---

## 2.5 Verificar los deployments

```powershell
kubectl get deployments
```

### ¿Qué hace el comando?

Muestra los Deployments administrados por Kubernetes.

Un Deployment define:

- la imagen del contenedor;
- la cantidad de réplicas;
- las variables de entorno;
- la estrategia de actualización;
- las etiquetas de los pods.

### Explicación para la presentación

> Este comando permite comprobar cuántas réplicas debe mantener Kubernetes para cada servicio.

---

## 2.6 Verificar los servicios de red

```powershell
kubectl get services
```

### ¿Qué hace el comando?

Muestra los objetos `Service` de Kubernetes.

Los Services proporcionan:

- una dirección estable;
- descubrimiento de servicios;
- distribución del tráfico entre pods;
- acceso interno o externo.

### Explicación para la presentación

> Los nombres de los pods cambian, pero los Services mantienen una dirección estable para que los microservicios puedan comunicarse.

---

# 3. Escenario 1: Inventario Fantasma

## 3.1 Objetivo

Demostrar qué ocurre cuando el Servicio de Inventario deja de estar disponible mientras el Servicio de Reservas necesita comprobar la disponibilidad de un asiento.

La prueba compara dos comportamientos:

- tolerancia activa;
- tolerancia desactivada.

---

## 3.2 Observar los pods del inventario

Abrir una nueva ventana de PowerShell y ejecutar:

```powershell
kubectl get pods -l app=inventario-service -w
```

### ¿Qué hace el comando?

La opción:

```text
-l app=inventario-service
```

filtra los pods que tengan la etiqueta:

```yaml
app: inventario-service
```

La opción:

```text
-w
```

significa `watch`.

Mantiene el comando abierto y muestra los cambios de estado en tiempo real.

### Qué ocurre internamente

`kubectl` abre una conexión de observación con la API de Kubernetes y recibe eventos cuando el estado de los pods cambia.

### Resultado esperado al apagar Inventario

```text
inventario-service-xxxxx   1/1   Terminating
```

---

## 3.3 Observar los logs del Servicio de Reservas

En otra ventana:

```powershell
kubectl logs -f -l app=reserva-service --tail=30
```

### ¿Qué hace el comando?

- `logs`: consulta la salida de los contenedores.
- `-f`: sigue los logs en tiempo real.
- `-l app=reserva-service`: selecciona los pods por etiqueta.
- `--tail=30`: muestra inicialmente las últimas 30 líneas.

### Explicación para la presentación

> Observo el Servicio de Reservas porque este servicio intenta comunicarse con Inventario. Aquí se podrán ver los reintentos, timeouts o errores de comunicación.

---

## 3.4 Apagar el Servicio de Inventario

```powershell
kubectl scale deployment inventario-service --replicas=0
```

### ¿Qué hace el comando?

Modifica el Deployment para que el número deseado de réplicas sea cero.

Internamente cambia:

```yaml
spec:
  replicas: 0
```

### Flujo interno

```text
kubectl envía la actualización
        ↓
Kubernetes API Server modifica el Deployment
        ↓
Deployment Controller actualiza el ReplicaSet
        ↓
ReplicaSet establece cero pods
        ↓
Kubernetes termina los pods de Inventario
```

### Importante

Este comando no elimina el Deployment.

Tampoco elimina su configuración.

Solo indica que temporalmente no debe existir ningún pod del Servicio de Inventario.

---

## 3.5 Ejecutar el script

```powershell
python .\tests\test_inventario_fantasma.py
```

### ¿Qué hace el comando?

El comando `python` inicia el intérprete de Python y ejecuta el archivo indicado.

El script se comporta como un cliente de prueba que envía solicitudes HTTP al API Gateway.

---

## 3.6 ¿Qué hace internamente el script?

El script realiza dos solicitudes de reserva.

### Solicitud con tolerancia activa

Envía una petición similar a:

```http
POST /reservations?tolerancia_activa=true
```

Flujo:

```text
Script
   ↓
API Gateway
   ↓
Servicio de Reservas
   ↓
Intenta consultar Inventario
   ↓
Inventario no responde
   ↓
Se aplica la estrategia de tolerancia
```

Dependiendo de la implementación, la estrategia puede incluir:

- reintentos;
- timeout;
- respuesta controlada;
- manejo de excepción;
- mensaje de servicio no disponible.

### Solicitud con tolerancia desactivada

Envía una petición similar a:

```http
POST /reservations?tolerancia_activa=false
```

En este caso, el fallo del Servicio de Inventario se transmite directamente al proceso de reserva.

### Explicación para la presentación

> El script compara la misma operación con la tolerancia activada y desactivada. Esto permite demostrar que el comportamiento diferente depende de la estrategia implementada en el backend.

---

## 3.7 Restaurar Inventario

```powershell
kubectl scale deployment inventario-service --replicas=2
```

Usar `1` o `2` según la cantidad normal de réplicas del proyecto.

Después:

```powershell
kubectl rollout status deployment/inventario-service
```

### ¿Qué hace `rollout status`?

Espera hasta que Kubernetes confirme que el Deployment alcanzó el número esperado de pods disponibles.

### Cierre del escenario

> El Servicio de Inventario fue retirado temporalmente. El Servicio de Reservas detectó la indisponibilidad y actuó según la configuración de tolerancia. Finalmente, Kubernetes restauró el servicio.

---

# 4. Escenario 2: Pasarela Lenta

## 4.1 Objetivo

Demostrar el comportamiento del sistema cuando el Servicio de Pagos demora demasiado.

La prueba busca evidenciar:

- timeout;
- circuit breaker;
- compensación SAGA;
- recuperación posterior.

---

## 4.2 Observar los logs del Servicio de Reservas

```powershell
kubectl logs -f -l app=reserva-service --tail=50
```

---

## 4.3 Observar los logs del Servicio de Pagos

```powershell
kubectl logs -f -l app=pagos-service --tail=50
```

### Explicación para la presentación

> Observo ambos servicios porque Pagos genera la demora y Reservas debe decidir cómo manejarla.

---

## 4.4 Ejecutar el script

```powershell
python .\tests\test_pasarela_lenta.py
```

---

## 4.5 ¿Qué hace internamente el script?

El script envía una reserva indicando que el pago debe demorarse artificialmente.

Ejemplo:

```text
simular_demora_pago=20
```

### Flujo interno

```text
Script
   ↓
API Gateway
   ↓
Servicio de Reservas
   ↓
Servicio de Pagos
   ↓
Pagos espera 20 segundos
   ↓
Se supera el timeout
```

---

## 4.6 Timeout

El Servicio de Reservas espera la respuesta del Servicio de Pagos.

Si se supera el tiempo configurado:

- la llamada falla;
- se registra un timeout;
- la reserva no debe quedar confirmada;
- puede iniciarse una compensación.

### Explicación para la presentación

> El timeout evita que el Servicio de Reservas espere indefinidamente por una respuesta del Servicio de Pagos.

---

## 4.7 Compensación SAGA

Una reserva puede involucrar varios pasos:

```text
1. Verificar asiento
2. Bloquear o descontar inventario
3. Crear reserva provisional
4. Procesar pago
5. Confirmar reserva
```

Si el pago falla después de haber modificado el inventario, la SAGA ejecuta operaciones compensatorias:

```text
Pago falla
   ↓
Cancelar reserva provisional
   ↓
Liberar asiento
   ↓
Restaurar el estado anterior
```

### Explicación para la presentación

> La SAGA no ejecuta un rollback global entre todas las bases de datos. En su lugar, cada microservicio ejecuta una operación compensatoria para devolver el sistema a un estado coherente.

---

## 4.8 Circuit Breaker

El circuit breaker puede pasar por estos estados:

```text
CLOSED
   ↓ varios fallos
OPEN
   ↓ tiempo de espera
HALF-OPEN
   ↓ prueba exitosa
CLOSED
```

### Estado CLOSED

Las solicitudes pasan normalmente hacia Pagos.

### Estado OPEN

Las llamadas se rechazan rápidamente sin contactar al Servicio de Pagos.

### Estado HALF-OPEN

Se permite una solicitud de prueba.

Si funciona, el circuito vuelve a `CLOSED`.

### Explicación para la presentación

> El circuit breaker evita seguir esperando a un servicio que ya se sabe que está lento o fallando. Esto protege los recursos del sistema y evita la acumulación de solicitudes.

---

## 4.9 Qué observar en los logs

Buscar mensajes similares a:

```text
timeout
circuit breaker
circuit open
compensación
rollback
liberar asiento
```

El texto exacto depende de la implementación del proyecto.

---

## 4.10 Cierre del escenario

> La prueba demostró que una respuesta lenta de Pagos no debe bloquear indefinidamente el sistema. Los timeouts limitan la espera, el circuit breaker evita llamadas repetidas y la SAGA compensa los cambios parciales.

---

# 5. Escenario 3: Diluvio de Peticiones

## 5.1 Objetivo

Enviar varias solicitudes simultáneas y comprobar que el API Gateway controla la cantidad de tráfico recibido.

---

## 5.2 Revisar la configuración de Nginx

```powershell
kubectl get configmap nginx-config -o yaml
```

### ¿Qué hace el comando?

Consulta el ConfigMap llamado `nginx-config` y muestra su contenido en formato YAML.

Buscar líneas similares a:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req zone=api_limit burst=50 nodelay;
```

---

## 5.3 Significado de la configuración

### `rate=10r/s`

Permite aproximadamente diez solicitudes por segundo por dirección IP.

### `burst=50`

Permite una ráfaga adicional de hasta cincuenta solicitudes.

### `nodelay`

Las solicitudes permitidas dentro de la ráfaga se procesan inmediatamente.

### Advertencia

Con esta configuración, diez solicitudes simultáneas pueden no producir errores `429`.

Para una demostración visible puede utilizarse temporalmente:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=2r/s;
limit_req zone=api_limit burst=3 nodelay;
```

---

## 5.4 Reiniciar el API Gateway

Después de cambiar la configuración:

```powershell
kubectl rollout restart deployment/api-gateway
```

### ¿Qué hace internamente?

Kubernetes modifica una anotación de la plantilla del Deployment.

Esto provoca:

```text
Deployment actualizado
        ↓
ReplicaSet nuevo
        ↓
Pods nuevos
        ↓
Nginx carga la configuración actualizada
```

Después:

```powershell
kubectl rollout status deployment/api-gateway
```

---

## 5.5 Observar los logs del API Gateway

```powershell
kubectl logs -f -l app=api-gateway --tail=50
```

### Explicación para la presentación

> Observo el API Gateway porque Nginx es el componente encargado de aplicar el rate limiting.

---

## 5.6 Ejecutar el script

```powershell
python .\tests\test_sobrecarga.py
```

---

## 5.7 ¿Qué hace internamente el script?

El script utiliza concurrencia para enviar varias solicitudes casi al mismo tiempo.

Conceptualmente:

```text
Hilo 1  ── solicitud
Hilo 2  ── solicitud
Hilo 3  ── solicitud
...
Hilo 10 ── solicitud
```

Todas las solicitudes llegan al API Gateway desde la misma dirección IP.

---

## 5.8 Funcionamiento interno de Nginx

```text
Solicitudes entrantes
        ↓
Nginx identifica la IP del cliente
        ↓
Consulta la zona api_limit
        ↓
Calcula la tasa de solicitudes
        ↓
Acepta o rechaza
```

Las solicitudes aceptadas continúan al backend.

Las rechazadas pueden recibir:

```text
HTTP 429 Too Many Requests
```

---

## 5.9 Diferencia entre 429 y 409

### HTTP 429

Significa que el Gateway rechazó la solicitud por exceso de tráfico.

### HTTP 409

Significa que ocurrió un conflicto de negocio, por ejemplo:

```text
El asiento ya no está disponible
```

### Explicación para la presentación

> Para demostrar sobrecarga, la evidencia principal debe ser el código HTTP 429 o los mensajes de limitación en los logs de Nginx. Un 409 pertenece a la lógica de reservas y no al rate limiting.

---

## 5.10 Cierre del escenario

> El script genera varias solicitudes concurrentes. El API Gateway controla el tráfico y rechaza las solicitudes que superan la tasa permitida, evitando que los microservicios internos se saturen.

---

# 6. Escenario 4: Base de Datos Intermitente

## 6.1 Objetivo

Apagar temporalmente PostgreSQL durante una operación de escritura, comprobar el error y posteriormente restaurar la base de datos.

---

## 6.2 Observar PostgreSQL

```powershell
kubectl get pods -l app=postgres -w
```

### ¿Qué hace el comando?

Filtra los pods con la etiqueta `app=postgres` y observa sus cambios en tiempo real.

Durante la prueba se puede observar:

```text
Running
Terminating
ContainerCreating
Running
```

---

## 6.3 Observar los logs de Reservas

```powershell
kubectl logs -f -l app=reserva-service --tail=50
```

### Explicación para la presentación

> El Servicio de Reservas intenta escribir en PostgreSQL. Por eso sus logs permiten observar los errores de conectividad durante la caída.

---

## 6.4 Configurar el script

```powershell
$env:SEAT_IDS="2,3,5,6"
$env:DB_FLAP_CYCLES="1"
$env:DB_DOWN_SECONDS="6"
$env:DB_UP_TIMEOUT="90"
```

### Significado de las variables

- `SEAT_IDS`: asientos utilizados en las escrituras.
- `DB_FLAP_CYCLES`: cantidad de ciclos de caída y recuperación.
- `DB_DOWN_SECONDS`: tiempo que PostgreSQL permanece apagado.
- `DB_UP_TIMEOUT`: tiempo máximo para esperar su recuperación.

---

## 6.5 Ejecutar el script

```powershell
python .\tests\test_base_datos_intermitente.py
```

---

## 6.6 ¿Qué hace internamente el script?

### Fase 1: escritura inicial

El script crea una reserva con PostgreSQL activo.

```text
Script
   ↓
API Gateway
   ↓
Servicio de Reservas
   ↓
PostgreSQL
```

Resultado esperado:

```text
HTTP 200 o HTTP 201
```

---

### Fase 2: apagar PostgreSQL

El script ejecuta internamente:

```powershell
kubectl scale deployment/postgres --replicas=0
```

Internamente se modifica:

```yaml
spec:
  replicas: 0
```

Kubernetes termina el pod de PostgreSQL.

PostgreSQL realiza un cierre controlado:

```text
received fast shutdown request
aborting any active transactions
checkpoint starting
checkpoint complete
database system is shut down
```

### Explicación para la presentación

> La base no se elimina. Únicamente se apaga el pod. El volumen persistente conserva los datos.

---

### Fase 3: escritura durante la caída

El script envía una nueva reserva.

El Service de PostgreSQL existe, pero no tiene endpoints disponibles porque no existe ningún pod.

Posibles resultados:

```text
500
502
503
504
timeout
connection refused
```

### Explicación para la presentación

> La operación falla porque el Servicio de Reservas no puede establecer una conexión con PostgreSQL. La reserva no debe confirmarse si no pudo persistirse.

---

### Fase 4: restaurar PostgreSQL

El script ejecuta:

```powershell
kubectl scale deployment/postgres --replicas=1
```

Después espera:

```powershell
kubectl rollout status deployment/postgres --timeout=90s
```

Kubernetes:

```text
Crea un nuevo pod
        ↓
Monta el volumen persistente
        ↓
Inicia PostgreSQL
        ↓
La base vuelve a aceptar conexiones
```

---

### Fase 5: escritura posterior

El script envía una nueva reserva.

Resultado esperado:

```text
HTTP 200 o HTTP 201
```

### Explicación para la presentación

> Esta operación confirma que la aplicación recuperó la conectividad sin reiniciar manualmente todos los microservicios.

---

### Fase 6: bloque de seguridad

El script incluye un bloque `finally`.

Este bloque intenta restaurar PostgreSQL aunque:

- ocurra un error;
- se cancele el script;
- una solicitud falle;
- el usuario presione `Ctrl+C`.

### Explicación para la presentación

> El script incorpora un mecanismo de seguridad para no dejar la base de datos apagada al finalizar la prueba.

---

## 6.7 Aclaración técnica

Esta prueba no demuestra alta disponibilidad de PostgreSQL.

Con un solo pod, cuando la réplica se reduce a cero, toda la base queda fuera de servicio.

Lo que sí demuestra es:

- pérdida temporal de conectividad;
- fallo controlado de escritura;
- recuperación posterior.

---

## 6.8 Cierre del escenario

> La prueba demostró que la aplicación detecta la indisponibilidad temporal de PostgreSQL y vuelve a procesar escrituras cuando la base se recupera.

---

# 7. Escenario 5: Correo Perdido

## 7.1 Objetivo

Demostrar que una falla en el Servicio de Notificaciones no debe cancelar una reserva que ya fue confirmada correctamente.

---

## 7.2 Observar Notificaciones

```powershell
kubectl logs -f -l app=notificaciones-service --tail=50
```

---

## 7.3 Observar Reservas

```powershell
kubectl logs -f -l app=reserva-service --tail=50
```

### Explicación para la presentación

> Observo ambos servicios porque Reservas ejecuta la operación principal y Notificaciones representa una operación secundaria.

---

## 7.4 Ejecutar el script

```powershell
python .\tests\test_correo_perdido.py
```

---

## 7.5 ¿Qué hace internamente el script?

### Fase 1: crear una reserva

Envía:

```http
POST /reservations
```

Flujo:

```text
Script
   ↓
API Gateway
   ↓
Servicio de Reservas
   ↓
Inventario
   ↓
Pagos
   ↓
PostgreSQL
```

---

### Fase 2: confirmar la reserva

La reserva pasa al estado:

```text
CONFIRMADA
```

---

### Fase 3: simular el fallo de notificación

El script realiza una llamada al Servicio de Notificaciones usando un parámetro similar a:

```text
simular_fallo=true
```

El servicio genera intencionalmente un error en lugar de enviar el correo.

---

### Fase 4: verificar el estado de la reserva

El script vuelve a consultar la reserva.

El estado debe continuar siendo:

```text
CONFIRMADA
```

### Explicación para la presentación

> El correo es una operación secundaria. Si el envío falla, no debe revertirse una reserva que ya fue pagada y guardada correctamente.

---

## 7.6 Patrón demostrado

Este escenario demuestra degradación controlada:

```text
Proceso principal funciona
        ↓
Servicio secundario falla
        ↓
Se registra el error
        ↓
La reserva permanece válida
```

---

## 7.7 Aclaración técnica

El script normalmente no apaga físicamente el pod de Notificaciones.

El fallo se genera mediante un parámetro de simulación controlado.

### Explicación para la presentación

> El modo de simulación permite repetir el fallo sin modificar manualmente la infraestructura.

---

## 7.8 Cierre del escenario

> La falla del correo no afecta la operación principal. La reserva permanece confirmada y el sistema puede registrar el problema de notificación para un reintento posterior.

---

# 8. Escenario 6: Condición de Carrera

## 8.1 Objetivo

Enviar dos reservas simultáneas para el mismo asiento y verificar que solamente una tenga éxito.

---

## 8.2 Observar Reservas

```powershell
kubectl logs -f -l app=reserva-service --tail=50
```

---

## 8.3 Observar Inventario

```powershell
kubectl logs -f -l app=inventario-service --tail=50
```

### Explicación para la presentación

> Reservas procesa las solicitudes e Inventario controla el estado del asiento. Los logs permiten observar cuál solicitud fue aceptada y cuál fue rechazada.

---

## 8.4 Consultar previamente los asientos

```powershell
Invoke-RestMethod -Uri "$env:GATEWAY_URL/inventory/seats"
```

### ¿Qué hace el comando?

`Invoke-RestMethod` envía una solicitud HTTP desde PowerShell.

La respuesta JSON se convierte automáticamente en un objeto de PowerShell.

### Resultado esperado

El asiento utilizado por la prueba debe estar:

```text
DISPONIBLE
```

---

## 8.5 Ejecutar el script

```powershell
python .\tests\test_condicion_carrera.py
```

---

## 8.6 ¿Qué hace internamente el script?

El script crea dos tareas o hilos que envían solicitudes casi al mismo tiempo.

```text
Cliente A → reservar asiento 3
Cliente B → reservar asiento 3
```

Ambas solicitudes llegan al sistema de forma concurrente:

```text
Solicitud A ─┐
             ├─→ API Gateway → Reservas → Inventario/BD
Solicitud B ─┘
```

---

## 8.7 Problema que se busca evitar

Sin control de concurrencia podría ocurrir:

```text
A consulta: disponible
B consulta: disponible
A reserva
B reserva
```

Esto produciría una doble venta.

---

## 8.8 Resultado correcto

```text
Solicitud A → éxito
Solicitud B → conflicto
```

o al contrario.

Posibles códigos:

```text
200 o 201 → reserva creada
409        → asiento ya no disponible
```

### Explicación para la presentación

> No importa cuál cliente gane. Lo importante es que solo una solicitud pueda reservar el asiento y que la segunda reciba un rechazo controlado.

---

## 8.9 Mecanismos internos posibles

El sistema puede evitar la doble reserva mediante:

- transacciones;
- bloqueo de fila;
- restricción única;
- actualización atómica;
- control de concurrencia optimista;
- verificación y actualización en una única operación.

---

## 8.10 Verificar el estado final

```powershell
Invoke-RestMethod -Uri "$env:GATEWAY_URL/inventory/seats"
```

También se pueden consultar las reservas:

```powershell
Invoke-RestMethod -Uri "$env:GATEWAY_URL/reservations"
```

### Evidencia esperada

Debe existir una sola reserva para el asiento utilizado.

---

## 8.11 Cierre del escenario

> La prueba demostró que el sistema evita la doble reserva cuando dos clientes intentan adquirir el mismo asiento simultáneamente.

---

# 9. Prueba adicional: Balanceo de carga

## 9.1 Objetivo

Comprobar que el API Gateway distribuye solicitudes entre varias réplicas del Servicio de Reservas.

---

## 9.2 Verificar réplicas

```powershell
kubectl get pods -l app=reserva-service -o wide
```

### ¿Qué hace el comando?

Muestra los pods del Servicio de Reservas e incluye información adicional:

- IP del pod;
- nodo;
- estado;
- nombre completo.

---

## 9.3 Ejecutar el script

```powershell
python .\tests\test_balanceo.py
```

---

## 9.4 ¿Qué hace internamente el script?

El script envía varias solicitudes al endpoint:

```http
GET /server
```

El endpoint responde con datos como:

- hostname;
- nombre del pod;
- IP interna.

El script almacena las respuestas y verifica si contestaron varios pods diferentes.

### Flujo

```text
Solicitud 1 → Gateway → Pod A
Solicitud 2 → Gateway → Pod B
Solicitud 3 → Gateway → Pod A
Solicitud 4 → Gateway → Pod B
```

### Explicación para la presentación

> La prueba demuestra balanceo entre réplicas dentro del mismo clúster de Kubernetes. No demuestra por sí sola balanceo entre dos computadoras físicas.

---

# 10. Orden recomendado de presentación

Se recomienda presentar los escenarios en este orden:

1. Condición de Carrera.
2. Correo Perdido.
3. Inventario Fantasma.
4. Pasarela Lenta.
5. Diluvio de Peticiones.
6. Base de Datos Intermitente.
7. Balanceo de carga como prueba adicional.

### Razón del orden

Los primeros escenarios no requieren apagar infraestructura.

Los escenarios más invasivos se dejan para el final.

---

# 11. Resumen de comandos

## Estado general

```powershell
kubectl config current-context
kubectl get pods
kubectl get deployments
kubectl get services
```

---

## Inventario Fantasma

```powershell
kubectl get pods -l app=inventario-service -w
kubectl logs -f -l app=reserva-service --tail=30
kubectl scale deployment inventario-service --replicas=0
python .\tests\test_inventario_fantasma.py
kubectl scale deployment inventario-service --replicas=2
kubectl rollout status deployment/inventario-service
```

---

## Pasarela Lenta

```powershell
kubectl logs -f -l app=pagos-service --tail=50
kubectl logs -f -l app=reserva-service --tail=50
python .\tests\test_pasarela_lenta.py
```

---

## Diluvio de Peticiones

```powershell
kubectl get configmap nginx-config -o yaml
kubectl logs -f -l app=api-gateway --tail=50
python .\tests\test_sobrecarga.py
```

---

## Base de Datos Intermitente

```powershell
kubectl get pods -l app=postgres -w
kubectl logs -f -l app=reserva-service --tail=50

$env:SEAT_IDS="2,3,5,6"
$env:DB_FLAP_CYCLES="1"
$env:DB_DOWN_SECONDS="6"
$env:DB_UP_TIMEOUT="90"

python .\tests\test_base_datos_intermitente.py
```

---

## Correo Perdido

```powershell
kubectl logs -f -l app=notificaciones-service --tail=50
kubectl logs -f -l app=reserva-service --tail=50
python .\tests\test_correo_perdido.py
```

---

## Condición de Carrera

```powershell
kubectl logs -f -l app=reserva-service --tail=50
kubectl logs -f -l app=inventario-service --tail=50
python .\tests\test_condicion_carrera.py
```

---

## Balanceo de carga

```powershell
kubectl get pods -l app=reserva-service -o wide
python .\tests\test_balanceo.py
```

---

# 12. Evidencias recomendadas

## Evidencia 1: estado inicial

```powershell
kubectl get pods
```

Todos los componentes deben aparecer en estado `Running`.

---

## Evidencia 2: Inventario apagado

```powershell
kubectl get pods -l app=inventario-service
```

Debe observarse que no existen pods disponibles.

---

## Evidencia 3: timeout de Pagos

Capturar:

- salida del script;
- logs de Reservas;
- logs de Pagos.

---

## Evidencia 4: rate limiting

Capturar:

```text
HTTP 429 Too Many Requests
```

o los mensajes de limitación en los logs del API Gateway.

---

## Evidencia 5: PostgreSQL apagado

Capturar:

```text
Terminating
```

o la ausencia del pod de PostgreSQL.

---

## Evidencia 6: recuperación de PostgreSQL

Capturar:

```text
database system is ready to accept connections
```

y una escritura exitosa posterior.

---

## Evidencia 7: correo fallido

Capturar:

- error en Notificaciones;
- reserva en estado `CONFIRMADA`.

---

## Evidencia 8: condición de carrera

Capturar:

- una solicitud exitosa;
- una solicitud rechazada;
- una sola reserva final.

---

# 13. Guion breve de introducción

> En esta demostración voy a ejecutar seis pruebas automatizadas sobre una arquitectura de microservicios desplegada en Kubernetes. Todas las solicitudes ingresan por el API Gateway y atraviesan los servicios de Reservas, Inventario, Pagos, Notificaciones y PostgreSQL. Los scripts simulan fallos de infraestructura, lentitud, sobrecarga, pérdida de servicios y concurrencia. El objetivo no es solamente provocar errores, sino comprobar que el sistema responde de forma controlada, evita inconsistencias y recupera su funcionamiento.

---

# 14. Guion breve de cierre

> Las pruebas demostraron distintos mecanismos de resiliencia. La condición de carrera evitó la doble reserva; el fallo de notificación no anuló la operación principal; la caída de Inventario permitió comparar el comportamiento con y sin tolerancia; la lentitud de Pagos activó timeouts, compensación y circuit breaker; la sobrecarga fue controlada en el API Gateway; y la caída temporal de PostgreSQL permitió comprobar la recuperación de las operaciones de escritura. En conjunto, los scripts validan el comportamiento del sistema frente a fallos parciales y temporales.

---

# 15. Conclusión técnica

Los seis scripts permiten evaluar diferentes dimensiones de tolerancia a fallos:

| Script | Fallo simulado | Mecanismo observado |
|---|---|---|
| `test_inventario_fantasma.py` | Inventario no disponible | Reintentos, timeout y manejo controlado |
| `test_pasarela_lenta.py` | Pagos demasiado lento | Timeout, circuit breaker y SAGA |
| `test_sobrecarga.py` | Exceso de solicitudes | Rate limiting |
| `test_base_datos_intermitente.py` | PostgreSQL temporalmente apagado | Detección del fallo y recuperación |
| `test_correo_perdido.py` | Fallo de notificación | Degradación controlada |
| `test_condicion_carrera.py` | Reservas simultáneas | Control de concurrencia |
| `test_balanceo.py` | Solicitudes repetidas | Balanceo entre pods |

Estas pruebas no solo generan errores, sino que verifican que el sistema mantenga la consistencia, limite el impacto de los fallos y recupere su funcionamiento.
