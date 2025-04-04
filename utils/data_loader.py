import pandas as pd

# Define a function to get the most common value
def most_common(series):
    return series.mode()[0]

# Load datasets
lfs_file = "LFS-PUF-December-2023.csv"
income_expenditure_file = "Family Income and Expenditure.csv"

df_lfs = pd.read_csv(lfs_file)
df_income_expenditure = pd.read_csv(income_expenditure_file)

# Region name corrections
region_corrections = {
    "IVB - MIMAROPA": "IV-B - MIMAROPA",
    "IVA - CALABARZON": "IV-A - CALABARZON",
    "IX - Zasmboanga Peninsula": "IX - Zamboanga Peninsula",
    " ARMM": "ARMM",
    "Caraga": "Region XIII  (Caraga)"
}
df_income_expenditure["Region"] = df_income_expenditure["Region"].replace(region_corrections)

# Group income-expenditure data by region
df_income_expenditure_grouped = (
    df_income_expenditure
    .groupby("Region")
    .agg({
        "Total Household Income": "mean",
        "Total Food Expenditure": "mean",
        "Household Head Highest Grade Completed": most_common
    })
    .reset_index()
)

# Rename columns for better understanding
df_income_expenditure_grouped.columns = [
    "Region",
    "Mean Household Income",
    "Mean Household Expenditure",
    "Most Common HH Head Education"
]

# Clean and compute unemployment rate
df_lfs_clean = df_lfs.dropna(subset=["PUFNEWEMPSTAT"])
df_lfs_clean["PUFNEWEMPSTAT"] = df_lfs_clean["PUFNEWEMPSTAT"].astype(str).str.strip()
df_lfs_clean = df_lfs_clean[df_lfs_clean["PUFNEWEMPSTAT"].str.isnumeric()]
df_lfs_clean["PUFNEWEMPSTAT"] = df_lfs_clean["PUFNEWEMPSTAT"].astype(int)

# Calculate unemployment rate
labor_force = df_lfs_clean.groupby("PUFREG")["PUFNEWEMPSTAT"].count()
unemployed = df_lfs_clean[df_lfs_clean["PUFNEWEMPSTAT"].isin([2, 3])].groupby("PUFREG")["PUFNEWEMPSTAT"].count()
unemployed = unemployed.reindex(labor_force.index, fill_value=0)
unemployment_rate = (unemployed / labor_force) * 100

# Prepare the unemployment data
df_unemployment = unemployment_rate.reset_index()
df_unemployment.columns = ["Region_Code", "Unemployment Rate"]

# Mapping of region codes to region names
region_mapping = {
    13: "NCR", 14: "CAR", 1: "I - Ilocos Region", 2: "II - Cagayan Valley",
    3: "III - Central Luzon", 4: "IV-A - CALABARZON", 17: "IV-B - MIMAROPA",
    5: "V - Bicol Region", 6: "VI - Western Visayas", 7: "VII - Central Visayas",
    8: "VIII - Eastern Visayas", 9: "IX - Zamboanga Peninsula", 10: "X - Northern Mindanao",
    11: "XI - Davao Region", 12: "XII - SOCCSKSARGEN", 16: "Region XIII  (Caraga)", 19: "ARMM"
}

# Map region codes to region names in the unemployment data
df_unemployment["Region"] = df_unemployment["Region_Code"].map(region_mapping)
df_unemployment = df_unemployment.drop(columns=["Region_Code"], errors="ignore")

# Merge datasets
df_final_combined = pd.merge(df_income_expenditure_grouped, df_unemployment, on="Region", how="outer")

# Clean up and sort the merged dataset
df_final_cleaned = df_final_combined[df_final_combined["Unemployment Rate"].notna()]
df_final_cleaned = df_final_cleaned.sort_values(by="Mean Household Income", ascending=False)

# Print the cleaned final dataframe for inspection
print(df_final_cleaned.head())

def get_final_dataframes():
    return df_final_cleaned


