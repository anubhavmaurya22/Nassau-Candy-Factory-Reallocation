<<<<<<< HEAD
# Nassau Candy Distributor — Factory Optimization Dashboard

## Setup (Windows PowerShell)

```powershell
cd nassau-candy
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Make sure `data/Nassau_Candy_Distributor.csv` is present (the raw dataset).

## Run the pipeline

```powershell
python src\data_prep.py      # cleans data, joins factories, computes features -> data/processed.csv
python src\model.py          # trains + saves lead time and profit margin models -> models/
python src\optimizer.py      # generates full recommendation table -> outputs/recommendations.csv
```

## Run the dashboard

```powershell
cd app
streamlit run Home.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Project structure

```
nassau-candy/
├── data/               # raw + processed CSV
├── src/
│   ├── reference_data.py   # factory coords, product->factory map, modeling assumptions
│   ├── data_prep.py         # cleaning + feature engineering
│   ├── model.py              # trains lead-time & profit-margin models
│   └── optimizer.py          # scores every factory per product, generates recommendations
├── app/
│   ├── Home.py
│   ├── utils.py
│   └── pages/
│       ├── 1_Factory_Simulator.py
│       ├── 2_What_If_Analysis.py
│       ├── 3_Recommendation_Dashboard.py
│       └── 4_Risk_Impact_Panel.py
├── models/             # trained .pkl files
├── outputs/            # exported CSVs, charts
├── reports/            # research paper + executive summary
└── requirements.txt
```

## Key methodology notes (see research paper for full detail)

- **Date columns are corrupted by anonymization** — Order ID prefixes show
  2021-2024, Order Date shows 2024-2025, Ship Date shows 2026-2030. Raw
  `Ship Date - Order Date` is unusable (~1,320 day average). Lead time is
  instead derived from Ship Mode + a disclosed distance-based transit
  assumption (documented in `src/reference_data.py`).
- **Distance & shipping cost assumptions** are explicit, stated modeling
  choices (not measured facts), since the raw data has no real link
  between factory location and delivery speed/cost.
=======
# Nassau-Candy-Factory-Reallocation-Shipping-Optimization
>>>>>>> 23a58ba1bbc1030c79630b3d375b08f655bd8bd1
# Nassau-Candy-Factory-Reallocation
