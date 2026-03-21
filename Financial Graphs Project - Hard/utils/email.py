import os
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, datetime


import logging
from logging import exception
from openpyxl import Workbook, worksheet

import pandas as pd
from pandas import DataFrame
from configparser import ConfigParser
logger = logging.getLogger(__name__)



def send_error_email(error_message:str, config:ConfigParser, district:str):
    """Sends an email to a user when an error occurs during the program execution.

    Args:
        error_message (str): The error message that will be sent in the email body.
        receiver_email (str): The email address of the administrator that will receive the error notification email. This should be an adminstrator in charge of this program
    """
    emails_enabled = config['EMAIL_SETTINGS'].getboolean('enable_email_sending')

    if emails_enabled:
        try:
            admin_email = config['EMAIL_SETTINGS']['admin_email_address'] #the administrator email address from the config.ini file, this is used in the body of the email to tell the user who to contact if they have any problems or feedback about the graphs.
            sender_email = config['EMAIL_SETTINGS']['sender_email_address'] #the sender email address from the config.ini file
            subject = "Error Occurred in Graphs Program" 
            body = f"An error occurred while running the graphs program for {district}. The error message is: {error_message}. Please check the logs for more details."      
            #password = config['EMAIL_SETTINGS']['email_sender_password'] #sender email account may not have a password. This variable might not be necessary.
            
            #These can be edited in the config file.
            host = config['EMAIL_SETTINGS']['host']
            port = int(config['EMAIL_SETTINGS']['port'])

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = admin_email
            message["Subject"] = subject
            message.attach(MIMEText(body,"plain"))
            text = message.as_string()

            with smtplib.SMTP(host , int(port)) as server: #outlook is: smtp-mail.outlook.com and verizon is smtp.verizon.net (port 465)   gmail is: smtp.gmail.com
                #server.starttls()  # Most modern servers (Gmail/Outlook) require this for security. This may need to be uncommented depending on your email provider's requirements. If your email provider requires a secure connection, you would need to uncomment this line to start TLS encryption for the email transmission.
                #NOTE - depending on the sender email you may need to use a password, if so, you would need to uncomment the line below and enter the sender email password in the config file.
                server.sendmail(sender_email, admin_email, text)
                logging.info(f"Successfully sent error email to {admin_email} for district: {district}")
            server.close()

        #error handling for the email sending process. This will log any errors that occur during the email sending process to the log file defined in the config file.    

        except Exception as e:
            # Catch-all for any other weird errors (like a bad email address)
            logging.error(f"Failed to send error email to {admin_email}: {str(e)}")
            

    else:
        print("Email sending is disabled in the config file, not sending error email to administrator for error: " + error_message)



