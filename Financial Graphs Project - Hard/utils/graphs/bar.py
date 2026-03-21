import logging
from logging import exception
import pandas as pd
from pandas import DataFrame

from openpyxl import Workbook, worksheet
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.utils.dataframe import dataframe_to_rows

from ..base_chart import BaseChart
from ..data_processing import format_to_currency, auto_adjust_column_width, create_pivot_dataframe, sort_fiscal_years_by_months
from ..currency_types import CurrencyType


#allows logging to be used in this file
logger = logging.getLogger(__name__)

class BarGraph(BaseChart):

    width = 34
    height = 10

    def __init__(self, district_code:str, input_file:str, input_df:DataFrame, workbook:Workbook, account_code:str):
        super().__init__(district_code, input_file, input_df, workbook, account_code)


    def create_chart(self, chart_title:str, current_ws:worksheet, currency_type:CurrencyType):
        """Creates a bar chart by reading the dataframe. 
        It takes a dataframe that contains multiple fiscal years with each month's information in it and creates a 'pivot' dataframe.
        It writes the dataframe row by row to a spreadsheet and uses that data to create the chart.
        The chart will display dollar amounts for each month in a fiscal year for multiple fiscal years.

        Args:
            df (DataFrame): a sorted pivot dataframe. The fiscal years must be in column 1 while the months must be in row 1
            current_ws (worksheet): The current worksheet the data and chart will be added to.
            data_type (str): Currency Type determines the title of the chart
        """

        pivot_df = create_pivot_dataframe(self.input_df, currency_type) #creates a pivot dataframe where the fiscal years are rows and each month is a column
        sorted_df = sort_fiscal_years_by_months(pivot_df) #This sorts the months by fiscal year order instead of alphabetical order
      
        ws = current_ws
        ws.title = currency_type.value

        #adds data row by row from the dataframe into the spreadsheet
        for row in dataframe_to_rows(sorted_df, index=True, header=True):
            ws.append(row)

        auto_adjust_column_width(ws) #adjust column sizes to fit all numbers
        format_to_currency(ws, min_column=2) #makes each number in the worksheet into currency format starting a column 2. Column 1 is the fiscal year's. Those should not be in currency format

        chart = BarChart() #uses openpyxl bar chart library

        chart.title = chart_title  
        chart.legend.position = 'tr' #positions the legend to the top right corner of the chart
        chart.layout = Layout(ManualLayout(x = 0, y = 0, h = 0.9, w = 0.9)) #This shrinks the graph slightly so the legend does not overlap the actualy chart

        #set the chart height and width
        chart.width = self.width
        chart.height = self.height
        
        # Add tick marks to the x-axis
        chart.x_axis.majorTickMark = "out"  # "in", "out", "cross", "none"
        chart.x_axis.minorTickMark = "out" # "in", "out", "cross", "none"

        chart.x_axis.delete = False #enables the x axis labels - Months
        chart.y_axis.delete = False #enables the y axis labels - Dollar amount
    
        #chart's data that was written to the spreadsheet
        months_only = Reference(ws, min_row=1, max_row=1, min_col=2, max_col=ws.max_column) #the range of months from July to June as a column range. Columns B1 to M1
        data_only = Reference(ws, min_col=1, max_col=13, min_row=3, max_row = ws.max_row) # Includes all cells from B3 to M6. Does NOT include month names header row

        chart.add_data(data_only, from_rows=True, titles_from_data=True)  #This gets all data except month names. Includes year and that years data
        chart.set_categories(months_only) #This sets the categories as the months in fiscal year order
        
        #These 2 lines of code turn the bar chart into a stacked bar chart. Currently disabled
        # chart.grouping = "stacked"
        # chart.overlap = 100

        ws.add_chart(chart, "A8") #adds the chart to the spreadsheet
        print("\t\t\tFinished creating " + str(currency_type.value) + " bar chart for district: " + self.district_code + " and account code: " + self.account_code)
        logging.info("  Finished creating " + str(currency_type.value) + " bar chart for district: " + self.district_code + " and account code: " + self.account_code)

