# utils/email.py
from django.conf import settings
import os
import json
import base64
import datetime
import time
import urllib.parse
import urllib.request
import urllib.error


def send_email_via_brevo(subject, message, recipient_list, html_message=None):
    api_key = os.environ.get("BREVO_API_KEY", "")
    from_email = settings.DEFAULT_FROM_EMAIL

    payload = {
        "sender": {"email": from_email},
        "to": [{"email": email} for email in recipient_list],
        "subject": subject,
        "textContent": message,
    }
    if html_message:
        payload["htmlContent"] = html_message

    data = json.dumps(payload).encode("utf-8")
    print(f"[BREVO] Sending email to: {recipient_list}, from: {from_email}", flush=True)
    print(f"[BREVO] API key present: {bool(api_key)}", flush=True)
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=data,
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[BREVO] Email sent OK. Status: {resp.status}", flush=True)
            return True, ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[BREVO] API error {e.code}: {body}", flush=True)
        return False, f"Brevo API error {e.code}: {body}"
    except Exception as e:
        print(f"[BREVO] Connection error: {str(e)}", flush=True)
        return False, f"Connection error: {str(e)}"


# ============================================================
# Agregado: 2026-08-05 - Migracion de send_email_with_attachment a la API de Brevo
# Se agrego porque el puerto SMTP (25/587/465) esta bloqueado en DigitalOcean.
# La API de Brevo envia por HTTPS (puerto 443) via POST a https://api.brevo.com/v3/smtp/email
# con el header "api-key" y un payload JSON.
#
# Como funciona con la API de Brevo:
#   1. Se construye un payload JSON con:
#      - sender.email       -> remitente (DEFAULT_FROM_EMAIL)
#      - to[].email         -> lista de destinatarios
#      - subject            -> asunto
#      - textContent/htmlContent -> cuerpo del correo
#      - attachment[]       -> adjuntos [{name, content}], donde content es el archivo
#                              codificado en base64 (Brevo NO acepta archivos binarios crudos)
#   2. Se envia una peticion POST con urllib.request al endpoint de Brevo.
#   3. Respuesta HTTP 201 = exito. Cualquier otro codigo (400/401/403/429) se captura
#      y se devuelve como error para poder diagnosticarlo.
#
# Retorna una tupla (success, error_message):
#   - (True,  "")           -> envio exitoso
#   - (False, error_message) -> fallo (error de API o de conexion)
# ============================================================
def send_email_via_brevo_with_attachment(
    subject,
    message,
    recipient_list,
    attachment_paths=None,
    html_message=None,
    from_email=None
):
    """
    Send email with optional attachments using the Brevo API (HTTPS).
    Added: 2026-08-05

    Args:
        subject (str): Email subject
        message (str): Plain text message
        recipient_list (list): List of recipient emails
        attachment_paths (list, optional): List of file paths to attach
        html_message (str, optional): HTML version of the message
        from_email (str, optional): From email address

    Returns:
        tuple: (True, "") on success, (False, error_message) on error
    """
    api_key = os.environ.get("BREVO_API_KEY", "")
    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    payload = {
        "sender": {"email": from_email},
        "to": [{"email": email} for email in recipient_list],
        "subject": subject,
        "textContent": message,
    }
    if html_message:
        payload["htmlContent"] = html_message

    # Adjuntos: Brevo requiere el contenido del archivo en base64.
    if attachment_paths:
        attachments = []
        for file_path in attachment_paths:
            if os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                with open(file_path, 'rb') as file:
                    file_content = file.read()
                encoded_content = base64.b64encode(file_content).decode('utf-8')
                attachments.append({"name": file_name, "content": encoded_content})
            else:
                return False, f"Attachment not found: {file_path}"
        payload["attachment"] = attachments

    data = json.dumps(payload).encode("utf-8")
    print(f"[BREVO] Sending email with attachment to: {recipient_list}, from: {from_email}", flush=True)
    print(f"[BREVO] API key present: {bool(api_key)}", flush=True)
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=data,
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[BREVO] Email sent OK. Status: {resp.status}", flush=True)
            return True, ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[BREVO] API error {e.code}: {body}", flush=True)
        return False, f"Brevo API error {e.code}: {body}"
    except Exception as e:
        print(f"[BREVO] Connection error: {str(e)}", flush=True)
        return False, f"Connection error: {str(e)}"


