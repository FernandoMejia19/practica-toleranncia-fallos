import logging
import threading
import time
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 2,
        recovery_timeout: int = 10
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()

    def before_call(self):
        with self.lock:
            if self.state == CircuitState.OPEN:
                tiempo_transcurrido = (
                    time.time() - self.last_failure_time
                )
                if tiempo_transcurrido >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.warning("Circuit Breaker cambia a HALF_OPEN")
                else:
                    tiempo_restante = int(
                        self.recovery_timeout - tiempo_transcurrido
                    )
                    raise CircuitOpenError(
                        "Circuito de Pagos abierto. "
                        f"Reintente en {tiempo_restante} segundos."
                    )

    def register_success(self):
        with self.lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
            logger.info("Circuit Breaker de Pagos en estado CLOSED")

    def register_failure(self):
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.warning(
                "Fallo registrado en Circuit Breaker: %s/%s",
                self.failure_count,
                self.failure_threshold
            )
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error("Circuit Breaker de Pagos cambia a OPEN")