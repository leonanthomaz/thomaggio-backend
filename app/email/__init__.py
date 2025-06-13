from pydantic import EmailStr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
from jinja2 import Environment, FileSystemLoader
from app.configuration.settings import Configuration
from fastapi import BackgroundTasks

# Inicializa a configuração
configuration = Configuration()

# Define a classe EmailService
class EmailService:
    def __init__(self):
        self.email_user = os.getenv('EMAIL_USER') or configuration.email_user
        self.email_password = os.getenv('EMAIL_PASSWORD') or configuration.email_password
        self.template_env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

    def send_email(self, to_email: EmailStr, subject: str, html_content: str, background_tasks: BackgroundTasks = None):
        def send_email_task():
            try:
                msg = MIMEMultipart()
                msg['From'] = self.email_user
                msg['To'] = to_email
                msg['Subject'] = subject

                msg.attach(MIMEText(html_content, 'html'))

                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(self.email_user, self.email_password)
                    server.sendmail(self.email_user, to_email, msg.as_string())

                print(f"E-mail enviado com sucesso para {to_email}!")
            except Exception as e:
                print(f"Erro ao enviar o e-mail para {to_email}: {e}")

        if background_tasks:
            background_tasks.add_task(send_email_task)
        else:
            send_email_task()

    def render_template(self, template_name: str, **kwargs):
        template = self.template_env.get_template(template_name)
        return template.render(**kwargs)

    def send_create_enterprise_email(self, email: EmailStr, name_company: str, background_tasks: BackgroundTasks):
        subject = "Bem-vindo(a) à nossa plataforma!"
        html_content = self.render_template('create_enterprise.html', name_company=name_company)
        self.send_email(email, subject, html_content, background_tasks)

    def send_notification_email(self, email: EmailStr, message: str, background_tasks: BackgroundTasks):
        subject = "Notificação importante"
        html_content = self.render_template('notification.html', message=message)
        self.send_email(email, subject, html_content, background_tasks)

    def send_payment_reminder_email(self, email: EmailStr, due_date: str, amount: float, background_tasks: BackgroundTasks):
        subject = "Lembrete de pagamento"
        html_content = self.render_template('payment_reminder.html', due_date=due_date, amount=amount)
        self.send_email(email, subject, html_content, background_tasks)
        
    def send_validate_email(self, link: str, email: EmailStr, background_tasks: BackgroundTasks):
        subject = "Redefinição de senha"
        html_content = self.render_template('validate_email.html', reset_link=link)
        self.send_email(email, subject, html_content, background_tasks)
        
    
