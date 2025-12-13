#!/usr/bin/env python3
"""
Fix dataset quality issues in the data/ folder.
- Backs up original files as *_old.csv
- Writes cleaned data to original file names
"""

import pandas as pd
import os
import shutil
import re

DATA_DIR = "data"


def backup_file(filename):
    """Rename original to _old suffix."""
    original = os.path.join(DATA_DIR, filename)
    backup = os.path.join(DATA_DIR, filename.replace('.csv', '_old.csv'))
    if os.path.exists(original):
        shutil.move(original, backup)
        print(f"  Backed up: {filename} -> {filename.replace('.csv', '_old.csv')}")
    return backup


def convert_european_decimal(value):
    """Convert European decimal format (comma) to standard (period)."""
    if pd.isna(value):
        return value
    if isinstance(value, str):
        # Replace comma with period for decimal
        return value.replace(',', '.')
    return value


def fix_logistics_data():
    """Fix logistics-data-merged.csv:
    - Convert European decimal formats
    - Drop empty cost columns
    - Standardize dates to YYYY-MM-DD
    """
    filename = "logistics-data-merged.csv"
    print(f"\nFixing {filename}...")

    # Read file as strings first to handle European decimals
    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, dtype=str)

    # Columns with European decimal format
    decimal_cols = ['Net Revenue', 'Weight (Kg)', 'Weight (Cubic)', 'Goods Value']

    for col in decimal_cols:
        if col in df.columns:
            df[col] = df[col].apply(convert_european_decimal)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop empty cost columns
    cost_cols = [
        'Costs_Date', 'Costs_Drive ID', 'Costs_KM Traveled',
        'Costs_Liters', 'Costs_Fuel', 'Costs_Maintenance', 'Costs_Fixed Costs'
    ]
    existing_cost_cols = [c for c in cost_cols if c in df.columns]
    df = df.drop(columns=existing_cost_cols)
    print(f"  Removed {len(existing_cost_cols)} empty cost columns")

    # Standardize date format (YYYY/MM/DD -> YYYY-MM-DD)
    if 'Date' in df.columns:
        df['Date'] = df['Date'].str.replace('/', '-')

    # Backup and save
    backup_file(filename)
    output_path = os.path.join(DATA_DIR, filename)
    df.to_csv(output_path, index=False)
    print(f"  Saved cleaned file: {filename}")


def remove_thousands_separator(value):
    """Remove comma thousands separator from numbers."""
    if pd.isna(value):
        return value
    if isinstance(value, str):
        # Remove commas that are thousands separators (not decimal points)
        # Pattern: digit,digit (thousands sep) vs digit.digit (decimal)
        cleaned = re.sub(r'(\d),(\d)', r'\1\2', value)
        return cleaned
    return value


def fix_truck_travel_times():
    """Fix truck-travel-times.csv:
    - Remove thousands separators from numeric columns
    - Fix Year column
    """
    filename = "truck-travel-times.csv"
    print(f"\nFixing {filename}...")

    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, dtype=str)

    # Columns with thousands separators
    numeric_cols = [
        'Year', '25th Percentile (minutes)',
        '50th Percentile (minutes)', '75th Percentile (minutes)'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(remove_thousands_separator)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert Year to integer
    if 'Year' in df.columns:
        df['Year'] = df['Year'].astype('Int64')  # nullable integer

    # Backup and save
    backup_file(filename)
    output_path = os.path.join(DATA_DIR, filename)
    df.to_csv(output_path, index=False)
    print(f"  Saved cleaned file: {filename}")


def fix_texas_rail_data():
    """Fix texas_rail_data.csv:
    - Convert from TSV to CSV format
    - Add proper headers (same schema as railroad-lines.csv)
    """
    filename = "texas_rail_data.csv"
    print(f"\nFixing {filename}...")

    # Get headers from railroad-lines.csv (same schema)
    ref_file = os.path.join(DATA_DIR, "railroad-lines.csv")
    ref_df = pd.read_csv(ref_file, nrows=0)
    headers = ref_df.columns.tolist()

    # Read as TSV without headers
    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, sep='\t', header=None, names=headers)

    # Backup and save as CSV
    backup_file(filename)
    output_path = os.path.join(DATA_DIR, filename)
    df.to_csv(output_path, index=False)
    print(f"  Converted TSV to CSV with headers: {filename}")


def main():
    print("=" * 50)
    print("Dataset Cleaning Script")
    print("=" * 50)

    fix_logistics_data()
    fix_truck_travel_times()
    fix_texas_rail_data()

    print("\n" + "=" * 50)
    print("Done! Original files backed up as *_old.csv")
    print("=" * 50)


if __name__ == "__main__":
    main()
