import os
import json

from google import genai

from .prompts import SYSTEM_PROMPT

from data.normalizer import (
    normalize_frame,
    quality_report,
)

from analytics.bi import (
    pipeline_summary,
    work_order_summary,
    cross_board,
)


class BIAGent:

    def __init__(self, monday_client):

        self.monday = monday_client

        self.llm = (
            genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )
            if os.getenv("GEMINI_API_KEY")
            else None
        )

        self._cache = None

    def fetch(self):

        wo = self.monday.get_board_items(
            os.getenv(
                "MONDAY_WORK_ORDERS_BOARD_ID"
            )
        )

        deals = self.monday.get_board_items(
            os.getenv(
                "MONDAY_DEALS_BOARD_ID"
            )
        )

        return wo, deals

    @staticmethod
    def items_to_df(board):

        import pandas as pd

        if not board:
            return pd.DataFrame()

        column_map = {
            c["id"]: c["title"]
            for c in board.get("columns", [])
        }

        rows = []

        items = (
            board
            .get("items_page", {})
            .get("items", [])
        )

        for item in items:

            row = {
                "Item Name": item.get("name")
            }

            for column_value in item.get(
                "column_values",
                []
            ):

                column_id = column_value.get("id")

                column_name = column_map.get(
                    column_id,
                    column_id
                )

                row[column_name] = (
                    column_value.get("text")
                )

            rows.append(row)

        return pd.DataFrame(rows)

    def answer(self, question):

        # -------------------------------------------------
        # 1. Retrieve live data from Monday.com
        # -------------------------------------------------

        wo_raw, deals_raw = self.fetch()

        # -------------------------------------------------
        # 2. Convert Monday data to DataFrames
        # -------------------------------------------------

        wo = normalize_frame(
            self.items_to_df(wo_raw),
            "work_orders"
        )

        deals = normalize_frame(
            self.items_to_df(deals_raw),
            "deals"
        )

        # -------------------------------------------------
        # 3. Calculate deterministic business metrics
        # -------------------------------------------------

        work_summary = work_order_summary(wo)

        deal_summary = pipeline_summary(deals)

        cross_summary = cross_board(
            deals,
            wo
        )

        # -------------------------------------------------
        # 4. Build context for Gemini
        # -------------------------------------------------

        context = {

            "question": question,

            "EXACT_TOTAL_WORK_ORDERS":
                len(wo),

            "EXACT_TOTAL_DEALS":
                len(deals),

            "work_orders_summary":
                work_summary,

            "deals_pipeline":
                deal_summary,

            "cross_board":
                cross_summary,

            "work_orders_quality":
                quality_report(wo),

            "deals_quality":
                quality_report(deals),
        }

        # -------------------------------------------------
        # 5. If Gemini is unavailable, return raw metrics
        # -------------------------------------------------

        if not self.llm:

            return json.dumps(
                context,
                default=str,
                indent=2
            )

        # -------------------------------------------------
        # 6. Tell Gemini exact metrics must not be changed
        # -------------------------------------------------

        prompt = (
            SYSTEM_PROMPT
            + """

IMPORTANT NUMERICAL RULES:

1. EXACT_TOTAL_WORK_ORDERS is the exact number
   of Work Orders retrieved from Monday.com.

2. EXACT_TOTAL_DEALS is the exact number
   of Deals retrieved from Monday.com.

3. Do NOT confuse total deals with open deals.

4. If the user asks "How many deals are there?",
   answer using EXACT_TOTAL_DEALS.

5. If the user asks "How many open deals are there?",
   answer using deals_pipeline.open_deals.

6. Do not invent or recalculate exact counts.

7. Use the Python-calculated metrics as the
   source of truth.

IMPORTANT OPERATIONAL-RISK RULES:

If the user asks which projects are operationally at risk,
use work_orders_summary.at_risk_projects.

Do not claim that project names are unavailable if
at_risk_projects contains names.

Report the count first, followed by the most relevant
project names.

Treat "Unknown / Missing" execution status as an
information-quality risk, not proof that the project
itself is operationally delayed.

For operational-risk questions, group the at-risk projects
by their execution status when the underlying data allows it.

Do not interpret repeated project names as repeated failures.
They may represent separate work orders.

State the risk count as a percentage of total work orders.

Use precise wording:
"X of Y work orders are flagged by the defined
operational-risk rules."

Do not say that all work orders are active unless the data
explicitly supports that conclusion.

DATA CONTEXT:
"""
            + json.dumps(
                context,
                default=str
            )
            + """

USER QUESTION:
"""
            + question
        )

        # -------------------------------------------------
        # 7. Gemini with retry for temporary 503/429
        # -------------------------------------------------

        import time

        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        for attempt in range(3):

            try:

                response = (
                    self.llm
                    .models
                    .generate_content(
                        model=model,
                        contents=prompt,
                    )
                )

                return response.text

            except Exception as e:

                error_text = str(e)

                if (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "429" in error_text
                ):

                    if attempt < 2:

                        time.sleep(
                            2 ** attempt
                        )

                        continue

                raise