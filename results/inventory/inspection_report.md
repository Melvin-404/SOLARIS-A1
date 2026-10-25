# SOLARIS-A1: FITS Metadata Inspection Report

> **Note:** All observed values in this report are extracted directly from FITS headers and tables. Any interpretations are explicitly marked as candidate interpretations and require student review.

---

## File: `AL1_SOLEXS_20261018_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20261018_SDD2_L1.lc.gz`
- **Size:** 256,172 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1792281600.0` | Extracted from FITS header |
| `TSTOP` | `1792367999.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2026-10-18 00:00:00` | Extracted from FITS header |
| `DATE-END` | `2026-10-18 23:59:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1792281600.0 s alongside DATE-OBS='2026-10-18 00:00:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.792e+09 | 1.792e+09 | 1.792e+09 | 1.792e+09 |
| `COUNTS` | 86,400 | 4,849 | 0 | 0 | 185 | 13.35 | 9 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.792e+09 | 1.792e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20261018_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20261018_SDD2_L1.gti.gz`
- **Size:** 1,084 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 8 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2026-10-18T01:20:28+00:00` | Extracted from FITS header |
| `TSTOP` | `2026-10-18T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 8 | 0 | 0 | 1.792e+09 | 1.792e+09 | 1.792e+09 | 1.792e+09 |
| `STOP` | 8 | 0 | 0 | 1.792e+09 | 1.792e+09 | 1.792e+09 | 1.792e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 8 | 1.792e+09 | 1.792e+09 | 85 s | True | 8 |
| `STOP` | 8 | 1.792e+09 | 1.792e+09 | 30 s | True | 8 |

---

## File: `AL1_SOLEXS_20261018_SDD1_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20261018_SDD1_L1.gti.gz`
- **Size:** 957 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 0 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `` | Extracted from FITS header |
| `TSTOP` | `` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `I` | *None recorded* |  |
| `STOP` | `I` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 0 | 0 | 0 | None | None | None | None |
| `STOP` | 0 | 0 | 0 | None | None | None | None |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 0 | None | None | None | False | 0 |
| `STOP` | 0 | None | None | None | False | 0 |

---

## File: `AL1_SOLEXS_20261018_SDD2_L1.pi.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20261018_SDD2_L1.pi.gz`
- **Size:** 5,669,587 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `SPECTRUM` | 1 | BinTableHDU | () | 86,400 | 6 |

### Observed Time-System Keywords
*No standard time keywords observed.*

### Extension `SPECTRUM` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TSTART` | `D` | `s` |  |
| `TELAPSE` | `D` | `s` |  |
| `SPEC_NUM` | `J` | *None recorded* |  |
| `CHANNEL` | `340K` | *None recorded* |  |
| `COUNTS` | `340D` | *None recorded* |  |
| `EXPOSURE` | `D` | `s` |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TSTART` | 86,400 | 0 | 0 | 1.792e+09 | 1.792e+09 | 1.792e+09 | 1.792e+09 |
| `TELAPSE` | 86,400 | 0 | 0 | 1 | 1 | 1 | 1 |
| `SPEC_NUM` | 86,400 | 0 | 0 | 1 | 8.64e+04 | 4.32e+04 | 4.32e+04 |
| `CHANNEL` | 29,376,000 | 0 | 0 | 0 | 339 | 169.5 | 169.5 |
| `COUNTS` | 29,376,000 | 1,648,660 | 0 | 0 | 25 | 0.0831 | 0 |
| `EXPOSURE` | 86,400 | 0 | 0 | 1 | 1 | 1 | 1 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TSTART` | 86,400 | 1.792e+09 | 1.792e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240701_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240701_SDD2_L1.lc.gz`
- **Size:** 270,003 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1719792000.0` | Extracted from FITS header |
| `TSTOP` | `1719878399.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-01 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-02 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1719792000.0 s alongside DATE-OBS='2024-07-01 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `COUNTS` | 86,400 | 128 | 0 | 3 | 1554 | 30.59 | 20 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.72e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240701_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240701_SDD2_L1.gti.gz`
- **Size:** 1,055 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 4 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-01T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-01T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 4 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `STOP` | 4 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 4 | 1.72e+09 | 1.72e+09 | 131 s | True | 4 |
| `STOP` | 4 | 1.72e+09 | 1.72e+09 | 2.313e+04 s | True | 4 |

