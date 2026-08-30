import re
import pandas as pd


# ---------------------------------------------------------
# Common missing-value representations
# ---------------------------------------------------------

MISSING_VALUES = {
    "",
    " ",
    "null",
    "none",
    "nan",
    "n/a",
    "na",
    "not available",
    "not provided",
    "-",
    "--",
    "unknown",
}


# ---------------------------------------------------------
# Sector normalization
# ---------------------------------------------------------

SECTOR_MAP = {
    "energy": "Energy",
    "energy sector": "Energy",
    "power": "Energy",
    "powerline": "Powerline",

    "renewable": "Renewables",
    "renewables": "Renewables",
    "renewable energy": "Renewables",

    "railway": "Railways",
    "railways": "Railways",

    "mining": "Mining",

    "construction": "Construction",
}


# ---------------------------------------------------------
# Status normalization
# ---------------------------------------------------------

STATUS_MAP = {
    "open": "Open",
    "opened": "Open",

    "closed": "Closed",
    "close": "Closed",

    "won": "Won",
    "lost": "Lost",

    "in progress": "In Progress",
    "ongoing": "Ongoing",

    "not started": "Not Started",
    "pending": "Pending",

    "on hold": "On Hold",
    "hold": "On Hold",

    "completed": "Completed",
    "complete": "Completed",
    "done": "Completed",
}


# ---------------------------------------------------------
# Column aliases
#
# These allow the BI layer to work even when the source
# uses slightly different names.
# ---------------------------------------------------------

COLUMN_ALIASES = {
    "deal status": "Deal Status",

    "deal stage": "Deal Stage",
    "stage": "Deal Stage",

    "owner code": "Owner code",
    "client code": "Client Code",

    "masked deal value": "Masked Deal value",
    "deal value": "Masked Deal value",

    "closure probability": "Closure Probability",
    "close probability": "Closure Probability",

    "close date": "Close Date (A)",
    "close date (a)": "Close Date (A)",

    "tentative close date": "Tentative Close Date",

    "customer name code": "Customer Name Code",

    "execution status": "Execution Status",

    "nature of work": "Nature of Work",

    "document type": "Document Type",

    "billing status": "Billing Status",

    "collection status": "Collection status",

    "wo status (billed)": "WO Status (billed)",
}


# ---------------------------------------------------------
# Basic text cleaning
# ---------------------------------------------------------

def clean_text(value):

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    text = str(value)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Normalize unusual dash characters
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Treat common placeholders as missing
    if text.lower() in MISSING_VALUES:
        return None

    return text or None


# ---------------------------------------------------------
# Column-name cleaning
# ---------------------------------------------------------

def normalize_column_name(column):

    column = clean_text(column)

    if not column:
        return None

    # Normalize whitespace
    key = re.sub(r"\s+", " ", column).strip().lower()

    # Direct alias
    if key in COLUMN_ALIASES:
        return COLUMN_ALIASES[key]

    return column


# ---------------------------------------------------------
# Sector normalization
# ---------------------------------------------------------

def normalize_sector(value):

    value = clean_text(value)

    if not value:
        return None

    key = value.lower()

    if key in SECTOR_MAP:
        return SECTOR_MAP[key]

    return value.title()


# ---------------------------------------------------------
# Status normalization
# ---------------------------------------------------------

def normalize_status(value):

    value = clean_text(value)

    if not value:
        return None

    key = value.lower()

    if key in STATUS_MAP:
        return STATUS_MAP[key]

    return value.title()


# ---------------------------------------------------------
# Date normalization
# ---------------------------------------------------------

def normalize_date(value):

    if value is None:
        return pd.NaT

    try:
        if pd.isna(value):
            return pd.NaT
    except Exception:
        pass

    # Already a datetime
    if isinstance(value, pd.Timestamp):
        return value

    text = clean_text(value)

    if not text:
        return pd.NaT

    # Try normal parsing first
    parsed = pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=False
    )

    if pd.notna(parsed):
        return parsed

    # Try day-first formats as fallback
    parsed = pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=True
    )

    return parsed


# ---------------------------------------------------------
# Money / numeric normalization
# ---------------------------------------------------------

