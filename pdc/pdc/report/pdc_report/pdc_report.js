// Copyright (c) 2026, Aysha kv and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PDC Report"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today()
		},
		{
			fieldname: "pdc_type",
			label: __("PDC Type"),
			fieldtype: "Select",
			options: ["", "PDC Receivable", "PDC Payable"]
		},
		{
			fieldname: "pdc_status",
			label: __("PDC Status"),
			fieldtype: "Select",
			options: ["", "Pending", "Cleared", "Bounced"]
		},
		{
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Link",
			options: "Party Type"
		},
		{
			fieldname: "party",
			label: __("Party"),
			fieldtype: "Dynamic Link",
			options: "party_type"
		}
	]
};
