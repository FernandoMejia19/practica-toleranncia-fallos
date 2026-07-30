# Diagrama de Arquitectura y Distribución en Kubernetes

Este documento contiene la descripción y el diagrama de distribución de los 6 componentes de la aplicación entre los dos nodos del clúster de Kubernetes, cumpliendo con la directriz de tolerancia a fallos multi-nodo (con distribución de réplicas críticas usando anti-afinidad de pods).

---

## 1. Diagrama de Arquitectura Visual

A continuación se presenta el diagrama de arquitectura generado que detalla la topología de red, el flujo de llamadas de API y cómo se distribuyen los pods entre los dos nodos de cómputo del clúster:

![Diagrama de Arquitectura de Kubernetes](k8s_architecture_diagram.jpg)

---

## 2. Diagrama de Arquitectura en Mermaid

```mermaid
graph TD
    %% Cliente Externo
    Cliente([Cliente Web]) -->|Acceso HTTP Puerto 30080| GW

    subgraph Cluster_K8S["Clúster Kubernetes (Multi-Nodo)"]
        
        %% Nodo 1
        subgraph Nodo_1["Nodo 1 (node-1)"]
            GW[api-gateway <br> NodePort: 30080]
            DB[(postgres <br> ClusterIP: 5432)]
            R1[reserva-service <br> Replica 1]
            I1[inventario-service <br> Replica 1]
            P1[pagos-service <br> Replica 1]
        end

        %% Nodo 2
        subgraph Nodo_2["Nodo 2 (node-2)"]
            R2[reserva-service <br> Replica 2]
            I2[inventario-service <br> Replica 2]
            N1[notificaciones-service <br> Replica 1]
        end

    end

    %% Enrutamiento del Gateway
    GW -->|/reservations| R1
    GW -->|/reservations| R2
    GW -->|/payments| P1
    GW -->|/notifications| N1
    GW -->|/inventario| I1
    GW -->|/inventario| I2

    %% Flujos de comunicación entre servicios
    R1 -.->|Verifica y descuenta| I1
    R2 -.->|Verifica y descuenta| I2
    R1 -.->|Procesa cobro| P1
    R2 -.->|Procesa cobro| P1
    R1 -.->|Solicita email| N1
    R2 -.->|Solicita email| N1

    %% Conexiones a Base de Datos
    R1 ==>|Lectura/Escritura| DB
    R2 ==>|Lectura/Escritura| DB
    I1 ==>|Lectura/Escritura| DB
    I2 ==>|Lectura/Escritura| DB
    P1 ==>|Lectura/Escritura| DB
    N1 ==>|Lectura/Escritura| DB

    %% Estilos
    classDef nodo1 fill:#f5f7fa,stroke:#3a4b5c,stroke-width:2px;
    classDef nodo2 fill:#f2f9f5,stroke:#2c6e49,stroke-width:2px;
    classDef database fill:#fff9db,stroke:#f59f00,stroke-width:2px;
    classDef gateway fill:#e8f4fd,stroke:#1971c2,stroke-width:2px;
    
    class GW gateway;
    class DB database;
    class R1,I1,P1 nodo1;
    class R2,I2,N1 nodo2;
```

---

## 3. Detalles de Resiliencia en la Distribución de Pods

### Anti-Afinidad de Pods (Pod Anti-Affinity)
Para cumplir con la restricción de que **la caída de un nodo no elimine todas las réplicas del servicio crítico**, los manifiestos `reservacion.yaml` e `inventario.yaml` definen reglas de anti-afinidad:
- El planificador de Kubernetes (`kube-scheduler`) detecta que el pod `reserva-service` o `inventario-service` ya está corriendo en el `node-1`.
- Al planificar la segunda réplica, detecta la regla de exclusión y la asigna obligatoriamente al `node-2`.
- Si el `node-1` sufre un fallo de hardware (crash) y queda inaccesible:
  - El `api-gateway` detectará el fallo en las conexiones hacia el `node-1`.
  - El balanceador interno de Kubernetes redirigirá el 100% de las solicitudes de reserva e inventario a las réplicas activas en el `node-2`, manteniendo la disponibilidad del sistema.
