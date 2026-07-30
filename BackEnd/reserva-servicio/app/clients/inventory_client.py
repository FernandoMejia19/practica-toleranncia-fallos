import logging
import os
import time
import requests

logger = logging.getLogger(__name__)

INVENTORY_URL = os.getenv(
    "INVENTORY_URL",
    "http://inventario-service:8000"
)

class InventoryUnavailableError(Exception):
    pass

class SeatUnavailableError(Exception):
    pass

def reservar_asiento_con_retry(
    id_asiento: int,
    max_intentos: int = 3,
    timeout_segundos: int = 3,
    tolerancia_activa: bool = True
) -> dict:
    url = (
        f"{INVENTORY_URL}/inventory/"
        f"seats/{id_asiento}/hold"
    )
    
    intentos_limite = max_intentos if tolerancia_activa else 1

    for intento in range(1, intentos_limite + 1):
        try:
            logger.info(
                "Intentando reservar asiento %s. Intento %s/%s",
                id_asiento,
                intento,
                intentos_limite
            )
            response = requests.post(
                url,
                timeout=timeout_segundos
            )
            if response.status_code == 200:
                logger.info(
                    "Asiento %s reservado correctamente",
                    id_asiento
                )
                return response.json()
            if response.status_code == 409:
                logger.warning(
                    "Asiento %s no disponible",
                    id_asiento
                )
                raise SeatUnavailableError(
                    "El asiento seleccionado ya no está disponible"
                )
            if response.status_code >= 500:
                raise requests.RequestException(
                    f"Inventario respondió {response.status_code}"
                )
            response.raise_for_status()
        except SeatUnavailableError:
            raise
        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.RequestException
        ) as error:
            logger.warning(
                "Fallo temporal al consultar Inventario: %s",
                error
            )
            if intento == intentos_limite:
                logger.error(
                    "Inventario no disponible después de %s intentos",
                    intentos_limite
                )
                raise InventoryUnavailableError(
                    "El servicio de inventario no está disponible"
                ) from error
            
            espera = 0.5 * (2 ** (intento - 1))
            logger.info(
                "Reintentando en %s segundo(s)",
                espera
            )
            time.sleep(espera)

    raise InventoryUnavailableError(
        "No fue posible comunicarse con Inventario"
    )

def confirmar_asiento(
    id_asiento: int,
    timeout_segundos: int = 3
) -> dict:
    url = (
        f"{INVENTORY_URL}/inventory/"
        f"seats/{id_asiento}/confirm"
    )
    try:
        response = requests.post(
            url,
            timeout=timeout_segundos
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        logger.error(
            "No fue posible confirmar el asiento %s: %s",
            id_asiento,
            error
        )
        raise InventoryUnavailableError(
            "No fue posible confirmar el asiento"
        ) from error

def liberar_asiento(
    id_asiento: int,
    timeout_segundos: int = 5
) -> dict | None:
    url = (
        f"{INVENTORY_URL}/inventory/"
        f"seats/{id_asiento}/release"
    )
    logger.info(
        "Solicitando liberación del asiento %s en %s",
        id_asiento,
        url
    )
    try:
        response = requests.post(
            url,
            timeout=timeout_segundos
        )
        logger.info(
            "Inventario respondió HTTP %s al liberar asiento %s",
            response.status_code,
            id_asiento
        )
        if response.status_code == 200:
            return response.json()
        logger.error(
            "No fue posible liberar el asiento %s. Respuesta: %s",
            id_asiento,
            response.text
        )
        return None
    except requests.Timeout as error:
        logger.error(
            "Timeout liberando asiento %s: %s",
            id_asiento,
            error
        )
        return None
    except requests.ConnectionError as error:
        logger.error(
            "Error de conexión liberando asiento %s: %s",
            id_asiento,
            error
        )
        return None
    except requests.RequestException as error:
        logger.error(
            "Error HTTP liberando asiento %s: %s",
            id_asiento,
            error
        )
        return None