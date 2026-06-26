# Research Farm

## Overview

This channel covers research and development work for the AIML Farm team, primarily focused on two workstreams: (1) building a reusable ML pipeline template, and (2) broiler chicken weight prediction from camera images.

## Timeline

### Phase 1: Research & Template Foundation (Oct 2025)

- **2025-10-22**: Channel created by SpikeGuard for research and new project briefs.
- **2025-10-23**: c0ntinve (Penguin) shares research on two approaches:
  1. **Hidden Technical Debt in ML Systems** — encapsulating the full model lifecycle (load, fit, save as .pkl) into reusable classes to freeze model behavior at prediction time.
  2. **Hydra + MLflow** — Hydra for config management with CLI overrides; MLflow for experiment tracking (parameters, metrics, artifacts) across runs, superior to AutoGluon's built-in leaderboard for iterative comparison.
- c0ntinve proposes modularizing the template into multiple files with imports, keeping the main file as `.ipynb` and supporting files as `.py`.
- SpikeGuard clarifies: the template lives in `src/`; the existing `POC_to_pipeline` file is actual POC code, not part of the template. The pipeline runs 5 components (stages), each independently executable.

### Phase 2: BigQuery & GCP Access (Oct 2025)

- **2025-10-27 to 10-28**: Extensive troubleshooting of BigQuery access for c0ntinve. Key issues:
  - Permission errors on `aiml-cpf-th-farm-dev` project
  - ADC (Application Default Credentials) configuration needed
  - Data lives in `cpf-farm-th` project but client runs under `aiml-cpf-th-farm-dev`
  - After pH requests permissions, access is resolved
- SpikeGuard warns: always use `LIMIT` on queries — the data tables can have billions of rows, and billing goes to `cpf-farm-th` (not their own project).

### Phase 3: Template v1 — Dask & Pandera (Nov 2025)

- **2025-11-06 to 11-16**: c0ntinve researches operational limits and proposes solutions:
  1. **OOM**: Use Dask (or Ray) instead of pandas for parallel chunked processing. Also explored inputting GCS paths directly to AutoGluon/LightGBM.
  2. **GCS data retention**: Set auto-deletion for old data (>180 days). pH clarifies: keep GCS raw data, only delete temporary BigQuery tables.
  3. **Data format validation**: Pandera for range/category checking; chosen over TensorFlow Data Validation (TFDV) due to less code impact.
  4. **Scheduler failure alerting**: Email + Discord webhook notifications via GCP Cloud Monitoring.
- pH adds: explore **Ray** as an alternative to Dask; use BigQuery temp tables + export to Parquet for preprocessing.
- SpikeGuard on model accuracy: currently they retrain monthly and don't monitor accuracy drops — detection relies on user complaints. Data drift is the main risk.

### Phase 4: Discord Notifications (Nov 2025)

- **2025-11-12 to 11-19**: c0ntinve designs a Discord notification system for pipeline status:
  - Per-stage success/failure reporting
  - Configurable webhook URLs (stored in `.env`, later to use GCP Secret Manager)
  - Channel organization: unstable pipelines share one channel; stable pipelines split by animal type (aqua, poultry, etc.)
  - Notification format example:
    ```
    Pipeline Daily Report
    Wednesday, 2025-11-19
    Query (Train): Success
    Preprocess (Train): Success
    Train & Evaluate: Fail (Error: MemoryError)
    ```
- pH confirms: notifications should support multiple destinations; show success/fail per stage with minimal detail (check logs for specifics).

### Phase 5: Template Finalization & Config (Nov-Dec 2025)

- **2025-11-20 to 12-07**: Template refinements:
  - Dask replaces pandas where possible
  - Pandera validates inference input data ranges
  - Models addable by changing `MODEL_TYPE` only (no `model_factory` edits needed)
  - `config.yaml` added for structured configuration
  - Custom metrics support for evaluation
  - Testing uses `research_template` dataset in BigQuery and GCS bucket
  - Code pushed to `dask` branch on Azure DevOps repo `Research_Structure_Template`
  - Instructions created in Canva + README
