# Broiler Weight Prediction

## Overview

This channel tracks the development and deployment of ML models to predict broiler chicken weight — both daily weight tracking and catch weight at slaughter. The project spans from May 2023 to November 2025, involving data quality investigations, model development, pipeline deployment, and ongoing coordination with farm users and BI teams.

## Project Goals (Pinned)

1. **Daily weight prediction** — alert when weight falls below standard
2. **Catch weight prediction (slaughter)** — target MAE <= 50g at 3 days before catch

## Timeline

### Phase 1: Data Exploration & Validation (Jun 2023)

- **Data quality issues**: Manually entered farm data has many typos; upper/lower house weights differ in two-story farms
- **Weight terminology confusion**: Multiple weight types discovered:
  - Farm catch weight (sampled, calculated by farm)
  - Slaughter house weight (actual, with loss rate calculated back to farm equivalent)
  - Hatchery entry weight (DOC_WGH, ~40-46g, some outliers near 100g identified as data entry errors)
- **Key features**: sex (newly added), breed (STRAIN), ADG (Average Daily Gain), age, hatchery weight
- **Baseline**: User's manual method achieves ~60g MAE at 3 days before catch
- Wave1Win built custom K-fold CV ("สั่งตัด" method) to prevent data leakage across flocks

### Phase 2: Model Training & Evaluation (Jun 2023)

- **Model error**: MAPE 3-4%, MAE 80-100g (without weight as feature)
- **With weight feature**: significantly better but user may stop manual weighing in future
- **Focus farms**: 5402 (ห้วยชุมพร), 5410 (บ้านบึง), 5411 (อ่างเวียน), 7447 (ใหม่พัฒนา 3)
- chinaphanz (ม่อกก้อก/intern) helped with baseline error analysis and data visualization
- tata (ลิเบอโร่) brought in to investigate prediction issues
- **diff approach**: Predicting weight change (diff) instead of absolute weight to prevent predictions decreasing day-over-day; increased error — needs further investigation

### Phase 3: Pipeline Deployment (Jun-Jul 2023)

- Wave1Win worked on migrating training pipeline to AIML infrastructure
- Added PRED_DATE column to BigQuery prediction table
- Pipeline scheduling issues: worked locally but failed on cloud
- BI integration challenges: data tables not updating, prediction display issues
- Farm coverage: 24 farms with combox data available for prediction

### Phase 4: Ongoing Maintenance (Sep 2023)

- Permission issues when Wave1Win's email changed to axonstech
- Breeder table missing open farm status for 14 days
- Coordination with new BI team members

### Phase 5: Revival — Camera-Based Weight Prediction (Oct-Nov 2025)

- pH resumes work with structured data fields for image-based prediction:
  - `storage_path`, `timestamp`, `inference_datetime`, `id` (chicken ID in image)
- Weight growth curves analyzed: very consistent patterns across ~19,560 training flocks
  - Three distinct weight groups likely correspond to different breeds
  - Near-zero variance in weight curves — SpikeGuard notes patterns match breed standards closely

## Key Technical Details

- **Data source**: BigQuery (`cpf-farm-th.PoultryFarmML`), including `BROILER_WEIGHT_PREDICTION_DEPLOY`
- **Models**: AutoGluon, ensemble methods
- **Evaluation**: K-fold CV by flock (to prevent data leakage)
- **Features**: age, sex, breed/strain, ADG, hatchery weight (DOC_WGH), combox data
- **Pipeline**: GCP Vertex AI, scheduled runs
- **Presentation**: Canva slides for user meetings

## Participants

| Username | Display Name | Role |
|---|---|---|
| spikeguard | SpikeGuard | Tech lead, user liaison |
| wave1win | Wave1Win | Primary DS, model development & pipeline |
| champ_pornthep | Champ Pornthep | Manager, user coordination |
| chinaphanz | chinaphanz (ม่อกก้อก) | Intern, baseline analysis |
| tnptataa | tata | DS support (ลิเบอโร่) |
| phum1901 | pH | DS, data analysis (later phase) |
| jiissee | TN | DevOps/infra, BigQuery permissions |

## Key Challenges

- Manual data entry by farms causes significant data quality issues
- Multiple weight definitions across farm and slaughter house create confusion
- User baseline is surprisingly accurate (~60g MAE), making it hard to beat
- Weight predictions sometimes decrease day-over-day (non-physical), requiring diff approach
- BI dashboard integration and data freshness issues
