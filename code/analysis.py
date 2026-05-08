"""
Analysis for policing feedback loop.
Produces descriptive stats, time series plots, scatter plot,
and three OLS regression models testing whether prior stops
predict future arrests independent of reported crime.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from statsmodels.formula.api import ols

df = pd.read_csv("data/ca_month_dataset.csv")


# DESCRIPTIVE STATISTICS - community-area-by-month level

print(f"Observations: {len(df):,}  (77 areas x 120 months)")
print(df[["crime_count", "arrest_count", "stops_count"]].describe().round(1))


# CITY-WIDE TIME SERIES - monthly totals aggregated across all 77 community areas

city = (
    df.groupby(["year", "month"])[["crime_count", "arrest_count", "stops_count"]]
    .sum()
    .reset_index()
)
city["date"] = pd.to_datetime(city[["year", "month"]].assign(day=1))

fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
fig.suptitle("Chicago Policing Data, 2016–2025 (City-Wide Monthly Totals)", fontsize=13)

series = [
    ("crime_count", "Reported Crime Incidents", "#2c7bb6"),
    ("arrest_count", "Arrests", "#d7191c"),
    ("stops_count", "Investigatory Stops (ISR)", "#1a9641"),
]
for ax, (col, label, color) in zip(axes, series):
    ax.plot(city["date"], city[col], color=color, linewidth=1.2)
    ax.set_ylabel(label, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.grid(axis="y", linestyle="--", alpha=0.4)

axes[-1].set_xlabel("Month")
plt.tight_layout()
plt.savefig("figures/timeseries_citywide.png", dpi=150)
plt.close()


# NEIGHBORHOOD SCATTER - average monthly stops vs arrests, colored by % Black residents

area_avg = df.groupby("community_area")[
    ["stops_count", "arrest_count", "pct_black"]
].mean()

fig, ax = plt.subplots(figsize=(7, 5))
sc = ax.scatter(
    area_avg["stops_count"],
    area_avg["arrest_count"],
    c=area_avg["pct_black"],
    cmap="RdYlBu_r",
    alpha=0.75,
    s=60,
    edgecolors="grey",
    linewidths=0.4,
)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label("% Black residents (ACS 2023)", fontsize=9)
ax.set_xlabel("Avg. Monthly Investigatory Stops")
ax.set_ylabel("Avg. Monthly Arrests")
ax.set_title(
    "Police Stops vs. Arrests by Community Area\n(Monthly averages, 2016–2025)",
    fontsize=11,
)
ax.grid(linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig("figures/scatter_stops_arrests.png", dpi=150)
plt.close()


# OLS REGRESSIONS - prior stops (t-1) predicting current arrests (t)
# drops first month of each area where lag is NaN

reg_df = df.dropna(subset=["stops_lag1", "arrest_lag1", "crime_lag1"])

# Model 1: stops only
m1 = ols("arrest_count ~ stops_lag1", data=reg_df).fit()

# Model 2: add lagged crime as control
m2 = ols("arrest_count ~ stops_lag1 + crime_lag1", data=reg_df).fit()

# Model 3: add demographic controls
m3 = ols(
    "arrest_count ~ stops_lag1 + crime_lag1 + pct_black + pct_poverty + population",
    data=reg_df,
).fit()
