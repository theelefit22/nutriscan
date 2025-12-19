import requests
import pandas as pd

# === CONFIGURATION ===
USDA_API_KEY = "DEMO_KEY"  # Replace with your real key for more requests
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Load Indian database (must have indb_recipes.xlsx in same folder)
try:
    indb_df = pd.read_excel("indb_recipes.xlsx")
    # Assume columns: Common name for recipe, Energy (kcal), Protein (g), Fat (g), Carbohydrate (g) per 100g
    # Adjust column names if different (check your file!)
    # Example common columns from INDB: 'Recipe Name', 'Energy_kcal', 'Protein_g', 'Total Fat_g', 'Carbohydrate_g'
    # Rename if needed below
    indb_df.columns = indb_df.columns.str.lower().str.replace(" ", "_")
    # Standardize expected columns
    indb_df.rename(columns={
        'recipe_name': 'name',
        'energy_kcal': 'calories',
        'protein_g': 'protein',
        'total_fat_g': 'fat',
        'carbohydrate_g': 'carbs'
    }, inplace=True, errors='ignore')
except Exception as e:
    print("Error loading indb_recipes.xlsx:", e)
    indb_df = None

def search_usda(query):
    url = f"{USDA_BASE_URL}/foods/search"
    params = {
        "query": query,
        "dataType": ["Foundation", "SR Legacy", "Branded", "Survey (FNDDS)"],
        "pageSize": 20,
        "api_key": USDA_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("USDA API Error:", response.text)
        return []
    data = response.json()
    return data.get("foods", [])

def clean_usda_name(food):
    desc = food.get("description", "Unknown").strip().capitalize()
    prefixes = ["Bread, ", "Indian flatbread, ", "Naan, ", "Restaurant, ", "Fast foods, "]
    for p in prefixes:
        if desc.lower().startswith(p.lower()):
            desc = desc[len(p):].strip()
    return desc.capitalize()

def get_usda_nutrients(food_data, weight_grams):
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
    scale = weight_grams / 100.0
    for k in nutrients:
        nutrients[k] *= scale
    total_cal = nutrients["calories"]
    if total_cal > 0:
        nutrients["fat_percent"] = (nutrients["fat"] * 9 / total_cal) * 100
        nutrients["protein_percent"] = (nutrients["protein"] * 4 / total_cal) * 100
        nutrients["carbs_percent"] = (nutrients["carbs"] * 4 / total_cal) * 100
    else:
        nutrients["fat_percent"] = nutrients["protein_percent"] = nutrients["carbs_percent"] = 0
    return nutrients

def search_indian(query):
    if indb_df is None:
        return []
    # Search in recipe name column (adjust 'name' if your column is different)
    matches = indb_df[indb_df['name'].str.contains(query, case=False, na=False)]
    return matches.to_dict('records')  # List of dicts

def main():
    print("🍛🍔 Multi-Cuisine Food Nutrition Calculator\n")
    print("Choose database:")
    print("1. American/Global (USDA - live API, broad coverage)")
    print("2. Indian (INDB - 1014 recipes/dishes, offline)")
    
    choice = input("\nEnter 1 or 2: ").strip()
    if choice not in ["1", "2"]:
        print("Invalid choice.")
        return
    
    is_indian = choice == "2"
    if is_indian and indb_df is None:
        print("Indian database not loaded. Place indb_recipes.xlsx in this folder.")
        return
    
    query = input(f"\nEnter food name (e.g., {'french fries' if not is_indian else 'naan or chicken curry'}): ").strip()
    if not query:
        return
    
    print("\nSearching...")
    
    if not is_indian:
        foods = search_usda(query)
        if not foods:
            print("No results.")
            return
        displayed = []
        unique = set()
        for food in foods:
            name = clean_usda_name(food)
            if name not in unique:
                unique.add(name)
                displayed.append((name, food))
    else:
        recipes = search_indian(query)
        if not recipes:
            print("No matching Indian recipes found.")
            return
        displayed = [(r['name'].capitalize(), r) for r in recipes]
    
    print(f"\nFound {len(displayed)} items:\n")
    for i, (name, _) in enumerate(displayed, 1):
        print(f"{i}. {name}")
    
    try:
        sel = int(input(f"\nSelect (1-{len(displayed)}): ")) - 1
        if sel < 0 or sel >= len(displayed):
            return
    except:
        print("Invalid.")
        return
    
    selected_name, selected_data = displayed[sel]
    
    try:
        weight = float(input("\nEnter weight in grams: "))
        if weight <= 0:
            return
    except:
        return
    
    if not is_indian:
        fdc_id = selected_data["fdcId"]
        details_resp = requests.get(f"{USDA_BASE_URL}/food/{fdc_id}", params={"api_key": USDA_API_KEY})
        if details_resp.status_code != 200:
            print("Error fetching details.")
            return
        details = details_resp.json()
        nutrients = get_usda_nutrients(details, weight)
    else:
        # Indian: values already per 100g
        nutrients = {
            "calories": selected_data.get('calories', 0) * (weight / 100),
            "protein": selected_data.get('protein', 0) * (weight / 100),
            "fat": selected_data.get('fat', 0) * (weight / 100),
            "carbs": selected_data.get('carbs', 0) * (weight / 100),
        }
        total_cal = nutrients["calories"]
        if total_cal > 0:
            nutrients["fat_percent"] = (nutrients["fat"] * 9 / total_cal) * 100
            nutrients["protein_percent"] = (nutrients["protein"] * 4 / total_cal) * 100
            nutrients["carbs_percent"] = (nutrients["carbs"] * 4 / total_cal) * 100
        else:
            nutrients["fat_percent"] = nutrients["protein_percent"] = nutrients["carbs_percent"] = 0
    
    print(f"\n📊 Nutrition for {weight}g of {selected_name}:\n")
    print(f"Calories      : {nutrients['calories']:.1f} kcal")
    print(f"Protein       : {nutrients['protein']:.1f} g   ({nutrients['protein_percent']:.1f}% of calories)")
    print(f"Fat           : {nutrients['fat']:.1f} g       ({nutrients['fat_percent']:.1f}% of calories)")
    print(f"Carbohydrates : {nutrients['carbs']:.1f} g   ({nutrients['carbs_percent']:.1f}% of calories)")

if __name__ == "__main__":
    main()
