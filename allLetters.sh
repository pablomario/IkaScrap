#!/bin/bash

# Definir el comando a ejecutar (programa en Python)
PYTHON_SCRIPT="main.py"

# Definir el abecedario en una cadena
ALPHABET="0123456789"

# Iterar sobre cada letra del abecedario
for letter in $(echo $ALPHABET | fold -w1); do
    # Llamar al script de Python y pasar la letra como parámetro
    python3 $PYTHON_SCRIPT $letter
done
