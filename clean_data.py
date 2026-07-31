import pandas as pd
import numpy as np

df = pd.read_csv('/mnt/user-data/outputs/messy_customer_data.csv')
print(f"Starting shape: {df.shape}")

# ------------------------------------------------------------------
# 0. Remove duplicate rows first (exact dupes injected in generation)
# ------------------------------------------------------------------
df = df.drop_duplicates()
print(f"After dropping exact duplicates: {df.shape}")

# ------------------------------------------------------------------
# 1. customer_id — no nulls expected, just make sure it's clean int
# ------------------------------------------------------------------
df['customer_id'] = pd.to_numeric(df['customer_id'], errors='coerce').astype('Int64')

# ------------------------------------------------------------------
# 2. full_name — strip, title-case, fill nulls
# ------------------------------------------------------------------
df['full_name'] = (
    df['full_name']
    .str.strip()
    .str.title()
)
df['full_name'] = df['full_name'].fillna('Not Provided')

# ------------------------------------------------------------------
# 3. age — coerce to numeric, business rule: valid range 0-120
# ------------------------------------------------------------------
df['age'] = pd.to_numeric(df['age'], errors='coerce')
df.loc[(df['age'] < 0) | (df['age'] > 120), 'age'] = np.nan   # invalid outliers -> NaN, not fabricated
df['age'] = df['age'].astype('Int64')  # nullable int, no fill (per your original rule: "No fill")

# ------------------------------------------------------------------
# 4. gender — normalize, THEN fillna (order matters)
# ------------------------------------------------------------------
map_gender = {'M': 'Male', 'm': 'Male', 'F': 'Female', 'f': 'Female'}
df['gender'] = (
    df['gender']
    .str.strip()
    .replace(map_gender)
    .fillna('Not Provided')
)

# ------------------------------------------------------------------
# 5. email — fix known text errors, validate, FLAG (don't drop rows)
# ------------------------------------------------------------------
df['email'] = df['email'].str.replace(r'\s+at\s+', '@', case=False, regex=True)
df['email'] = df['email'].str.strip().str.lower()

email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
df['is_valid_email'] = df['email'].str.contains(email_regex, regex=True, na=False)

# business rule: keep the row, just mark bad/missing emails instead of deleting customer data
df.loc[~df['is_valid_email'], 'email'] = 'Not Provided'

# ------------------------------------------------------------------
# 6. phone_number — strip to digits only, fill
# ------------------------------------------------------------------
df['phone_number'] = df['phone_number'].astype(str).str.strip()
df['phone_number'] = df['phone_number'].replace(['nan', 'None', 'NULL', 'unknown'], np.nan)
df['phone_number'] = df['phone_number'].str.replace(r'\D', '', regex=True)
df.loc[df['phone_number'] == '', 'phone_number'] = np.nan
df['phone_number'] = df['phone_number'].fillna('Not Provided')

# ------------------------------------------------------------------
# 7. country — normalize with map, THEN fillna, fix Deutschland bug
# ------------------------------------------------------------------
country_map = {
    'United States of America': 'United States Of America',
    'United States': 'United States Of America',
    'U.S.': 'United States Of America',
    'USA': 'United States Of America',
    'usa': 'United States Of America',
    'UK': 'United Kingdom',
    'Uk': 'United Kingdom',
    'england': 'United Kingdom',
    'S. Africa': 'South Africa',
    'RSA': 'South Africa',
    'south africa': 'South Africa',
    'france': 'France',
    'germany': 'Germany',
    'Deutschland': 'Germany',   # was mapping to itself before — bug fix
}
df['country'] = (
    df['country']
    .str.strip()
    .replace(country_map)
    .fillna('Not Provided')
)

# ------------------------------------------------------------------
# 8. zip_code — safe float -> string conversion (avoids "12345.0" bug)
# ------------------------------------------------------------------
def clean_zip(x):
    if pd.isna(x):
        return np.nan
    try:
        return str(int(float(x)))
    except (ValueError, TypeError):
        return str(x).strip()

df['zip_code'] = df['zip_code'].apply(clean_zip)
df['zip_code'] = df['zip_code'].fillna('Not Provided')

