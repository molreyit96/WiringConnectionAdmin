# utils/email.py
from django.conf import settings
import os
import json
import base64
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