# ============================================================
# Agregado: 2026-08-30 - Verificacion de remitentes para los recaps
# Consulta GET /v3/senders de la API de Brevo y devuelve el conjunto de
# emails de remitentes verificados/activos. Si la API falla devuelve None
# para indicar que no se pudo verificar (y no bloquear el envio).
# ============================================================
def get_brevo_verified_sender_emails():
    # La API de Brevo exige que el remitente (sender) este verificado/activo,
    # de lo contrario el envio falla con error "Sender not verified".
    api_key = os.environ.get("BREVO_API_KEY", "")
    req = urllib.request.Request(
        "https://api.brevo.com/v3/senders",
        headers={"Content-Type": "application/json", "api-key": api_key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        senders = data.get("senders", [])
        verified = set()
        for s in senders:
            email = s.get("email")
            if not email:
                continue
            # Incluye el sender solo si esta verificado/activo (active=True),
            # compatible tambien con el campo legacy emailVerified si existiera.
            is_verified = s.get("emailVerified", s.get("active"))
            if is_verified:
                verified.add(email.lower())
        return verified
    except Exception as e:
        # Si la API de Brevo falla no se puede saber el estado del remitente;
        # se devuelve None para que la vista NO bloquee el envio por este motivo.
        print(f"[BREVO] Error fetching senders: {str(e)}", flush=True)
        return None


# ============================================================
# Agregado: 2026-08-30 - Dominios validados en Brevo
# Si el dominio de un remitente esta autenticado/validado en Brevo
# (GET /v3/senders/domains -> authenticated == true), CUALQUIER correo de
# ese dominio es valido como remitente, aunque no este registrado como sender
# individual. Esto evita falsos positivos al bloquear correos de un dominio
# validado en produccion.
# ============================================================
def get_brevo_validated_domains():
    """
    Consulta GET /v3/senders/domains y devuelve el conjunto de dominios
    autenticados/validados (lowercase). Si la API falla devuelve None
    para indicar que no se pudo confirmar.
    """
    api_key = os.environ.get("BREVO_API_KEY", "")
    req = urllib.request.Request(
        "https://api.brevo.com/v3/senders/domains",
        headers={"Content-Type": "application/json", "api-key": api_key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        domains = data.get("domains", [])
        validated = set()
        for d in domains:
            # Un dominio lista para envio tiene authenticated == True.
            if d.get("authenticated"):
                name = d.get("domain_name")
                if name:
                    validated.add(name.lower())
        return validated
    except Exception as e:
        # Si la API falla no se puede saber el estado de los dominios;
        # se devuelve None para que la vista NO bloquee el envio.
        print(f"[BREVO] Error fetching sender domains: {str(e)}", flush=True)
        return None


def sender_is_valid_in_brevo(from_email, verified_senders=None, validated_domains=None):
    """
    Decide si un remitente es valido en Brevo:
      - Si el email esta en la lista de senders verificados/activos, o
      - Si el dominio del email esta autenticado/validado en Brevo.
    Retorna True si es valido, False si no lo es.
    """
    if not from_email:
        return False
    email_l = from_email.lower()
    if verified_senders and email_l in verified_senders:
        return True
    domain = email_l.split("@")[-1]
    if validated_domains and domain in validated_domains:
        return True
    return False


# ============================================================
# Agregado: 2026-08-30 - Confirmacion de entrega post-envio
# Brevo devuelve 201 al aceptar el correo, pero puede rechazarlo despues
# de forma asincrona (p.ej. remitente no validado: "Sending has been
# rejected because the sender you used ..."). Para no marcar mailingDate
# como exito sin confirmacion, se consulta el evento real de entrega.
# ============================================================
def check_recent_delivery_status(recipient_email, since_minutes=3):
    """
    Consulta GET /v3/smtp/statistics/events para el destinatario y clasifica
    el estado de entrega mas reciente dentro de la ventana configurada.
    Retorna una tupla (status, info):
      ('delivered', '')   -> hubo evento delivered/opened/clicked (entrego)
      ('rejected', reason)-> hubo evento 'error' (p.ej. remitente no validado)
      ('pending', '')     -> no hay aun eventos concluyentes
      (None, msg)         -> la API fallo y no se pudo confirmar
    """
    api_key = os.environ.get("BREVO_API_KEY", "")
    url = ("https://api.brevo.com/v3/smtp/statistics/events?limit=50&offset=0&email="
           + urllib.parse.quote(recipient_email))
    try:
        req = urllib.request.Request(
            url,
            headers={"Content-Type": "application/json", "api-key": api_key},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        events = data.get("events", [])
        window_start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=since_minutes)
        for e in events:
            date_str = e.get("date")
            if not date_str:
                continue
            try:
                ev_date = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ev_date < window_start:
                continue
            evt = e.get("event")
            if evt in ("delivered", "opened", "clicked"):
                return "delivered", ""
            if evt == "error":
                return "rejected", (e.get("reason") or "")
        return "pending", ""
    except Exception as ex:
        print(f"[BREVO] Error checking delivery events for {recipient_email}: {str(ex)}", flush=True)
        return None, str(ex)


def confirm_delivery_or_reject(recipient_email, max_attempts=5, delay=2):
    """
    Polling corto tras recibir 201: consulta los eventos hasta confirmar
    entrega o rechazo (p.ej. remitente no validado). Retorna:
      (True, '')      -> entregado confirmado
      (False, reason) -> rechazado (no se envia)
      (None, '')      -> no se pudo confirmar en la ventana
    """
    for attempt in range(max_attempts):
        status, info = check_recent_delivery_status(recipient_email)
        if status == "delivered":
            return True, ""
        if status == "rejected":
            return False, info
        if status is None:
            return None, ""
        time.sleep(delay)
    return None, ""


# ============================================================
# COMENTADA: 2026-08-05 - Migrada a send_email_via_brevo_with_attachment()
# Esta funcion usaba django.core.mail.EmailMessage.send() que envia via SMTP.
# El SMTP esta bloqueado en DigitalOcean, por lo que se reemplaza por la API de Brevo.
# Se mantiene comentada como referencia historica.
# ============================================================
# def send_email_with_attachment(
#     subject,
#     message,
#     recipient_list,
#     attachment_paths=None,
#     html_message=None,
#     from_email=None
# ):
#     """
#     Send email with optional attachments
#     
#     Args:
#         subject (str): Email subject
#         message (str): Plain text message
#         recipient_list (list): List of recipient emails
#         attachment_paths (list, optional): List of file paths to attach
#         html_message (str, optional): HTML version of the message
#         from_email (str, optional): From email address
#     
#     Returns:
#         bool: True if email was sent successfully
#     """
#     try:
#         from_email = from_email or settings.DEFAULT_FROM_EMAIL
#         email = EmailMessage(
#             subject=subject,
#             body=html_message or message,
#             from_email=from_email,
#             to=recipient_list,
#         )
#         
#         if html_message:
#             email.content_subtype = "html"
#         
#         # Attach files if provided
#         if attachment_paths:
#             for file_path in attachment_paths:
#                 if os.path.exists(file_path):
#                     with open(file_path, 'rb') as file:
#                         file_name = os.path.basename(file_path)
#                         email.attach(file_name, file.read(), 'application/octet-stream')
#                 else:
#                     raise FileNotFoundError(f"Attachment not found: {file_path}")
#         
#         #email.send()
#         return False, ""
#     except Exception as e:
#         # Log the error in production
#         if settings.DEBUG:
#             print(f"Email sending failed: {str(e)} - from {from_email} to {recipient_list}")
#         return True, f"Email sending failed: {str(e)} - from {from_email} to {recipient_list} "