def send_email_to_user(district_code, district_file_paths:dict, user_email:str, config:ConfigParser):
    """Sends an email to the user with the graphs attached.
    The email will be sent to the district's email address.
    The email will contain a message and the graphs as attachments.

    Args:
        district_code (str): The district code of the district that is being emailed
        district_file_paths (dict): A dictionary containing the file paths of the graphs for each currency type
        file_name (str): The name of the file to be attached to the email
    """
    emails_enabled = config['EMAIL_SETTINGS'].getboolean('enable_email_sending')

    if emails_enabled:
        admin_email = config['EMAIL_SETTINGS']['admin_email_address'] #the administrator email address from the config.ini file, this is used in the body of the email to tell the user who to contact if they have any problems or feedback about the graphs.
        sender_email = config['EMAIL_SETTINGS']['sender_email_address'] #the sender email address from the config.ini file
        subject = "Month End Graphs" 
        body = f"This is an automatic email containing graphs for the most recent month. If you notice any problems or have any feedback, then please contact me at {admin_email}."      
        #password = config['EMAIL']['password'] #sender email account may not have a password. This variable might not be necessary.
        receiver_email = user_email
        
        host = config['EMAIL_SETTINGS']['host']
        port = int(config['EMAIL_SETTINGS']['port'])

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body,"plain")) #attaches the body text to the email

        #this loop attaches all the graph files for the district to the email. It loops through the district_file_paths dictionary and attaches each file to the email. The file name is extracted from the file path and used as the attachment file name.
        if district_file_paths:
            for output_file in district_file_paths.values():
                with open(output_file, "rb") as attachment:
                    file_name = os.path.basename(output_file) #gets the file name from the file path
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {file_name}", #gets the file name from the file path
                    )
                    message.attach(part)
            try:
                # Add attachment to message and convert message to string
                text = message.as_string()
                context = ssl.create_default_context() #not used anymore
                with smtplib.SMTP(host , int(port)) as server: #outlook is: smtp-mail.outlook.com and verizon is smtp.verizon.net (port 465)   gmail is: smtp.gmail.com                    
                    
                    #server.starttls()  # Most modern servers (Gmail/Outlook) require this for security. This may need to be uncommented depending on your email provider's requirements. If your email provider requires a secure connection, you would need to uncomment this line to start TLS encryption for the email transmission.
                    #NOTE - depending on the sender email you may need to use a password, if so, you would need to uncomment the line below and enter the sender email password in the config file.              
                    print(f"Sending email with graphs to: {user_email}")
                    logging.info("  SENDING EMAIL TO: " + user_email + " " + str(datetime.now()))
                    server.sendmail(sender_email, receiver_email, text)#sends the email with the graphs attached.
                server.close()
                print(f"email was sent to: {user_email}") #"smtp-mail.outlook.com" , 465, context=context) as server:

            except Exception as e:
                print(f"EMAIL ERROR: {e}")
                logging.info("  ERROR IN SENDING EMAIL: " + str(e) + " " + str(datetime.now()))
                send_error_email(e, config, district_code)
                
        else:
            print("No output files to send for district code: " + district_code + " not sending email.")

    else:
        print("Email sending is disabled in the config file, not sending email to user: " + user_email)


def send_completion_email(config:ConfigParser):
    """Sends an email to the administrator to notify them that the program has finished running. The email will be sent to the administrator's email address defined in the config file.

    Args:
        config (ConfigParser): The config file that contains the email settings. It is define in main.py and is the config.ini file.
    """

    emails_enabled = config['EMAIL_SETTINGS'].getboolean('enable_email_sending')  

    if emails_enabled:
        print("sending completion email")
        subject = "Finished Running Graphs Program"
        body = "Excel Graphs Finished Running..."

        try:

            sender_email = config['EMAIL_SETTINGS']['sender_email_address'] #the sender email address from the config.ini file
            receiver_email = config['EMAIL_SETTINGS']['admin_email_address'] #my email is
            host = config['EMAIL_SETTINGS']['host']
            port = int(config['EMAIL_SETTINGS']['port'])
            password = config['EMAIL_SETTINGS']['email_sender_password'] #sender email account may not have a password. This variable might not be necessary.

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject
            message.attach(MIMEText(body,"plain"))
            text = message.as_string()

            with smtplib.SMTP(host , int(port)) as server: #outlook is: smtp-mail.outlook.com and verizon is smtp.verizon.net (port 465)   gmail is: smtp.gmail.com
                #server.starttls()  # Most modern servers (Gmail/Outlook) require this for security. This may need to be uncommented depending on your email provider's requirements. If your email provider requires a secure connection, you would need to uncomment this line to start TLS encryption for the email transmission.
                #NOTE - depending on the sender email you may need to use a password, if so, you would need to uncomment the line below and enter the sender email password in the config file.
                server.sendmail(sender_email, receiver_email, text) #this sends the actual email to the adminstrator to notify them that the program has finished running.
            server.close()
            
            #error handling for the email sending process. This will log any errors that occur during the email sending process to the log file defined in the config file.    
        except Exception as e:
            # Catch-all for any other weird errors (like a bad email address)
            logging.error(f"Failed to send error email to {receiver_email}: {str(e)}")

    else:
        print("Email sending is disabled in the config file, not sending completion email.")