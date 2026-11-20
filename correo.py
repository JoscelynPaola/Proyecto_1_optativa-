"""Envío de correos por SMTP. Lee la configuración del .env en cada envío."""
import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from dotenv import load_dotenv

log = logging.getLogger("correo")


def _config():
    load_dotenv(override=True)
    cfg = {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587") or 587),
        "user": os.getenv("SMTP_USER", "").strip(),
        "pass": os.getenv("SMTP_PASS", "").replace(" ", ""),
        "from": os.getenv("SMTP_FROM", "").strip() or os.getenv("SMTP_USER", "").strip(),
        "app_url": os.getenv("APP_URL", "http://127.0.0.1:8000").rstrip("/"),
    }
    faltan = [k for k in ("host", "user", "pass") if not cfg[k]]
    if faltan:
        raise RuntimeError(
            "Falta configurar el correo en .env (" + ", ".join(
                "SMTP_" + k.upper() for k in faltan) + "). Ejecuta: python configurar_correo.py")
    return cfg


def app_url() -> str:
    return _config()["app_url"]


def enviar_correo(destino: str, asunto: str, texto: str, html: Optional[str] = None):
    """Envía un correo. Devuelve (True, None) o (False, 'mensaje de error'). Nunca lanza excepción."""
    try:
        cfg = _config()
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = formataddr(("Sistema de Tienda", cfg["from"]))
        msg["To"] = destino
        msg.set_content(texto)
        if html:
            msg.add_alternative(html, subtype="html")

        if cfg["port"] == 465:
            srv = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20)
        else:
            srv = smtplib.SMTP(cfg["host"], cfg["port"], timeout=20)
        with srv:
            if cfg["port"] != 465:
                srv.starttls()
            srv.login(cfg["user"], cfg["pass"])
            srv.send_message(msg)
        log.info("Correo enviado a %s", destino)
        return True, None
    except smtplib.SMTPAuthenticationError:
        err = "Gmail/SMTP rechazó el usuario o la contraseña (usa contraseña de aplicación)."
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    log.error("No se pudo enviar correo a %s: %s", destino, err)
    print(f"[CORREO] ERROR enviando a {destino}: {err}")
    return False, err