# ------------------------------------------------------------------
# 9 & 10. dates — mixed format parse, coerce errors instead of crashing
# ------------------------------------------------------------------
df['signup_date'] = pd.to_datetime(df['signup_date'], format='mixed', errors='coerce')
df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'], format='mixed', errors='coerce')

# "0000-00-00" and "N/A" strings become NaT automatically via errors='coerce'
df['signup_date'] = df['signup_date'].dt.strftime('%Y-%m-%d')
df['last_purchase_date'] = df['last_purchase_date'].dt.strftime('%Y-%m-%d')

# ------------------------------------------------------------------
# 11. product_category — title case, fill
# ------------------------------------------------------------------
df['product_category'] = (
    df['product_category']
    .str.strip()
    .str.title()
    .fillna('Not Provided')
)

# ------------------------------------------------------------------
# 12. purchase_amount — strip currency text, coerce, reject negatives
# ------------------------------------------------------------------
df['purchase_amount'] = pd.to_numeric(
    df['purchase_amount'].astype(str).str.strip().str.replace(r'[A-Za-z\$, ]', '', regex=True),
    errors='coerce'
)
df.loc[df['purchase_amount'] < 0, 'purchase_amount'] = np.nan  # negative price isn't valid

# ------------------------------------------------------------------
# 13. annual_salary — same treatment, reject negatives and 0
# ------------------------------------------------------------------
df['annual_salary'] = pd.to_numeric(
    df['annual_salary'].astype(str).str.strip().str.replace(r'[A-Za-z\$, ]', '', regex=True),
    errors='coerce'
)
df.loc[df['annual_salary'] <= 0, 'annual_salary'] = np.nan

# ------------------------------------------------------------------
# 14. satisfaction_rating — coerce, enforce valid 1-5 range, round to 1dp
# ------------------------------------------------------------------
df['satisfaction_rating'] = pd.to_numeric(df['satisfaction_rating'], errors='coerce')
df.loc[(df['satisfaction_rating'] < 1) | (df['satisfaction_rating'] > 5), 'satisfaction_rating'] = np.nan
df['satisfaction_rating'] = df['satisfaction_rating'].round(1)

# ------------------------------------------------------------------
# 15. is_subscribed — fix dict syntax bug + fix order-of-operations bug
# ------------------------------------------------------------------
map_is_subscribed = {
    'NO': 'No', 'N': 'No', '0': 'No', 'FALSE': 'No',
    'YES': 'Yes', 'Y': 'Yes', '1': 'Yes', 'TRUE': 'Yes',
}
df['is_subscribed'] = (
    df['is_subscribed']
    .astype(str)
    .str.strip()
    .str.upper()          # normalize case FIRST
    .replace(map_is_subscribed)  # THEN map (keys are uppercase to match)
)
df['is_subscribed'] = df['is_subscribed'].replace('NAN', np.nan).fillna('Not Provided')

# ------------------------------------------------------------------
# 16. notes — fill nulls, clean whitespace-only strings too
# ------------------------------------------------------------------
df['notes'] = df['notes'].astype(str).str.strip()
df.loc[df['notes'].isin(['', 'nan', 'NULL', 'None']), 'notes'] = np.nan
df['notes'] = df['notes'].str.title()
df['notes'] = df['notes'].fillna('-')

# ------------------------------------------------------------------
# 17. loyalty_points — coerce to float, strip junk characters
# ------------------------------------------------------------------
df['loyalty_points'] = pd.to_numeric(
    df['loyalty_points'].astype(str).str.strip().str.replace(r'[A-Za-z\$, -]', '', regex=True),
    errors='coerce'
)

# ------------------------------------------------------------------
# Drop the helper validation column if you don't want it in final output
# (keeping it here is often useful for QA / audit purposes)
# ------------------------------------------------------------------
# df = df.drop(columns=['is_valid_email'])

print(f"\nFinal shape: {df.shape}")
print("\nNull counts after cleaning:")
print(df.isnull().sum())

out_path = '/mnt/user-data/outputs/cleaned_customer_data.csv'
df.to_csv(out_path, index=False)
print(f"\nSaved cleaned file to {out_path}")
