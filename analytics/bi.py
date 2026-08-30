import pandas as pd


PROB = {
    "High": 1.0,
    "Medium": 0.5,
    "Low": 0.25,
}


def pipeline_summary(deals, sector=None, start=None, end=None):
    """
    Calculate pipeline metrics.

    Important:
    - total_deals = ALL deals
    - open_deals = deals whose status is Open
    """

    d = deals.copy()

    total_deals = len(d)    

    if sector and "Sector" in d:
        d = d[
            d["Sector"]
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq(str(sector).strip().casefold())
        ]

    if start is not None and "Tentative Close Date" in d:
        d = d[
            d["Tentative Close Date"].ge(
                pd.Timestamp(start)
            )
        ]

    if end is not None and "Tentative Close Date" in d:
        d = d[
            d["Tentative Close Date"].lt(
                pd.Timestamp(end)
            )
        ]

    filtered_deals = len(d)

    if "Deal Status" in d.columns:

        status = d["Deal Status"].copy()

        # Normalize status values defensively
        status = (
            status
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        open_d = d[status == "open"].copy()

    else:
        open_d = d.copy()

    open_deals = len(open_d)

    # Pipeline value
    if "Masked Deal value" in open_d:
        values = pd.to_numeric(
            open_d["Masked Deal value"],
            errors="coerce"
        )
        pipeline_value = float(values.sum(min_count=1) or 0)
    else:
        pipeline_value = 0.0

    # -------------------------------------------------
    # Weighted pipeline
    #
    # Closure Probability has already been normalized
    # to a numeric value between 0 and 1.
    # -------------------------------------------------

    weighted_pipeline = 0.0

    if (
        "Masked Deal value" in open_d.columns
        and "Closure Probability" in open_d.columns
    ):

        values = pd.to_numeric(
            open_d["Masked Deal value"],
            errors="coerce"
        )

        probabilities = pd.to_numeric(
            open_d["Closure Probability"],
            errors="coerce"
        )

        valid = (
            values.notna()
            & probabilities.notna()
        )

        weighted_pipeline = float(
            (
                values[valid]
                * probabilities[valid]
            ).sum()
        )

    stages = {}

    if "Deal Stage" in open_d:
        stages = (
            open_d["Deal Stage"]
            .value_counts(dropna=False)
            .to_dict()
        )

    return {
        "total_deals": total_deals,
        "filtered_deals": filtered_deals,
        "open_deals": open_deals,
        "pipeline_value": pipeline_value,
        "weighted_pipeline": float(weighted_pipeline),
        "stages": stages,
    }


def work_order_summary(wo):

    out = {
        "total_work_orders": len(wo)
    }

    # -----------------------------------------------
    # Execution status breakdown
    # -----------------------------------------------

    if "Execution Status" in wo.columns:

        status = (
            wo["Execution Status"]
            .fillna("Unknown / Missing")
            .astype(str)
            .str.strip()
        )

        out["execution_status"] = (
            status
            .value_counts()
            .to_dict()
        )

        # -------------------------------------------
        # Operational risk statuses
        # -------------------------------------------

        risk_statuses = {
            "not started",
            "pause / struck",
            "details pending from client",
            "unknown / missing",
        }

        risk_mask = (
            status
            .str.casefold()
            .isin(risk_statuses)
        )

        risky = wo[risk_mask].copy()

        out["at_risk_count"] = len(risky)

        # -------------------------------------------
        # Include project/customer identifiers
        # -------------------------------------------

        project_column = None

        for candidate in [
            "Item Name",
            "Deal name masked",
            "Deal Name",
            "Item",
        ]:

            if candidate in risky.columns:

                project_column = candidate
                break

        if project_column:

            out["at_risk_projects"] = (
                risky[project_column]
                .fillna("Unnamed project")
                .astype(str)
                .str.strip()
                .tolist()
            )

        else:

            out["at_risk_projects"] = []

    else:

        out["execution_status"] = {}

        out["at_risk_count"] = 0

        out["at_risk_projects"] = []

    # -----------------------------------------------
    # Financial metrics
    # -----------------------------------------------

    for col, key in [

        (
            "Amount in Rupees (Incl of GST) (Masked)",
            "contract_value",
        ),

        (
            "Billed Value in Rupees (Incl of GST.) (Masked)",
            "billed_value",
        ),

        (
            "Collected Amount in Rupees (Incl of GST.) (Masked)",
            "collected_value",
        ),

        (
            "Amount Receivable (Masked)",
            "receivable",
        ),

    ]:

        if col in wo.columns:

            values = pd.to_numeric(
                wo[col],
                errors="coerce"
            )

            out[key] = float(
                values.sum()
            )

    return out



def _get_column(df, column_name):

    if column_name not in df.columns:
        return None

    result = df[column_name]

    # Duplicate column names can return a DataFrame.
    if isinstance(result, pd.DataFrame):
        result = result.iloc[:, 0]

    return result


def cross_board(deals, wo):

    # -------------------------------------------------
    # DEALS
    # -------------------------------------------------

    deal_client_series = _get_column(
        deals,
        "Client Code"
    )

    deal_status_series = _get_column(
        deals,
        "Deal Status"
    )

    if (
        deal_client_series is not None
        and deal_status_series is not None
    ):

        deal_status = (
            deal_status_series
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        open_deals = deals[
            deal_status == "open"
        ].copy()

        open_deal_clients = (
            _get_column(
                open_deals,
                "Client Code"
            )
            .dropna()
            .astype(str)
            .str.strip()
        )

        open_deal_clients = set(
            open_deal_clients[
                open_deal_clients != ""
            ]
        )

    else:

        open_deal_clients = set()


    # -------------------------------------------------
    # WORK ORDERS
    # -------------------------------------------------

    wo_client_series = _get_column(
        wo,
        "Customer Name Code"
    )

    wo_status_series = _get_column(
        wo,
        "Execution Status"
    )

    if wo_client_series is not None:

        wo_clients = (
            wo_client_series
            .dropna()
            .astype(str)
            .str.strip()
        )

        wo_clients = set(
            wo_clients[
                wo_clients != ""
            ]
        )

        # If execution status exists, identify active
        # work orders.
        if wo_status_series is not None:

            execution_status = (
                wo_status_series
                .fillna("")
                .astype(str)
                .str.strip()
                .str.casefold()
            )

            active_mask = execution_status.isin([
                "ongoing",
                "in progress",
                "executed until current month",
                "working on it",
                "started",
            ])

            active_wo = wo[
                active_mask
            ].copy()

            active_wo_clients = (
                _get_column(
                    active_wo,
                    "Customer Name Code"
                )
                .dropna()
                .astype(str)
                .str.strip()
            )

            active_wo_clients = set(
                active_wo_clients[
                    active_wo_clients != ""
                ]
            )

        else:

            active_wo_clients = wo_clients

    else:

        active_wo_clients = set()


    # -------------------------------------------------
    # OVERLAP
    # -------------------------------------------------

    overlap = (
        open_deal_clients
        & active_wo_clients
    )

    return {

        "open_deal_customer_count":
            len(open_deal_clients),

        "active_work_order_customer_count":
            len(active_wo_clients),

        "overlap_customer_codes":
            sorted(overlap),

        "overlap_count":
            len(overlap),
    }