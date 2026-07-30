// Configuración de endpoints del Backend. 
// Ajustar según el puerto de despliegue local o la IP del Gateway de Kubernetes.
const API_URLS = {
    reservas: '/reservations',
    pagos: '/payments',
    notificaciones: '/notifications'
};

// Listado de eventos precargados que corresponden a los datos insertados en init.sql
const EVENTS = [
    {
        id: 1,
        nombre: 'Concierto de Rock',
        fecha: '2026-08-20',
        lugar: 'Quito',
        precio: 35.00,
        asientos: [1, 2, 3] // IDs de asientos disponibles del concierto en base de datos
    },
    {
        id: 2,
        nombre: 'Festival de Jazz',
        fecha: '2026-09-15',
        lugar: 'Guayaquil',
        precio: 40.00,
        asientos: [4, 5, 6] // IDs de asientos disponibles del festival en base de datos
    }
];

// Estado de la aplicación
let cart = {
    // id_evento: cantidad
};

// Inicializar el carrito a 0 para cada evento
EVENTS.forEach(event => {
    cart[event.id] = 0;
});

// Referencias a elementos del DOM
const eventsGrid = document.getElementById('events-grid');
const cartItemsContainer = document.getElementById('cart-items');
const cartTotalValue = document.getElementById('cart-total-value');
const btnCheckout = document.getElementById('btn-checkout');
const clientNameInput = document.getElementById('client-name');
const clientEmailInput = document.getElementById('client-email');

// Función para renderizar los eventos
function renderEvents() {
    eventsGrid.innerHTML = '';
    
    EVENTS.forEach(event => {
        const card = document.createElement('div');
        card.className = 'event-card';
        
        card.innerHTML = `
            <div>
                <h3 class="event-name">${event.nombre}</h3>
                <p class="event-details">${event.fecha} &bull; ${event.lugar}</p>
            </div>
            <div>
                <p class="event-price">$${event.precio.toFixed(2)} c/u</p>
                <div class="counter-container">
                    <button class="btn-counter" onclick="updateQuantity(${event.id}, -1)">-</button>
                    <span class="counter-value" id="counter-${event.id}">0</span>
                    <button class="btn-counter" onclick="updateQuantity(${event.id}, 1)">+</button>
                </div>
            </div>
        `;
        eventsGrid.appendChild(card);
    });
}

// Función para actualizar la cantidad seleccionada
window.updateQuantity = function(eventId, change) {
    const event = EVENTS.find(e => e.id === eventId);
    if (!event) return;
    
    const currentQty = cart[eventId];
    const newQty = currentQty + change;
    
    // El mínimo es 0, y el máximo es la cantidad de asientos disponibles
    if (newQty >= 0 && newQty <= event.asientos.length) {
        cart[eventId] = newQty;
        document.getElementById(`counter-${eventId}`).textContent = newQty;
        updateCart();
    } else if (newQty > event.asientos.length) {
        showStatus(`No hay más asientos disponibles para ${event.nombre}. Max: ${event.asientos.length}`, 'error');
    }
};

// Función para actualizar la UI del carrito
function updateCart() {
    cartItemsContainer.innerHTML = '';
    let total = 0;
    let hasItems = false;
    
    EVENTS.forEach(event => {
        const qty = cart[event.id];
        if (qty > 0) {
            hasItems = true;
            const subtotal = qty * event.precio;
            total += subtotal;
            
            const itemElement = document.createElement('div');
            itemElement.className = 'cart-item';
            itemElement.innerHTML = `
                <div>
                    <span class="cart-item-name">${event.nombre}</span>
                    <span class="cart-item-meta"> x${qty}</span>
                </div>
                <strong>$${subtotal.toFixed(2)}</strong>
            `;
            cartItemsContainer.appendChild(itemElement);
        }
    });
    
    if (!hasItems) {
        cartItemsContainer.innerHTML = '<p class="empty-cart-msg">El carrito está vacío.</p>';
        btnCheckout.disabled = true;
    } else {
        btnCheckout.disabled = false;
    }
    
    cartTotalValue.textContent = `$${total.toFixed(2)}`;
}

