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
