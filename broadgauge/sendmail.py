import mandrill
import default_settings


import os
import jinja2

def sendmail(template, **kwargs):
    """
    Sends an email with the selected html template.
    html templates can be found inside the broadguage/templates
    directory. 

    Params:
    =======
    template: str
    Link to the html file to be used as template. The html
    file is parsed by Jinja Templating before sending to the
    recipient. 

    Keyword Args:
    =============
    to: str
    Recipient's email
    
    P.S: Other keywords are sent to Jinja Templating Language for 
    direct parsing, as it is.
    
    Example:
    >>> from sendmail import sendmail
    >>> sendmail("templates/emails/trainers/welcome.html",to=
                               ..."some_email.com",variable1=var,variable2=var2)
    Email sent to some_email.com
    """

    template_loader = jinja2.FileSystemLoader(".")
    env = jinja2.Environment(loader=template_loader)
    unparsed_template = env.get_template(template)
    send_to = kwargs.pop("to")
    parsed_template = unparsed_template.render(**kwargs)

    # Set up email msg:
    msg = {}
    msg["html"]= parsed_template
    msg["subject"]= "Signup notification for PythonExpress"
    msg["from_email"] = "tarun.gaba7@gmail.com"
    msg["to"] = [{'email': send_to }]

    mandrill_client = mandrill.Mandrill(default_settings.mandrill_secret) 
    result = mandrill_client.messages.send(message=msg)
    print "Email to %s"%send_to
    print "Status:%s"%result