---

## File: `AL1_SOLEXS_20240703_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240703_SDD2_L1.lc.gz`
- **Size:** 272,958 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1719964800.0` | Extracted from FITS header |
| `TSTOP` | `1720051199.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-03 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-04 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1719964800.0 s alongside DATE-OBS='2024-07-03 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `COUNTS` | 86,400 | 2 | 0 | 2 | 943 | 36.97 | 22 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.72e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240703_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240703_SDD2_L1.gti.gz`
- **Size:** 1,049 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 3 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-03T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-03T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `STOP` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 1.72e+09 | 1.72e+09 | 9020 s | True | 3 |
| `STOP` | 3 | 1.72e+09 | 1.72e+09 | 3.418e+04 s | True | 3 |

---

## File: `AL1_SOLEXS_20240704_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240704_SDD2_L1.lc.gz`
- **Size:** 283,681 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720051200.0` | Extracted from FITS header |
| `TSTOP` | `1720137599.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-04 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-05 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720051200.0 s alongside DATE-OBS='2024-07-04 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `COUNTS` | 86,400 | 1 | 0 | 4 | 827 | 60.5 | 41 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.72e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240704_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240704_SDD2_L1.gti.gz`
- **Size:** 1,045 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 2 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-04T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-04T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `STOP` | 2 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 1.72e+09 | 1.72e+09 | 4.292e+04 s | True | 2 |
| `STOP` | 2 | 1.72e+09 | 1.72e+09 | 4.348e+04 s | True | 2 |

---

## File: `AL1_SOLEXS_20240705_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240705_SDD2_L1.lc.gz`
- **Size:** 284,789 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720137600.0` | Extracted from FITS header |
| `TSTOP` | `1720223999.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-05 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-06 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720137600.0 s alongside DATE-OBS='2024-07-05 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `COUNTS` | 86,400 | 1 | 0 | 8 | 547 | 59.9 | 45 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.72e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240705_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240705_SDD2_L1.gti.gz`
- **Size:** 1,045 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 2 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-05T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-05T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `STOP` | 2 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 1.72e+09 | 1.72e+09 | 1.249e+04 s | True | 2 |
| `STOP` | 2 | 1.72e+09 | 1.72e+09 | 7.392e+04 s | True | 2 |

---

## File: `AL1_SOLEXS_20240706_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240706_SDD2_L1.lc.gz`
- **Size:** 288,272 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720224000.0` | Extracted from FITS header |
| `TSTOP` | `1720310399.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-06 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-07 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720224000.0 s alongside DATE-OBS='2024-07-06 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `COUNTS` | 86,400 | 2 | 0 | 10 | 546 | 81.57 | 49 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.72e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240706_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240706_SDD2_L1.gti.gz`
- **Size:** 1,048 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 3 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-06T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-06T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `STOP` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 1.72e+09 | 1.72e+09 | 1.866e+04 s | True | 3 |
| `STOP` | 3 | 1.72e+09 | 1.72e+09 | 4.32e+04 s | True | 3 |

---

## File: `AL1_SOLEXS_20240707_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240707_SDD2_L1.lc.gz`
- **Size:** 305,845 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720310400.0` | Extracted from FITS header |
| `TSTOP` | `1720396799.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-07 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-08 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720310400.0 s alongside DATE-OBS='2024-07-07 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `COUNTS` | 86,400 | 2 | 0 | 28 | 1547 | 164.5 | 90 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.72e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240707_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240707_SDD2_L1.gti.gz`
- **Size:** 1,048 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 3 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-07T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-07T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `STOP` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 1.72e+09 | 1.72e+09 | 3026 s | True | 3 |
| `STOP` | 3 | 1.72e+09 | 1.72e+09 | 4.018e+04 s | True | 3 |

---

