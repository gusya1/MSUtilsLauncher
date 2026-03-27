from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend



class CeleryEmailBackend(EmailBackend):

    def send_messages(self, email_messages):

        if not email_messages:
            return 0

        backend_path = settings.EMAIL_BACKEND_SYNC

        if backend_path == "snmprogs.email_backend.CeleryEmailBackend":
            return super().send_messages(email_messages)

        from celery_email.tasks import send_messages_task

        serialized_messages = []

        for message in email_messages:

            serialized_messages.append({
                "subject": message.subject,
                "body": message.body,
                "from_email": message.from_email,
                "to": message.to,
                "bcc": message.bcc,
                "cc": message.cc,
                "reply_to": message.reply_to,
                "attachments": message.attachments,
                "alternatives": getattr(message, "alternatives", []),
                "headers": message.extra_headers,
            })

        backend_kwargs = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "timeout": self.timeout,
        }

        try:
            send_messages_task.delay(
                backend_path,
                backend_kwargs,
                serialized_messages,
            )
        except Exception:
            return super().send_messages(email_messages)

        return len(email_messages) 