# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"
import smtplib
from email.mime.text import MIMEText

from jinja2 import Environment
from jinja2 import FileSystemLoader


def assemble_mail(message, to_address, from_address, subject):
    """Adds to and from address and subject to mail"""
    message = MIMEText(message, 'html')
    message['From'] = from_address
    message['To'] = to_address
    message['Subject'] = subject
    return message.as_string()


class MailServer:

    def __init__(self, from_address, password, host, port, templates):
        """Starts and logs into mail server"""
        self.from_address = from_address
        self.server = smtplib.SMTP(host, port)
        self.server.starttls()
        self.server.login(self.from_address, password)
        self.env = Environment(loader=FileSystemLoader(templates))

    def close(self):
        self.server.quit()

    def send_mail(self, to_address, subject, data, template):
        """Creates mail and sends it"""
        template = self.env.get_template(template + '.tmpl')
        content = template.render(data)
        mail = assemble_mail(content, to_address, self.from_address, subject)
        return self.server.sendmail(self.from_address, to_address, mail)
