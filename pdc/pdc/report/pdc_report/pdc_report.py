# Copyright (c) 2026, Aysha kv and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    filters = frappe._dict(filters or {})

    filters.setdefault("company", "")
    filters.setdefault("from_date", None)
    filters.setdefault("to_date", None)
    filters.setdefault("pdc_type", "")
    filters.setdefault("pdc_status", "")
    filters.setdefault("party_type", "")
    filters.setdefault("party", "")

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Payment Entry",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 160
        },
        {
            "label": "PDC Type",
            "fieldname": "pdc_type",
            "width": 130
        },
        {
            "label": "PDC Status",
            "fieldname": "pdc_status",
            "width": 120
        },
        {
            "label": "Party Type",
            "fieldname": "party_type",
            "width": 120
        },
        {
            "label": "Party",
            "fieldname": "party",
            "width": 180
        },
        {
            "label": "Cheque No",
            "fieldname": "cheque_no",
            "width": 120
        },
        {
            "label": "Cheque Date",
            "fieldname": "cheque_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "PDC Amount",
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": "Clearance Date",
            "fieldname": "clearance_date",
            "fieldtype": "Date",
            "width": 130
        },
        {
            "label": "Pending Days",
            "fieldname": "pending_days",
            "width": 120
        }
    ]


def get_data(filters):
    return frappe.db.sql("""
        SELECT
            pe.name,
            CASE
                WHEN pe.payment_type = 'Receive'
                    THEN 'PDC Receivable'
                ELSE 'PDC Payable'
            END AS pdc_type,
            pe.custom_pdc_status AS pdc_status,
            pe.party_type,
            pe.party,
            pe.custom_cheque_number AS cheque_no,
            pe.custom_cheque_date AS cheque_date,
            pe.paid_amount,
            pe.custom_clearance_date AS clearance_date,
            CASE
                WHEN pe.custom_pdc_status = 'Pending'
                    THEN DATEDIFF(%(to_date)s, pe.custom_cheque_date)
                ELSE NULL
            END AS pending_days
        FROM `tabPayment Entry` pe
        WHERE
            pe.docstatus = 1
            AND pe.custom_is_pdc = 1
            AND pe.company = %(company)s
            AND pe.custom_cheque_date BETWEEN %(from_date)s AND %(to_date)s

            AND (
                %(pdc_type)s = ''
                OR (
                    %(pdc_type)s = 'PDC Receivable'
                    AND pe.payment_type = 'Receive'
                )
                OR (
                    %(pdc_type)s = 'PDC Payable'
                    AND pe.payment_type = 'Pay'
                )
            )

            AND (
                %(pdc_status)s = ''
                OR pe.custom_pdc_status = %(pdc_status)s
            )

            AND (
                %(party_type)s = ''
                OR pe.party_type = %(party_type)s
            )

            AND (
                %(party)s = ''
                OR pe.party = %(party)s
            )

        ORDER BY pe.custom_cheque_date
    """, filters, as_dict=True)
