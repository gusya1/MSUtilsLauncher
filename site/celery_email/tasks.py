from celery import shared_task
from django.core.mail import get_connection, EmailMultiAlternatives


@shared_task
def send_messages_task(backend_path, backend_kwargs, messages):

    connection = get_connection(
        backend_path,
        **backend_kwargs,
    )

    email_objects = []

    for msg in messages: 

        email = EmailMultiAlternatives(
            subject=msg["subject"],
            body=msg["body"],
            from_email=msg["from_email"],
            to=msg["to"],
            cc=msg["cc"],
            bcc=msg["bcc"],
            reply_to=msg["reply_to"],
            headers=msg["headers"],
        )

        for alt in msg["alternatives"]:
            email.attach_alternative(*alt)

        for attachment in msg["attachments"]:
            email.attach(*attachment)

        email_objects.append(email)

    connection.send_messages(email_objects)