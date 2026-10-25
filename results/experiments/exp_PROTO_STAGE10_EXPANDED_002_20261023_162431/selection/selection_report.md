# MODEL SELECTION REPORT — VALIDATION ONLY

> **GOVERNANCE NOTICE: VALIDATION METRICS ONLY**  
> All performance metrics in this document were evaluated exclusively on the **VALIDATION partition**.  
> The sealed TEST set was not read, scored, or evaluated in this stage.  

**Selection Metric:** `PR_AUC`  
**Refit Mode:** `train_only`  

| Model Name | Status | Validation Score (PR_AUC) | Selected Hyperparameters |
|------------|:------:|:---------------------------------:|--------------------------|
| `logistic_regression` | `TRAINED` | **0.5315** | `{'C': 1.0, 'solver': 'lbfgs', 'max_iter': 1000, 'class_weight': None}` |
| `random_forest` | `TRAINED` | **0.5743** | `{'n_estimators': 100, 'max_depth': 10, 'min_samples_split': 5, 'class_weight': None}` |
| `xgboost` | `TRAINED` | **0.5956** | `{'n_estimators': 100, 'max_depth': 3, 'learning_rate': 0.1, 'scale_pos_weight': 6.0}` |
