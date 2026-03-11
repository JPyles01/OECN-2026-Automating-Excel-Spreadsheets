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
import openpyxl
import pandas as pd #pandas is a library used for data manipulation and analysis. It provides data structures and functions needed to manipulate structured data, such as CSV files. In this program, we use pandas to read the input CSV files into DataFrames, which are then modified and written back to CSV files.
import csv
import logging
import configparser
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

def process_file(input_file_path:str, district:str, application:str):
    print(f"Processing file: {input_file_path}")  
    users_df = pd.read_csv(input_file_path) #reads the csv file into a pandas dataframe
    users_df = add_columns(input_file_path, users_df, district, application) #calls the add_columns function to add the application and district columns to the dataframe and overwrite the source csv file with the new columns.
    process_password_expiration_check(users_df) #calls the process_password_expiration_check function to check if any passwords are expiring soon and print the results to the console. This is where you would call the function to send reminder emails to users with expiring passwords.

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
    

def add_dataframe_to_output_file(output_file: str, df: pd.DataFrame, index: int) -> None:
    """
    Appends a DataFrame to a CSV file or creates a new file if it does not exist.
    
    Args:
        output_file: Path to the destination CSV file.
        df: The DataFrame containing the data to be written.
        index: The current iteration count in the processing loop.
    """
    # Check if file exists on disk
    file_exists = os.path.isfile(output_file)
    
    # Write header if file is new or if processing the first item in the loop
    include_header = not file_exists or index == 0
    
    # Use 'w' (write) mode for new files; 'a' (append) mode for existing files
    write_mode = 'w' if not file_exists else 'a'

    # Execute file operation with determined parameters
    df.to_csv(output_file, mode=write_mode, header=include_header, index=False)

def process_password_expiration_check(users_df: pd.DataFrame):
    print("checking if password is about to expire")

    #Converts the string date into a date time format
    users_df['Password Expiration'] = pd.to_datetime(users_df['Password Expiration'], errors='coerce') 
    
    #Converts the date time format back into a string but in the format of month/day/year. This is necessary for the is_password_expiring_soon function to work properly because it expects the date to be in this format.
    users_df['Password Expiration'] = users_df['Password Expiration'].dt.strftime('%m/%d/%Y') 
    
    for index, row in users_df.iterrows(): #Iterates through each row of the users dataframe
        username = row['Username']
        user_email = row['Email Address']     
        password_expiration_str = row['Password Expiration'] #gets the password expiration date as a string
        password_expired = is_password_expiring_soon(password_expiration_str, PASSWORD_REMINDER_THRESHOLD) #calls the is_password_expiring_soon function to check if the password is expiring soon based on the password expiration date and the password reminder threshold defined in the config file.
       
        # if password_expired: #if the password is expiring soon, print a message to the console. This is where you would call the function to send reminder emails to users with expiring passwords.
        #     #start email process here


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
    

def send_password_expiration_email(username:str, user_email:str, password_expiration_date:str, application:str, district:str):
    #email sending process would go here. You would use the username, user_email, and password_expiration_date variables to personalize the email message and send it to the user.
    pass

if __name__ == "__main__":

    print("Start Password Project")

    CONFIG_FILE = config_setup() #sets up the config file and returns the config settings
    logging_setup(CONFIG_FILE) #sets up the logging configuration. Info and error messages will be written to this file

    INPUT_DIR = CONFIG_FILE['INPUT_FOLDER_PATH']['parent_districts_dir'] #gets the input file path from the config file
    OUTPUT_FILE = CONFIG_FILE['OUTPUT_FOLDER_PATH']['output_file'] #gets the output file path from the config file

    PASSWORD_REMINDER_THRESHOLD = int(CONFIG_FILE['PASSWORD_REMINDER']['password_reminder_threshold']) #gets the password reminder threshold from the config file. This is the number of days before a password expires that a reminder email will be sent to the user.

    #iterates through each district directory in the input directory
    for district in Path(INPUT_DIR).iterdir():

        district_name = str(district.name) #gets the name of the district, for example, District 1

        print(f"Processing {district.name}")
        logging.info(f"Processing {district.name}")     
        files_list = os.listdir(district) #gets a list of all the files a district's directory. For example, it will list USAS users.csv and USPS users.csv in the District 1 directory
        
        for file in files_list:
            input_file_path = os.path.join(district, file) #gets the file path for each file in the district directory. Password Reminder Project - Easy\input\District 1\USAS users.csv
            print(f"Processing {input_file_path} file")
            logging.info(f"Processing {file} file")
            application_name = file.split(" ")[0] #gets the application name from the file name. For example, it will get USAS from USAS users.csv. THIS ONLY WORKS IF USAS OR USPS IS THE FIRST PART OF THE FILE NAME. IF THERE ARE OTHER FILES IN THE DISTRICT DIRECTORIES THIS MAY CAUSE AN ISSUE.
            process_file(input_file_path, district_name, application_name) #calls the process_file function to read the csv file into a dataframe, add the application and district columns, and overwrite the source csv file with the new columns.

            
