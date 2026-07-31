# Python Data Cleaning Practice

A messy customer dataset and a full pandas cleaning pipeline that fixes every
issue in it — built to practice and demonstrate real-world data cleaning
techniques.

## Contents

| File | Description |
|---|---|
| `clean_data.py` | Cleans the messy dataset end-to-end and writes the cleaned output |
| `data/messy_customer_data.csv` | The raw, messy dataset (515 rows × 17 columns) |
| `data/cleaned_customer_data.csv` | The cleaned output after running `clean_data.py` |

## Issues present in the raw data

- Missing values across every column
- Duplicate rows and duplicate `customer_id`s
- Inconsistent string casing and whitespace (`"  John Smith  "`, `"JANE DOE"`)
- Inconsistent categorical labels (`"USA"` vs `"United States"` vs `"usa"`)
- Multiple date formats in the same column, plus junk values (`"N/A"`, `"0000-00-00"`)
- Invalid/out-of-range values (negative ages, salaries of -1000, ratings of 11)
- Currency-formatted numeric strings (`"$1,234.56"`, `"150 USD"`)
- Malformed emails (`"name at gmail.com"`) and inconsistent phone formats
- Mixed data types within a single column (`loyalty_points`: int, float, string, `"-"`)

## Usage

```bash
python clean_data.py
```

## Cleaning approach

The cleaning script follows a few core principles rather than just "fill
everything with something":

- **Don't fabricate certainty.** Invalid values (negative salary, out-of-range
  ratings) are converted to `NaN` rather than guessed at.
- **Fill nulls contextually.** Categorical/identity fields get an explicit
  `"Not Provided"` label instead of a statistical guess. Numeric fields are
  left null rather than silently defaulted to 0.
- **Flag instead of destroy.** Invalid emails are marked (`is_valid_email`)
  rather than dropping the entire customer row.
- **Fix order-of-operations bugs.** e.g. normalizing case *before* mapping
  values, so replacement dictionaries actually match.

## License

