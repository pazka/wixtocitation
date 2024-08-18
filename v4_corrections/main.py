import pandas as pd
from pandas import DataFrame, Series
import numpy as np
from datetime import date
import uuid
import os


orig_data: DataFrame = pd.read_csv(
    "catalog_products (virgule).csv", sep=',',  keep_default_na=False, encoding='utf-8')

orig_data.to_csv("new_catalog_products (virgule).csv",encoding='utf-8')