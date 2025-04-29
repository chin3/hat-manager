# hat_templates.py

import os
import json
from datetime import datetime
from hat_manager import load_hat, save_hat, list_hats,normalize_hat

def register_template(hat_id):
    """
    Marks an existing Hat as a base template (base_hat_id == hat_id, team_id=None).
    """
    hat = load_hat(hat_id)
    hat["base_hat_id"] = hat["hat_id"]
    hat["team_id"] = None
    save_hat(hat_id, hat)
    print(f"✅ Registered {hat_id} as a base template.")
    
def list_hat_templates():
    """
    Lists all Hats that are considered base templates (no team_id or base_hat_id == hat_id).
    """
    templates = []
    for hat_id in list_hats():
        hat = load_hat(hat_id)
        if hat.get("team_id") is None and hat.get("base_hat_id") == hat.get("hat_id"):
            templates.append(hat)
    return templates


def clone_hat_template(base_hat_id, new_suffix=None, team_id=None, flow_order=None):
    """
    Clone a base Hat with a new unique ID (optionally for a team).
    """
    base_hat = load_hat(base_hat_id)
    if not base_hat:
        raise ValueError(f"Hat template '{base_hat_id}' not found.")

    # Generate unique ID
    suffix = new_suffix or datetime.now().strftime('%Y%m%d%H%M%S')
    cloned_id = f"{base_hat_id}_{suffix}"

    # Clone and normalize
    cloned_hat = normalize_hat(base_hat, team_id=team_id, flow_order=flow_order)
    cloned_hat["hat_id"] = cloned_id
    cloned_hat["name"] = f"{base_hat['name']} Clone"
    cloned_hat["base_hat_id"] = base_hat_id

    save_hat(cloned_id, cloned_hat)
    return cloned_hat


def find_hats_by_base_id(base_id):
    """
    Finds all Hats cloned from a given base_hat_id.
    """
    hats = []
    for hat_id in list_hats():
        hat = load_hat(hat_id)
        if hat.get("base_hat_id") == base_id:
            hats.append(hat)
    return hats

if __name__ == "__main__":
    print("🧪 Running Hat Templates Tests...")

    # Step 1: List available base templates
    templates = list_hat_templates()
    print(f"📋 Found {len(templates)} template(s).")
    for t in templates:
        print(f"- Template: {t['hat_id']} | {t['name']}")

    if not templates:
        print("⚠️ No templates found. Please create a base Hat first!")
    else:
        # Step 2: Clone the first template
        base_hat_id = templates[0]['hat_id']
        print(f"🔧 Cloning template '{base_hat_id}'...")
        cloned_hat = clone_hat_template(base_hat_id)

        print(f"✅ Cloned Hat ID: {cloned_hat['hat_id']}")
        print(f"✅ Base Hat ID: {cloned_hat['base_hat_id']}")
        print(f"✅ Name: {cloned_hat['name']}")
        print(f"✅ Team ID: {cloned_hat['team_id']} (should be None if not specified)")

        # Step 3: Find all clones of the base hat
        related_hats = find_hats_by_base_id(base_hat_id)
        print(f"🔎 Found {len(related_hats)} hats cloned from '{base_hat_id}':")
        for hat in related_hats:
            print(f"- {hat['hat_id']} (Name: {hat['name']})")

    print("🧪 Hat Templates Tests Completed.")
