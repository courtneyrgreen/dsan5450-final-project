"""
Community-area-by-month dataset builder for policing feedback loop analysis.
Unit of analysis: Chicago community area x month, 2016-2025.

Outputs: ca_month_dataset.csv with columns:
  community_area, year, month, crime_count, arrest_count, stops_count,
  crime_lag1, arrest_lag1, stops_lag1,
  + ACS demographic controls
"""

import glob
import os
import pandas as pd

DATA_DIR = "data"

# Standard Chicago community area number -> name mapping (1-77)
# Source: https://en.wikipedia.org/wiki/Community_areas_of_Chicago
COMMUNITY_AREA_NAMES = {
    1: "ROGERS PARK",
    2: "WEST RIDGE",
    3: "UPTOWN",
    4: "LINCOLN SQUARE",
    5: "NORTH CENTER",
    6: "LAKE VIEW",
    7: "LINCOLN PARK",
    8: "NEAR NORTH SIDE",
    9: "EDISON PARK",
    10: "NORWOOD PARK",
    11: "JEFFERSON PARK",
    12: "FOREST GLEN",
    13: "NORTH PARK",
    14: "ALBANY PARK",
    15: "PORTAGE PARK",
    16: "IRVING PARK",
    17: "DUNNING",
    18: "MONTCLARE",
    19: "BELMONT CRAGIN",
    20: "HERMOSA",
    21: "AVONDALE",
    22: "LOGAN SQUARE",
    23: "HUMBOLDT PARK",
    24: "WEST TOWN",
    25: "AUSTIN",
    26: "WEST GARFIELD PARK",
    27: "EAST GARFIELD PARK",
    28: "NEAR WEST SIDE",
    29: "NORTH LAWNDALE",
    30: "SOUTH LAWNDALE",
    31: "LOWER WEST SIDE",
    32: "LOOP",
    33: "NEAR SOUTH SIDE",
    34: "ARMOUR SQUARE",
    35: "DOUGLAS",
    36: "OAKLAND",
    37: "FULLER PARK",
    38: "GRAND BOULEVARD",
    39: "KENWOOD",
    40: "WASHINGTON PARK",
    41: "HYDE PARK",
    42: "WOODLAWN",
    43: "SOUTH SHORE",
    44: "CHATHAM",
    45: "AVALON PARK",
    46: "SOUTH CHICAGO",
    47: "BURNSIDE",
    48: "CALUMET HEIGHTS",
    49: "ROSELAND",
    50: "PULLMAN",
    51: "SOUTH DEERING",
    52: "EAST SIDE",
    53: "WEST PULLMAN",
    54: "RIVERDALE",
    55: "HEGEWISCH",
    56: "GARFIELD RIDGE",
    57: "ARCHER HEIGHTS",
    58: "BRIGHTON PARK",
    59: "McKINLEY PARK",
    60: "BRIDGEPORT",
    61: "NEW CITY",
    62: "WEST ELSDON",
    63: "GAGE PARK",
    64: "CLEARING",
    65: "WEST LAWN",
    66: "CHICAGO LAWN",
    67: "WEST ENGLEWOOD",
    68: "ENGLEWOOD",
    69: "GREATER GRAND CROSSING",
    70: "ASHBURN",
    71: "AUBURN GRESHAM",
    72: "BEVERLY",
    73: "WASHINGTON HEIGHTS",
    74: "MOUNT GREENWOOD",
    75: "MORGAN PARK",
    76: "O'HARE",
    77: "EDGEWATER",
}

NAME_TO_NUM = {v.upper().replace("'", ""): k for k, v in COMMUNITY_AREA_NAMES.items()}


# CRIMES - from CPD's Clear System Incident Reports 2016 - present """
def load_crimes():
    """Counts how many incidents happened per neighborhood per
    month twice, once for all incidents and once for just those
    that resulted in arrest (Arrest == True)
    """
    print("Loading crimes...")
    df = pd.read_csv(
        os.path.join(DATA_DIR, "crimes_2016-present.csv"),
        usecols=["Date", "Community Area", "Arrest"],
        parse_dates=["Date"],
    )
    df = df.dropna(subset=["Community Area"])
    df["community_area"] = df["Community Area"].astype(int)
    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month

    df = df[(df["year"] >= 2016) & (df["year"] <= 2025)]

    crime_counts = (
        df.groupby(["community_area", "year", "month"])
        .size()
        .reset_index(name="crime_count")
    )

    # Arrests with community area come from this same dataset (Arrest == True)
    arrest_counts = (
        df[df["Arrest"] == True]
        .groupby(["community_area", "year", "month"])
        .size()
        .reset_index(name="arrest_count")
    )

    print(f"  Crime rows: {len(crime_counts):,}  Arrest rows: {len(arrest_counts):,}")
    return crime_counts, arrest_counts


# POLICE ACTIVITY - from ISR Stop Report files (2016-2025)


def build_beat_to_community_map():
    """
    Reads crime data to build a mapping from police beats
    to community areas, then uses that mapping to aggregate ISR
    stop reports by community area and month (modal community area per beat).
    """

    print("Building beat -> community area mapping from crimes data...")
    df = pd.read_csv(
        os.path.join(DATA_DIR, "crimes_2016-present.csv"),
        usecols=["Beat", "Community Area"],
    )
    df = df.dropna()
    mapping = (
        df.groupby("Beat")["Community Area"].agg(lambda x: int(x.mode()[0])).to_dict()
    )
    print(f"  Mapped {len(mapping)} beats to community areas.")
    return mapping


