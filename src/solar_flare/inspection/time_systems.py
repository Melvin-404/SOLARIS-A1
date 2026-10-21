"""Time system metadata extraction and candidate interpretations for SoLEXS FITS files.

Extracts time-related FITS header keywords and notes candidate interpretations
without applying automatic conversions or assuming unverified conventions.
"""

from pathlib import Path
from typing import Any, Dict, List, Union
from astropy.io import fits

TIME_SYSTEM_KEYWORDS = (
    "TIMESYS",
    "MJDREF",
    "MJDREFI",
    "MJDREFF",
    "TIMEZERO",
    "TIMZERO",
    "TSTART",
    "TSTOP",
    "TIMEDEL",
    "TIMEUNIT",
    "TIMEREF",
    "DATE-OBS",
    "DATE-END",
    "TIMEPIXR",
)


def extract_time_system_metadata(path: Union[Path, str]) -> Dict[str, Any]:
    """Scan all HDUs of a FITS file for time-system keywords and document observations.

    Does not modify the file or implement unilateral time system conversions.

    Args:
        path: Path to the FITS file.

    Returns:
        Dict[str, Any]: Structured report containing:
            - keywords_found: Mapping of keyword to observed values across HDUs.
            - consolidated_keywords: Best-effort merged dictionary of time parameters.
            - candidate_interpretations: Labelled interpretations requiring human confirmation.
            - unresolved_questions: Questions needing verification against official manuals.
    """
    file_path = Path(path)
    keywords_found: Dict[str, List[Dict[str, Any]]] = {}
    consolidated: Dict[str, Any] = {}

    with fits.open(str(file_path), mode="readonly", memmap=False) as hdul:
        for idx, hdu in enumerate(hdul):
            hdu_name = hdu.name if hdu.name else f"HDU_{idx}"
            for kw in TIME_SYSTEM_KEYWORDS:
                if kw in hdu.header:
                    val = hdu.header[kw]
                    com = hdu.header.comments[kw]
                    if kw not in keywords_found:
                        keywords_found[kw] = []
                    keywords_found[kw].append({
                        "hdu_index": idx,
                        "hdu_name": hdu_name,
                        "value": val,
                        "comment": com if com else "",
                    })
                    if kw not in consolidated:
                        consolidated[kw] = val

    # Candidate interpretations strictly labelled per requirements
    candidate_interpretations: List[str] = []
    unresolved_questions: List[str] = []

    timesys = consolidated.get("TIMESYS")
    mjdrefi = consolidated.get("MJDREFI", consolidated.get("MJDREF"))
    timeunit = consolidated.get("TIMEUNIT", "s")
    tstart = consolidated.get("TSTART")
    tstop = consolidated.get("TSTOP")
    date_obs = consolidated.get("DATE-OBS")

    if timesys:
        candidate_interpretations.append(
            f"Observed TIMESYS = '{timesys}'. "
            "(candidate interpretation — requires confirmation against official documentation)"
        )
    else:
        unresolved_questions.append("Header does not define TIMESYS; time standard is UNRESOLVED.")

    if mjdrefi == 40587:
        candidate_interpretations.append(
            "Observed MJDREFI = 40587. In standard astronomical FITS conventions, "
            "MJD 40587.0 represents the Unix Epoch (1970-01-01 00:00:00 UTC). "
            "(candidate interpretation — requires confirmation against official documentation)"
        )
    elif mjdrefi is not None:
        candidate_interpretations.append(
            f"Observed MJD reference: {mjdrefi}. "
            "(candidate interpretation — requires confirmation against official documentation)"
        )

    if tstart is not None and date_obs is not None:
        candidate_interpretations.append(
            f"Observed TSTART={tstart} {timeunit} alongside DATE-OBS='{date_obs}'. "
            "If timestamps denote elapsed seconds from MJD 40587, TSTART corresponds "
            f"closely to DATE-OBS. (candidate interpretation — requires confirmation against official documentation)"
        )

    if consolidated.get("TIMEREF"):
        candidate_interpretations.append(
            f"Observed TIMEREF = '{consolidated.get('TIMEREF')}'. "
            "(candidate interpretation — requires confirmation against official documentation)"
        )
    else:
        unresolved_questions.append(
            "TIMEREF keyword missing; barycentric/geocentric/spacecraft clock origin is UNRESOLVED."
        )

    return {
        "file_name": file_path.name,
        "keywords_found": keywords_found,
        "consolidated_keywords": consolidated,
        "candidate_interpretations": candidate_interpretations,
        "unresolved_questions": unresolved_questions,
    }
