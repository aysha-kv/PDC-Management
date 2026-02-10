import frappe
from frappe.utils import nowdate



import frappe
from frappe.utils import getdate

@frappe.whitelist()
def clear_pdc(payment_entry, clearance_date=None, clearance_bank_account=None):

	pe = frappe.get_doc("Payment Entry", payment_entry)

	if pe.docstatus != 1:
		frappe.throw("Payment Entry must be submitted")

	if not pe.custom_is_pdc:
		frappe.throw("Not a PDC Payment Entry")

	if pe.custom_pdc_status != "Pending":
		frappe.throw("Only Pending PDC can be cleared")

	if pe.paid_amount <= 0:
		frappe.throw("Invalid paid amount")

	if clearance_date:
		pe.custom_clearance_date = clearance_date

	if clearance_bank_account:
		pe.custom_clearance_bank_account = clearance_bank_account

	if not pe.custom_clearance_date:
		frappe.throw("Please set Clearance Date")

	if not pe.custom_clearance_bank_account:
		frappe.throw("Please select Clearance Bank Account")

	if pe.custom_cheque_date and getdate(pe.custom_clearance_date) < getdate(pe.custom_cheque_date):
		frappe.throw("Clearance Date cannot be before Cheque Date")

	settings = frappe.get_single("Accounts Settings")
	bank_account = pe.custom_clearance_bank_account

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

	je.insert(ignore_permissions=True)
	je.submit()

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
