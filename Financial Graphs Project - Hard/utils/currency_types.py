from enum import Enum

"""An enum type used to determine which dollar amount column in a dataframe to filter down by. 
The headers in initial csv file must spelled and have the same capitilizations as below. If there is a difference it will cause an error
"""
class CurrencyType(Enum):
    Revenue = "MTD Received"
    Expended = "MTD Expended"
    Balances = "Month End Balance"

