# services/lineup_validator.py

# Diccionario maestro de formaciones permitidas
VALID_FORMATIONS = {
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    "5-3-2": {"GK": 1, "DEF": 5, "MID": 3, "FWD": 2},
    "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
}

def validar_alineacion(formation_code, jugadores_titulares):
    """
    Recibe: "4-3-3" y la lista de objetos Player que el usuario quiere poner de titular.
    Devuelve: True si es válida, o lanza un error explicando por qué.
    """
    
    # 1. ¿Existe la formación?
    reglas = VALID_FORMATIONS.get(formation_code)
    if not reglas:
        raise ValueError("Formación no válida.")

    # 2. Contar qué ha mandado el usuario
    conteo_usuario = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
    
    for jugador in jugadores_titulares:
        pos = jugador.position  # Esto viene de tu Enum (GK, DEF, MID, FWD)
        conteo_usuario[pos] += 1
        
    # 3. COMPARAR (Aquí es donde evitas que ponga un Defensa de Portero)
    
    # Regla estricta: Tiene que cuadrar EXACTO
    for pos, cantidad_requerida in reglas.items():
        if conteo_usuario[pos] != cantidad_requerida:
            raise ValueError(
                f"La formación {formation_code} requiere {cantidad_requerida} {pos}, "
                f"pero has puesto {conteo_usuario[pos]}."
            )
            
    return True # ¡Alineación válida!