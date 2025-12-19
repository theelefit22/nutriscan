import requests
import os

# === CONFIGURATION ===
# Try to get from environment (deployment), fallback to hardcoded (local)
API_KEY = os.environ.get("USDA_API_KEY", "weuVeNftwbkitBApbKXdLkllWMdgY1blq3bl9I4t") 
BASE_URL = "https://api.nal.usda.gov/fdc/v1"

def search_foods(query):
    # Stage 1: Search for Dishes (Survey FNDDS)
    # The user prioritizes "dishes" and "varieties" over raw ingredients
    url = f"{BASE_URL}/foods/search"
    
    def fetch_results(data_types):
        params = {
            "query": query,
            "dataType": data_types,
            "pageSize": 20, 
            "sortBy": "dataType.keyword",
            "sortOrder": "asc",
            "api_key": API_KEY
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return None
        return res.json()

    # Try Survey (Dishes) first
    data = fetch_results(["Survey (FNDDS)"])
    if data and "foods" in data and len(data["foods"]) > 0:
        return data

    # Stage 2: Fallback to Ingredients (Foundation, SR Legacy) if no dishes found
    # This covers cases like "raw spinach" where there might not be a survey dish
    return fetch_results(["Foundation", "SR Legacy"])

def get_food_details(fdc_id):
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Error fetching details:", response.text)
        return None
    return response.json()

def clean_food_name(food):
    """Return only the clean food description, no brand or extra info"""
    desc = food.get("description", "Unknown Food")
    # Remove common prefixes/suffixes like "Restaurant, ", "Fast foods, "
    unwanted = ["Restaurant, ", "Fast foods, ", "Inc., ", "Co., "]
    for prefix in unwanted:
        if desc.startswith(prefix):
            desc = desc[len(prefix):]
    return desc.strip().capitalize()

def extract_nutrients(food_data, weight_grams):
    nutrients = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    
    for nutrient in food_data.get("foodNutrients", []):
        name = nutrient["nutrient"]["name"]
        amount = nutrient.get("amount", 0) or 0
        unit = nutrient["nutrient"]["unitName"].upper()

        if name == "Energy" and unit == "KCAL":
            nutrients["calories"] = amount
        elif name == "Protein":
            nutrients["protein"] = amount
        elif name == "Total lipid (fat)":
            nutrients["fat"] = amount
        elif name == "Carbohydrate, by difference":
            nutrients["carbs"] = amount

    # Scale to entered weight (USDA data is usually per 100g)
    scale_factor = weight_grams / 100.0
    for key in ["calories", "protein", "fat", "carbs"]:
        nutrients[key] *= scale_factor

    # Calculate macro percentages
    total_cal = nutrients["calories"]
    if total_cal > 0:
        nutrients["fat_percent"] = (nutrients["fat"] * 9 / total_cal) * 100
        nutrients["protein_percent"] = (nutrients["protein"] * 4 / total_cal) * 100
        nutrients["carbs_percent"] = (nutrients["carbs"] * 4 / total_cal) * 100
    else:
        nutrients["fat_percent"] = nutrients["protein_percent"] = nutrients["carbs_percent"] = 0

    return nutrients

def main():
    print("🍛 Simple Food Nutrition Calculator (Clean Names)\n")
    
    query = input("Enter food name (e.g., french fries, chicken curry, dal, gulab jamun): ").strip()
    if not query:
        print("Please enter something!")
        return

    print("\nSearching USDA database...")
    data = search_foods(query)
    if not data or "foods" not in data or len(data["foods"]) == 0:
        print("❌ No matching foods found. Try a different spelling or broader term.")
        return

    foods = data["foods"]
    print(f"\nFound {len(foods)} similar items:\n")

    for i, food in enumerate(foods, 1):
        clean_name = clean_food_name(food)
        print(f"{i}. {clean_name}")

    try:
        choice = int(input(f"\nSelect the correct food (1-{len(foods)}): ")) - 1
        if choice < 0 or choice >= len(foods):
            print("Invalid number.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    selected = foods[choice]
    food_name = clean_food_name(selected)
    fdc_id = selected["fdcId"]

    print(f"\nFetching nutrition data for: {food_name}")
    details = get_food_details(fdc_id)
    if not details:
        return

    try:
        weight = float(input(f"\nEnter weight in grams (from your kitchen scale): "))
        if weight <= 0:
            print("Weight must be positive.")
            return
    except ValueError:
        print("Invalid weight.")
        return

    nutrients = extract_nutrients(details, weight)

    print(f"\n📊 Nutrition for {weight}g of {food_name}:\n")
    print(f"Calories      : {nutrients['calories']:.1f} kcal")
    print(f"Protein       : {nutrients['protein']:.1f} g   ({nutrients['protein_percent']:.1f}% of calories)")
    print(f"Fat           : {nutrients['fat']:.1f} g       ({nutrients['fat_percent']:.1f}% of calories)")
    print(f"Carbohydrates : {nutrients['carbs']:.1f} g   ({nutrients['carbs_percent']:.1f}% of calories)")

    print("\nDone! 🍽️")

if __name__ == "__main__":
    main()