// Función para mostrar mensajes de estado
function showStatus(message, type) {
    // Si no existe el div de estado, lo creamos
    let statusDiv = document.getElementById('status-box');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.id = 'status-box';
        document.querySelector('.cart-section').appendChild(statusDiv);
    }
    
    statusDiv.className = `status-msg status-${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    
    // Ocultar mensaje automáticamente si es éxito o error después de 5 segundos
    if (type !== 'loading') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

// Lógica de checkout / integración con el Backend
btnCheckout.addEventListener('click', async () => {
    const clientName = clientNameInput.value.trim();
    const clientEmail = clientEmailInput.value.trim();
    
    if (!clientName || !clientEmail) {
        showStatus('Por favor complete su nombre y correo.', 'error');
        return;
    }
    
    // Validación básica de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(clientEmail)) {
        showStatus('Por favor ingrese un correo válido.', 'error');
        return;
    }
    
    btnCheckout.disabled = true;
    showStatus('Procesando compra en los servidores...', 'loading');
    
    let summaryText = 'Resumen de la Compra:\n';
    let total = 0;
    const checkoutItems = [];
    
    EVENTS.forEach(event => {
        const qty = cart[event.id];
        if (qty > 0) {
            const subtotal = qty * event.precio;
            total += subtotal;
            summaryText += `- ${event.nombre} x${qty}: $${subtotal.toFixed(2)}\n`;
            checkoutItems.push({
                event: event,
                qty: qty,
                subtotal: subtotal
            });
        }
    });
    
    summaryText += `Total: $${total.toFixed(2)}\n\n`;
    
    // Intentar llamadas a microservicios del Backend (Tolerancia a fallos en el frontend)
    let reservationSuccess = true;
    let paymentSuccess = true;
    let notificationSuccess = true;
    let errorDetails = '';
    
    const reservationsCreated = [];
    
    try {
        // 1. Crear reservas para cada ticket seleccionado
        for (const item of checkoutItems) {
            for (let i = 0; i < item.qty; i++) {
                // Seleccionar un ID de asiento secuencial
                const seatId = item.event.asientos[i];
                
                try {
                    const resReserva = await fetch(API_URLS.reservas, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id_asiento: seatId,
                            cliente: clientName,
                            correo: clientEmail
                        })
                    });
                    
                    if (!resReserva.ok) {
                        throw new Error(`Código de estado ${resReserva.status}`);
                    }
                    
                    const dataReserva = await resReserva.json();
                    reservationsCreated.push({
                        id_reserva: dataReserva.id_reserva,
                        monto: item.event.precio
                    });
                } catch (e) {
                    reservationSuccess = false;
                    errorDetails += `[Servicio Reservas] Falla al reservar asiento ${seatId}: ${e.message}\n`;
                }
            }
        }
        
        // 2. Procesar pagos para las reservas creadas
        if (reservationSuccess && reservationsCreated.length > 0) {
            for (const res of reservationsCreated) {
                try {
                    const resPago = await fetch(API_URLS.pagos, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id_reserva: res.id_reserva,
                            monto: res.monto
                        })
                    });
                    
                    if (!resPago.ok) {
                        throw new Error(`Código de estado ${resPago.status}`);
                    }
                } catch (e) {
                    paymentSuccess = false;
                    errorDetails += `[Servicio Pagos] Falla al procesar pago para reserva #${res.id_reserva}: ${e.message}\n`;
                }
            }
        }
        
        // 3. Enviar notificaciones para las reservas confirmadas
        if (reservationSuccess && paymentSuccess && reservationsCreated.length > 0) {
            for (const res of reservationsCreated) {
                try {
                    const resNotif = await fetch(API_URLS.notificaciones, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id_reserva: res.id_reserva,
                            correo: clientEmail
                        })
                    });
                    
                    if (!resNotif.ok) {
                        throw new Error(`Código de estado ${resNotif.status}`);
                    }
                } catch (e) {
                    notificationSuccess = false;
                    errorDetails += `[Servicio Notificaciones] Falla al notificar reserva #${res.id_reserva}: ${e.message}\n`;
                }
            }
        }
        
    } catch (globalError) {
        reservationSuccess = false;
        errorDetails += `Error global en la conexión: ${globalError.message}\n`;
    }
    
    // Decisión de visualización basada en la tolerancia a fallos
    let messageType = 'success';
    let finalAlertText = '';
    
    if (reservationSuccess && paymentSuccess && notificationSuccess) {
        showStatus('¡Compra completada con éxito en todos los servicios!', 'success');
        finalAlertText = `¡Compra Finalizada Exitosamente!\n\n${summaryText}El pago ha sido acreditado y se ha enviado la notificación por correo electrónico.`;
    } else {
        // Comportamiento resiliente (degradación elegante en el cliente)
        messageType = 'error';
        showStatus('Compra procesada de forma local con advertencias de servicios.', 'error');
        finalAlertText = `Compra procesada con advertencias (Resiliencia local activada):\n\n${summaryText}Estado de servicios:\n- Reservas: ${reservationSuccess ? 'OK' : 'FALLÓ'}\n- Pagos: ${paymentSuccess ? 'OK' : 'FALLÓ'}\n- Notificaciones: ${notificationSuccess ? 'OK' : 'FALLÓ'}\n\nDetalles del fallo:\n${errorDetails || 'N/A'}`;
    }
    
    // Mostrar alert resumen obligatorio
    alert(finalAlertText);
    
    // Reiniciar todas las cantidades a 0 (Limpiar Carrito)
    EVENTS.forEach(event => {
        cart[event.id] = 0;
        document.getElementById(`counter-${event.id}`).textContent = '0';
    });
    
    // Limpiar campos de texto
    clientNameInput.value = '';
    clientEmailInput.value = '';
    
    // Actualizar UI del carrito
    updateCart();
    
    // Ocultar caja de estado después de limpiar
    const statusBox = document.getElementById('status-box');
    if (statusBox) statusBox.style.display = 'none';
});

// Render inicial
renderEvents();
updateCart();
