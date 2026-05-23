# Biginerz Farm - Field Force Intelligence

Biginerz Farm is a modern, offline-first Field Force Intelligence platform. It empowers sales representatives with AI-driven insights to prioritize retailer visits, optimize territories, and maximize ROI even in areas with poor or intermittent network connectivity.

## Technology Stack
- **Backend:** FastAPI, Python, PostgreSQL (SQLAlchemy + async psycopg)
- **Frontend:** Vue 3, Vite, Pinia (State Management), Dexie.js (Offline-first IndexedDB)
- **Machine Learning:** Scikit-Learn (Gradient Boosting Regressor), Pandas, Joblib

---

## 1. Setup & Installation Requirements

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+**

### Database Setup (PostgreSQL)
1. Ensure PostgreSQL is running on your local machine or server.
2. Create a database named `new_db_biginerz` (or your preferred name in pgAdmin/psql).
3. Create a `.env` file in `backend/app/.env` (or rely on the defaults in `config.py`):
   ```env
   DATABASE_URL="postgresql+psycopg://postgres:1234@localhost:5432/new_db_biginerz"
   ```

### Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure `sqlalchemy`, `psycopg`, `pandas`, `scikit-learn`, and `joblib` are installed in your environment for the DB and ML features to function).*

4. Seed the database with initial data:
   ```bash
   # Ensure you are in the backend directory
   python seed.py --data-dir ../data
   ```

5. Generate and hash passwords for the seeded Reps and Retailers:
   ```bash
   python generate_passwords.py
   ```
   *(Note: By default, the seed script sets empty passwords. This script generates secure hashed passwords like `Syngenta@REP_0001` or `Syngenta@RTL_001` based on the ID).*

6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend API will run on `http://localhost:8000`.

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:5173`.



---

## 2. Machine Learning Pipeline: How It Predicts

BiginerzFarm utilizes an advanced Machine Learning pipeline to calculate a **Retailer Priority Score**. The model predicts the expected weekly revenue for each retailer and translates that into an actionable priority tier to guide the field force.

### A. Data Sources
The model aggregates data from multiple operational dimensions (usually stored in the `data/` folder):
- **POS/Sales Data:** Weekly sales quantities, transactions, average quantity per transaction, and recent sales growth rates.
- **Inventory Data:** Average inventory levels and stockout ratios.
- **Visit History:** Days since the last visit and weekly visit frequency.
- **Grower (Farmer) Metrics:** Average farm size, grower age, product scan rates, and offline campaign attendance per territory.

### B. Feature Engineering
Before training, the pipeline engineers highly predictive domain-specific features:
1. **Revenue Proxy:** `weekly_sales_qty * avg_qty_per_txn`
2. **Visit Recency Score:** `1 / (1 + days_since_last_visit)` *(Calculates how recently a retailer was visited)*
3. **Engagement Index:** `(scan_rate + campaign_attendance_rate) / 2`
4. **Inventory Pressure:** `stockout_ratio / (avg_inventory + 1)` *(Identifies high-velocity retailers rapidly running out of stock)*

### C. The Model Engine
We use a **Gradient Boosting Regressor** (`GradientBoostingRegressor` from `scikit-learn`):
- **Why?** It effectively captures non-linear relationships (e.g., how stockout ratios interact with sales velocity) better than linear models, handles missing data gracefully, and is highly robust to outliers.
- **Training:** The model learns to predict `weekly_revenue`. It uses a 5-fold cross-validation strategy to score itself on Mean Absolute Error (MAE) and R² to prevent overfitting.
- **Pipeline Structure:** Raw inputs flow through a `ColumnTransformer` (standardizing numeric fields via `StandardScaler` and encoding categorical fields via `OneHotEncoder`) directly into the Boosting model.

### D. Scoring & Classification
Once the model predicts the absolute expected revenue for a given retailer, it applies **Percentile Calibration**:
1. It compares the prediction against the 5th (P5) and 95th (P95) percentiles of the training data.
2. The raw predicted revenue is normalized into a crisp **0 to 100 Score**.
3. Based on the score, the system assigns a **Priority Label**:
   - **80 to 100:** `CRITICAL` - High revenue potential or severe inventory pressure; must visit immediately.
   - **60 to 79:** `HIGH`
   - **40 to 59:** `MEDIUM`
   - **0 to 39:** `LOW`

### E. Executing the ML Training
To train the model and generate the predictive artifact (`pipeline.pkl`), run the following from the root directory:

```bash
cd backend
python -m ml_models.retailer_priority.train
```

*Note: If no CSV data is found in the `data/` directory, the training script automatically generates synthetic, mathematically realistic data to ensure you can bootstrap the model and develop without interruptions.*
