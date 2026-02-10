
frappe.ui.form.on('Payment Entry', {
	refresh(frm) {
		if (
			frm.doc.docstatus === 1 &&
			frm.doc.custom_is_pdc &&
			frm.doc.custom_pdc_status === "Pending"
		) {
			frm.add_custom_button(__('Clear PDC'), () => {

				frappe.db.get_single_value(
					"Accounts Settings",
					"custom_pdc_clearence_account"
				).then((default_account) => {

					frappe.prompt(
						[
							{
								fieldname: "clearance_date",
								fieldtype: "Date",
								label: __("Clearance Date"),
								reqd: 1,
								default: frm.doc.custom_cheque_date || frappe.datetime.get_today()
							},
							{
								fieldname: "clearance_bank_account",
								fieldtype: "Link",
								label: __("Clearance Bank Account"),
								options: "Account",
								reqd: 1,
								default: default_account || undefined,
								get_query: () => ({
									filters: {
										company: frm.doc.company,
										account_type: "Bank",
										disabled: 0
									}
								})
							}
						],
						(values) => {

							if (
								frm.doc.custom_cheque_date &&
								frappe.datetime.str_to_obj(values.clearance_date) <
								frappe.datetime.str_to_obj(frm.doc.custom_cheque_date)
							) {
								frappe.msgprint({
									title: __("Invalid Clearance Date"),
									message: __("Clearance Date cannot be before Cheque Date"),
									indicator: "red"
								});
								return;
							}

							frappe.call({
								method: "pdc.pdc.custom_script.payment_entry.clear_pdc",
								args: {
									payment_entry: frm.doc.name,
									clearance_date: values.clearance_date,
									clearance_bank_account: values.clearance_bank_account
								},
								freeze: true,
								freeze_message: __("Clearing PDC..."),
								callback(r) {
									if (!r.exc) {
										frappe.msgprint({
											message: __(
												"PDC Cleared Successfully.<br>Journal Entry: <b>{0}</b>",
												[r.message.journal_entry]
											),
											indicator: "green"
										});
										frm.reload_doc();
									}
								}
							});
						},
						__("Clear PDC"),
						__("Clear")
					);
				});
			});
		}
	}
});


frappe.ui.form.on("Payment Entry", {
    custom_is_pdc(frm) {
        frm.toggle_display("mode_of_payment", !frm.doc.custom_is_pdc);
        if (frm.doc.custom_is_pdc) {
            frm.set_value("mode_of_payment", "");
        }
    }
});

frappe.ui.form.on("Payment Entry", {
    refresh(frm) {
        set_pdc_account_filter(frm);
    },
    custom_is_pdc(frm) {
        set_pdc_account_filter(frm);
    }
});

function set_pdc_account_filter(frm) {
    if (frm.doc.custom_is_pdc && frm.doc.payment_type === "Receive") {
        frm.set_query("paid_to", function () {
            return {
                filters: {
                    is_group: 0
                }
            };
        });
    }

    if (frm.doc.custom_is_pdc && frm.doc.payment_type === "Pay") {
        frm.set_query("paid_from", function () {
            return {
                filters: {
                    is_group: 0
                }
            };
        });
    }
}


frappe.ui.form.on("Payment Entry", {
    refresh(frm) {
        if (
            frm.doc.docstatus === 1 &&
            frm.doc.custom_is_pdc &&
            frm.doc.custom_pdc_status === "Pending"
        ) {
            frm.add_custom_button("Mark as Bounced", () => {
                frappe.confirm(
                    "Are you sure you want to mark this cheque as bounced?",
                    () => {
                        frappe.call({
                            method: "pdc.pdc.custom_script.payment_entry.mark_pdc_as_bounced",  
                            args: {
                                payment_entry: frm.doc.name
                            },
                            callback(r) {
                                if (!r.exc) {
                                    frappe.msgprint(
                                        `Cheque marked as bounced.<br>Reversal JE: <b>${r.message.journal_entry}</b>`
                                    );
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }).addClass("btn-danger");
        }
    }
});

frappe.ui.form.on('Payment Entry', {

    custom_is_pdc(frm) {
        if (!frm.doc.custom_is_pdc) return;

        if (!frm.doc.payment_type || !frm.doc.party_type) {
            frappe.msgprint("Please select Payment Type and Party Type first");
            return;
        }

        frappe.call({
            method: "pdc.pdc.custom_script.payment_entry.get_pdc_accounts",
            callback(r) {
                if (!r.message) return;

                if (frm.doc.payment_type === "Receive" &&
                    frm.doc.party_type === "Customer") {

                    frm.set_value("paid_to", r.message.pdc_receivable);
                }

                if (frm.doc.payment_type === "Pay" &&
                    frm.doc.party_type === "Supplier") {

                    frm.set_value("paid_from", r.message.pdc_payable);
                }
            }
        });
    }
});

frappe.ui.form.on("Payment Entry", {
	custom_is_pdc(frm) {

		if (!frm.doc.custom_is_pdc) {
			return;
		}

		if (frm.doc.custom_clearance_bank_account) {
			return;
		}

		frappe.db.get_single_value(
			"Accounts Settings",
			"custom_pdc_clearence_account"
		).then((value) => {

			if (!value) {
				frappe.msgprint({
					title: __("Missing Setup"),
					message: __("PDC Clearance Account is not set in Accounts Settings"),
					indicator: "red"
				});
				return;
			}

			frm.set_value("custom_clearance_bank_account", value);

			frappe.show_alert({
				message: __("PDC Clearance Bank Account auto-set. You may change it if required."),
				indicator: "green"
			});
		});
	}
});
