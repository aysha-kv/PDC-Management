# Copyright (c) 2026, Aysha kv and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

from erpnext.accounts.report.general_ledger.general_ledger import (
    execute as general_ledger_execute,
)


def execute(filters=None):
    """
    General Ledger (PDC)
    - Reuses ERPNext General Ledger
    - Shows Pending PDC details (Payment Entry wise)
    - Shows 'Clearance Date' label ONLY inside PDC section
    - Adds conditional PDC Summary & Effective Balance
    """

    columns, data = general_ledger_execute(filters)

    if not data:
        return columns, data

    party_type = filters.get("party_type") if filters else None

    pdc_receivable = get_pdc_receivable_account()
    pdc_payable = get_pdc_payable_account()

    show_receivable = False
    show_payable = False

    if not party_type:
        show_receivable = True
        show_payable = True
    elif party_type == "Customer":
        show_receivable = True
    elif party_type == "Supplier":
        show_payable = True

    if not show_receivable and not show_payable:
        return columns, data

    pe_names = {
        row.get("voucher_no")
        for row in data
        if isinstance(row, dict)
        and row.get("voucher_type") == "Payment Entry"
    }

    pending_pe_map = get_pending_pdc_map(pe_names)


    pdc_receivable_pending = 0.0
    pdc_payable_pending = 0.0

    if show_receivable and pdc_receivable:
        pdc_receivable_pending = calculate_pdc_pending(
            data, pending_pe_map, pdc_receivable, side="credit"
        )

    if show_payable and pdc_payable:
        pdc_payable_pending = calculate_pdc_pending(
            data, pending_pe_map, pdc_payable, side="debit"
        )

    closing_balance = get_closing_balance(data)


    append_pending_pdc_rows(
        data,
        pending_pe_map,
        pdc_receivable,
        pdc_payable,
        show_receivable,
        show_payable,
    )

    append_pdc_summary(
        data,
        pdc_receivable_pending,
        pdc_payable_pending,
        closing_balance,
        show_receivable,
        show_payable,
    )

    return columns, data


def get_pdc_receivable_account():
    try:
        return frappe.get_single("Accounts Settings").custom_pdc_receivable_account
    except Exception:
        return None


def get_pdc_payable_account():
    try:
        return frappe.get_single("Accounts Settings").custom_pdc_payable_account
    except Exception:
        return None


def get_pending_pdc_map(pe_names):
    """
    Fetch only Pending PDC Payment Entries
    """
    if not pe_names:
        return {}

    return {
        d.name: d
        for d in frappe.get_all(
            "Payment Entry",
            filters={
                "name": ["in", list(pe_names)],
                "custom_pdc_status": "Pending",
                "docstatus": 1,
            },
            fields=[
                "name",
                "custom_clearance_date",
                "party_type",
                "party",
            ],
        )
    }


def calculate_pdc_pending(data, pending_pe_map, pdc_account, side):
    """
    Calculate total pending PDC amount
    """
    total = 0.0

    for row in data:
        if not isinstance(row, dict):
            continue

        if row.get("voucher_type") != "Payment Entry":
            continue

        if row.get("voucher_no") not in pending_pe_map:
            continue

        if row.get("against") != pdc_account:
            continue

        amount = flt(row.get(side, 0))
        if amount > 0:
            total += amount

    return flt(total)


def get_closing_balance(data):
    """
    Extract closing balance from GL output
    """
    for row in reversed(data):
        if isinstance(row, dict) and row.get("balance") is not None:
            return flt(row.get("balance"))
    return 0.0


def append_pending_pdc_rows(
    data,
    pending_pe_map,
    pdc_receivable,
    pdc_payable,
    show_receivable,
    show_payable,
):
    """
    Append detailed Pending PDC rows
    Adds a visual 'Clearance Date' label inside Posting Date column
    ONLY for the PDC section
    """

    if not pending_pe_map:
        return

    data.append({})
    data.append({
        "account": "— Pending PDC Details —",
        "is_group": 1,
    })

    data.append({
        "posting_date": "Clearance Date",
        "account": "",
        "debit": "",
        "credit": "",
        "balance": "",
        "voucher_type": "",
        "voucher_no": "",
        "against": "",
        "party_type": "",
        "party": "",
        "remarks": "",
    })

    for row in data.copy():
        if not isinstance(row, dict):
            continue

        if row.get("voucher_type") != "Payment Entry":
            continue

        pe_name = row.get("voucher_no")
        if pe_name not in pending_pe_map:
            continue

        against = row.get("against")

        if against == pdc_receivable and not show_receivable:
            continue

        if against == pdc_payable and not show_payable:
            continue

        pe = pending_pe_map[pe_name]

        data.append({
            "posting_date": pe.custom_clearance_date,
            "account": against,
            "debit": row.get("debit"),
            "credit": row.get("credit"),
            "voucher_type": "Payment Entry",
            "voucher_no": pe_name,
            "party_type": pe.party_type,
            "party": pe.party,
            "remarks": "Pending PDC",
        })


def append_pdc_summary(
    data,
    pdc_receivable_pending,
    pdc_payable_pending,
    closing_balance,
    show_receivable,
    show_payable,
):
    """
    Append PDC Summary rows
    """

    effective_balance = flt(closing_balance)

    if show_receivable:
        effective_balance += flt(pdc_receivable_pending)

    if show_payable:
        effective_balance -= flt(pdc_payable_pending)

    data.append({})

    data.append({
        "account": "— PDC Summary —",
        "is_group": 1,
    })

    if show_receivable:
        data.append({
            "account": "PDC Receivable Pending",
            "debit": pdc_receivable_pending,
            "credit": 0,
            "balance": "",
        })

    if show_payable:
        data.append({
            "account": "PDC Payable Pending",
            "debit": 0,
            "credit": pdc_payable_pending,
            "balance": "",
        })

    data.append({
        "account": "Effective Balance",
        "balance": effective_balance,
    })
