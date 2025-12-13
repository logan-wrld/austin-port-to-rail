#!/usr/bin/env python3
"""
Convert railroad-nodes.csv from tab-separated format to proper CSV format.
Parses the data and outputs clean CSV with proper columns.
"""

import csv
import sys

def convert_railroad_nodes(input_file, output_file):
    """Convert tab-separated railroad nodes file to clean CSV."""
    
    # Define the expected columns
    columns = [
        'OBJECTID', 'FRANODEID', 'COUNTRY', 'STATE', 'STFIPS', 
        'CTYFIPS', 'STCYFIPS', 'FRADISTRCT', 'PASSNGR', 'PASSNGRSTN', 
        'BNDRY', 'x', 'y'
    ]
    
    rows_written = 0
    rows_skipped = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        writer = csv.writer(outfile)
        
        # Write header
        writer.writerow(columns)
        
        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                rows_skipped += 1
                continue
            
            # Split by tab
            parts = line.split('\t')
            
            # Skip header line if present
            if line_num == 1 and parts[0] == 'OBJECTID':
                continue
            
            # Skip lines that don't have enough data
            # The file has 13 columns but some might be empty
            if len(parts) < 3:
                rows_skipped += 1
                continue
            
            # Skip lines where first field is not a number (header or invalid)
            try:
                int(parts[0])
            except ValueError:
                rows_skipped += 1
                continue
            
            # Pad with empty strings to ensure we have 13 columns
            while len(parts) < 13:
                parts.append('')
            
            # Extract the 13 columns
            row = parts[:13]
            
            # Write the row
            writer.writerow(row)
            rows_written += 1
    
    return rows_written, rows_skipped


def main():
    input_file = 'railroad-nodes.csv'
    output_file = 'railroad-nodes-clean.csv'
    
    print(f"Converting {input_file} to {output_file}...")
    
    try:
        rows_written, rows_skipped = convert_railroad_nodes(input_file, output_file)
        print(f"✅ Conversion complete!")
        print(f"   Rows written: {rows_written:,}")
        print(f"   Rows skipped: {rows_skipped:,}")
        print(f"   Output file: {output_file}")
        
        # Show sample of output
        print(f"\n📋 Sample of converted data:")
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i < 6:  # Show header + 5 rows
                    print(f"   {row}")
                else:
                    break
                    
    except FileNotFoundError:
        print(f"❌ Error: Could not find {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
