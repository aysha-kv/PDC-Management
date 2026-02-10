// Copyright (c) 2026, Aysha kv and contributors
// For license information, please see license.txt


frappe.ui.form.on("Bulk PDC Clearance", {

    refresh(frm) {
        if (frm.doc.status === "Draft") {
            frm.add_custom_button(
                __("Fetch Pending PDCs"),
                function () {
                    if (!frm.doc.company || !frm.doc.cheque_date) {
                        frappe.msgprint(__("Please select Company and Cheque Date"));
                        return;
                    }

                    if (frm.is_new()) {
                        frm.save().then(() => {
                            fetch_pending_pdcs(frm);
                        });
                    } else {
                        fetch_pending_pdcs(frm);
                    }
                }
            );
        }
    },

    company(frm) {
        reset_fetched_data(frm, "Company");
    },

    cheque_date(frm) {
        reset_fetched_data(frm, "Cheque Date");
    },

    pdc_type(frm) {
        reset_fetched_data(frm, "PDC Type");
    }
});


function reset_fetched_data(frm, field_label) {
    if (frm.doc.pdc_entries && frm.doc.pdc_entries.length > 0) {

        frm.clear_table("pdc_entries");
        frm.set_value("total_pdc", 0);
        frm.set_value("total_amount", 0);

        frm.refresh_fields(["pdc_entries", "total_pdc", "total_amount"]);

        frappe.msgprint({
            title: __("Data Reset"),
            message: __(
                `${field_label} was changed. Previously fetched PDCs were cleared. Please fetch again.`
            ),
            indicator: "orange",
        });
    }
}


function fetch_pending_pdcs(frm) {
    frappe.call({
        method: "pdc.pdc.doctype.bulk_pdc_clearance.bulk_pdc_clearance.fetch_pending_pdcs",
        args: {
            docname: frm.doc.name,
        },
        freeze: true,
        freeze_message: __("Fetching Pending PDCs..."),
        callback: function (r) {
            if (!r.exc) {
                frm.reload_doc();

                if (!r.message || !r.message.has_data) {
                    frappe.msgprint({
                        title: __("No Pending PDCs"),
                        message: __("No Pending PDCs found for the selected criteria."),
                        indicator: "blue",
                    });
                } else {
                    frappe.msgprint(__("Pending PDCs fetched successfully"));
                }
            }
        },
    });
}


// frappe.ui.form.on("Bulk PDC Clearance", {
// 	refresh(frm) {

// 		if (frm.doc.status === "Draft" && frm.doc.pdc_entries?.length) {

// 			const has_pending = frm.doc.pdc_entries.some(
// 				row => row.status === "Pending"
// 			);

// 			if (!has_pending) return;

// 			frm.add_custom_button(
// 				__("Clear PDCs"),
// 				function () {

// 					frappe.db.get_single_value(
// 						"Accounts Settings",
// 						"custom_pdc_clearence_account"
// 					).then((default_bank) => {

// 						frappe.prompt(
// 							[
// 								{
// 									fieldname: "clearance_date",
// 									fieldtype: "Date",
// 									label: __("Clearance Date"),
// 									reqd: 1,
// 									default: frappe.datetime.get_today()
// 								},
// 								{
// 									fieldname: "clearance_bank_account",
// 									fieldtype: "Link",
// 									label: __("Clearance Bank Account"),
// 									options: "Account",
// 									reqd: 1,
// 									default: default_bank || undefined,
// 									get_query: () => ({
// 										filters: {
// 											company: frm.doc.company,
// 											account_type: ["in", ["Bank", "Cash"]],
// 											disabled: 0
// 										}
// 									})
// 								}
// 							],
// 							(values) => {

// 								const invalid_row = frm.doc.pdc_entries.find(row =>
// 									row.status === "Pending" &&
// 									row.cheque_date &&
// 									frappe.datetime.str_to_obj(values.clearance_date) <
// 									frappe.datetime.str_to_obj(row.cheque_date)
// 								);

// 								if (invalid_row) {
// 									frappe.msgprint({
// 										title: __("Invalid Clearance Date"),
// 										message: __(
// 											"Clearance Date cannot be before Cheque Date.<br>" +
// 											`Cheque No: <b>${invalid_row.cheque_no}</b>`
// 										),
// 										indicator: "red"
// 									});
// 									return;
// 								}

