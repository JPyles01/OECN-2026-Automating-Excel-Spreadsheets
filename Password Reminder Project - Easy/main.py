#How to activate virtual envirnonment in Visual Studio Code (VS Code) terminal:
#1. Open Powershell Terminal
#2. Navigate to the directory where your virtual environment is located using the `cd` command.
#3. Activate the virtual environment:
#   - cd into the OECN-2026-Automating-Excel-Spreadsheets directory where the virtual environment is located and enter: .\venv\Scripts\Activate.ps1
#   - if there is an execution policy error, run the following in the powershell terminal: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   - then try activating the virtual environment again: .\venv\Scripts\Activate.ps1

#How to install libraries into the virtual environment:
    # - cd into OECN-2026-Automating-Excel-Spreadsheets and enter .venv/Scripts/python.exe -m pip install moduleName
    # - Note replace moduleName with the name of the library you want to install, for example: .venv/Scripts/python.exe -m pip install openpyxl


#How to run scripts in the virtual environment:
    # - cd into OECN-2026-Automating-Excel-Spreadsheets/Password Reminder Project - Easy and enter python main.py
    #(.venv) PS C:\Users\Jon\source\repos\OECN 2026 Demos\OECN-2026-Automating-Excel-Spreadsheets\Password Reminder Project - Easy> python main.py


import os
import pandas as pd #pandas is a library used for data manipulation and analysis. It provides data structures and functions needed to manipulate structured data, such as CSV files. In this program, we use pandas to read the input CSV files into DataFrames, which are then modified and written back to CSV files.
import logging
import configparser
import time #used to create brief pauses in the program if needed, for example, between sending emails to avoid overwhelming the email server with too many requests at once.
from datetime import datetime, timedelta
from pathlib import Path

#email libraries necessary for emailing the output file to the district contacts.
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



def config_setup():
    """Sets up the config file. The config file is used to define file paths used in this program such as the input and output directories.

    Returns:
        _type_: returns the config settings
    """
    
    try:
        print("Setting up config file")
        #config_dir = "config"
        config_file = "config.ini"
        config = configparser.ConfigParser()
        config.read(config_file)
        return config
    except Exception as e:
        print(f"Error reading config file: {e}")

def logging_setup(config:configparser.ConfigParser):
    """Sets up the logging configuration. It creates a log file and sets the format of the log messages.
    Args:
        config (ConfigParser): The config file that contains the log file path and format
    """
    try:
        print("Setting up logging configuration")
        log_file = config['LOG_FILE_PATH']['log_file']
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s' #what the message will look like in the log file
        logging.basicConfig(filename=log_file, level=logging.INFO, format=format)
        return log_file
    except Exception as e:
        print(f"Error: {e} not found in config file.")

def process_file(input_file_path:str, district:str, application:str, output_file_path:str):
    """_summary_

    Args:
        input_file_path (str): _description_
        district (str): _description_
        application (str): _description_
        output_file_path (str): _description_
    """
    try:
        print(f"Processing file: {input_file_path}")  
        users_df = pd.read_csv(input_file_path) #reads the csv file into a pandas dataframe
        users_df = add_columns(input_file_path, users_df, district, application) #calls the add_columns function to add the application and district columns to the dataframe and overwrite the source csv file with the new columns.
        
        process_password_expiration_check(users_df, output_file_path) #calls the process_password_expiration_check function to check if any passwords are expiring soon and print the results to the console. This is where you would call the function to send reminder emails to users with expiring passwords.
    except Exception as e:
        logging.error(f"Error processing file {input_file_path} for {application} in {district}: {str(e)}")
        send_error_email(str(e), ADMIN_EMAIL_ADDRESS, district, application) #calls the send_error_email function to send an email to the administrator email address defined in the config file with the error message if an error occurs during the file processing.


def add_columns(input_file_path: str, users_df: pd.DataFrame, district: str, application: str) -> pd.DataFrame:
    """
    Appends two new columns to a DataFrame and overwrites the source CSV file.
    The two new columns are 'Application' and 'District', which are populated with the provided application name and district identifier
    For example, USAS and Springfield

    Args:
        input_file_path: Path to the CSV file for permanent storage.
        users_df: The DataFrame containing user records to be modified.
        application: The application name to be assigned to all rows.
        district: The district identifier to be assigned to all rows.
    """

     # Assign the district identifier to all rows in a new 'District' column
    users_df['District'] = district 

    # Assign the application name to all rows in a new 'Application' column
    users_df['Application'] = application 
 
    # Export the modified DataFrame to the specified path, excluding the row index
    users_df.to_csv(input_file_path, index=False)

    return users_df #returns the modified dataframe with the new columns added.
    

