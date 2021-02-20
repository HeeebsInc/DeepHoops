import imaplib
import email as email_module
import smtplib
import pandas as pd
import DeleteAddShow
import datetime
import re


org_email = '@gmail.com'
from_email = 'LilyScraper@gmail.com'
from_pwd = 'Lilyscraper555!'
smtp_server = 'imap.gmail.com'
smtp_port = 993


linespace = '-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------'
def add_delete_website():
    try:
        mail = imaplib.IMAP4_SSL(smtp_server)
        mail.login(from_email,from_pwd)
        mail.select('inbox')
        type, data = mail.search(None, 'ALL')
        mail_ids = data[0]
        id_list = mail_ids.split()
        first_email_id = int(id_list[0])
        latest_email_id = int(id_list[-1])

        email_list = pd.read_csv('../Data/EmailList.csv')
        email_array = pd.array(email_list['Email'])     #checks to see if the email is stored in the saved emails list
        #print(email_array)
        for i in range(latest_email_id,first_email_id, -1):
            i = str.encode(str(i))
            type, data = mail.fetch(i, '(RFC822)')
            for response_part in data:
                if isinstance(response_part,tuple):
                    msg = email_module.message_from_bytes(response_part[1])
                    email_from = msg['from'].lower()
                    start_index = email_from.find('<')
                    symbol_index = email_from.find('@')
                    end_index = email_from.find('>')
                    email_f = email_from[start_index + 1: symbol_index] #FOR IDENTIFYING THE FOLER DIRECTORY
                    email_from = email_from[start_index+1: end_index]
                    if email_from in email_array:
                        #print(email_from)
                        email_subject = msg['subject']
                        email_subject = email_subject.split()


                        if email_subject[0].lower() == 'add':  #add website to list
                            mail.store(i, '+FLAGS', '\\Deleted')
                            web_name = email_subject[1]
                            regex = re.compile('[^A-Za-z0-9]')
                            web_name = regex.sub('', web_name)

                            code, message, website_list = DeleteAddShow.website_adder(dir_name= email_f, web_name = web_name, url= email_subject[2])
                            print('ADD', message)
                            bool, message = email_sender_code(code = code, dataframe = website_list, email = email_from, message = message)
                            print('ADD', message)

                        elif email_subject[0].lower() == 'delete': #delete website to list
                            mail.store(i, '+FLAGS', '\\Deleted')
                            #print(f'Delete: {email_subject}')
                            if isinstance(email_subject[1], list): #if the user inputs a list of names to delete (threading)
                                pass
                            else:
                                code, message, website_list = DeleteAddShow.website_deleter(name = email_subject[1], dir_name= email_f)
                                print('DELETE', message)
                                bool, message = email_sender_code(code = code, dataframe = website_list, email = email_from, message = message)
                                print('DELETE', message)

                        elif email_subject[0].lower() == 'show':
                            mail.store(i, '+FLAGS', '\\Deleted')
                            code, message, website_list = DeleteAddShow.website_shower(dir_name= email_f)
                            print('SHOW', message)
                            bool, message = email_sender_code(code=code, dataframe=website_list, email=email_from,
                                                              message=message)
                            print('SHOW', message)


                    else:
                        continue
        #mail.expunge() #will delete all messages flagged with delete
        return '\t\t~~Successfully checked inbox for add and delete message'


    except Exception as e:
        raise
        error = str(e)
        return f'An Error Occurred: \n{error}'



def email_sender_code(*args, **kwargs):
    message = kwargs.get('message', None)
    email = kwargs.get('email', None)
    dataframe = kwargs.get('dataframe', None)
    code = kwargs.get('code', None)
    date = datetime.datetime.now()
    timestamp = f'{date.month}/{date.day}/{date.year}'
    subject = ''
    statement = ''
    if code == -1:
        subject = 'WEBSITE LIST'
    elif code == 0: #skip because adding or deleting was successful --> to avoid spamming only send emails if there are errors
        return None, 'Successfully Added/Deleted Url'
    else:
        subject = 'ERROR'
        statement = f'Successfully Sent Email....'
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()                # start TLS for security
        s.login("LilyScraper@gmail.com", "Lilyscraper555!")  # Authentication
        s.sendmail("LilyScraper@gmail.com", f'{email}',
                   f'Subject: {subject}: {timestamp} \n\n {message}\n{dataframe}')       # sending the mail
        s.quit()                # terminating the session



        return (True, statement)
    except:
        #raise
        statement = 'We could not send the email.  An error occurred when trying to connect to LilyScraper@gmail.com'
        return (False, statement)



def report_sender(dic_list, email_address):#(dictionary, email, total_changes):

    date = datetime.datetime.now()
    day = date.day
    month = date.month
    year = date.year
    message_list = [f'\n{linespace}\n\n', '\t\t\tWORD REPORT']
    url_list = []
    concat_list = ['\t\t\tList Of Websites With Changes']
    timestamp = f'Website Report: {month}/{day}/{year}'
    #print('\n\n\n')
    for websites in dic_list:
        for items in websites.items():
            message_list.append(f'{linespace}\n\n')

            message_list.append(f'\t\t\t\t{items[0]}\n') #add title and url
            url_list.append(f'{number+1}.{items[0]}')
            message_list.append(f'Old Words\t\t\t\t\tNew Words')
            for words in items[1].items():
                if words[1].get('New') == 'N': #new words
                    row = f'\t\t\t\t\t{words[0].capitalize()}\t+{words[1].get("Count")}'  # {value.get("New")}'
                    message_list.append(row)
                else:
                    row = f'{words[0].capitalize()}\t+{words[1].get("Count")}'  # //{value.get("New")}'
                    message_list.append(row)
    message_list = '\n'.join(message_list)
    url_list = '\n'.join(url_list)
    concat_list.append(url_list)
    concat_list.append(message_list)
    concat_list = '\n\n'.join(concat_list)

    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)

        # start TLS for security
        s.starttls()

        # Authentication
        s.login("LilyScraper@gmail.com", "Lilyscraper555!")


        # sending the mail
        s.sendmail("LilyScraper@gmail.com", f'{email_address}', f'Subject: CHANGES DETECTED! {timestamp} \n\n {concat_list}')

        # terminating the session
        s.quit()

        message = f'\t\t\t - Detected changes for {email_address} and successfully Sent Email report....'
        return (True, message)
    except:
        statement = f'\t\t\tWe could not send the email to {email_address}.  An error occurred when trying to connect to LilyScraper@gmail.com'
        return (False,message)
