from logging import exception
from typing import List
import pandas as pd
from pandas import DataFrame
import openpyxl
import csv
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import BarChart, Reference
import os

import logging

from utils.currency_types import CurrencyType

#Fiscal year order of months. DO NOT CHANGE!
MONTH_ORDER = {'July': 1, 'August': 2, 'September': 3, 'October': 4, 'November': 5, 'December': 6, 'January': 7, 'February': 8, 'March': 9, 'April': 10, 'May': 11, 'June': 12}

logger = logging.getLogger(__name__)

#not being used
def csv_to_excel(csv_file_path, excel_file_path):
    """
    reads data from a csv file and writes it to an excel file.

    args:
        csv_file_path (str): path to the input csv file.
        excel_file_path (str): path to the output excel file.
    """
    try:
        # read the csv file into a dataframe using pandas
        df = pd.read_csv(csv_file_path)
        
        # write the dataframe to an excel file using pandas with openpyxl as the engine
        df.to_excel(excel_file_path, index=False, engine='openpyxl')

        print(f"data successfully written to {excel_file_path}")
    except exception as e:
        print(f"an error occurred: {e}")


#is being used to create bar and line graphs
def create_pivot_dataframe(input_df:DataFrame, y_axis_value_header:CurrencyType) -> DataFrame:
    """Creates a dataframe of a csv file and shifts the data to look like a "pivot table".
    This format is necessary to make a bar/line chart within excel
    It will place each year in the fiscal year column as it's own column removing duplicates.
    It will make each month as it's own rows removing duplicates.
    It will then place each month's data in the month row and the correct year.

    Args:
        csv_file (str): csv file name of the input csv file
        y_axis_value_header (CurrencyType): Name of the header in the csv file for what kind of dollar amount the chart will be for. For example, MTD-Expended or MTD-Received
        The argument must match exactly what is in the csv file or else it will return an error
    """

    try:
        #create dataframe from csv file. Contains all data in the csv file
        #base_df = pd.read_csv(csv_file)

        #pivot_df = base_df.pivot(index="Month", columns="Fiscal-Year", values = "MTD Expended") #This option will have each row by a month and each column will be a fiscal year. The reverse of the next line. I keep this here in case I want to reverse the data frame
        
        #creates the pivot dataframe
        pivot_df = input_df.pivot(index="Fiscal-Year", columns="Month", values = y_axis_value_header.value) #sorts by year
        return pivot_df
    
    except Exception as e:
        logger.error(f"An error has occurred in creating the pivot dataframe: {e}")
        print(f"\tAn error has occurred in creating the pivot dataframe {e}")


#currently not being used
def copy_dataframe_to_excel(pivot_df:DataFrame, excel_file:str, workbook:Workbook):
    """Copies a dataframe in pivot format to an excel file row by row. Each row is a month and each column is a fiscal year.
    It writes the dataframe to the first worksheet in the excel file

    Args:
        pivot_df (DataFrame): "pivot table" formatted dataframe
        excel_file (str): .xlsx output file name. Need full file path
        workbook (Workbook): main excel worksheet that will show all data. Other worksheets will contain graphs 
    """

    ws = workbook.active
    ws.title = "All Data"

    for month, row in pivot_df.iterrows():
        ws.append([month] + list(row))  # Add data rows

    workbook.save(excel_file)


#Currently not being used. Basically creates a reverse of the current dataframe where each row is a month and each column is a fiscal year
def sort_by_months_in_fiscal_year(df:DataFrame)->DataFrame:
    """Sorts the dataframe by months in fiscal year order

    Args:
        df (DataFrame): pivot table like dataframe where months are the index in column 0 and fiscal years are in row 0 (labels)

    Returns:
        DataFrame: a sorted dataframe where each row is a month and each column is a fiscal year. The months are in fiscal year order instead of alphabetically
    """

    sorted_df = df.sort_index(key=lambda x: x.map(MONTH_ORDER))

    return sorted_df


def sort_fiscal_years_by_months(df:DataFrame)->DataFrame:
    """This takes a pivot dataframe where each month of a year are in it's own column.
    By default, each month is in alphabetical order. This function changes the columns to be in fiscal year order.
    Fiscal year order is where July is first and June is the last month.
    Uses constant MONTH_ORDER to get the fiscal year sort order

    Args:
        df (DataFrame): a pivot dataframe where each year is it's own row and each month is it's own column.

    Returns:
        DataFrame: a pivot dataframe that is now sorted in fiscal year order.
    """
  
    column_order = {} #empty dictionary
    for col in df.columns:
        month = col  # The column name is the month and it's data
        order = MONTH_ORDER.get(month)  # Get order or None if not a month
        if order is not None: #Only include months
            column_order[col] = order
        else:
            print(f"Warning: Column '{col}' is not a valid month. It will not be reordered.")

    #Sort the columns based on the fiscal year order:
    sorted_columns = sorted(column_order.keys(), key=column_order.get)

    #Reorder the columns in the DataFrame:
    sorted_df = df[sorted_columns]

    return sorted_df


def format_to_currency(worksheet, min_column):
    """Iterates through each cell in an Excel worksheet. If the cell contains an integer or a float number it will format the number into a currency.

    Args:
        worksheet (Worksheet): A worksheet in an existing Workbook
    """
    ws = worksheet


    for col in ws.iter_cols(min_col=min_column):  # Iterate through all columns
        for cell in col:  # Iterate through all cells in the column
            if isinstance(cell.value, (int, float)): # Check if the cell contains a number
                cell.number_format = '$#,##0.00' #formats number to two decimal places