def normalize_money(value):

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, (int, float)):
        return float(value)

    text = clean_text(value)

    if not text:
        return None

    # Remove currency symbols and spaces
    text = (
        text
        .replace("₹", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("INR", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )

    # Handle accounting-style negative numbers:
    # (125000) -> -125000
    negative = (
        text.startswith("(")
        and text.endswith(")")
    )

    text = text.replace("(", "")
    text = text.replace(")", "")

    # Remove commas
    text = text.replace(",", "")

    # Remove percentage sign if accidentally present
    text = text.replace("%", "")

    # Keep only numeric characters, decimal point and minus
    text = re.sub(r"[^0-9.\-]", "", text)

    if not text:
        return None

    try:
        number = float(text)

        if negative:
            number = -abs(number)

        return number

    except ValueError:
        return None


# ---------------------------------------------------------
# Probability normalization
# ---------------------------------------------------------

def normalize_probability(value):

    value = clean_text(value)

    if not value:
        return None

    text = value.lower()

    # Examples:
    # 50%
    # 0.5
    # 50
    if text.endswith("%"):

        try:
            return float(
                text[:-1].strip()
            ) / 100

        except ValueError:
            return None

    try:

        number = float(text)

        # 50 means 50%
        if number > 1:
            number = number / 100

        return number

    except ValueError:

        # Handle labels
        probability_map = {
            "high": 1.0,
            "medium": 0.5,
            "low": 0.25,
        }

        return probability_map.get(text)


# ---------------------------------------------------------
# Normalize one DataFrame
# ---------------------------------------------------------

def normalize_frame(df, kind):

    if df is None:
        return pd.DataFrame()

    df = df.copy()

    # -----------------------------------------------------
    # Normalize column names
    # -----------------------------------------------------

    new_columns = []

    for index, column in enumerate(df.columns):

        normalized = normalize_column_name(column)

        if normalized is None:
            normalized = f"unnamed_{index}"

        new_columns.append(normalized)

    df.columns = new_columns
    # -----------------------------------------------------
    # Prevent duplicate column names from breaking pandas
    # operations such as Series.str
    # -----------------------------------------------------

    seen = {}
    unique_columns = []

    for column in df.columns:

        if column not in seen:

            seen[column] = 0
            unique_columns.append(column)

        else:

            seen[column] += 1

            unique_columns.append(
                f"{column}_{seen[column]}"
            )

    df.columns = unique_columns
    # -----------------------------------------------------
    # Normalize every cell that looks like text
    # -----------------------------------------------------

    for column in df.columns:

        # Skip columns that should remain numeric/date
        lower = column.lower()

        if (
            "date" not in lower
            and "month" not in lower
            and "value" not in lower
            and "amount" not in lower
            and "rupees" not in lower
        ):

            df[column] = df[column].apply(clean_text)

    # -----------------------------------------------------
    # Date columns
    # -----------------------------------------------------

    for column in df.columns:

        lower = column.lower()

        if (
            "date" in lower
            or "month" in lower
        ):

            # Do not treat recurring project month as a date
            # unless it actually contains date-like values.
            df[column] = df[column].apply(
                normalize_date
            )

    # -----------------------------------------------------
    # Sector
    # -----------------------------------------------------

    if "Sector" in df.columns:

        df["Sector"] = df["Sector"].apply(
            normalize_sector
        )

    # -----------------------------------------------------
    # DEALS
    # -----------------------------------------------------

    if kind == "deals":

        # Deal value
        if "Masked Deal value" in df.columns:

            df["Masked Deal value"] = (
                df["Masked Deal value"]
                .apply(normalize_money)
            )

        # Deal status
        if "Deal Status" in df.columns:

            df["Deal Status"] = (
                df["Deal Status"]
                .apply(normalize_status)
            )

        # Deal stage
        if "Deal Stage" in df.columns:

            df["Deal Stage"] = (
                df["Deal Stage"]
                .apply(clean_text)
            )

        # Closure probability
        if "Closure Probability" in df.columns:

            df["Closure Probability"] = (
                df["Closure Probability"]
                .apply(normalize_probability)
            )

    # -----------------------------------------------------
    # WORK ORDERS
    # -----------------------------------------------------

    else:

        # Normalize all financial columns
        money_columns = [

            column

            for column in df.columns

            if (
                "rupees" in column.lower()
                or "amount" in column.lower()
                or "receivable" in column.lower()
                or "value" in column.lower()
            )
        ]

        for column in money_columns:

            df[column] = (
                df[column]
                .apply(normalize_money)
            )

        # Normalize common categorical fields
        status_columns = [
            "Execution Status",
            "Billing Status",
            "Collection status",
            "WO Status (billed)",
        ]

        for column in status_columns:

            if column in df.columns:

                df[column] = (
                    df[column]
                    .apply(normalize_status)
                )

        # General text columns
        text_columns = [
            "Nature of Work",
            "Document Type",
        ]

        for column in text_columns:

            if column in df.columns:

                df[column] = (
                    df[column]
                    .apply(clean_text)
                )

    return df


# ---------------------------------------------------------
# Data quality report
# ---------------------------------------------------------

def quality_report(df):

    if df is None or df.empty:

        return {
            "rows": 0,
            "columns": 0,
            "missing_cells": 0,
            "missing_percentage": 0,
            "missing_by_column": {},
        }

    missing_by_column = (
        df.isna()
        .sum()
        .to_dict()
    )

    missing_cells = int(
        df.isna()
        .sum()
        .sum()
    )

    total_cells = (
        len(df)
        * len(df.columns)
    )

    missing_percentage = (
        round(
            missing_cells
            / total_cells
            * 100,
            2
        )
        if total_cells
        else 0
    )

    return {

        "rows": len(df),

        "columns": len(df.columns),

        "missing_cells":
            missing_cells,

        "missing_percentage":
            missing_percentage,

        "missing_by_column": {
            str(key): int(value)

            for key, value
            in missing_by_column.items()

            if value > 0
        },
    }


# ---------------------------------------------------------
# Identify columns that are completely missing
# ---------------------------------------------------------

def completely_missing_columns(df):

    if df is None or df.empty:
        return []

    return [
        column

        for column in df.columns

        if df[column].isna().all()
    ]


# ---------------------------------------------------------
# Human-readable data-quality summary
# ---------------------------------------------------------

def quality_summary(df):

    report = quality_report(df)

    completely_missing = (
        completely_missing_columns(df)
    )

    return {

        "rows":
            report["rows"],

        "columns":
            report["columns"],

        "missing_cells":
            report["missing_cells"],

        "missing_percentage":
            report["missing_percentage"],

        "completely_missing_columns":
            completely_missing,

        "missing_by_column":
            report["missing_by_column"],
    }