def load_isr(beat_to_community):
    print("Loading ISR files...")
    isr_files = sorted(glob.glob(os.path.join(DATA_DIR, "isr", "????-ISR*.csv")))
    frames = []
    for path in isr_files:
        try:
            chunk = pd.read_csv(
                path,
                usecols=["CONTACT_DATE", "BEAT"],
                parse_dates=["CONTACT_DATE"],
                low_memory=False,
            )
            frames.append(chunk)
        except Exception as e:
            print(f"  Warning: could not load {path}: {e}")

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["BEAT"])
    df["BEAT"] = df["BEAT"].astype(int)
    df["community_area"] = df["BEAT"].map(beat_to_community)
    df = df.dropna(subset=["community_area"])
    df["community_area"] = df["community_area"].astype(int)
    df["year"] = df["CONTACT_DATE"].dt.year
    df["month"] = df["CONTACT_DATE"].dt.month
    df = df[(df["year"] >= 2016) & (df["year"] <= 2025)]

    stops = (
        df.groupby(["community_area", "year", "month"])
        .size()
        .reset_index(name="stops_count")
    )
    print(f"  ISR rows: {len(stops):,}")
    return stops


# DEMOGRAPHICS: ACS 5-year estimates by community area (2023-2025)
def load_acs():
    """
    loads ACS data, maps community area names to numeric codes, computes demographic shares, and returns a cleaned DataFrame with one row per community area.
    """
    print("Loading ACS...")
    df = pd.read_csv(os.path.join(DATA_DIR, "ACS_5_Year_Data_by_Community_Area.csv"))

    # Strip whitespace from community area names and map to numeric codes
    df["Community Area"] = (
        df["Community Area"].str.strip().str.upper().str.replace("'", "", regex=False)
    )
    df["community_area"] = df["Community Area"].map(NAME_TO_NUM)
    missing = df[df["community_area"].isna()]["Community Area"].tolist()
    if missing:
        print(f"  Warning: could not map ACS areas: {missing}")

    # Parse numeric columns (they come in as strings with commas)
    numeric_cols = [
        "Total Population",
        "Black or African American",
        "White Not Hispanic or Latino",
        "Hispanic or Latino",
        "Under $25,000",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", ""), errors="coerce"
        )

    # Compute shares
    pop = df["Total Population"].replace(0, pd.NA)
    df["pct_black"] = df["Black or African American"] / pop
    df["pct_white_nh"] = df["White Not Hispanic or Latino"] / pop
    df["pct_hispanic"] = df["Hispanic or Latino"] / pop
    df["pct_poverty"] = df["Under $25,000"] / pop

    acs = df[
        [
            "community_area",
            "Total Population",
            "pct_black",
            "pct_white_nh",
            "pct_hispanic",
            "pct_poverty",
        ]
    ].rename(columns={"Total Population": "population"})
    acs = acs.dropna(subset=["community_area"])
    acs["community_area"] = acs["community_area"].astype(int)
    print(f"  ACS rows: {len(acs)}")
    return acs


def build_dataset(crime_counts, arrest_counts, stops, acs):
    print("Building community-area-by-month dataset...")
    """ Merges crime counts, arrest counts, ISR stop counts, and 
        ACS demographics into a single DataFrame with one row per
        community area x month, then creates lagged variables for crime_count, 
        arrest_count, and stops_count.
    """

    # all community_area x year x month combinations
    years = range(2016, 2026)
    months = range(1, 13)
    areas = list(range(1, 78))
    skeleton = pd.MultiIndex.from_product(
        [areas, list(years), list(months)],
        names=["community_area", "year", "month"],
    ).to_frame(index=False)

    dataset = skeleton.merge(
        crime_counts, on=["community_area", "year", "month"], how="left"
    )
    dataset = dataset.merge(
        arrest_counts, on=["community_area", "year", "month"], how="left"
    )
    dataset = dataset.merge(stops, on=["community_area", "year", "month"], how="left")
    dataset = dataset.merge(acs, on="community_area", how="left")

    dataset[["crime_count", "arrest_count", "stops_count"]] = (
        dataset[["crime_count", "arrest_count", "stops_count"]].fillna(0).astype(int)
    )

    # Sort for lag creation
    dataset = dataset.sort_values(["community_area", "year", "month"]).reset_index(
        drop=True
    )

    # Lag variables (within community area)
    dataset["crime_lag1"] = dataset.groupby("community_area")["crime_count"].shift(1)
    dataset["arrest_lag1"] = dataset.groupby("community_area")["arrest_count"].shift(1)
    dataset["stops_lag1"] = dataset.groupby("community_area")["stops_count"].shift(1)

    print(f"  Dataset shape: {dataset.shape}")
    print(dataset.head())
    return dataset


if __name__ == "__main__":
    crime_counts, arrest_counts = load_crimes()
    beat_map = build_beat_to_community_map()
    stops = load_isr(beat_map)
    acs = load_acs()
    dataset = build_dataset(crime_counts, arrest_counts, stops, acs)

    out_path = os.path.join(DATA_DIR, "ca_month_dataset.csv")
    dataset.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")
    print(dataset.describe())
