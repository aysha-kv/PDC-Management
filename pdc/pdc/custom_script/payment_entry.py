import frappe
from frappe.utils import nowdate


# @frappe.whitelist()
# def clear_pdc(payment_entry):
#     pe = frappe.get_doc("Payment Entry", payment_entry)

#     # 1. Basic safety checks
#     if pe.docstatus != 1:
#         frappe.throw("Payment Entry must be submitted")

#     if not pe.custom_is_pdc:
#         frappe.throw("Not a PDC Payment Entry")

#     if pe.custom_pdc_status != "Pending":
#         frappe.throw("Only Pending PDC can be cleared")

#     if not pe.custom_clearance_date:
#         frappe.throw("Please set Clearance Date")

#     if not pe.custom_clearance_bank_account:
#         frappe.throw("Please select Clearance Bank Account")

#     if pe.paid_amount <= 0:
#         frappe.throw("Invalid paid amount for PDC")

#     # 2. Cheque date validation (VERY IMPORTANT)
#     if pe.custom_cheque_date and getdate(pe.custom_clearance_date) < getdate(pe.custom_cheque_date):
#         frappe.throw("Clearance Date cannot be before Cheque Date")

#     # 3. Fetch settings
#     settings = frappe.get_single("Accounts Settings")
#     bank_account = pe.custom_clearance_bank_account

#     # 4. Create Journal Entry
#     je = frappe.new_doc("Journal Entry")
#     je.voucher_type = "Journal Entry"
#     je.company = pe.company
#     je.posting_date = pe.custom_clearance_date
#     je.remark = f"PDC Clearance for Payment Entry {pe.name}"
#     je.user_remark = f"Auto-generated PDC Clearance JE for {pe.name}"

#     if pe.payment_type == "Receive":
#         pdc_account = settings.custom_pdc_receivable_account

#         je.append("accounts", {
#             "account": bank_account,
#             "debit_in_account_currency": pe.paid_amount,
#             "reference_type": "Payment Entry",
#             "reference_name": pe.name
#         })

#         je.append("accounts", {
#             "account": pdc_account,
#             "credit_in_account_currency": pe.paid_amount,
#             "reference_type": "Payment Entry",
#             "reference_name": pe.name
#         })

#     elif pe.payment_type == "Pay":
#         pdc_account = settings.custom_pdc_payable_account

#         je.append("accounts", {
#             "account": pdc_account,
#             "debit_in_account_currency": pe.paid_amount,
#             "reference_type": "Payment Entry",
#             "reference_name": pe.name
#         })

#         je.append("accounts", {
#             "account": bank_account,
#             "credit_in_account_currency": pe.paid_amount,
#             "reference_type": "Payment Entry",
#             "reference_name": pe.name
#         })

#     else:
#         frappe.throw("Unsupported Payment Type for PDC")

#     # 5. Insert & submit JE
#     je.insert(ignore_permissions=True)
#     je.submit()

#     # 6. Mark PDC as cleared
#     pe.db_set("custom_pdc_status", "Cleared")

#     return {
#         "journal_entry": je.name,
#         "status": "Cleared"
#     }

# @frappe.whitelist()
# def mark_pdc_as_bounced(payment_entry):
#     pe = frappe.get_doc("Payment Entry", payment_entry)

#     if not pe.custom_is_pdc:
#         frappe.throw("This Payment Entry is not marked as PDC")

#     if pe.docstatus != 1:
#         frappe.throw("Payment Entry must be submitted")

#     if pe.custom_pdc_status in ("Cleared", "Bounced"):
#         frappe.throw(f"Cheque already {pe.custom_pdc_status}")

#     settings = frappe.get_single("Accounts Settings")
#     pdc_receivable = settings.custom_pdc_receivable_account
#     pdc_payable = settings.custom_pdc_payable_account

#     if not pdc_receivable or not pdc_payable:
#         frappe.throw("Configure PDC accounts in Accounts Settings")

#     if not pe.references:
#         frappe.throw("No invoice references found in Payment Entry")

#     je = frappe.new_doc("Journal Entry")
#     je.voucher_type = "Journal Entry"
#     je.company = pe.company
#     je.posting_date = nowdate()
#     je.remark = f"PDC Cheque bounced for Payment Entry {pe.name}"

#     for ref in pe.references:
#         amount = ref.allocated_amount
#         if amount <= 0:
#             continue

#         if pe.payment_type == "Receive":
#             je.append("accounts", {
#                 "account": pe.party_account,
#                 "party_type": pe.party_type,
#                 "party": pe.party,
#                 "against_voucher_type": ref.reference_doctype,
#                 "against_voucher": ref.reference_name,
#                 "debit_in_account_currency": amount,
#             })

