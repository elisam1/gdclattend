import smtplib
import ssl
from email.message import EmailMessage


class EmailManager:
    def __init__(self, db):
        self.db = db

    def _config(self):
        enabled = str(self.db.get_setting('email_notifications', 'false')).lower() == 'true'
        server = self.db.get_setting('smtp_server', '')
        port = int(str(self.db.get_setting('smtp_port', '587') or '587'))
        user = self.db.get_setting('smtp_user', '')
        password = self.db.get_setting('smtp_password', '')
        use_tls = str(self.db.get_setting('smtp_use_tls', 'true')).lower() == 'true'
        use_ssl = str(self.db.get_setting('smtp_use_ssl', 'false')).lower() == 'true'
        return {
            'enabled': enabled,
            'server': server,
            'port': port,
            'user': user,
            'password': password,
            'use_tls': use_tls,
            'use_ssl': use_ssl,
        }

    def send_email(self, to_address: str, subject: str, body: str) -> bool:
        cfg = self._config()
        if not cfg['enabled'] or not to_address or not cfg['server']:
            return False
        msg = EmailMessage()
        msg['From'] = cfg['user'] or 'no-reply@example.com'
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.set_content(body)

        try:
            if cfg['use_ssl']:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(cfg['server'], cfg['port'], context=context) as server:
                    if cfg['user'] and cfg['password']:
                        server.login(cfg['user'], cfg['password'])
                    server.send_message(msg)
            else:
                with smtplib.SMTP(cfg['server'], cfg['port']) as server:
                    if cfg['use_tls']:
                        server.starttls()
                    if cfg['user'] and cfg['password']:
                        server.login(cfg['user'], cfg['password'])
                    server.send_message(msg)
            return True
        except Exception:
            return False