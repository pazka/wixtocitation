import pandas as pd
from pandas import DataFrame, Series
import numpy as np
from datetime import date
import uuid
import os


orig_data: DataFrame = pd.read_csv(
    "catalog_products.csv", sep=',',  keep_default_na=False, encoding='utf-8')
edited_data: DataFrame = pd.read_excel(
    "labels-ad-db.xlsx",  keep_default_na=False)

columns_to_copy = []

edited_data["name"] = edited_data["name"].apply(lambda x: x.strip())
orig_data["visible"] = orig_data["visible"].apply(lambda x: str(x).upper())

for col in edited_data.columns:
    if 'additionalInfo' in col:
        columns_to_copy.append(col)

# add those columns to the original data
for col in columns_to_copy:
    if col not in orig_data.columns:
        orig_data[col] = None

for col in orig_data.columns:
    orig_data[col] = orig_data[col].apply(lambda x: x.replace(
        "\n", "<br/>") if type(x) == str else x)
    orig_data[col] = orig_data[col].apply(lambda x: x.replace(
        "<br>", "<br/>") if type(x) == str else x)
    orig_data[col] = orig_data[col].apply(lambda x: x.replace(
        "<br/><br/>", "<br/>") if type(x) == str else x)


for orig_index, original_row in orig_data.iterrows():
    orig_name = original_row['name'].replace("[NEW] ", "")
    if "TO_DELETE" in orig_name:
        continue
    found = False
    for edited_index, edited_row in edited_data.iterrows():
        if original_row['handleId'] == edited_row['handleId'] or orig_name == edited_row['name']:
            found = True
            for col in columns_to_copy:
                orig_data.at[orig_index,
                             col] = edited_data.at[edited_index, col]
            continue
    if not found:
        print(f"Could not find {original_row['name']} in edited data")


orig_data.to_csv("./dest/new_catalog_products.csv",
                 index=False, encoding='utf-8')
