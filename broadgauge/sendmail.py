import mandrill
import default_settings

def send_welcome_mail(recipient):
    """
    Sends an email to the recipient email 
    With mandrill client from Mailchimp.
    API documentation for mandrilla can be 
    checked here:
    
    """
    # This secret key is for my personal account. It should be changed
    # to one account for PythonExpress, and placed in config file
    mandrill_client = mandrill.Mandrill(default_settings.mandrill_secret) 
    msg = {}
    msg["text"]= "Hi \n Welcome to PythonExpress."
    msg["subject"]= "Signup notification for PythonExpress"
    msg["from_email"] = "tarun.gaba7@gmail.com"
    msg["to"] = [{'email': recipient.email,'name': recipient.name }]
    result = mandrill_client.messages.send(message=msg, async=False)
    
