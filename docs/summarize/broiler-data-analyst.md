# broiler-data-analyst

## Overview

This channel documents a data analytics project for CPF (Charoen Pokphand Foods, Thailand) focused on predicting Feed Conversion Ratio (FCR) in broiler chicken farming. The project spans from January 2024 through April 2025 and involves building machine learning models -- primarily XGBoost with Optuna hyperparameter tuning -- to predict daily and close-house (end-of-flock) FCR using IoT sensor data from Combox devices, farm operational data, and environmental variables. The goal is to provide actionable insights to farm operators: identifying causes of high FCR (via SHAP explainability) and recommending corrective actions (via counterfactual explanations using DiCE ML).

The project evolved from initial model exploration and data analysis into a production system that outputs daily predictions to BigQuery, generates Excel reports for farm staff, and feeds a Looker dashboard. Key challenges throughout included persistent data quality issues (missing sensor data, incomplete feed records, unreliable mortality counts), the difficulty of beating a simple mean-FCR baseline, and the complexity of communicating ML outputs to non-technical farm stakeholders.

## Timeline

### Phase 1: Exploration and Initial Modeling (January -- April 2024)

- Explored initial datasets from BigQuery (`cpf-farm-th.PoultryFarmML.*`).
- Built early XGBoost regression models for FCR prediction.
- Investigated feature importance using SHAP values.
- Conducted data quality analysis, identifying issues with missing sensor readings, outside temperature discrepancies between houses, and inconsistent mortality records.
- Compared insample vs. outsample performance to diagnose overfitting.
- Discussed whether to use regression or classification for FCR prediction; decided regression is more robust since threshold values can change.
- Explored rolling averages (3-day, 5-day) and cross-multiplication targets as feature engineering strategies.

### Phase 2: Feature Engineering and Model Refinement (May -- July 2024)

- Implemented Optuna-based hyperparameter tuning (lambda, alpha, gamma, subsample, colsample_bytree, min_child_weight, max_depth, eta).
- Introduced FCR standard/threshold calculation using Q3 percentiles smoothed with Linear Regression.
- Explored splitting models by chicken age for improved accuracy.
- Began work on counterfactual explanations using DiCE ML to recommend actionable feature adjustments.
- Discovered that gamma in XGBoost was acting as implicit feature selection, removing features from importance rankings.
- Shared L1 vs. L2 regularization insights; decided to use L1 for feature selection then tune with L2.
- Prepared presentation slides in Canva for stakeholder meetings (slides 146-153+).
- Discussed the distinction between SHAP (explaining past causes) and counterfactual (recommending future actions).

### Phase 3: Wind Chill and Environmental Modeling (August -- September 2024)

- Introduced wind chill (WChill) as a key variable for poultry comfort; required chill factor data from farms.
- Encountered discrepancies between farm regions: one veterinarian (Nes) provided target internal temperatures requiring diff subtraction to get wind chill, while another (Sa) provided direct wind chill targets. This caused confusion about whether targets should be uniform across all farms.
- Built separate models: one for temperature/humidity/wind speed (ENV model) and one for wind chill (WINDCHILL model).
- Developed standard curves for environmental variables using historical data, grouped by farm type and chicken age.
- Experimented with smoothing techniques: spline fitting caused parabola artifacts with sparse data; tried exponential smoothing and polynomial regression (degree 2-3); settled on polynomial with degree constraints and a filter to prevent curves from dropping below previous values.
- Uploaded model outputs to BigQuery tables (`cpf-aiml-innovation.AI_Broiler.*`).
- Created BigQuery views for Excel export and BI consumption (~250 columns of features).
- Prepared data for a workshop with external collaborators regarding survival rate and body weight prediction.

### Phase 4: Production Deployment and Monitoring (October -- December 2024)

- Deployed daily prediction pipeline writing results to BigQuery.
- Created Excel outputs sent to farm staff (Khun Muk) for review; farm feedback was slow to arrive.
- Built Looker dashboard pages: daily prediction view and historical performance tracking.
- Set up data monitoring to track missing data percentages per feature group per farm.
- Found that farm 7447 (Krok Sombun) had missing feed data for entire weeks, causing actual FCR calculations to be wildly off (1.0-1.3 range).
- Farms 7415, 7419, 7420 had ~15 missing Combox feature columns across all rows.
- Opened Change Requests (CRs) for BI integration; coordinated with BI team for Looker access.
- Created documentation in Canva explaining the system for stakeholders.
- Trained farm users on reading Looker dashboards and documentation.
- Duck farm division expressed interest in applying similar AI approach; a meeting was scheduled for October 24.

### Phase 5: Continued Monitoring and Iteration (January -- April 2025)

