# broiler-sr-prediction

## Overview

The broiler-sr-prediction channel documents a machine learning project at CPF (Charoen Pokphand Foods) aimed at predicting the survival rate (SR) of broiler chickens across farming operations. The project ran from approximately June 2023 through August 2024, with the core development phase concentrated between June and November 2023. The team explored multiple ML approaches -- starting with regression models and eventually pivoting to classification -- to predict daily and cumulative chicken mortality, using farm sensor data (temperature, humidity, wind speed from Combox devices), flock metadata, and historical mortality records.

The project was driven by a business need to provide early warnings of abnormal mortality events so that farm managers could intervene. A key competitive dimension was benchmarking against True Corporation's existing prediction model. The team ultimately deployed a pipeline on BigQuery with Power BI dashboards for visualization, achieving classification accuracy in the range of 67-83% depending on the model and configuration. The project involved significant data quality challenges, including sparse sensor coverage (only ~2.27% overlap between Combox sensor data and mortality records) and issues with bottom-of-pen chicken counting that introduced noise into the ground truth data.

## Timeline

### Phase 1: Baseline and POC (June 2023)
- Project kickoff with initial data exploration on Farm 7447 as the primary test case.
- Established a cross-multiplication baseline for mortality prediction.
- Defined the standard mortality rate (STD) at 0.07% daily, with 0.15% for the first 7 days of a flock's life.
- Early EDA (Exploratory Data Analysis) to understand data availability and quality.

### Phase 2: Model Development (July 2023)
- Built initial regression models: XGBoost, LightGBM, Random Forest, SVM, KNN, and Logistic Regression.
- Implemented multi-output regressor for multi-day ahead predictions.
- Began SHAP (SHapley Additive exPlanations) analysis for model interpretability.
- Identified that Combox sensor data had very limited overlap with mortality records (~2.27%).

### Phase 3: Feature Engineering and Refinement (July - August 2023)
- Developed an ammonia proxy feature using humidity divided by ventilation level.
- Created lag features to capture temporal patterns in mortality data.
- Introduced a "feature-minus-standard" approach to normalize features against expected baselines.
- Used IQR-based outlier detection to create custom farm-level standards.
- Explored expanding from single-farm to multi-farm models.

### Phase 4: Classification Pivot and Competitive Analysis (August - September 2023)
- Pivoted from regression to classification (predicting whether mortality would be "normal" or "abnormal").
- Conducted competitor analysis against True Corporation's existing model.
- Refined classification thresholds and evaluated precision/recall tradeoffs.
- Achieved accuracy results in the 67-83% range across different configurations.

### Phase 5: Cause Analysis and Documentation (September - October 2023)
- Focused on root cause analysis of abnormal mortality events.
- Investigated bottom-of-pen chicken counting issues as a source of data noise.
- Prepared presentations and documentation for stakeholders.
- Conducted SHAP-based feature importance analysis for model explainability.

### Phase 6: Pipeline Deployment and Project Closure (October - November 2023)
- Deployed prediction pipeline on BigQuery with scheduled cronjob execution.
- Built Power BI dashboards for visualization and monitoring.
- Finalized documentation and project handoff materials.
- Conducted project retrospective.

### Phase 7: Maintenance and Follow-up (December 2023 - August 2024)
- Periodic monitoring and minor adjustments to the deployed pipeline.
- Addressed ad-hoc data quality issues.
- Sporadic follow-up discussions on model performance.

## Key Technical Details

- **Primary models**: XGBoost and LightGBM performed best among the models tested. Random Forest, SVM, KNN, and Logistic Regression were also evaluated.
- **Approach evolution**: The project started as a regression problem (predicting exact mortality numbers) but pivoted to classification (predicting normal vs. abnormal mortality) for better practical utility.
- **Feature engineering**: Key engineered features included an ammonia proxy (humidity / ventilation level), lag features for temporal patterns, and a feature-minus-standard normalization technique.
- **Standard mortality rate**: Defined as 0.07% daily (0.15% for the first 7 days), used as a baseline for "normal" classification.
- **Custom standards**: IQR-based outlier detection was used to derive farm-specific mortality standards rather than relying solely on global averages.
- **Explainability**: SHAP values were used extensively to explain model predictions and identify the most influential features for stakeholder presentations.
- **Data sources**: Farm metadata, daily mortality records, and Combox sensor data (temperature, humidity, wind speed). Sensor data coverage was extremely sparse (~2.27% overlap with mortality data).
- **Infrastructure**: BigQuery for data storage and pipeline execution, Power BI for dashboards and reporting, cronjob scheduling for automated pipeline runs.
- **Multi-output regression**: Used for predicting mortality across multiple future days simultaneously before the classification pivot.

## Participants

| Username       | Display Name | Role                                                                 |
|----------------|--------------|----------------------------------------------------------------------|
| spikeguard     | spikeguard   | Team lead / project manager; directed strategy, reviewed results     |
| tnptataa       | tata         | Primary developer; built models, feature engineering, pipeline work  |
| nistadesu      | Nista        | Developer; data analysis, model development support                  |
| _woratum       | _NOBITA      | Developer; contributed to analysis and technical discussions         |
| wave1win       | Wave1Win     | Developer; data processing and support tasks                         |
| nodsong        | Nod          | Contributor; participated in discussions and review                  |
| jiissee        | TN           | Contributor; involved in data and analysis discussions               |
| _mochai        | _mochai      | Contributor; occasional technical input                              |
| chinaphanz     | chinaphanz   | Contributor; participated in project discussions                     |

## Key Challenges and Notes

- **Sensor data sparsity**: Only about 2.27% of mortality records had corresponding Combox sensor data, severely limiting the usefulness of environmental features (temperature, humidity, wind speed) in predictions.
- **Bottom-of-pen counting**: Chickens that died at the bottom of the pen were not always counted promptly, introducing systematic noise into the daily mortality figures used as ground truth.
- **Regression to classification pivot**: The team found that predicting exact mortality numbers (regression) was less practically useful than predicting whether a day's mortality would be abnormal (classification), leading to a mid-project pivot.
- **Competitor benchmarking**: True Corporation had an existing model in this space, and the team needed to demonstrate competitive or superior performance, adding pressure to achieve strong accuracy metrics.
- **Multi-farm generalization**: Models trained on a single farm (7447) did not generalize well to other farms, requiring careful consideration of farm-specific standards and features.
- **Stakeholder communication**: Significant effort was spent on making the model explainable (via SHAP) and preparing presentations, as the project required buy-in from non-technical farm management stakeholders.
- **Data quality overall**: Beyond sensor sparsity and counting issues, the team encountered various data quality problems including missing records, inconsistent reporting across farms, and the need for extensive data cleaning.
