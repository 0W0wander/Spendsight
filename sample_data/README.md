# Sample Data

This directory can contain sample CSV files for testing.

## Creating Test Data

If you want to test Spendsight without your real bank data, you can create sample CSV files here.

### Sample Chase CSV Format

Create a file named `chase_sample.csv`:

```csv
Transaction Date,Post Date,Description,Category,Type,Amount,Memo
01/15/2025,01/16/2025,STARBUCKS,Food & Dining,Sale,-5.67,
01/14/2025,01/15/2025,AMAZON.COM,Shopping,Sale,-45.99,
01/13/2025,01/14/2025,WHOLE FOODS,Groceries,Sale,-87.34,
01/12/2025,01/13/2025,SHELL GAS,Gas,Sale,-52.00,
01/10/2025,01/11/2025,NETFLIX,Entertainment,Sale,-15.99,
01/05/2025,01/06/2025,PAYCHECK,Income,Payment,3500.00,
```

### Sample Discover CSV Format

Create a file named `discover_sample.csv`:

```csv
Trans. Date,Post Date,Description,Amount,Category
01/15/2025,01/16/2025,TARGET,-89.45,Merchandise
01/14/2025,01/15/2025,CHIPOTLE,-12.87,Restaurants
01/13/2025,01/14/2025,CVS PHARMACY,-23.56,Services
01/12/2025,01/13/2025,UBER,-18.32,Transportation
01/10/2025,01/11/2025,SPOTIFY,-9.99,Entertainment
```

## Notes

- Negative amounts = expenses
- Positive amounts = income/refunds
- Dates should be in MM/DD/YYYY format
- Make sure to use the exact column names as shown above

