# MODEL SELECTION REPORT — VALIDATION ONLY

> **GOVERNANCE NOTICE: VALIDATION METRICS ONLY**  
> All performance metrics in this document were evaluated exclusively on the **VALIDATION partition**.  
> The sealed TEST set was not read, scored, or evaluated in this stage.  

**Selection Metric:** `PR_AUC`  
**Refit Mode:** `train_only`  

| Model Name | Status | Validation Score (PR_AUC) | Selected Hyperparameters |
|------------|:------:|:---------------------------------:|--------------------------|
| `logistic_regression` | `TRAINED` | **1.0000** | `{'C': 0.01, 'solver': 'lbfgs', 'max_iter': 1000, 'class_weight': None}` |
| `random_forest` | `TRAINED` | **1.0000** | `{'n_estimators': 50, 'max_depth': 5, 'min_samples_split': 2, 'class_weight': 'balanced'}` |
| `xgboost` | `TRAINED` | **1.0000** | `{'n_estimators': 50, 'max_depth': 3, 'learning_rate': 0.05, 'tree_method': 'hist', 'n_jobs': 1}` |
