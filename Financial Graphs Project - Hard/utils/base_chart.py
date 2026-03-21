from abc import ABC, abstractmethod

import pandas as pd
from pandas import DataFrame
from openpyxl import Workbook, worksheet
from utils.currency_types import CurrencyType


class BaseChart(ABC):
    def __init__(self, district_code:str, input_file:str, input_df:DataFrame, workbook:Workbook, account_code:str): #I could probably remove either the input file or input_df since they contain the same information
        
        self.district_code = district_code
        self.input_file = input_file
        self.input_df = input_df #I could probably remove this since the input file and account code are arguments.
        self.workbook = workbook
        self.account_code = account_code

    @abstractmethod
    def create_chart(self, chart_title:str, current_ws:worksheet, currency_type:CurrencyType):
        pass





