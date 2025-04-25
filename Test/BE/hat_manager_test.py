from hat_manager import list_hats, load_hat, save_hat
import json
import os

def run_tests():
    print("🔍 Running Hat Manager Tests...")

    # Test 1: List Hats
    hats = list_hats()
    print("✅ list_hats():", hats)
    assert "planner" in hats, "❌ 'planner' hat not found in list_hats()"

    # Test 2: Load a Hat
    planner = load_hat("planner")
    print("✅ load_hat('planner')['model']:", planner["model"])
    assert planner["model"] == "gpt-4", "❌ 'planner' hat model is not 'gpt-4'"

    # Test 3: Modify and Save Hat
    planner["name"] = "Updated Planner Hat"
    save_hat("planner_test", planner)

    # Reload and check saved changes
    updated = load_hat("planner_test")
    print("✅ save_hat + load_hat('planner_test')['name']:", updated["name"])
    assert updated["name"] == "Updated Planner Hat", "❌ Hat save/load failed"

    # Cleanup test file
    os.remove("./hats/planner_test.json")
    print("🧹 Cleaned up test hat file.")

    print("🎉 All tests passed!")

if __name__ == "__main__":
    run_tests()