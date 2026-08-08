import frappe
from frappe.utils import flt
from erpnext.assets.doctype.asset_depreciation_schedule.asset_depreciation_schedule import (
    make_new_active_asset_depr_schedules_and_cancel_current_ones,
)


def recalculate_salvage_value(doc, method):
    """Registered as an additional on_submit hook for Asset Repair.
    Runs after core on_submit already capitalized the repair cost
    and rebuilt the depreciation schedule with the OLD salvage value —
    this corrects the salvage value and rebuilds it a second time."""

    if not doc.capitalize_repair_cost:
        return

    asset = frappe.get_doc("Asset", doc.asset)
    if not asset.calculate_depreciation:
        return

    changed = False
    for row in asset.finance_books:
        if flt(row.salvage_value_percentage) <= 0:
            continue

        new_evaul = flt(asset.total_asset_cost) * flt(row.salvage_value_percentage) / 100
        if new_evaul != flt(row.expected_value_after_useful_life):
            row.db_set("expected_value_after_useful_life", new_evaul)
            row.expected_value_after_useful_life = new_evaul  # keep in-memory row in sync
            changed = True

    if not changed:
        return

    asset.flags.increase_in_asset_value_due_to_repair = True

    notes = frappe._("Salvage value recalculated after Asset Repair {0}.").format(doc.name)
    make_new_active_asset_depr_schedules_and_cancel_current_ones(asset, notes)

def recalculate_salvage_value_on_cancel(doc, method):
    if not doc.capitalize_repair_cost:
        return

    asset = frappe.get_doc("Asset", doc.asset)
    if not asset.calculate_depreciation:
        return

    changed = False
    for row in asset.finance_books:
        if flt(row.salvage_value_percentage) <= 0:
            continue

        new_evaul = flt(asset.total_asset_cost) * flt(row.salvage_value_percentage) / 100
        if new_evaul != flt(row.expected_value_after_useful_life):
            row.db_set("expected_value_after_useful_life", new_evaul)
            row.expected_value_after_useful_life = new_evaul
            changed = True

    if changed:
        notes = frappe._("Salvage value reverted after cancelling Asset Repair {0}.").format(doc.name)
        make_new_active_asset_depr_schedules_and_cancel_current_ones(asset, notes)