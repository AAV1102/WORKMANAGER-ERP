DEFAULT_ADMIN = {
    "email": "sistemas2@integralips.com.co",
    "cedula": "1110579854",
    "nombre": "Sistemas Integral",
    "apellido": "IPS",
    "nombre_completo": "Sistemas Integral IPS",
    "password": "Vihonco25+",
    "rol": "admin",
}

DEMO_USER = {
    "email": "demo@integralips.com.co",
    "cedula": "000000-demo",
    "nombre": "Demo",
    "apellido": "Integral IPS",
    "nombre_completo": "Demo WorkManager (solo lectura)",
    "password": "demo-readonly",
    "rol": "demo",
}


def mask_password(pwd: str) -> str:
    """Returns a lightly masked password for UI rendering."""
    if not pwd:
        return ""
    if len(pwd) <= 4:
        return "*" * len(pwd)
    return f"{pwd[:2]}***{pwd[-2:]}"