def add_dataframe_to_file(file_path: str, df: pd.DataFrame) -> None:
    """
    Appends a DataFrame to a CSV. Automatically handles headers and file creation.
    """
    # 1. Only check the physical file, ignore the loop index
    file_exists = os.path.isfile(file_path)
    
    # 2. Always use 'a' (append). 
    # If the file doesn't exist, 'a' creates it anyway!
    # 3. Only include header if the file is brand new
    df.to_csv(file_path, mode='a', header=not file_exists, index=False)

def process_password_expiration_check(users_df: pd.DataFrame, output_file_path:str):
   
    #Converts the string date into a date time format
    users_df['Password Expiration'] = pd.to_datetime(users_df['Password Expiration'], errors='coerce') 
    
    #Converts the date time format back into a string but in the format of month/day/year. This is necessary for the is_password_expiring_soon function to work properly because it expects the date to be in this format.
    users_df['Password Expiration'] = users_df['Password Expiration'].dt.strftime('%m/%d/%Y') 

    emailing_enabled = CONFIG_FILE['EMAIL_SETTINGS'].getboolean('enable_email_sending') #gets the email sending enabled setting from the config file and converts it to a boolean
    print(f"Email sending enabled: {emailing_enabled}")
    
    for index, row in users_df.iterrows(): #Iterates through each row of the users dataframe
        add_dataframe_to_file(output_file_path, pd.DataFrame([row])) #calls the add_dataframe_to_file function to append the current row of the dataframe to the output file. This will create a new csv file with all the user listings and their password expiration status.
        user_email = row['Email Address']     
        password_expiration_str = row['Password Expiration'] #gets the password expiration date as a string

        #boolean, is set to true if the password is expiring soon and false if it is not. 
        password_expired = is_password_expiring_soon(password_expiration_str, PASSWORD_REMINDER_THRESHOLD) #calls the is_password_expiring_soon function to check if the password is expiring soon based on the password expiration date and the password reminder threshold defined in the config file.

        if password_expired: #if the password is expiring soon, print a message to the console. This is where you would call the function to send reminder emails to users with expiring passwords.
            #start email process here
            send_password_expiration_email(user_email, password_expiration_str, row['Application'], row['District']) #calls the send_password_expiration_email function to send a reminder email to the user with the expiring password. The email includes the application name, district, and password expiration date.

        #send completion email

def is_password_expiring_soon(password_expiration_str:str, days_threshold:int)-> bool:
    """Checks if a password is expiring within a certain number of days.

    Args:
        expiration_date (str): The expiration date of the password in string
        """
    if not password_expiration_str or password_expiration_str =="nan": #if there is no expiration date, return false
        return False   

    current_date = datetime.now() #gets the current date and time as a datetime object
    expiration_date = datetime.strptime(password_expiration_str, '%m/%d/%Y') #converts the password expiration date from a string to a datetime object in the format of month/day/year. 
    warning_deadline = current_date + timedelta(days=days_threshold) #calculates the warning deadline by adding the threshold number of days to the current date.

    if  expiration_date <= warning_deadline: #if the expiration date is less than or equal to the warning deadline, return true
        return True
    
    else:
        return False
    

