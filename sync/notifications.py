"""
sync/notifications.py
----------------------
Envío de alertas por email cuando el pipeline de sync falla.

Si las variables de entorno SMTP no están configuradas, solo registra
el evento en el log (warning). Nunca lanza excepción al caller.
"""

import logging
import os
import smtplib
import ssl
from email.mime.text import MIMEText

log = logging.getLogger("corfo.sync.notify")


def send_alert(subject: str, body: str) -> None:
    """
    Envía un email de alerta al destinatario configurado en ALERT_EMAIL_TO.

    Requiere las variables de entorno:
        ALERT_EMAIL_TO   — dirección destino
        SMTP_HOST        — servidor SMTP (ej: smtp.gmail.com)
        SMTP_USER        — usuario / remitente
        SMTP_PASSWORD    — contraseña o app password

    Opcional:
        SMTP_PORT        — puerto (default: 465 para SSL, usa 587 para STARTTLS)

    Si alguna var falta, registra warning y retorna sin enviar.
    Si el envío falla, registra error y retorna sin relanzar.
    """
    alert_to   = os.environ.get("ALERT_EMAIL_TO", "").strip()
    smtp_host  = os.environ.get("SMTP_HOST", "").strip()
    smtp_user  = os.environ.get("SMTP_USER", "").strip()
    smtp_pass  = os.environ.get("SMTP_PASSWORD", "").strip()
    smtp_port  = os.environ.get("SMTP_PORT", "").strip()

    # Si falta alguna var esencial, solo loguear y salir
    if not all([alert_to, smtp_host, smtp_user, smtp_pass]):
        log.warning("ALERT: %s — %s", subject, body)
        return

    log.info("send_alert: enviando '%s'", subject)

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = smtp_user
        msg["To"]      = alert_to

        # Determinar puerto y método de conexión
        if smtp_port:
            port = int(smtp_port)
        else:
            port = 465  # SSL por defecto

        if port == 587:
            # STARTTLS
            with smtplib.SMTP(smtp_host, port, timeout=15) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [alert_to], msg.as_string())
        else:
            # SSL directo (puerto 465 u otro)
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, port, context=context, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [alert_to], msg.as_string())

        log.info("send_alert: email enviado correctamente a %s", alert_to)

    except Exception as e:
        log.error("send_alert: error al enviar alerta '%s': %s", subject, e)
