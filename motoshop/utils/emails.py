from django.core.mail import send_mail, get_connection, EmailMultiAlternatives
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import logging

logger = logging.getLogger(__name__)

def get_base_html(title, content):
    """
    Plantilla base HTML para todos los correos.
    Estilo oscuro Premium basado en la interfaz web de AuraRider (Monocromático Negro/Blanco).
    """
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0a0a0a; color: #e5e5e5;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #121212; margin: 40px auto; border-radius: 12px; overflow: hidden; border: 1px solid #222222; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.9);">
            <!-- Header -->
            <tr>
                <td style="padding: 40px 20px 20px 20px; text-align: center;">
                    <!-- Logotipo Oficial AuraRider -->
                    <img src="https://motoshop-api.uaeftt-ute.site/static/images/aurarider_para_pantallas.png" alt="AuraRider" style="width: auto; height: 90px; margin: 0 auto 15px auto; display: block; max-width: 100%; object-fit: contain;">
                    <p style="color: #888888; margin: 5px 0 0 0; font-size: 13px; font-weight: 400; text-transform: uppercase; letter-spacing: 2px;">Diseño, potencia y control en tus manos</p>
                </td>
            </tr>
            
            <!-- Body -->
            <tr>
                <td style="padding: 30px 40px;">
                    <h2 style="color: #ffffff; margin-top: 0; font-size: 22px; border-bottom: 1px solid #222222; padding-bottom: 15px; font-weight: 600;">{title}</h2>
                    {content}
                </td>
            </tr>
            
            <!-- Footer -->
            <tr>
                <td style="background-color: #070707; padding: 25px 40px; text-align: center; border-top: 1px solid #1a1a1a;">
                    <p style="margin: 0; color: #666666; font-size: 12px;">
                        Has recibido este correo porque estás registrado en AuraRider MotoShop.
                    </p>
                    <p style="margin: 8px 0 0 0; color: #444444; font-size: 11px;">
                        © 2026 AuraRider MotoShop. Todos los derechos reservados.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def send_welcome_email(user):
    """
    Envía un correo de bienvenida al registrarse.
    """
    subject = '¡Bienvenido a AuraRider MotoShop!'
    
    # Texto plano alternativo
    text_content = f'Hola {user.username},\n\nGracias por registrarte en AuraRider MotoShop. ¡Estamos emocionados de tenerte con nosotros!\n\nSaludos,\nEl equipo de AuraRider'
    
    # Contenido HTML
    html_body = f"""
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff;">{user.username}</strong>,</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">¡Gracias por unirte a la familia AuraRider MotoShop! Estamos muy emocionados de tenerte con nosotros.</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Desde ahora podrás explorar nuestro catálogo, gestionar tus servicios de mantenimiento, comprar repuestos y mucho más, todo desde la palma de tu mano.</p>
        <div style="text-align: center; margin: 40px 0;">
            <a href="{settings.FRONTEND_URL}" style="background-color: #ffffff; color: #000000; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);">Iniciar Sesión</a>
        </div>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Saludos,<br>El equipo de <strong style="color: #ffffff;">AuraRider</strong></p>
    """
    
    html_content = get_base_html("¡Tu cuenta ha sido creada con éxito!", html_body)
    
    try:
        send_mail(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_content
        )
    except Exception as e:
        logger.error(f"Error al enviar correo de bienvenida a {user.email}: {str(e)}")

def send_password_reset_email(user):
    """
    Genera un token y envía un correo para recuperar contraseña.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    reset_url = f"{settings.FRONTEND_URL}reset-password?uid={uid}&token={token}"
    subject = 'Recuperación de contraseña - AuraRider MotoShop'
    
    # Texto plano alternativo
    text_content = f'Hola {user.username},\n\nHas solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para crear una nueva:\n\n{reset_url}\n\nSi no solicitaste este cambio, puedes ignorar este correo.\n\nSaludos,\nEl equipo de AuraRider'
    
    # Contenido HTML
    html_body = f"""
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff;">{user.username}</strong>,</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hemos recibido una solicitud para restablecer la contraseña asociada a esta cuenta.</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Para crear una nueva contraseña, por favor haz clic en el siguiente botón:</p>
        <div style="text-align: center; margin: 40px 0;">
            <a href="{reset_url}" style="background-color: #ffffff; color: #000000; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);">Restablecer Contraseña</a>
        </div>
        <p style="font-size: 14px; line-height: 1.6; color: #888888; background-color: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #222222;">
            Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:<br>
            <a href="{reset_url}" style="color: #ffffff; word-break: break-all;">{reset_url}</a>
        </p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Si no realizaste esta solicitud, puedes ignorar este correo de forma segura. Tu contraseña actual no cambiará.</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Saludos,<br>El equipo de <strong style="color: #ffffff;">AuraRider</strong></p>
    """
    
    html_content = get_base_html("Restablecer Contraseña", html_body)
    
    try:
        send_mail(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_content
        )
    except Exception as e:
        logger.error(f"Error al enviar correo de recuperación a {user.email}: {str(e)}")

def send_notification_email(user, title, message):
    """
    Envía un correo de notificación individual.
    """
    html_body = f"""
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff;">{user.username}</strong>,</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Tienes una nueva notificación de AuraRider MotoShop:</p>
        <div style="margin: 30px 0; padding: 20px; border-left: 4px solid #ffffff; background-color: #1a1a1a; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; font-size: 16px; color: #ffffff; line-height: 1.6;">{message.replace(chr(10), '<br>')}</p>
        </div>
        <div style="text-align: center; margin: 40px 0;">
            <a href="{settings.FRONTEND_URL}" style="background-color: #ffffff; color: #000000; text-decoration: none; padding: 12px 25px; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);">Ir a la plataforma</a>
        </div>
    """
    
    html_content = get_base_html(title, html_body)
    
    try:
        send_mail(
            title,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_content
        )
    except Exception as e:
        logger.error(f"Error al enviar notificación a {user.email}: {str(e)}")

def send_mass_notification_emails(users, title, message):
    """
    Envía un correo HTML masivo a una lista de usuarios utilizando EmailMultiAlternatives
    y reutilizando la misma conexión al servidor SMTP para ser eficiente.
    """
    connection = get_connection(fail_silently=False)
    messages = []
    
    for user in users:
        if user.email:
            # Texto plano
            text_content = f'Hola {user.username},\n\n{message}'
            
            # Contenido HTML
            html_body = f"""
                <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff;">{user.username}</strong>,</p>
                <div style="margin: 30px 0; padding: 20px; border-left: 4px solid #ffffff; background-color: #1a1a1a; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; font-size: 16px; color: #ffffff; line-height: 1.6;">{message.replace(chr(10), '<br>')}</p>
                </div>
                <div style="text-align: center; margin: 40px 0;">
                    <a href="{settings.FRONTEND_URL}" style="background-color: #ffffff; color: #000000; text-decoration: none; padding: 12px 25px; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);">Visitar AuraRider MotoShop</a>
                </div>
            """
            html_content = get_base_html(title, html_body)
            
            email = EmailMultiAlternatives(
                title,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            messages.append(email)
            
    if messages:
        try:
            # Enviar todos los correos usando una sola conexión
            connection.send_messages(messages)
        except Exception as e:
            logger.error(f"Error al enviar correos masivos: {str(e)}")
