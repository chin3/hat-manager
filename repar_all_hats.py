from hat_templates import list_hats
from hat_manager import load_hat, save_hat, normalize_hat

print("🔧 Normalizing all hats...")

for hat_id in list_hats():
    hat = load_hat(hat_id)
    normalized = normalize_hat(hat)
    save_hat(hat_id, normalized)
    print(f"✅ Normalized: {hat_id}")

print("🎉 All hats have been repaired and saved.")