- **2025-12-26**: Final template version pushed with improved dynamic configuration.

### Phase 6: Ray Template (Jan-Mar 2026)

- **2026-01-09**: New goal — convert existing projects to template format; research Ray vs Dask performance.
- **2026-01-22 to 02-25**: c0ntinve builds Ray version of template:
  - Requirements version compatibility resolved
  - Dynamic model addition without editing `model_factory.py`
  - Two run modes: **isolated** (per-stage) and **unified** (all stages chained)
  - Unified mode enables processing data larger than RAM for inference
  - OOM issues on Windows due to Ray's Linux-optimized design; resolved by running on WSL/Linux
  - Batch size made configurable with sensible defaults for 16GB RAM
- **2026-02-25**: Ray branch pushed to repo.
- **2026-03-27**: Both `dask` and `ray` branches available; _NOBITA plans to have another team member try the template.

### Phase 7: Broiler Weight Prediction from Camera (Mar-Apr 2026)

- **2026-03-09**: pH introduces new project — predicting broiler chicken weight from camera images.
- **2026-03-17 to 04-23**: c0ntinve iterates on weight prediction models:
  - Features: bounding box, ellipse fitting, estimated volume, fatness ratio, age, camera ID
  - Best results with AutoGluon: **MAE 56.00g, MAPE 9.11%** (5-fold cross-validation)
  - XGBoost: **MAE 63.73g, MAPE 11.41%** (without age: MAE 199.33g — age is the dominant feature)
  - On held-out test set (618 samples): **MAE 87.35g, MAPE 7.88%** (after retraining to avoid data leakage)
  - ResNet + MLP explored: ~12% MAPE but significantly slower (1hr vs 1min for XGBoost)
  - Additional features (feed quantity, water, temperature) explored from BigQuery tables; feed data available daily, water/temperature mostly zeros
  - Data quality issues: many zero values in `chick_weight`; referred to BI team for clarification
  - Image data stored as `.npy` files in GCS bucket `broiler_weight_vision_project`

## Key Technical Stack

| Component           | Technology                                               |
| ------------------- | -------------------------------------------------------- |
| Data Processing     | Dask, Ray, pandas                                        |
| ML Models           | AutoGluon, LightGBM, XGBoost, GradientBoost, ResNet, MLP |
| Data Validation     | Pandera                                                  |
| Config Management   | Hydra, config.yaml                                       |
| Experiment Tracking | MLflow                                                   |
| Cloud Platform      | GCP (BigQuery, GCS, Vertex AI Workbench, Secret Manager) |
| Pipeline            | Kubeflow Pipelines (KFP) with dsl.pipeline               |
| CI/CD               | Azure DevOps                                             |
| Notifications       | Discord webhooks                                         |
| Documentation       | Canva, README                                            |

## Participants

| Username    | Display Name       | Role                                         |
| ----------- | ------------------ | -------------------------------------------- |
| spikeguard  | SpikeGuard         | Tech lead, template owner                    |
| phum1901    | pH                 | Senior DS, GCP infra, data coordination      |
| c0ntinve    | c0ntinve (Penguin) | Intern/junior developer, primary implementer |
| _woratum    | _NOBITA            | Engineering manager, coordination            |
| smhmaay4827 | (new member)       | Onboarded to use template                    |

## Key Repos & Resources

- **Template repo**: `https://dev.azure.com/DM-IoT-Business-Solution/AIML_Farm_Business/_git/Research_Structure_Template` (branches: `dask`, `ray`)
- **GCP Project**: `aiml-cpf-th-farm-dev` (dev), `cpf-farm-th` (data source)
- **BigQuery datasets**: `AI_Pig`, `IoT_CHICKEN`, `PoultryFarmML`, `research_template` (test)
- **GCS bucket**: `broiler_weight_vision_project` (image data), `research_template` (test)