#             je.append("accounts", {
#                 "account": pdc_receivable,
#                 "credit_in_account_currency": amount,
#             })

#         else:
#             je.append("accounts", {
#                 "account": pdc_payable,
#                 "debit_in_account_currency": amount,
#             })

#             je.append("accounts", {
#                 "account": pe.party_account,
#                 "party_type": pe.party_type,
#                 "party": pe.party,
#                 "against_voucher_type": ref.reference_doctype,
#                 "against_voucher": ref.reference_name,
#                 "credit_in_account_currency": amount,
#             })

#     je.insert()
#     je.submit()

#     pe.custom_pdc_status = "Bounced"
#     pe.custom_clearance_date = None
#     pe.custom_clearance_bank_account = None

#     pe.add_comment(
#         "Info",
#         f"PDC bounced. Reversal Journal Entry {je.name} created and invoices reopened."
#     )

#     pe.save(ignore_permissions=True)

#     return {
#         "journal_entry": je.name,
#         "status": "Bounced"
#     }


import frappe
from frappe.utils import getdate

@frappe.whitelist()
def clear_pdc(payment_entry, clearance_date=None, clearance_bank_account=None):

	pe = frappe.get_doc("Payment Entry", payment_entry)

	# 1. Safety validations
	if pe.docstatus != 1:
		frappe.throw("Payment Entry must be submitted")

	if not pe.custom_is_pdc:
		frappe.throw("Not a PDC Payment Entry")

	if pe.custom_pdc_status != "Pending":
		frappe.throw("Only Pending PDC can be cleared")

	if pe.paid_amount <= 0:
		frappe.throw("Invalid paid amount")

	# 2. Set values from prompt
	if clearance_date:
		pe.custom_clearance_date = clearance_date

	if clearance_bank_account:
		pe.custom_clearance_bank_account = clearance_bank_account

	if not pe.custom_clearance_date:
		frappe.throw("Please set Clearance Date")

	if not pe.custom_clearance_bank_account:
		frappe.throw("Please select Clearance Bank Account")

	# 3. Cheque vs Clearance date validation
	if pe.custom_cheque_date and getdate(pe.custom_clearance_date) < getdate(pe.custom_cheque_date):
		frappe.throw("Clearance Date cannot be before Cheque Date")

	# 4. Fetch Accounts Settings
	settings = frappe.get_single("Accounts Settings")
	bank_account = pe.custom_clearance_bank_account

	# 5. Create Journal Entry
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = pe.company
	je.posting_date = pe.custom_clearance_date
	je.remark = f"PDC Clearance for Payment Entry {pe.name}"
	je.user_remark = f"Auto-generated PDC Clearance JE for {pe.name}"

	if pe.payment_type == "Receive":
		if not settings.custom_pdc_receivable_account:
			frappe.throw("PDC Receivable Account not set in Accounts Settings")

		je.append("accounts", {
			"account": bank_account,
			"debit_in_account_currency": pe.paid_amount,
			"reference_type": "Payment Entry",
			"reference_name": pe.name
		})

		je.append("accounts", {
			"account": settings.custom_pdc_receivable_account,
			"credit_in_account_currency": pe.paid_amount,
			"reference_type": "Payment Entry",
			"reference_name": pe.name
		})

	elif pe.payment_type == "Pay":
		if not settings.custom_pdc_payable_account:
			frappe.throw("PDC Payable Account not set in Accounts Settings")

		je.append("accounts", {
			"account": settings.custom_pdc_payable_account,
			"debit_in_account_currency": pe.paid_amount,
			"reference_type": "Payment Entry",
			"reference_name": pe.name
		})

		je.append("accounts", {
			"account": bank_account,
			"credit_in_account_currency": pe.paid_amount,
			"reference_type": "Payment Entry",
			"reference_name": pe.name
		})

	else:
		frappe.throw("Unsupported Payment Type")

	# 6. Submit Journal Entry
	je.insert(ignore_permissions=True)
	je.submit()

	# 7. Update Payment Entry
	pe.db_set({
		"custom_pdc_status": "Cleared",
		"custom_clearance_date": pe.custom_clearance_date,
		"custom_clearance_bank_account": pe.custom_clearance_bank_account
	})

	return {
		"journal_entry": je.name,
		"status": "Cleared"
	}


@frappe.whitelist()
def get_pdc_accounts():
    settings = frappe.get_single("Accounts Settings")

    if not settings.custom_pdc_receivable_account or not settings.custom_pdc_payable_account:
        frappe.throw(
            "Please configure PDC accounts in Accounts Settings"
        )

    return {
        "pdc_receivable": settings.custom_pdc_receivable_account,
        "pdc_payable": settings.custom_pdc_payable_account
    }
