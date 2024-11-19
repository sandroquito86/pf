import re
# utils.py
def validar_cedula(cedula):
    if not cedula or len(cedula) != 10 or not cedula.isdigit():
        return False

    # Extraer los dígitos
    digitos = [int(d) for d in cedula]

    # Aplicar el algoritmo de validación
    suma = 0
    for i in range(9):
        if i % 2 == 0:
            v = digitos[i] * 2
            if v > 9:
                v -= 9
            suma += v
        else:
            suma += digitos[i]

    modulo = suma % 10
    verificador = 0 if modulo == 0 else 10 - modulo

    # Comparar el dígito verificador calculado con el proporcionado
    return verificador == digitos[9]

def validar_email(email):
        """
        Validate the email format using a regular expression.
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None