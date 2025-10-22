# Microservicio de Cálculo de Factorial

## Descripción del Proyecto

Este microservicio recibe un número a través de la URL y devuelve una respuesta en formato JSON que contiene:
- El número recibido
- Su factorial
- Una etiqueta indicando si el número es "par" o "impar"

## Tecnologías Utilizadas

- **Python 3**: Lenguaje de programación
- **Flask**: Framework web minimalista para crear el microservicio
- **Math**: Librería estándar de Python para cálculos matemáticos

## Instalación y Ejecución

### Requisitos Previos
- Python 3.7 o superior instalado
- pip (gestor de paquetes de Python)

### Pasos para Ejecutar

1. **Clonar el repositorio**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd Parcial02_Arqui
   ```

2. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el microservicio**
   ```bash
   python app.py
   ```

4. **El servicio estará disponible en:**
   ```
   http://localhost:5000
   ```

## Uso del Microservicio

### Endpoint Principal

**GET** `/factorial/<numero>`

**Ejemplo de uso:**
```
http://localhost:5000/factorial/5
```

**Respuesta JSON:**
```json
{
  "numero": 5,
  "factorial": 120,
  "tipo": "impar"
}
```

### Otros Ejemplos

**Factorial de 0:**
```
GET http://localhost:5000/factorial/0
```
Respuesta:
```json
{
  "numero": 0,
  "factorial": 1,
  "tipo": "par"
}
```

**Factorial de 7:**
```
GET http://localhost:5000/factorial/7
```
Respuesta:
```json
{
  "numero": 7,
  "factorial": 5040,
  "tipo": "impar"
}
```

**Factorial de 8:**
```
GET http://localhost:5000/factorial/8
```
Respuesta:
```json
{
  "numero": 8,
  "factorial": 40320,
  "tipo": "par"
}
```

**Número negativo (error):**
```
GET http://localhost:5000/factorial/-5
```
Respuesta:
```json
{
  "error": "El número debe ser mayor o igual a 0"
}
```

## Arquitectura Actual

```
Cliente HTTP → Microservicio (Flask) → Cálculo Local → Respuesta JSON
```

El microservicio actual es **stateless** (sin estado), es decir:
- No almacena información entre peticiones
- Cada cálculo es independiente
- No hay persistencia de datos
- Es simple y fácil de escalar horizontalmente

## Modificación para Comunicación con Servicio de Historial

### Pregunta de Análisis

**¿Cómo modificaría el diseño si este microservicio tuviera que comunicarse con otro servicio que almacena el historial de cálculos en una base de datos externa?**

### Respuesta:

Para integrar el microservicio con un sistema de almacenamiento de historial, implementaría los siguientes cambios:

#### 1. **Arquitectura Propuesta**

```
Cliente HTTP → Microservicio de Factorial (Flask)
                    ↓
                    ↓ (Comunicación HTTP/REST o Message Queue)
                    ↓
              Microservicio de Historial
                    ↓
              Base de Datos 
```

#### 2. **Patrón de Comunicación: Event-Driven con Message Queue**

**Opción :** Usar una cola de mensajes (AWS SQS)

**Ventajas:**
- **Desacoplamiento**: Los servicios no dependen directamente uno del otro
- **Asincronía**: El microservicio de factorial no espera a que se guarde el historial
- **Resiliencia**: Si el servicio de historial está caído, los mensajes se guardan en la cola
- **Escalabilidad**: Podemos tener múltiples consumidores procesando el historial

**Implementación:**
```python
# En app.py - después de calcular el factorial

import pika  # Cliente de RabbitMQ
import json

def enviar_a_historial(numero, factorial, tipo):
    """Envía el resultado a la cola de mensajes para ser procesado"""
    # Conexión a RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    # Declaramos la cola
    channel.queue_declare(queue='historial_calculos')
    
    # Preparamos el mensaje
    mensaje = {
        "numero": numero,
        "factorial": factorial,
        "tipo": tipo,
        "timestamp": datetime.now().isoformat()
    }
    
    # Publicamos el mensaje
    channel.basic_publish(
        exchange='',
        routing_key='historial_calculos',
        body=json.dumps(mensaje)
    )
    
    connection.close()

# Modificación en el endpoint
@app.route('/factorial/<int:numero>', methods=['GET'])
def obtener_factorial(numero):
    # ... código existente ...
    
    # Enviamos a la cola de forma asíncrona
    try:
        enviar_a_historial(numero, factorial, tipo)
    except Exception as e:
        # Log del error, pero no afecta la respuesta al usuario
        print(f"Error al enviar historial: {e}")
    
    return jsonify(respuesta), 200
```

#### 3. **Patrón Alternativo: Comunicación HTTP Directa**

Esta esta otra opcion que aprendi en proyecto 2 y tambien puede ser util:

```python
import requests

def guardar_historial(numero, factorial, tipo):
    """Envía el resultado al servicio de historial via HTTP"""
    try:
        url = "http://servicio-historial:8080/api/historial"
        datos = {
            "numero": numero,
            "factorial": factorial,
            "tipo": tipo,
            "timestamp": datetime.now().isoformat()
        }
        
        # Timeout de 2 segundos para no bloquear
        response = requests.post(url, json=datos, timeout=2)
        
        if response.status_code != 201:
            print(f"Error al guardar historial: {response.status_code}")
    except requests.exceptions.RequestException as e:
        # No propagamos el error al usuario
        print(f"Servicio de historial no disponible: {e}")
```

#### 4. **Esquema del Servicio de Historial**

El servicio de historial tendría:

**Base de Datos (PostgreSQL ya que es la que uso para otros proyectos pero puede ser con otras bases de datos):**
```sql
CREATE TABLE historial_calculos (
    id SERIAL PRIMARY KEY,
    numero INTEGER NOT NULL,
    factorial BIGINT NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_cliente VARCHAR(50)
);
```

**Endpoints del Servicio de Historial:**
- `POST /api/historial` - Guardar un cálculo
- `GET /api/historial` - Obtener todos los cálculos
- `GET /api/historial/<numero>` - Obtener historial de un número específico

#### 5. **Diagrama de Secuencia**

```
Usuario → [GET /factorial/5] → Microservicio Factorial
                                      ↓
                               1. Calcular factorial
                                      ↓
                               2. Preparar respuesta
                                      ↓
                               3. Enviar a cola/servicio historial (async)
                                      ↓
                               4. Retornar JSON → Usuario
                                      
Proceso Separado:
    Cola de Mensajes ← Consumer (Servicio Historial)
                            ↓
                      Base de Datos
```

#### 6. **Dependencias Adicionales Necesarias**

```txt
# Para comunicación con RabbitMQ
pika==1.3.2

# Para llamadas HTTP
requests==2.31.0

# Para manejo de circuit breaker
pybreaker==1.0.1
```

### Conclusión

La mejor opción si tuvieramos que implementarla realmente depende de los requisitos que se nos pidan, como pueden ser:

- **Para alta disponibilidad y escalabilidad**: Message Queue (RabbitMQ/Kafka)
- **Para simplicidad y proyectos pequeños**: HTTP directo con manejo de errores
- **Para arquitecturas cloud**: Servicios administrados (AWS SQS + Lambda, Google Cloud Pub/Sub)