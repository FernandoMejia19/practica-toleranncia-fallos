import logging
import os
import requests
from ..resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError
)

logger = logging.getLogger(__name__)

PAYMENTS_URL = os.getenv(
    "PAYMENTS_URL",
    "http://pagos-service:8000"
)

PAYMENT_TIMEOUT = float(
    os.getenv("PAYMENT_TIMEOUT", "3")
)

payment_breaker = CircuitBreaker(
    failure_threshold=2,
    recovery_timeout=10
)

class PaymentUnavailableError(Exception):
    pass

class PaymentRejectedError(Exception):
    pass

def procesar_pago(
    id_reserva: int,
    monto: float,
    simular_demora: int = 0,
    simular_fallo: bool = False,
    tolerancia_activa: bool = True
) -> dict:
    if tolerancia_activa:
        payment_breaker.before_call()

    url = f"{PAYMENTS_URL}/payments"
    parametros = {
        "simular_demora": simular_demora,
        "simular_fallo": str(simular_fallo).lower()
    }
    payload = {
        "id_reserva": id_reserva,
        "monto": monto
    }

    timeout_val = PAYMENT_TIMEOUT if tolerancia_activa else 30.0

    try:
        logger.info(
            "Procesando pago de la reserva %s",
            id_reserva
        )
        response = requests.post(
            url,
            params=parametros,
            json=payload,
            timeout=timeout_val
        )
        if response.status_code == 200:
            if tolerancia_activa:
                payment_breaker.register_success()
            return response.json()
        if 400 <= response.status_code < 500:
            raise PaymentRejectedError(
                f"Pago rechazado: {response.text}"
            )
        raise requests.RequestException(
            f"Pagos respondió HTTP {response.status_code}"
        )
    except PaymentRejectedError:
        raise
    except (
        requests.Timeout,
        requests.ConnectionError,
        requests.RequestException
    ) as error:
        if tolerancia_activa:
            payment_breaker.register_failure()
        logger.error(
            "Error temporal en Pagos: %s",
            error
        )
        raise PaymentUnavailableError(
            "La pasarela de pagos no respondió correctamente"
        ) from error