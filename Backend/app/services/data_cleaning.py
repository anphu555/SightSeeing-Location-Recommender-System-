import pandas as pd
import re

def clean_description(text):
    # Check if the cell is empty/NaN
    if pd.isna(text):
        return ""
    
    # Ensure text is a string
    text = str(text)
    
    # Replace one or more empty lines (and surrounding whitespace) with "|||"
    # \n\s*\n matches a newline, optional whitespace, and another newline
    return re.sub(r'(\n\s*\n)+', '|||', text).strip()

# 1. Read the CSV file
input_file = 'vietnam_tourism_data_copy.csv'
output_file = 'a_processed.csv'

try:
    df = pd.read_csv(input_file)

    # 2. Check if 'description' column exists to avoid errors
    if 'description' in df.columns:
        # Apply the function specifically to the 'description' column
        df['description'] = df['description'].apply(clean_description)
        
        # 3. Save the result to a new file
        # index=False prevents pandas from adding a new numbering column
        df.to_csv(output_file, index=False)
        print(f"Success! Processed data saved to {output_file}")
    else:
        print("Error: Column 'description' not found in the CSV.")

except FileNotFoundError:
    print(f"Error: The file {input_file} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")