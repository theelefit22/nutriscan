import requests

# === CONFIGURATION ===
API_KEY = "DEMO_KEY"  # Replace with your real api.data.gov key for more requests
BASE_URL = "https://api.nal.usda.gov/fdc/v1"

def search_foods(query):
    url = f"{BASE_URL}/foods/search"
    params = {
        "query": query,
        "dataType": ["Foundation", "SR Legacy", "Branded", "Survey (FNDDS)"],
        "pageSize": 20,  # More results for better cooked matches
        "sortBy": "lowercaseDescription.keyword",
        "sortOrder": "asc",
        "api_key": API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("API Error:", response.status_code, response.text)
        return None
    return response.json()

def get_food_details(fdc_id):
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Error fetching details:", response.text)
        return None
    return response.json()

def clean_food_name(food):
    desc = food.get("description", "Unknown Food").strip()
    # Remove unwanted prefixes
    unwanted = ["Restaurant, ", "Fast foods, "]
    for prefix in unwanted:
        if desc.startswith(prefix):
            desc = desc[len(prefix):]
    return desc.capitalize()

def is_cooked(desc_lower):
    cooked_keywords = ["cooked", "boiled", "roasted", "baked", "fried", "grilled", "steamed", "broiled"]
    return any(keyword in desc_lower for keyword in cooked_keywords)

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

    # Scale to entered weight (usually per 100g)
    scale_factor = weight_grams / 100.0
    for key in ["calories", "protein", "fat", "carbs"]:
        nutrients[key] *= scale_factor

    # Macro percentages
    total_cal = nutrients["calories"]
    if total_cal > 0:
        nutrients["fat_percent"] = (nutrients["fat"] * 9 / total_cal) * 100
        nutrients["protein_percent"] = (nutrients["protein"] * 4 / total_cal) * 100
        nutrients["carbs_percent"] = (nutrients["carbs"] * 4 / total_cal) * 100
    else:
        nutrients["fat_percent"] = nutrients["protein_percent"] = nutrients["carbs_percent"] = 0

    return nutrients

def main():
    print("🍲 Food Nutrition Calculator - Cooked Versions Prioritized\n")
    
    query = input("Enter food name (e.g., chicken, rice, dal, french fries): ").strip()
    if not query:
        print("Please enter something!")
        return

    print("\nSearching USDA database...")
    data = search_foods(query)
    if not data or "foods" not in data or len(data["foods"]) == 0:
        print("❌ No matching foods found. Try a broader term.")
        return

    all_foods = data["foods"]
    
    # Separate cooked and non-cooked
    cooked_foods = []
    other_foods = []
    for food in all_foods:
        desc_lower = food.get("lowercaseDescription", "").lower()
        if is_cooked(desc_lower):
            cooked_foods.append(food)
        else:
            other_foods.append(food)

    # Combine: cooked first
    sorted_foods = cooked_foods + other_foods

    if len(sorted_foods) == 0:
        print("No results.")
        return

    print(f"\nFound {len(sorted_foods)} results (cooked versions shown first if available):\n")

    for i, food in enumerate(sorted_foods, 1):
        clean_name = clean_food_name(food)
        prefix = "🍳 " if is_cooked(food.get("lowercaseDescription", "").lower()) else "   "
        print(f"{prefix}{i}. {clean_name}")

    try:
        choice = int(input(f"\nSelect the food (1-{len(sorted_foods)}): ")) - 1
        if choice < 0 or choice >= len(sorted_foods):
            print("Invalid number.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    selected = sorted_foods[choice]
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

    print("\nEnjoy your meal! 🍽️")

if __name__ == "__main__":
    main()