def send_password_expiration_email(user_email:str, password_expiration_date:str, application:str, district:str):
    """Sends a password expiration reminder email to the user with the expiring password. The email includes the application name, district, and password expiration date.

    Args:
        user_email (str): user email address that will receive the email. 
        password_expiration_date (str): the date that the user's password is set to expire. This should be a string an NOT a datetime object
        application (str): the name of the application that the password is for. For example, USAS or USPS
        district (str): the name of the district the user belongs to.
    """
    try:
        print("testing sending email")
        subject = f"Password Expiration Reminder for {application}"
        body = f"Your password for {application} is set to expire on {password_expiration_date}. Please click 'Change Password' on the log in screen and change your password before the expiration date. This is an automatic message. Please do not reply."
        
        sender_email = CONFIG_FILE['EMAIL_SETTINGS']['email_sender_address'] #the sender email address
        receiver_email = user_email #users email address that will receive the email
        password = CONFIG_FILE['EMAIL_SETTINGS']['email_sender_password']#sender email account doesn't have a password. This variable might not be necessary

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body,"plain")) #creates the email message with the subject and body defined above. The email will be sent as plain text.
        text = message.as_string()

        #These can be edited in the config file.
        host = CONFIG_FILE['EMAIL_SETTINGS']['host'] #the SMTP server address for the sender email account
        port = CONFIG_FILE['EMAIL_SETTINGS']['port'] #the SMTP server port for the sender

        with smtplib.SMTP(host , int(port)) as server: #outlook is: smtp-mail.outlook.com and verizon is smtp.verizon.net (port 465)   gmail is: smtp.gmail.com
            #server.starttls()  # NOTE - Most modern servers (Gmail/Outlook) require this for security. This may need to be uncommented depending on your email provider's requirements. If your email provider requires a secure connection, you would need to uncomment this line to start TLS encryption for the email transmission.
            #NOTE - depending on the sender email you may need to use a password, if so, you would need to uncomment the line below and enter the sender email password in the config file. You may also need to set up an app password for the sender email account if it has multi factor authentication enabled.
            server.sendmail(sender_email, receiver_email, text) #actually sends the email with the text
            logging.info(f"Successfully sent email to {user_email} for {application}")
        server.close()

    #error handling for the email sending process. This will log any errors that occur during the email sending process to the log file defined in the config file.    
    except KeyError as e:
        logging.error(f"Configuration Error: Missing key {e} in CONFIG_FILE")
    except smtplib.SMTPAuthenticationError:
        logging.error(f"Authentication Failed: Check the password/app-password for {sender_email}")
    except (smtplib.SMTPConnectError, ConnectionRefusedError):
        logging.error(f"Connection Failed: Could not reach {host} on port {port}")
    except Exception as e:
        # Catch-all for any other weird errors (like a bad email address)
        logging.error(f"Failed to send email to {user_email}: {str(e)}")

def send_completion_email(receiver_email:str):
    """Sends an email to a user when the program has completed running.

    Args:
        receiver_email (str): The email address of the administrator that will receive the completion email. This should be an adminstrator in charge of this program
    """
    try:
        subject = "Password Expiration Notice"
        body = "The Password Expiration program ran successfully. " + str(datetime.now())
        sender_email = CONFIG_FILE['EMAIL_SETTINGS']['email_sender_address'] #the sender email address
        password = CONFIG_FILE['EMAIL_SETTINGS']['email_sender_password']#sender email account doesn't have a password. This variable might not be necessary
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body,"plain"))
        text = message.as_string()

        #These can be edited in the config file.
        host = CONFIG_FILE['EMAIL_SETTINGS']['host'] #the SMTP server address for the sender email account
        port = CONFIG_FILE['EMAIL_SETTINGS']['port'] #the SMTP server port for the sender

        with smtplib.SMTP("mail.noacsc.org" , 25) as server: #outlook is: smtp-mail.outlook.com and verizon is smtp.verizon.net (port 465)   gmail is: smtp.gmail.com       
             #server.starttls()  # NOTE - Most modern servers (Gmail/Outlook) require this for security. This may need to be uncommented depending on your email provider's requirements. If your email provider requires a secure connection, you would need to uncomment this line to start TLS encryption for the email transmission.
            #NOTE - depending on the sender email you may need to use a password, if so, you would need to uncomment the line below and enter the sender email password in the config file.
            server.sendmail(sender_email, receiver_email, text)
        server.close()
        print(f"Completed running program. Sent completion email to {receiver_email}")

    #error handling for the email sending process. This will log any errors that occur during the email sending process to the log file defined in the config file.    
    except KeyError as e:
        logging.error(f"Configuration Error: Missing key {e} in CONFIG_FILE")
    except smtplib.SMTPAuthenticationError:
        logging.error(f"Authentication Failed: Check the password/app-password for {sender_email}")
    except (smtplib.SMTPConnectError, ConnectionRefusedError):
        logging.error(f"Connection Failed: Could not reach {host} on port {port}")
    except Exception as e:
        # Catch-all for any other weird errors (like a bad email address)
        logging.error(f"Failed to send email to {receiver_email}: {str(e)}")


