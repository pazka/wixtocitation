import pandas as pd
from pandas import DataFrame, Series
import numpy as np
from datetime import date
import uuid

orig_data: DataFrame = pd.read_csv("raw_from_old_wix.csv", sep=',')
edited_data: DataFrame = pd.read_excel(
    "curated.xlsx", sheet_name="okcatalog_products (7)",  keep_default_na=False)

optionDescriptionTypes = {}
optionTitles = {}
done_ops = []

print(len(orig_data))
print(len(edited_data))
print(len(orig_data.columns.values))
print(len(edited_data.columns.values))


def utils_search_row_in(df, id) -> pd.Series | None:
    found = df[df['handleId'] == id]

    if not found.empty:
        return found.iloc[0]
    else:
        return None


def check_option_types_unicity(df: DataFrame):
    done_ops.append("checked 'optionName' and 'additionalInfoTitle' coherence")
    for col in df.columns:
        if "OptionName" in col:
            if len(df[col].unique()) > 1:
                print(f"Option type {col} is not unique : {df[col].unique()}")
        if "additionalInfoTitle" in col:
            if len(df[col].unique()) > 1:
                print(
                    f"additionalInfoTitle {col} is not unique : {df[col].unique()}")


def standardize_visible_values(df: DataFrame):
    done_ops.append("checked 'visible' values")
    df['visible'] = df['visible'].apply(lambda x: str(x).upper())


def get_deleted_lines(orig_data: DataFrame, edited_data: DataFrame) -> DataFrame:
    done_ops.append("found deleted lines")
    deleted_lines: DataFrame = DataFrame(data=[], columns=edited_data.columns)

    for index, orig_row in orig_data.iterrows():
        found = utils_search_row_in(edited_data, orig_row['handleId'])
        orig_row_df = pd.DataFrame([orig_row])
        if found is None:
            deleted_lines = pd.concat([deleted_lines, orig_row_df])

    return deleted_lines


def get_value_with_over_n_chars(df: DataFrame, valueName, n) -> DataFrame:
    res = DataFrame(data=[], columns=df.columns)
    for col in df.columns:
        if valueName.lower() in col.lower():
            for index, row in df.iterrows():
                if len(str(row[col])) > n:
                    print(f"Option value {row[col]} is too long")
                    res = pd.concat([res, pd.DataFrame([row])])

    done_ops.append(f"checked {valueName} length>{n}, found " + str(len(res)))
    return res


def add_delete_label_in(df: DataFrame) -> DataFrame:
    df['name'] = df['name'].apply(lambda x: "TO_DELETE_" + x)
    df['collection'] = f"TO_DELETE"


def shorten_at_n_char_field(df: DataFrame, field, n) -> DataFrame:
    for col in df.columns:
        if field.lower() in col.lower():
            df[col] = df[col].apply(lambda x: str(x)[:n])


def remove_empty_lines_to(df: DataFrame) -> DataFrame:
    done_ops.append("removed deleted lines by alessia")
    res = DataFrame(data=[], columns=df.columns)
    for index, row in df.iterrows():
        if row['handleId'] != '' or row['fieldType'] != '':
            res = pd.concat([res, pd.DataFrame([row])])

    return res

def add_missing_values_to_columns_to(df: DataFrame) -> DataFrame:
    done_ops.append("added dropdown,price to columns where it was empty")
    for col in df.columns:
        if "OptionType" in col and not df[col].empty:
            df[col] = "DROP_DOWN"
        if "price" in col and not df[col].empty:
            df[col] = "0"


def insert_create_handleId_to_empty_products_in(df: DataFrame) -> DataFrame:
    for index, row in df.iterrows():
        if row['handleId'] == '':
            row['handleId'] = 'auto_created_' + str(uuid.uuid4())
            row['name'] = '[NEW] ' + row['name']


def edit_line_returns_to_columns_to(df: DataFrame) -> DataFrame:
    for col in df.columns:
        if "description" in col.lower() and not df[col].empty:
            df[col] = df[col].apply(lambda x: str(x).replace('\n', '<br/>'))
        if "name" in col.lower() and not df[col].empty:
            df[col] = df[col].apply(lambda x: str(x).replace('\n', ''))


def remove_empty_fields_to_columns_to(df: DataFrame) -> DataFrame:
    for col in df.columns:
        df[col] = df[col].apply(lambda x: str(x).replace('<p></p>', ''))
        df[col] = df[col].apply(lambda x: str(x).replace('<span></span>', ''))
        df[col] = df[col].apply(lambda x: str(x).replace('<span><span>', ''))
        df[col] = df[col].apply(lambda x: str(x).replace('</span></span>', ''))


def dump_df_to_tmp(df: DataFrame, name: str):
    df.to_csv(f"tmp/{name}_{date.today()}.csv", index=False)

### PROCESSING ###

dump_df_to_tmp(orig_data, "orig_data")
dump_df_to_tmp(edited_data, "edited_data")


deleted = get_deleted_lines(orig_data, edited_data)
add_delete_label_in(deleted)


add_missing_values_to_columns_to(edited_data)
edit_line_returns_to_columns_to(edited_data)
remove_empty_fields_to_columns_to(edited_data)

over_50_char_values = get_value_with_over_n_chars(
    edited_data, "optionvalue", 50)
edited_data = remove_empty_lines_to(edited_data)

insert_create_handleId_to_empty_products_in(edited_data)
check_option_types_unicity(edited_data)
shorten_at_n_char_field(edited_data, "name", 80)
res = pd.concat([edited_data, deleted])
standardize_visible_values(res)

res.to_csv(f"dest/a_importer_avec_deleted_{date.today()}.csv", index=False)
over_50_char_values.to_csv(
    f"dest/a_importer_avec_valeurs_trop_longues_{date.today()}.csv", index=False)
with open('dest/done_ops.txt', 'w') as f:
    for op in done_ops:
        f.write("%s\n" % op)
