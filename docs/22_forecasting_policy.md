# SOLARIS-A1: Pre-Flare Activity Forecasting Policy (Gate G6)

Status: APPROVED by Dr. Melvin / Solar Physics Group, date 2026-10-23

## 1. Overview and Operational Scope
This document formalizes the pre-flare activity forecasting protocol (Task B) for SOLARIS-A1 using Aditya-L1 SoLEXS Level-1 observations.
Task B evaluates whether light-curve characteristics strictly prior to reference time $t_0$ contain predictive information regarding whether an independently verified solar flare onset will occur within a future horizon $\Delta t_{\text{horizon}}$.

## 2. Decision D-07: Forecast Horizon Definition
- **Approved Horizon:** $\Delta t_{\text{horizon}} = 300.0\text{ s}$ (5 minutes) and secondary window $600.0\text{ s}$ (10 minutes).
- **Approved Reference Time:** $t_0 = \text{window\_end}$.
- **Approved Precursor Window:** $W_{\text{pre}} = 60.0\text{ s}$ (matching sliding window length).
- **Temporal Isolation Guard:** Strict exclusion of all data after $t_0$. Ongoing flaring activity within $[t_0 - W_{\text{pre}}, t_0]$ is assigned label `<NA>` with reason `ONGOING_EVENT` to prevent trivial auto-detection leakage into forecasting.

## 3. Decision D-08: Verified Negative and Embargo Rules
- **Pre-flare Embargo:** 1,800 s (30 minutes) prior to catalogue flare onset.
- **Post-flare Embargo:** 3,600 s (60 minutes) following catalogue flare end.
- **Negative Label Qualification:** Windows qualify as verified negative ($Y=0$) only if the entire forecast horizon $(t_0, t_0 + \Delta t_{\text{horizon}}]$ is free of flare onsets, maintains $\ge 80\%$ valid sample coverage, and falls outside the post-event recovery embargo.

## 4. Verification and Governance
- **Approved By:** Dr. Melvin / Solar Physics Group
- **Approval Date:** 2026-10-23
- **Gate Clearance:** Gate G6 formally APPROVED.
