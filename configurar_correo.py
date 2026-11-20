"""Agrega la configuración de correo (SMTP) a tu .env sin tocar lo demás y prueba que las credenciales funcionen.
Uso:  python configurar_correo.py
La contraseña se escribe sin mostrarse en pantalla y solo se guarda en tu .env.
"""
import getpass
import re
import smtplib
from pathlib import Path
from typing import Optional

SERVIDORES = {"gmail.com": ("smtp.gmail.com", 587), "googlemail.com": ("smtp.gmail.com", 587),
              "outlook.com": ("smtp-mail.outlook.com", 587), "hotmail.com": ("smtp-mail.outlook.com", 587),
              "live.com": ("smtp-mail.outlook.com", 587)}


def actualizar_env(ruta: Path, nuevos: dict) -> None:
    """Cambia o agrega claves en el .env conservando el resto. Escribe UTF-8 sin BOM."""
    lineas = ruta.read_text(encoding="utf-8-sig").splitlines() if ruta.exists() else []
    pendientes = dict(nuevos)
    for i, linea in enumerate(lineas):
        clave = linea.partition("=")[0].strip()
        if clave in pendientes and not linea.lstrip().startswith("#"):
            lineas[i] = f"{clave}={pendientes.pop(clave)}"
    lineas += [f"{k}={v}" for k, v in pendientes.items()]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def probar(host: str, puerto: int, usuario: str, clave: str) -> Optional[str]:
    """Devuelve None si el inicio de sesión funciona, o el texto del error."""
    try:
        srv = smtplib.SMTP_SSL(host, puerto, timeout=15) if puerto == 465 else smtplib.SMTP(host, puerto, timeout=15)
        with srv:
            if puerto != 465:
                srv.starttls()
            srv.login(usuario, clave)
        return None
    except smtplib.SMTPAuthenticationError:
        return "Usuario o contraseña rechazados. En Gmail debe ser una contraseña de aplicación de 16 letras, no tu contraseña normal."
    except Exception as e:
        return f"No se pudo conectar: {e}"


def pedir_correo() -> str:
    while True:
        c = input("1) Tu correo (el que enviará los mensajes): ").strip()
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", c):
            return c
        print("   Eso no parece un correo. Ejemplo: nombre@gmail.com")


if __name__ == "__main__":
    ruta = Path(__file__).parent / ".env"
    if not ruta.exists():
        raise SystemExit("No encuentro el archivo .env junto a este script. Debe llamarse exactamente .env (con punto).")

    print("Configurar correo. Responde solo lo que se pide, una cosa por pregunta.\n")
    usuario = pedir_correo()
    dominio = usuario.split("@")[1].lower()
    if dominio in SERVIDORES:
        host, puerto = SERVIDORES[dominio]
        print(f"   Usaré el servidor {host}.")
    else:
        host = input("   Servidor SMTP de tu proveedor (ej. smtp.tuproveedor.com): ").strip()
        puerto = int(re.sub(r"\D", "", input("   Puerto [587]: ")) or "587")

    print("\n2) Contraseña de APLICACIÓN (16 letras que te da Google). NO es la contraseña de tu correo.")
    clave = getpass.getpass("   Pégala aquí (no se verá al escribir): ").replace(" ", "")
    if dominio in ("gmail.com", "googlemail.com") and not re.fullmatch(r"[a-z]{16}", clave):
        print("\n   Aviso: una contraseña de aplicación de Google tiene exactamente 16 letras minúsculas, sin números.")
        print("   Lo que escribiste no tiene ese formato; Gmail la va a rechazar.")
    if not clave:
        raise SystemExit("Faltan datos. No se cambió nada.")

    print("\nProbando el inicio de sesión...")
    error = probar(host, puerto, usuario, clave)
    if error:
        print("X", error)
        if input("¿Guardar de todos modos? (s/n): ").strip().lower() != "s":
            raise SystemExit("No se guardó nada.")
    else:
        print("OK: las credenciales funcionan.")

    actualizar_env(ruta, {"SMTP_HOST": host, "SMTP_PORT": str(puerto), "SMTP_USER": usuario,
                          "SMTP_PASS": clave, "SMTP_FROM": usuario, "APP_URL": "http://127.0.0.1:8000"})
    print("\nGuardado en .env. Reinicia el servidor (Ctrl+C y python run.py) para que lo tome.")