def auto_adjust_column_width(worksheet):
    """Automatically adjusts the column width to fit the number in the cell

    Args:
        worksheet (Worksheet): A worksheet in an existing Workbook
    """
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        worksheet.column_dimensions[column_letter].width = adjusted_width

#   CURRENTLY NOT BEING USED
def create_monthly_dataframe(csv_file:str, y_axis_value_header:CurrencyType) -> DataFrame:
    """
    This function is currently not being used. It was used for testing purposes only.
    Creates a dataframe from a csv file where column 0 is the month and column 1 is the dollar amount.
    If the input csv file contains 4 years of data, then column 0 will contain 48 months and column 1 will contain 48 dollar amounts.
    This is the vertical format of the data. It is not a pivot table.
    Args:
        csv_file (str): input csv file name with the data in it. The csv file must contain the month and dollar amount.
        y_axis_value_header (CurrencyType): The currency type of the dollar amount. For example, MTD-Expended or MTD-Received.
        The argument must match exactly what is in the csv file or else it will return an error

    Returns:
        DataFrame: a dataframe where column 0 is the month and column 1 is the dollar amount.
    """
    try:
        base_df = pd.read_csv(csv_file)
        months = base_df['Month'].tolist()
        numbers = base_df[y_axis_value_header.value]
        headers = ['Month', str(y_axis_value_header.value)] #change Amount later
        data = {headers[0]:months, headers[1]: numbers}

        new_df = pd.DataFrame(data)
        
        #Todo - use this data frame to write the 48 months into a single row in and then the amounts in the next row
        #There should be 48 columns

        #pivot_df = base_df.pivot(columns="Month", values = "Month End Balance")
       
        return new_df

    except Exception as e:
        print(f"An error has occurred. {e}")
    


def format_input_file(input_csv_file:str, output_csv_file:str):
    """Formats the input CSV file and writes the formatted data to the output CSV file.

    Args:
        input_csv_file (str): Path to the input CSV file.
        output_csv_file (str): Path to the output CSV file.

    Returns:
        str: Path to the formatted output CSV file.
    """

    
    if not os.path.exists(input_csv_file):
        raise FileNotFoundError(f"Input file '{input_csv_file}' does not exist.")
        return

    # Ensure the output file exists or create it
    if not os.path.exists(output_csv_file):
        with open(output_csv_file, 'w') as f:
            print(f"Creating: {output_csv_file}")
            pass  # Create an empty file

    def remove_brackets(literal_data:str)-> str:
        """Strips the brackets and quotes from the string. It will also remove any spaces before or after the string.

        Args:
            literal_data (str): a string that contains brackets and quotes. For example: ['1', '2', '3']
            This string is pulled from a single cell in a csv file. It is NOT a row or column of data

        Returns:
            str: a string of text with no brackets or quotes. For example: 1, 2, 3
            Note: This function does not convert the string into a list. It just removes the brackets and quotes.
        """

        cleaned_data = literal_data.strip("[]'")  # Remove [] and potential surrounding quotes
        return cleaned_data
    

    def convert_to_list(literal_data:str)-> List[str]:
        """takes a string with commas in it and converts it to a list of strings.
        For example: '1, 2, 3' will be converted to ['1', '2', '3']
        It will also remove any spaces before or after the string.

        Args:
            literal_data (str): a string that contains commas. For example: '1, 2, 3'

        Returns:
            List[str]: a list of strings. For example: ['1', '2', '3']
        """
        string_list = [item.strip() for item in literal_data.split(',')] ## Split the string by commas and remove leading/trailing spaces
        return string_list


    try:
        print(f"\tFormatting input file {input_csv_file}")
        with open(input_csv_file, 'r', newline='') as infile, \
                open(output_csv_file, 'w', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            header = next(reader)
            output_header = header[:3] + ['MTD Received', 'MTD Expended', 'Month End Balance', 'Month', 'Fiscal-Year']
            writer.writerow(output_header)

            for row in reader:
                account_code = row[0] #does not need to be converted to a list. It is a single string         
                description = row[1] #does not need to be converted to a list. It is a single string
                active = row[2] #does not need to be converted to a list. It is a single string
               

                #months
                month_name_str = row[6]  #this does need to be converted to a list.
                temp_month_name = remove_brackets(month_name_str)
                month_name_list = convert_to_list(temp_month_name) #this is a list of month names. For example: ['July', 'August', 'September']

                #Received amounts
                mtd_received_str = row[3]  #this DOES need to be converted to a list.
                temp_received = remove_brackets(mtd_received_str)
                received_list = convert_to_list(temp_received)              
                
                #expended amounts
                mtd_expended_str = row[4]
                temp_expended = remove_brackets(mtd_expended_str)
                expended_list = convert_to_list(temp_expended)

                #month end balances
                month_end_balance_str = row[5]
                temp_balance = remove_brackets(month_end_balance_str)
                month_end_balance_list = convert_to_list(temp_balance)
             
             
                fiscal_year = row[7]

                for i in range(0,len(month_name_list)): #goes from 0 to 11. This is the number of months in a year
                    new_row = [account_code, description, active, received_list[i], expended_list[i], month_end_balance_list[i], month_name_list[i], fiscal_year]
                    writer.writerow(new_row)
        #print(f"\tcreating formatted file: {output_csv_file}")
        return output_csv_file
    
    except Exception as e:
        print(f"\tAn error occurred while formatting the file: {e}")
        