- Continued monitoring live prediction accuracy; weight prediction MAPE was extremely high (hundreds of percent) due to data issues.
- Discussed adding daily weight data from cameras (Phi Job's data) as a potential new feature, but camera data was too sparse (only 2 houses, incomplete daily coverage).
- Updated slides for management reviews with Phi Aun (new stakeholder).
- Coordinated sprint reviews covering project status, monitoring results, and future project planning.
- Explored survival rate (SR) and mean body weight (MBW) as additional prediction targets.

## Key Technical Details

- **Primary Model**: XGBoost regression for daily FCR prediction, tuned with Optuna (pruning enabled). Hyperparameters tuned: max_depth, eta, gamma, lambda, alpha, subsample, colsample_bytree, min_child_weight.
- **Two Model Variants**: ENV model (temperature, humidity, wind speed features) and WINDCHILL model (wind chill-specific features).
- **Explainability**: SHAP values for identifying which features drove high FCR on a given day (past-looking). Counterfactual explanations via DiCE ML for recommending what to change going forward (future-looking).
- **FCR Standard**: Calculated using Q3 (75th percentile) of historical FCR data per day-of-age, smoothed with Linear Regression. Used as the threshold for alerts.
- **Feature Engineering**: Cumulative feed intake, rolling averages, cross-multiplication of features with standards, placeholder values from standards when real data is missing.
- **Environmental Standards**: Historical median temperature/humidity/wind speed curves, grouped by farm type and season, smoothed with polynomial regression (degree 2-3) with monotonicity constraints.
- **Data Pipeline**: BigQuery for storage, with views separating internal tracking tables from user-facing tables. Automated daily model runs writing predictions to BQ.
- **Presentation/Delivery**: Looker dashboards for daily predictions and historical performance; Excel exports via BigQuery views; Canva for presentation slides; Figma for system flow diagrams.
- **Infrastructure**: Google Cloud Platform (BigQuery, Vertex AI service account), Looker Studio for dashboards. Change Requests managed through internal ticketing system.
- **Regularization Insight**: L1 (Lasso) used for feature selection, then L2 (Ridge) for final tuning. Gamma in XGBoost found to implicitly drop features, acting as another form of feature selection.

## Participants

| Username | Display Name | Role |
|---|---|---|
| spikeguard | SpikeGuard | Project lead / senior data scientist. Directed modeling strategy, reviewed slides and presentations, managed stakeholder communications, handled BigQuery permissions and infrastructure tasks. |
| tnptataa | tata | Primary analyst / data scientist. Performed all modeling, feature engineering, data quality analysis, visualization, dashboard development, and documentation. Prepared and delivered presentations. |
| winpat_ | winpat | Supporting team member. Mentioned in context of automation (email sending) and prior work on similar pipelines. Minimal direct messages in this channel. |
| mugmuk (referenced) | Khun Muk | Farm-side coordinator / product owner for poultry. Requested data, relayed farm feedback, coordinated with veterinarians. Not a direct channel participant but frequently referenced. |
| suthep (referenced) | Phi Suthep | Senior farm management stakeholder. Provided FCR alert standards. Referenced in discussions but not a channel participant. |

## Key Challenges and Notes

- **Data Quality**: The most persistent challenge. Combox IoT sensor data had frequent gaps (entire weeks of missing feed data for some farms, ~15 missing columns for others). Mortality data was unreliable because dead chickens were sometimes found days after dying. Weight data from cameras was too sparse to be useful. These gaps directly impacted prediction accuracy and required extensive fill/interpolation strategies.
- **Baseline Difficulty**: The mean FCR baseline was hard to beat, especially for well-managed farms where FCR was already low. The model tended to over-predict FCR for top-performing farms (e.g., farm 7419).
- **Stakeholder Communication**: Significant effort went into making ML outputs understandable to non-technical farm operators. Multiple presentation rehearsals were conducted. The distinction between SHAP (explaining past) and counterfactual (recommending future) was difficult to convey. Slides were revised many times to reduce text and improve clarity.
- **Wind Chill Confusion**: Different farm regions used different definitions for temperature targets (internal temperature vs. wind chill), causing weeks of confusion and requiring direct clarification meetings with veterinarians.
- **Smoothing Standard Curves**: Creating smooth reference curves from noisy historical data proved difficult. Spline fitting produced artifacts; exponential smoothing had parameter sensitivity; polynomial regression required careful degree selection and post-hoc monotonicity constraints.
- **Production Monitoring**: Once deployed, monitoring revealed that data quality issues in production were worse than in historical training data. A monitoring system tracking missing data percentages per feature group was built to quantify the problem.
- **Scope Expansion**: The project's scope gradually expanded from FCR prediction to include survival rate prediction, body weight tracking, wind chill modeling, and interest from duck farming operations. This expansion was managed cautiously with phased delivery.
