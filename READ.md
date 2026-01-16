# Agent 02: Trade Spend Auditor 📊

## Business Problem
In CPG (Consumer Packaged Goods), sales teams often negotiate "Trade Spend" (discounts and promotions) to secure shelf space. However, if these discounts are too deep, they can erode profit margins or violate company policy. 

**The Challenge:** Sales reps often use messy, non-standard product names (e.g., "kettle snacks" instead of "Kettle Cooked Jalapeno 8oz") and need real-time approval on complex margin math.

## The Solution
This Agent acts as a **Commercial "Logic Gate."** It ingests a master pricing database and evaluates incoming deal requests.

### Key Features:
- **Fuzzy Matching Engine:** Uses string similarity to map "messy" human input to exact SKU records in the CSV database.
- **Margin Logic Gate:** Calculates Net Price and Actual Margin % in real-time.
- **Policy Enforcement:** Automatically denies deals that exceed a 50% discount or fall below the minimum margin threshold.
- **Zero-Dependency Build:** Engineered using native Python libraries (`csv`, `os`) to ensure high portability and fast execution without heavy data overhead.

## Technical Architecture
The auditor follows a three-step process:
1. **Data Ingestion:** Loads `pricing_master.csv` from the `Shared_Assets` directory.
2. **Standardization:** Resolves the requested product name using a fuzzy-search algorithm.
3. **Audit:** Compares `List Price` vs. `COGS` to determine if the `Requested Discount` is financially viable.

## How to Run
Ensure you are in the project directory and run:
```bash
python3 main.py