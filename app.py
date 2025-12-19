from flask import Flask, render_template, request, jsonify
import food_nutrition_clean as backend

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    data = backend.search_foods(query)
    if not data or 'foods' not in data:
        return jsonify({'foods': []})
    
    # Process foods to add a clean name for display
    foods = data.get('foods', [])
    results = []
    seen_names = set()
    
    for food in foods:
        clean_name = backend.clean_food_name(food)
        
        # Normalize for deduplication (case-insensitive)
        norm_name = clean_name.lower().strip()
        
        # Skip if we already have this variety
        if norm_name in seen_names:
            continue
            
        seen_names.add(norm_name)
        
        results.append({
            'fdcId': food.get('fdcId'),
            'description': clean_name,
            'original_description': food.get('description'),
            'brandOwner': food.get('brandOwner', '') # Should be empty or filtered out mostly
        })
        
    return jsonify({'foods': results})

# Nutrient mapping dictionary
NUTRIENT_MAP = {
    # Macros
    "Energy": "Calories",
    "Protein": "Protein",
    "Total lipid (fat)": "Fat",
    "Carbohydrate, by difference": "Carbs",
    
    # Micros - General
    "Fiber, total dietary": "Dietary Fiber",
    "Cholesterol": "Cholesterol",
    
    # Vitamins
    "Vitamin A, RAE": "Vitamin A",
    "Thiamin": "Vitamin B1",
    "Riboflavin": "Vitamin B2",
    "Niacin": "Niacin", 
    "Vitamin C, total ascorbic acid": "Vitamin C",
    "Vitamin E (alpha-tocopherol)": "Vitamin E",
    # Vitamin K often yields multiple types, we'll try to find the standard phylloquinone
    "Vitamin K (phylloquinone)": "Vitamin K",
    
    # Minerals
    "Sodium, Na": "Na",
    "Calcium, Ca": "Ca",
    "Magnesium, Mg": "Mg",
    "Iron, Fe": "Fe", 
    "Manganese, Mn": "Mn",
    "Zinc, Zn": "Zn",
    "Copper, Cu": "Cu",
    "Phosphorus, P": "P",
    
    # Extra mentioned in image
    "Carotene, beta": "Carotene", # Approximation
    "Retinol": "Retinol Equivalent", # USDA separates RAE and Retinol usually
}

def extract_detailed_nutrients(food_data, weight_grams):
    # Initialize all with 0 and correct units if possible, or just build dynamically
    extracted = {}
    
    # Scale factor
    scale_factor = weight_grams / 100.0
    
    for nutrient in food_data.get("foodNutrients", []):
        name = nutrient["nutrient"]["name"]
        amount = nutrient.get("amount", 0) or 0
        unit = nutrient["nutrient"]["unitName"]
        
        # Check if we want this nutrient
        # We check exact match or if it's in our specific list
        target_name = NUTRIENT_MAP.get(name)
        
        if target_name:
            scaled_amount = amount * scale_factor
            extracted[target_name] = {
                "amount": round(scaled_amount, 2),
                "unit": unit.lower()
            }
            
    # Ensure macros exist even if 0
    defaults = ["Calories", "Protein", "Fat", "Carbs"]
    for d in defaults:
        if d not in extracted:
            extracted[d] = {"amount": 0, "unit": "g" if d != "Calories" else "kcal"}

    # Calculate percentages for macros (of calories)
    total_cal = extracted["Calories"]["amount"]
    if total_cal > 0:
        extracted["Fat"]["percent"] = round((extracted["Fat"]["amount"] * 9 / total_cal) * 100, 1)
        extracted["Protein"]["percent"] = round((extracted["Protein"]["amount"] * 4 / total_cal) * 100, 1)
        extracted["Carbs"]["percent"] = round((extracted["Carbs"]["amount"] * 4 / total_cal) * 100, 1)
    else:
        extracted["Fat"]["percent"] = 0
        extracted["Protein"]["percent"] = 0
        extracted["Carbs"]["percent"] = 0
        
    return extracted

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    fdc_id = data.get('fdcId')
    weight = data.get('weight')
    
    if not fdc_id or weight is None:
         return jsonify({'error': 'fdcId and weight are required'}), 400

    try:
        weight = float(weight)
    except ValueError:
        return jsonify({'error': 'Weight must be a number'}), 400

    details = backend.get_food_details(fdc_id)
    if not details:
        return jsonify({'error': 'Food details not found'}), 404

    nutrients = extract_detailed_nutrients(details, weight)
    
    return jsonify({
        'food_name': details.get('description'), 
        'weight': weight,
        'nutrients': nutrients
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
