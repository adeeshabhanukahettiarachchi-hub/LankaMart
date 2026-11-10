# Power BI build guide

1. Open Power BI Desktop, then Get data, Text/CSV, and choose `data/powerbi_orders.csv`.
2. In Power Query set types: `order_date` = Date, `unit_price`, `discount_rate`, `sales_amount`, `profit` = Decimal number, `quantity`, `delivery_days`, `returned`, `late_delivery` = Whole number.
3. Create these measures (Modeling, New measure):

```
Total Sales   = SUM(powerbi_orders[sales_amount])
Total Profit  = SUM(powerbi_orders[profit])
Orders        = COUNTROWS(powerbi_orders)
Avg Order     = DIVIDE([Total Sales], [Orders])
Late Rate     = AVERAGE(powerbi_orders[late_delivery])
Return Rate   = AVERAGE(powerbi_orders[returned])
Profit Margin = DIVIDE([Total Profit], [Total Sales])
```

4. Build the page: six Card visuals (the measures above), a Line chart (Axis `order_date` by month, Values `Total Sales`), a Clustered bar (Axis `category`, Values `Total Sales`), a Clustered bar (Axis `region`, Values `Late Rate`), and a Table of recent orders.
5. Add Slicers for `category`, `region` and `order_date`.
6. Optional live route: install the SQLite ODBC driver, then Get data, ODBC, and read the `v_orders` view from `database/lankamart.db`.
7. Save as `LankaMart.pbix` and screenshot the finished report for your evidence folder.

To refresh after the data changes, re-run `python database/seed.py --reset` (rewrites both CSV files) and click Refresh in Power BI.