def send_error_email(error_message:str, receiver_email:str, district:str, application:str):
    """Sends an email to a user when an error occurs during the program execution.

    Args:
        error_message (str): The error message that will be sent in the email body.
        receiver_email (str): The email address of the administrator that will receive the error notification email. This should be an adminstrator in charge of this program
    """
    try:
        subject = f"Error in Password Expiration Program for {application} in {district}"
        body = f"An error occurred during the execution of the Password Expiration program for {application} in {district}. The error message is as follows: {error_message}"
        sender_email = CONFIG_FILE['EMAIL_SETTINGS']['email_sender_address'] #the sender email address
        password = CONFIG_FILE['EMAIL_SETTINGS']['email_sender_password']#sender email account doesn't have a password. This variable might not be necessary
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body,"plain"))
        text = message.as_string()

        #These can be edited in the config file.
        host = CONFIG_FILE['EMAIL_SETTINGS']['host'] #the SMTP server address for the sender email account
        port = CONFIG_FILE['EMAIL_SETTINGS']['port'] #the SMTP server port for the sender

        with smtplib.SMTP(host , int(port)) as server: #outlook is: smtp-mail.outlook.com and verizon is smtp.verizon.net (port 465)   gmail is: smtp.gmail.com
            #server.starttls()  # Most modern servers (Gmail/Outlook) require this for security. This may need to be uncommented depending on your email provider's requirements. If your email provider requires a secure connection, you would need to uncomment this line to start TLS encryption for the email transmission.
            #NOTE - depending on the sender email you may need to use a password, if so, you would need to uncomment the line below and enter the sender email password in the config file.
           
            server.sendmail(sender_email, receiver_email, text)
            logging.info(f"Successfully sent error email to {receiver_email} for {application} in {district}")
        server.close()

    #error handling for the email sending process. This will log any errors that occur during the email sending process to the log file defined in the config file.    
    except KeyError as e:
        logging.error(f"Configuration Error: Missing key {e} in CONFIG_FILE")
    except smtplib.SMTPAuthenticationError:
        logging.error(f"Authentication Failed: Check the password/app-password for {sender_email}")
    except (smtplib.SMTPConnectError, ConnectionRefusedError):
        logging.error(f"Connection Failed: Could not reach {host} on port {port}")
    except Exception as e:
        # Catch-all for any other weird errors (like a bad email address)
        logging.error(f"Failed to send error email to {receiver_email}: {str(e)}")


if __name__ == "__main__":

    print("Start Password Project")

    CONFIG_FILE = config_setup() #sets up the config file and returns the config settings
    logging_setup(CONFIG_FILE) #sets up the logging configuration. Info and error messages will be written to this file

    INPUT_DIR = CONFIG_FILE['INPUT_FOLDER_PATH']['parent_districts_dir'] #gets the input file path from the config file
    OUTPUT_FILE = CONFIG_FILE['OUTPUT_FOLDER_PATH']['output_file'] #gets the output file path from the config file   
    PASSWORD_REMINDER_THRESHOLD = int(CONFIG_FILE['PASSWORD_REMINDER']['password_reminder_threshold']) #gets the password reminder threshold from the config file. This is the number of days before a password expires that a reminder email will be sent to the user.
    ADMIN_EMAIL_ADDRESS = CONFIG_FILE['EMAIL_SETTINGS']['admin_email_address'] #gets the administrator email address from the config file. This is the email address that will receive error notification and the completion email.

    #iterates through each district directory in the input directory
    for district in Path(INPUT_DIR).iterdir():

        district_name = str(district.name) #gets the name of the district, for example, District 1

        print(f"Starting proces for {district.name}")
        logging.info(f"Starting process for {district.name}")     
        files_list = os.listdir(district) #gets a list of all the files a district's directory. For example, it will list USAS users.csv and USPS users.csv in the District 1 directory
        
        for file in files_list:
            
            input_file_path = os.path.join(district, file) #gets the file path for each file in the district directory. Password Reminder Project - Easy\input\District 1\USAS users.csv
            
            print(f"Processing {input_file_path} file")
            logging.info(f"Processing {file} file")

            application_name = file.split(" ")[0] #gets the application name from the file name. For example, it will get USAS from USAS users.csv. THIS ONLY WORKS IF USAS OR USPS IS THE FIRST PART OF THE FILE NAME. IF THERE ARE OTHER FILES IN THE DISTRICT DIRECTORIES THIS MAY CAUSE AN ISSUE.
            process_file(input_file_path, district_name, application_name, OUTPUT_FILE) #calls the process_file function to read the csv file into a dataframe, add the application and district columns, and overwrite the source csv file with the new columns.
            time.sleep(1) #creates a brief pause of 1 second between processing each file.
    
    send_completion_email(ADMIN_EMAIL_ADDRESS) #Sends an email to the admin email address that the program has finished running.
