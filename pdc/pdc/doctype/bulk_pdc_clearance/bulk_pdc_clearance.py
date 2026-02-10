import frappe
from frappe.model.document import Document


class BulkPDCClearance(Document):
    pass


@frappe.whitelist()
def fetch_pending_pdcs(docname):
    """
    STEP 3:
    Fetch Pending PDC Payment Entries based on Cheque Date
    Supports filtering by PDC Type (Receivable / Payable / Both)
    Populate child table for preview
    (NO CLEARANCE DONE HERE)
    """

    doc = frappe.get_doc("Bulk PDC Clearance", docname)

    if not doc.company or not doc.cheque_date:
        frappe.throw("Company and Cheque Date are required")

    doc.set("pdc_entries", [])

    filters = {
        "company": doc.company,
        "custom_is_pdc": 1,
        "custom_pdc_status": "Pending",
        "custom_cheque_date": doc.cheque_date,
        "docstatus": 1,
    }

   
    if doc.pdc_type == "Receivable":
        filters["payment_type"] = "Receive"
    elif doc.pdc_type == "Payable":
        filters["payment_type"] = "Pay"

    payment_entries = frappe.get_all(
        "Payment Entry",
        filters=filters,
        fields=[
            "name",
            "party_type",
            "party",
            "payment_type",
            "custom_cheque_date",
            "paid_amount",
            "custom_clearance_date",
        ],
    )

    total_amount = 0
    valid_count = 0

    for pe in payment_entries:

        pdc_type = "Receivable" if pe.payment_type == "Receive" else "Payable"

        if not pe.custom_clearance_date:
            doc.append("pdc_entries", {
                "payment_entry": pe.name,
                "party_type": pe.party_type,
                "party": pe.party,
                "pdc_type": pdc_type,
                "cheque_date": pe.custom_cheque_date,
                "amount": pe.paid_amount,
                "status": "Skipped",
                "remarks": "Clearance date not set in Payment Entry",
            })
            continue

        doc.append("pdc_entries", {
            "payment_entry": pe.name,
            "party_type": pe.party_type,
            "party": pe.party,
            "pdc_type": pdc_type,
            "cheque_date": pe.custom_cheque_date,
            "clearance_date": pe.custom_clearance_date,
            "amount": pe.paid_amount,
            "status": "Pending",
        })

        total_amount += pe.paid_amount
        valid_count += 1

    doc.total_pdc = valid_count
    doc.total_amount = total_amount

    doc.save(ignore_permissions=True)

    return {
        "total_pdc": valid_count,
        "total_amount": total_amount,
        "has_data": True if valid_count else False
    }


# @frappe.whitelist()
# def bulk_clear_pdcs(docname):
#     """
#     STEP 5:
#     Perform actual bulk PDC clearance
#     Reuses existing single-PDC clear logic
#     """

#     doc = frappe.get_doc("Bulk PDC Clearance", docname)

#     if doc.status != "Draft":
#         frappe.throw("Only Draft documents can be cleared")

#     if not doc.pdc_entries:
#         frappe.throw("No PDC entries to clear")

#     cleared_count = 0
#     failed_count = 0

#     for row in doc.pdc_entries:

#         if row.status != "Pending":
#             continue

#         try:
#             frappe.call(
#                 "pdc.pdc.custom_script.payment_entry.clear_pdc",
#                 payment_entry=row.payment_entry
#             )

#             row.status = "Cleared"
#             row.remarks = "Cleared successfully"

#             cleared_count += 1

#         except Exception as e:
#             row.status = "Failed"
#             row.remarks = str(e)
#             failed_count += 1

#     if cleared_count and not failed_count:
#         doc.status = "Completed"
#     elif cleared_count and failed_count:
#         doc.status = "Failed"
#     else:
#         doc.status = "Draft"

#     doc.cleared_on = frappe.utils.now()
#     doc.save(ignore_permissions=True)

#     return {
#         "cleared": cleared_count,
#         "failed": failed_count
#     }


import frappe

@frappe.whitelist()
def bulk_clear_pdcs(docname, clearance_date=None, clearance_bank_account=None):
	"""
	STEP 5:
	Perform actual bulk PDC clearance
	Uses single PDC clear logic with shared clearance inputs
	"""

	doc = frappe.get_doc("Bulk PDC Clearance", docname)

	if doc.status != "Draft":
		frappe.throw("Only Draft documents can be cleared")

	if not doc.pdc_entries:
		frappe.throw("No PDC entries to clear")

	if not clearance_date:
		frappe.throw("Clearance Date is required")

	if not clearance_bank_account:
		frappe.throw("Clearance Bank Account is required")

	cleared_count = 0
	failed_count = 0

	for row in doc.pdc_entries:

		if row.status != "Pending":
			continue

		try:
			# Reuse single PDC clearance logic
			frappe.call(
				"pdc.pdc.custom_script.payment_entry.clear_pdc",
				payment_entry=row.payment_entry,
				clearance_date=clearance_date,
				clearance_bank_account=clearance_bank_account
			)

			row.status = "Cleared"
			row.remarks = "Cleared successfully"
			cleared_count += 1

		except Exception as e:
			row.status = "Failed"
			row.remarks = str(e)
			failed_count += 1

	# Final document status
	if cleared_count and not failed_count:
		doc.status = "Completed"
	elif cleared_count and failed_count:
		doc.status = "Failed"
	else:
		doc.status = "Draft"

	doc.cleared_on = frappe.utils.now()
	doc.save(ignore_permissions=True)

	return {
		"cleared": cleared_count,
		"failed": failed_count
	}