// 								if (!values.clearance_bank_account) {
// 									frappe.msgprint({
// 										title: __("Missing Bank Account"),
// 										message: __("Please select a Clearance Bank Account"),
// 										indicator: "red"
// 									});
// 									return;
// 								}

// 								frappe.confirm(
// 									__("Are you sure you want to clear all Pending PDCs?"),
// 									() => {
// 										frappe.call({
// 											method: "pdc.pdc.doctype.bulk_pdc_clearance.bulk_pdc_clearance.bulk_clear_pdcs",
// 											args: {
// 												docname: frm.doc.name,
// 												clearance_date: values.clearance_date,
// 												clearance_bank_account: values.clearance_bank_account
// 											},
// 											freeze: true,
// 											freeze_message: __("Clearing PDCs..."),
// 											callback: function (r) {
// 												if (!r.exc) {
// 													frm.reload_doc();
// 													frappe.msgprint({
// 														title: __("Bulk Clearance Completed"),
// 														message: __(
// 															`Cleared: ${r.message.cleared}<br>Failed: ${r.message.failed}`
// 														),
// 														indicator: r.message.failed ? "orange" : "green"
// 													});
// 												}
// 											}
// 										});
// 									}
// 								);
// 							},
// 							__("Clear PDCs"),
// 							__("Clear")
// 						);
// 					});
// 				},
// 				__("Actions")
// 			);
// 		}
// 	}
// });




frappe.ui.form.on("Bulk PDC Clearance", {
	refresh(frm) {

		if (frm.doc.status !== "Draft" || !frm.doc.pdc_entries?.length) return;

		const has_pending = frm.doc.pdc_entries.some(
			row => row.status === "Pending"
		);

		if (!has_pending) return;

		frm.add_custom_button(
			__("Clear PDCs"),
			function () {

				// Fetch default clearance account
				frappe.db.get_single_value(
					"Accounts Settings",
					"custom_pdc_clearence_account"
				).then((default_bank) => {

					frappe.prompt(
						[
							{
								fieldname: "clearance_date",
								fieldtype: "Date",
								label: __("Clearance Date"),
								reqd: 1,
								default: frappe.datetime.get_today()
							},
							{
								fieldname: "clearance_bank_account",
								fieldtype: "Link",
								label: __("Clearance Bank Account"),
								options: "Account",
								reqd: 1,
								default: default_bank || undefined,
								get_query: () => ({
									filters: {
										company: frm.doc.company,
										account_type: "Bank", // ✅ Bank only
										disabled: 0
									}
								})
							}
						],
						(values) => {

							// Validate clearance date vs cheque date
							const invalid_row = frm.doc.pdc_entries.find(row =>
								row.status === "Pending" &&
								row.cheque_date &&
								frappe.datetime.str_to_obj(values.clearance_date) <
								frappe.datetime.str_to_obj(row.cheque_date)
							);

							if (invalid_row) {
								frappe.msgprint({
									title: __("Invalid Clearance Date"),
									message: __(
										"Clearance Date cannot be before Cheque Date.<br>" +
										"Cheque No: <b>{0}</b>",
										[invalid_row.cheque_no]
									),
									indicator: "red"
								});
								return;
							}

							frappe.confirm(
								__("Are you sure you want to clear all Pending PDCs?"),
								() => {
									frappe.call({
										method:
											"pdc.pdc.doctype.bulk_pdc_clearance.bulk_pdc_clearance.bulk_clear_pdcs",
										args: {
											docname: frm.doc.name,
											clearance_date: values.clearance_date,
											clearance_bank_account: values.clearance_bank_account
										},
										freeze: true,
										freeze_message: __("Clearing PDCs..."),
										callback(r) {
											if (!r.exc) {
												frm.reload_doc();
												frappe.msgprint({
													title: __("Bulk Clearance Completed"),
													message: __(
														"Cleared: {0}<br>Failed: {1}",
														[r.message.cleared, r.message.failed]
													),
													indicator: r.message.failed ? "orange" : "green"
												});
											}
										}
									});
								}
							);
						},
						__("Clear PDCs"),
						__("Clear")
					);
				});
			},
			__("Actions")
		);
	}
});
