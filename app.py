# Importamos las librerías necesarias
from flask import Flask, jsonify
import math

# Creamos la aplicación Flask
app = Flask(__name__)


def calcular_factorial(n):

    # Usamos la función factorial de la librería math
    return math.factorial(n)


def es_par_o_impar(numero):

    # Usamos el operador módulo (%) para verificar si es divisible por 2
    if numero % 2 == 0:
        return "par"
    else:
        return "impar"


# Definimos la ruta principal del microservicio
# <numero> es un parámetro que se recibe en la URL
@app.route('/factorial/<int:numero>', methods=['GET'])
def obtener_factorial(numero):
    
    # Endpoint que recibe un número y devuelve su factorial y si el número es par o impar.
    

    try:
        # Validamos que el número sea positivo (el factorial solo existe para números >= 0)
        if numero < 0:
            return jsonify({
                "error": "El número debe ser mayor o igual a 0"
            }), 400
        
        # Calculamos el factorial del número
        factorial = calcular_factorial(numero)
        
        # Determinamos si el NÚMERO es par o impar (no el factorial)
        tipo = es_par_o_impar(numero)
        
        # Creamos la respuesta en formato JSON
        respuesta = {
            "numero": numero,
            "factorial": factorial,
            "tipo": tipo
        }
        
        # Retornamos la respuesta con código HTTP 200 (éxito)
        return jsonify(respuesta), 200
    
    except Exception as e:
        # Si ocurre algún error, lo capturamos y devolvemos un mensaje de error
        return jsonify({
            "error": f"Error al calcular: {str(e)}"
        }), 500


# Ruta raíz para verificar que el servicio está funcionando
@app.route('/', methods=['GET'])
def inicio():
    """
    Endpoint de bienvenida que muestra cómo usar el servicio.
    
    Returns:
        JSON: Mensaje de bienvenida con instrucciones
    """
    return jsonify({
        "mensaje": "Microservicio de Factorial",
        "uso": "Accede a /factorial/<numero> para obtener el factorial de un número",
        "ejemplo": "/factorial/5"
    }), 200


# Punto de entrada de la aplicación
if __name__ == '__main__':
    # Ejecutamos el servidor en modo debug para ver errores detallados
    # host='0.0.0.0' permite acceso desde cualquier IP
    # port=5000 es el puerto por defecto de Flask
    app.run(debug=True, host='0.0.0.0', port=5000)

