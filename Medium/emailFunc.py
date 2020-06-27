import imaplib
import smtplib
import datetime


org_email = '@gmail.com'
from_email = 'LilyScraper@gmail.com'
from_pwd = 'Lilyscraper555!'
smtp_server = 'imap.gmail.com'
smtp_port = 993






def error_sender(error, email_address = 'Samuel.mohebban@gmail.com'):#(dictionary, email, total_changes):

    date = datetime.datetime.now()
    day = date.day
    month = date.month
    year = date.year
    message_list = [f'\n{linespace}\n\n', '\t\t\tError Occured']
    url_list = []
    timestamp = f'Website Report: {month}/{day}/{year}'
    

    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)

        # start TLS for security
        s.starttls()

        # Authentication
        s.login("LilyScraper@gmail.com", "Lilyscraper555!")


        # sending the mail
        s.sendmail("LilyScraper@gmail.com", f'{email_address}', f'Subject: ERROR OCCURED! {timestamp} \n\n {error}')

        # terminating the session
        s.quit()

        message = f'\t\t\t - Error Occured- sent report to {email_address}....'
        return (True, message)
    except:
        statement = f'\t\t\tCould not send the email to {email_address}.  An error occurred when trying to connect to LilyScraper@gmail.com'
        return (False,message)
