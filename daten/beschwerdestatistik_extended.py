import pathlib

import pandas as pd

PATH = pathlib.Path(__file__).parent

TYPES = ["Kranken", "Leben", "Unfall"]
YEARS = list(range(2008, 2023))

SYNONYMS = {
    "Kranken": ["Kranken", "BeschwKrank", "Bestand_Kranken", "Beschw_Kranken"],
    "Leben": ["Leben", "BeschwLeben", "Bestand_Leben", "Beschw_Leben", "Leben "],
    "Unfall": ["Unfall", "BeschwUnfall", "Bestand_Unfall", "Beschw_Unfall"],
}


def extract(year: int, type_: str):
    # Discover file
    try:
        data_file = next((PATH / "rohdaten").glob(f"*{year}*"))
    except StopIteration:
        raise FileNotFoundError(f"Could not find a file for the year {year}.")

    # Discover the sheet name
    for sheet_name in SYNONYMS[type_]:
        try:
            df = pd.read_excel(data_file, sheet_name=sheet_name)
        except ValueError:
            print(f"No sheet {sheet_name} in {year}")
        else:
            print(
                f"Found sheet for '{type_}' in '{data_file}' for {year}: {sheet_name}"
            )
            break
    else:
        raise ValueError(f"Could not find a sheet for '{type_}' in '{data_file}'.")

    # Discover where the data starts
    for header_row in range(0, 5):
        df = pd.read_excel(data_file, sheet_name=sheet_name, header=header_row)
        if not df.empty:
            if "Beschwerden" in df.columns:
                break
            if "Anz. Beschwerden" in df.columns:
                df = df.rename(columns={"Anz. Beschwerden": "Beschwerden"})
                break
    else:
        raise ValueError(
            f"Could not find data in sheet '{sheet_name}' in '{data_file}'."
        )

    # Identify column names
    columns = list(df.columns)
    beschwerden_idx = columns.index("Beschwerden")
    reg_column = columns[beschwerden_idx - 3]
    name_column = columns[beschwerden_idx - 2]
    bestand_column = columns[beschwerden_idx - 1]

    # Select relevant columns and unify names
    df = df[[reg_column, name_column, bestand_column, "Beschwerden"]]
    df = df.rename(
        columns={reg_column: "Reg-Nr.", name_column: "Name", bestand_column: "Bestand"}
    )

    # Remove rows with unknown Bestand values
    df = df[~df["Bestand"].isin(("k.A.", "k.A. ", "k. A.", "k. A. "))]
    df = df.dropna()

    # Change types
    df = df.astype({"Reg-Nr.": int, "Beschwerden": int, "Bestand": int, "Name": str})

    # Add meta information
    df["Typ"] = type_
    df["Jahr"] = year

    return df


if __name__ == "__main__":
    dfs = [extract(year, type_) for year in YEARS for type_ in TYPES]

    df_full = pd.concat(dfs).reset_index().drop(columns="index")

    print(df_full.head())
    print(df_full.dtypes)

    df_full.to_excel(PATH / "beschwerdestatistik_komplett.xlsx")
    df_full.to_csv(PATH / "beschwerdestatistik_komplett.csv")
