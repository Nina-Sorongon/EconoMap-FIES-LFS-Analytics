# utils.py

import pandas as pd


# Define a function to get the most common value
def most_common(series):
    return series.mode()[0]

# Define the preprocess_data function
def preprocess_data(df_income_expenditure, df_unemployment, region_mapping):
    # Region name corrections (add any additional corrections if needed)
    region_corrections = {
        "IVB - MIMAROPA": "IV-B - MIMAROPA",
        "IVA - CALABARZON": "IV-A - CALABARZON",
        "IX - Zasmboanga Peninsula": "IX - Zamboanga Peninsula",
        " ARMM": "ARMM",
        "Caraga": "Region XIII  (Caraga)"
    }

    # Apply region corrections
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

    # Clean and compute unemployment rate from the LFS data
    df_lfs_clean = df_unemployment.dropna(subset=["PUFNEWEMPSTAT"])
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

    # Merge datasets on the 'Region' column
    df_final_combined = pd.merge(df_income_expenditure_grouped, df_unemployment, on="Region", how="outer")

    # Clean up and sort the merged dataset
    df_final_cleaned = df_final_combined[df_final_combined["Unemployment Rate"].notna()]
    df_final_cleaned = df_final_cleaned.sort_values(by="Mean Household Income", ascending=False)

    # Return the final cleaned DataFrame
    return df_final_cleaned


def create_bivariate_bins(df_final_cleaned):
    """
    Create bivariate bins based on education and income levels.
    """
    # Binning Household Income into 3 categories: Low, Medium, High
    df_final_cleaned['Binned Household Income'] = pd.qcut(
        df_final_cleaned['Mean Household Income'],
        q=3,  # 3 quantiles => 3 bins
        labels=['Low', 'Medium', 'High']
    )

    # Map education levels and income bins to numeric values for bivariate analysis
    education_map = {
        "Elementary Graduate": 0.25,
        "High School Graduate": 0.50,
        "College Graduate": 0.75
    }

    income_map = {
        "Low": 0.25,
        "Medium": 0.50,
        "High": 0.75
    }

    df_final_cleaned["EduVal"] = df_final_cleaned["Most Common HH Head Education"].map(education_map)
    df_final_cleaned["IncVal"] = df_final_cleaned["Binned Household Income"].map(income_map)

    # Create a function to get the bivariate choropleth color code
    def get_bivariate_choropleth_color_tester(p1, p2):
        percentile_bounds1 = [0.33, 0.66, 1]
        percentile_bounds2 = [0.33, 0.66, 1]
        count = 0
        for p1_bound in percentile_bounds1:
            for p2_bound in percentile_bounds2:
                if p1 <= p1_bound and p2 <= p2_bound:
                    return count
                count += 1
        return -1  # If no match, return -1

    df_final_cleaned["Bivariate Numeric Code"] = df_final_cleaned.apply(
        lambda row: get_bivariate_choropleth_color_tester(row["EduVal"], row["IncVal"]),
        axis=1
    )

    # Map numeric codes to bivariate color bins
    numeric_to_bin = {
        0: "A1", 1: "A2", 2: "A3",
        3: "B1", 4: "B2", 5: "B3",
        6: "C1", 7: "C2", 8: "C3",
        -1: "ZZ"
    }

    df_final_cleaned["Bivariate Bin"] = df_final_cleaned["Bivariate Numeric Code"].map(numeric_to_bin)

    return df_final_cleaned
