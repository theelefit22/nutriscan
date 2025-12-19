import requests
import json

# === CONFIGURATION ===
API_KEY = "weuVeNftwbkitBApbKXdLkllWMdgY1blq3bl9I4t"  # Replace with your real key from api.data.gov for better limits
BASE_URL = "https://api.nal.usda.gov/fdc/v1"

def search_foods(query):
    url = f"{BASE_URL}/foods/search"
    params = {
        "query": query,
        "dataType": ["Foundation", "SR Legacy", "Branded"],  # Good general coverage
        "pageSize": 10,
        "api_key": API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
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

def extract_nutrients(food_data, weight_grams):
    nutrients = {}
    for nutrient in food_data.get("foodNutrients", []):
        name = nutrient["nutrient"]["name"]
        amount = nutrient.get("amount", 0)
        unit = nutrient["nutrient"]["unitName"]
        if name == "Energy":
            nutrients["calories"] = amount  # kcal per 100g typically
        elif name == "Protein":
            nutrients["protein"] = amount
        elif name == "Total lipid (fat)":
            nutrients["fat"] = amount
        elif name == "Carbohydrate, by difference":
            nutrients["carbs"] = amount

    # Scale by weight (most USDA values are per 100g)
    scale_factor = weight_grams / 100.0
    for key in nutrients:
        nutrients[key] *= scale_factor

    # Calculate percentages (for calories from macros)
    total_calories = nutrients.get("calories", 0)
    if total_calories > 0:
        nutrients["fat_percent"] = (nutrients["fat"] * 9 / total_calories) * 100
        nutrients["protein_percent"] = (nutrients["protein"] * 4 / total_calories) * 100
        nutrients["carbs_percent"] = (nutrients["carbs"] * 4 / total_calories) * 100
    else:
        nutrients["fat_percent"] = nutrients["protein_percent"] = nutrients["carbs_percent"] = 0

    return nutrients

def main():
    print("🍎 USDA Food Nutrition Calculator\n")
    
    query = input("Enter food name to search: ").strip()
    if not query:
        print("Please enter a food name.")
        return

    print("\nSearching...")
    data = search_foods(query)
    if not data or "foods" not in data:
        print("No results found or API error.")
        return

    foods = data["foods"]
    if len(foods) == 0:
        print("No matching foods found.")
        return

    print(f"\nFound {len(foods)} results:\n")
    for i, food in enumerate(foods, 1):
        desc = food.get("description", "Unknown")
        brand = food.get("brandOwner", "")
        print(f"{i}. {desc} {f'({brand})' if brand else ''}")

    try:
        choice = int(input(f"\nSelect a food (1-{len(foods)}): ")) - 1
        if choice < 0 or choice >= len(foods):
            print("Invalid choice.")
            return
    except ValueError:
        print("Please enter a number.")
        return

    selected_food = foods[choice]
    fdc_id = selected_food["fdcId"]
    food_name = selected_food["description"]

    print(f"\nFetching details for: {food_name}")
    details = get_food_details(fdc_id)
    if not details:
        return

    try:
        weight = float(input(f"\nEnter weight in grams (from your scale): "))
        if weight <= 0:
            print("Weight must be positive.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    nutrients = extract_nutrients(details, weight)

    print(f"\n📊 Nutrition for {weight}g of {food_name}:\n")
    print(f"Calories      : {nutrients['calories']:.1f} kcal")
    print(f"Protein       : {nutrients['protein']:.1f} g  ({nutrients['protein_percent']:.1f}%)")
    print(f"Fat           : {nutrients['fat']:.1f} g      ({nutrients['fat_percent']:.1f}%)")
    print(f"Carbohydrates : {nutrients['carbs']:.1f} g  ({nutrients['carbs_percent']:.1f}%)")

if __name__ == "__main__":
    main()
