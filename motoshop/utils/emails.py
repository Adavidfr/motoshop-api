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
    Estilo oscuro de ultra-lujo (Negro y Blanco con acentos Rojos Premium de AuraRider).
    Carga la fuente de Google 'Outfit' para una tipografía sumamente llamativa y moderna.
    """
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <!-- Carga de fuente moderna y llamativa -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #050505; color: #d4d4d4; -webkit-font-smoothing: antialiased;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 40px auto; background-image: url('https://motoshop-api.uaeftt-ute.site/static/images/aurarider_email_background.png'); background-size: cover; background-position: center; border-radius: 16px; border: 1px solid #1f1f1f; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.85); overflow: hidden;">
            <tr>
                <!-- Capa negra translúcida (92%) para asegurar legibilidad impecable sobre la imagen de fondo -->
                <td style="background-color: rgba(13, 13, 13, 0.92); padding: 0;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 50px 40px 30px 40px; text-align: center; border-bottom: 1px solid #1f1f1f;">
                                <!-- Logotipo Oficial AuraRider (Proporcionado por el usuario) -->
                                <img src="https://motoshop-api.uaeftt-ute.site/static/images/aurarider_para_pantallas.png" alt="AuraRider Logo" style="width: 250px; height: auto; margin: 0 auto; display: block; max-width: 100%; object-fit: contain;">
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 50px;">
                                <h2 style="color: #ffffff; margin-top: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.3; margin-bottom: 25px; text-align: left; text-shadow: 0 2px 10px rgba(0,0,0,0.5); border-left: 4px solid #e50914; padding-left: 15px;">
                                    {title}
                                </h2>
                                <div style="font-size: 16px; line-height: 1.8; color: #b3b3b3; font-weight: 400;">
                                    {content}
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #060606; padding: 35px 50px; text-align: center; border-top: 1px solid #161616;">
                                <p style="margin: 0; color: #525252; font-size: 11px; line-height: 1.5; font-weight: 400;">
                                    Has recibido este correo electrónico porque eres miembro registrado de AuraRider MotoShop.
                                </p>
                                <p style="margin: 15px 0 0 0; color: #404040; font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;">
                                    © 2026 AuraRider MotoShop. Todos los derechos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
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
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff; font-weight: 700;">{user.username}</strong>,</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">¡Gracias por unirte a la familia <span style="color: #ffffff; font-weight: 700;">AuraRider MotoShop</span>! Estamos muy emocionados de tenerte con nosotros.</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Desde ahora podrás explorar nuestro catálogo, gestionar tus servicios de mantenimiento, comprar repuestos y mucho más, todo desde la palma de tu mano.</p>
        <div style="text-align: center; margin: 45px 0;">
            <a href="{settings.FRONTEND_URL}" style="background-color: #e50914; color: #ffffff; text-decoration: none; padding: 16px 36px; border-radius: 8px; font-weight: 800; font-size: 16px; display: inline-block; box-shadow: 0 6px 20px rgba(229, 9, 20, 0.4); text-transform: uppercase; letter-spacing: 1px;">Iniciar Sesión</a>
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
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff; font-weight: 700;">{user.username}</strong>,</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hemos recibido una solicitud para restablecer la contraseña asociada a esta cuenta.</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Para crear una nueva contraseña, por favor haz clic en el siguiente botón:</p>
        <div style="text-align: center; margin: 45px 0;">
            <a href="{reset_url}" style="background-color: #e50914; color: #ffffff; text-decoration: none; padding: 16px 36px; border-radius: 8px; font-weight: 800; font-size: 16px; display: inline-block; box-shadow: 0 6px 20px rgba(229, 9, 20, 0.4); text-transform: uppercase; letter-spacing: 1px;">Restablecer Contraseña</a>
        </div>
        <p style="font-size: 14px; line-height: 1.6; color: #888888; background-color: #161616; padding: 15px; border-radius: 8px; border: 1px solid #222222; margin-bottom: 25px;">
            Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:<br>
            <a href="{reset_url}" style="color: #e50914; word-break: break-all; font-weight: 600; text-decoration: none;">{reset_url}</a>
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
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff; font-weight: 700;">{user.username}</strong>,</p>
        <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Tienes una nueva notificación de AuraRider MotoShop:</p>
        <div style="margin: 30px 0; padding: 20px; border-left: 4px solid #e50914; background-color: #161616; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; font-size: 16px; color: #ffffff; line-height: 1.6;">{message.replace(chr(10), '<br>')}</p>
        </div>
        <div style="text-align: center; margin: 45px 0;">
            <a href="{settings.FRONTEND_URL}" style="background-color: #e50914; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: 800; font-size: 15px; display: inline-block; box-shadow: 0 6px 20px rgba(229, 9, 20, 0.4); text-transform: uppercase; letter-spacing: 1px;">Ir a la plataforma</a>
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
                <p style="font-size: 16px; line-height: 1.6; color: #cccccc;">Hola <strong style="color: #ffffff; font-weight: 700;">{user.username}</strong>,</p>
                <div style="margin: 30px 0; padding: 20px; border-left: 4px solid #e50914; background-color: #161616; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; font-size: 16px; color: #ffffff; line-height: 1.6;">{message.replace(chr(10), '<br>')}</p>
                </div>
                <div style="text-align: center; margin: 45px 0;">
                    <a href="{settings.FRONTEND_URL}" style="background-color: #e50914; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: 800; font-size: 15px; display: inline-block; box-shadow: 0 6px 20px rgba(229, 9, 20, 0.4); text-transform: uppercase; letter-spacing: 1px;">Visitar AuraRider MotoShop</a>
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