## File: `AL1_SOLEXS_20240708_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240708_SDD2_L1.lc.gz`
- **Size:** 250,007 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720396800.0` | Extracted from FITS header |
| `TSTOP` | `1720483199.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-08 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-09 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720396800.0 s alongside DATE-OBS='2024-07-08 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `COUNTS` | 86,400 | 50,212 | 0 | 0 | 332 | 90.82 | 81 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.72e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240708_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240708_SDD2_L1.gti.gz`
- **Size:** 1,046 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 3 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-08T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-08T23:47:06+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |
| `STOP` | 3 | 0 | 0 | 1.72e+09 | 1.72e+09 | 1.72e+09 | 1.72e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 1.72e+09 | 1.72e+09 | 4.281e+04 s | True | 3 |
| `STOP` | 3 | 1.72e+09 | 1.72e+09 | 2.726e+04 s | True | 3 |

---

## File: `AL1_SOLEXS_20240709_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240709_SDD2_L1.lc.gz`
- **Size:** 258,919 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720483200.0` | Extracted from FITS header |
| `TSTOP` | `1720569599.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-09 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-10 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720483200.0 s alongside DATE-OBS='2024-07-09 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.72e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `COUNTS` | 86,400 | 29,247 | 0 | 0 | 326 | 47.49 | 42 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.72e+09 | 1.721e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240709_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240709_SDD2_L1.gti.gz`
- **Size:** 1,054 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 3 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-09T08:23:27+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-09T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `STOP` | 3 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 3 | 1.721e+09 | 1.721e+09 | 1.22e+04 s | True | 3 |
| `STOP` | 3 | 1.721e+09 | 1.721e+09 | 1.59e+04 s | True | 3 |

---

## File: `AL1_SOLEXS_20240710_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240710_SDD2_L1.lc.gz`
- **Size:** 310,690 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720569600.0` | Extracted from FITS header |
| `TSTOP` | `1720655999.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-10 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-11 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720569600.0 s alongside DATE-OBS='2024-07-10 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `COUNTS` | 86,400 | 3 | 0 | 23 | 1000 | 153.5 | 114 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.721e+09 | 1.721e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240710_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240710_SDD2_L1.gti.gz`
- **Size:** 1,057 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 4 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-10T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-10T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 4 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `STOP` | 4 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 4 | 1.721e+09 | 1.721e+09 | 6 s | True | 4 |
| `STOP` | 4 | 1.721e+09 | 1.721e+09 | 2.289e+04 s | True | 4 |

---

## File: `AL1_SOLEXS_20240711_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240711_SDD2_L1.lc.gz`
- **Size:** 290,388 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720656000.0` | Extracted from FITS header |
| `TSTOP` | `1720742399.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-11 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-12 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720656000.0 s alongside DATE-OBS='2024-07-11 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `COUNTS` | 86,400 | 1 | 0 | 8 | 744 | 89.02 | 48 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.721e+09 | 1.721e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240711_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240711_SDD2_L1.gti.gz`
- **Size:** 1,044 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 2 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-11T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-11T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `STOP` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 1.721e+09 | 1.721e+09 | 7 s | True | 2 |
| `STOP` | 2 | 1.721e+09 | 1.721e+09 | 8.639e+04 s | True | 2 |

---

## File: `AL1_SOLEXS_20240712_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240712_SDD2_L1.lc.gz`
- **Size:** 280,159 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720742400.0` | Extracted from FITS header |
| `TSTOP` | `1720828799.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-12 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-13 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720742400.0 s alongside DATE-OBS='2024-07-12 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `COUNTS` | 86,400 | 1 | 0 | 9 | 296 | 49.99 | 41 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.721e+09 | 1.721e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240712_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240712_SDD2_L1.gti.gz`
- **Size:** 1,043 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 2 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-12T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-12T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `STOP` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 1.721e+09 | 1.721e+09 | 1.476e+04 s | True | 2 |
| `STOP` | 2 | 1.721e+09 | 1.721e+09 | 7.164e+04 s | True | 2 |

---

## File: `AL1_SOLEXS_20240713_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240713_SDD2_L1.lc.gz`
- **Size:** 315,076 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720828800.0` | Extracted from FITS header |
| `TSTOP` | `1720915199.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-13 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-14 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720828800.0 s alongside DATE-OBS='2024-07-13 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `COUNTS` | 86,400 | 1 | 0 | 20 | 4074 | 311.8 | 135 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.721e+09 | 1.721e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240713_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240713_SDD2_L1.gti.gz`
- **Size:** 1,044 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 2 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-13T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-13T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `STOP` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 1.721e+09 | 1.721e+09 | 3.893e+04 s | True | 2 |
| `STOP` | 2 | 1.721e+09 | 1.721e+09 | 4.747e+04 s | True | 2 |

---

## File: `AL1_SOLEXS_20240714_SDD2_L1.lc.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240714_SDD2_L1.lc.gz`
- **Size:** 318,963 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `RATE` | 1 | BinTableHDU | () | 86,400 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TIMESYS` | `UTC` | Extracted from FITS header |
| `MJDREFI` | `40587` | Extracted from FITS header |
| `MJDREFF` | `0.22916666651` | Extracted from FITS header |
| `TIMZERO` | `0` | Extracted from FITS header |
| `TSTART` | `1720915200.0` | Extracted from FITS header |
| `TSTOP` | `1721001599.0` | Extracted from FITS header |
| `TIMEDEL` | `1` | Extracted from FITS header |
| `TIMEUNIT` | `s` | Extracted from FITS header |
| `TIMEREF` | `LOCAL` | Extracted from FITS header |
| `DATE-OBS` | `2024-07-14 05:30:00` | Extracted from FITS header |
| `DATE-END` | `2024-07-15 05:29:59` | Extracted from FITS header |

#### Candidate Time Interpretations
- Observed TIMESYS = 'UTC'. (candidate interpretation — requires confirmation against official documentation)
- Observed MJDREFI = 40587. In standard astronomical FITS conventions, MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). (candidate interpretation — requires confirmation against official documentation)
- Observed TSTART=1720915200.0 s alongside DATE-OBS='2024-07-14 05:30:00'. If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)
- Observed TIMEREF = 'LOCAL'. (candidate interpretation — requires confirmation against official documentation)

### Extension `RATE` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `TIME` | `D` | *None recorded* |  |
| `COUNTS` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `COUNTS` | 86,400 | 1 | 0 | 39 | 9194 | 284 | 122 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` | 86,400 | 1.721e+09 | 1.721e+09 | 1 s | True | 86,400 |

---

## File: `AL1_SOLEXS_20240714_SDD2_L1.gti.gz`
- **File Path:** `C:\Users\melvi\Desktop\SOLARIS-A1\data\raw\AL1_SOLEXS_20240714_SDD2_L1.gti.gz`
- **Size:** 1,046 bytes

### HDU Structure
| Index | Name | Ver | Type | Shape | Rows | Columns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `PRIMARY` | 1 | PrimaryHDU | () | 0 | 0 |
| 1 | `GTI` | 1 | BinTableHDU | () | 2 | 2 |

### Observed Time-System Keywords
| Keyword | Observed Value | Description / Context |
| :--- | :--- | :--- |
| `TSTART` | `2024-07-14T00:00:00+00:00` | Extracted from FITS header |
| `TSTOP` | `2024-07-14T23:59:59+00:00` | Extracted from FITS header |

### Extension `GTI` (HDU 1) Columns
| Column Name | Format | Unit | Dimension |
| :--- | :--- | :--- | :--- |
| `START` | `D` | *None recorded* |  |
| `STOP` | `D` | *None recorded* |  |

#### Column Statistics
| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |
| `STOP` | 2 | 0 | 0 | 1.721e+09 | 1.721e+09 | 1.721e+09 | 1.721e+09 |

#### Time Column Diagnostics
| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `START` | 2 | 1.721e+09 | 1.721e+09 | 7536 s | True | 2 |
| `STOP` | 2 | 1.721e+09 | 1.721e+09 | 7.886e+04 s | True | 2 |

---
