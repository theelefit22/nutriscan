"""
Indian Nutrient Databank (INDB) module
Provides search and nutrient extraction for Indian recipes
"""
import json
import os

# Load INDB data once at module import
INDB_DATA = []
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'indb.json')

try:
    with open(DATA_PATH, 'r') as f:
        INDB_DATA = json.load(f)
    print(f"Loaded {len(INDB_DATA)} INDB recipes")
except FileNotFoundError:
    print(f"Warning: INDB data file not found at {DATA_PATH}")
except Exception as e:
    print(f"Error loading INDB data: {e}")


def search_indb(query, max_results=15):
    """
    Search INDB for recipes matching the query
    
    Args:
        query: Search term
        max_results: Maximum number of results to return
        
    Returns:
        List of matching recipes
    """
    if not INDB_DATA:
        return []
    
    query_lower = query.lower().strip()
    results = []
    
    for recipe in INDB_DATA:
        food_name = recipe.get('food_name', '').lower()
        
        # Simple substring matching
        if query_lower in food_name:
            results.append({
                'fdcId': recipe['food_code'],  # Use food_code as ID
                'description': recipe['food_name'],
                'source': 'INDB',
                'dataType': 'Indian Recipe',
                'brandOwner': '',
                'servingSize': recipe.get('serving_size_g', 100),
                'servingUnit': recipe.get('serving_unit', 'serving')
            })
            
            if len(results) >= max_results:
                break
    
    return results


def get_indb_nutrients(food_code, weight_grams=100):
    """
    Get detailed nutrients for an INDB recipe
    
    Args:
        food_code: INDB food code
        weight_grams: Weight in grams
        
    Returns:
        Dictionary of nutrients scaled to weight
    """
    # Find the recipe
    recipe = None
    for r in INDB_DATA:
        if r['food_code'] == food_code:
            recipe = r
            break
    
    if not recipe:
        return None
    
    # Scale nutrients from per 100g to requested weight
    scale_factor = weight_grams / 100.0
    per_100g = recipe['per_100g']
    
    nutrients = {
        'Calories': {
            'amount': round(per_100g['energy_kcal'] * scale_factor, 2),
            'unit': 'kcal',
            'percent': 0
        },
        'Protein': {
            'amount': round(per_100g['protein_g'] * scale_factor, 2),
            'unit': 'g',
            'percent': 0
        },
        'Fat': {
            'amount': round(per_100g['fat_g'] * scale_factor, 2),
            'unit': 'g',
            'percent': 0
        },
        'Carbs': {
            'amount': round(per_100g['carb_g'] * scale_factor, 2),
            'unit': 'g',
            'percent': 0
        },
        'Dietary Fiber': {
            'amount': round(per_100g['fibre_g'] * scale_factor, 2),
            'unit': 'g'
        },
        'Cholesterol': {
            'amount': round(per_100g['cholesterol_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Ca': {
            'amount': round(per_100g['calcium_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Fe': {
            'amount': round(per_100g['iron_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Mg': {
            'amount': round(per_100g['magnesium_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'P': {
            'amount': round(per_100g['phosphorus_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Na': {
            'amount': round(per_100g['sodium_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Zn': {
            'amount': round(per_100g['zinc_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Cu': {
            'amount': round(per_100g['copper_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Mn': {
            'amount': round(per_100g['manganese_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Vitamin A': {
            'amount': round(per_100g['vita_ug'] * scale_factor, 2),
            'unit': 'µg'
        },
        'Vitamin B1': {
            'amount': round(per_100g['vitb1_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Vitamin B2': {
            'amount': round(per_100g['vitb2_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Niacin': {
            'amount': round(per_100g['vitb3_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Vitamin B6': {
            'amount': round(per_100g['vitb6_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Vitamin C': {
            'amount': round(per_100g['vitc_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
        'Vitamin E': {
            'amount': round(per_100g['vite_mg'] * scale_factor, 2),
            'unit': 'mg'
        },
    }
    
    # Calculate macro percentages
    total_cal = nutrients['Calories']['amount']
    if total_cal > 0:
        nutrients['Fat']['percent'] = round((nutrients['Fat']['amount'] * 9 / total_cal) * 100, 1)
        nutrients['Protein']['percent'] = round((nutrients['Protein']['amount'] * 4 / total_cal) * 100, 1)
        nutrients['Carbs']['percent'] = round((nutrients['Carbs']['amount'] * 4 / total_cal) * 100, 1)
    
    return nutrients


# Indian food keywords for prioritization
INDIAN_KEYWORDS = [
    'dal', 'daal', 'dhal', 'curry', 'masala', 'biryani', 'pulao', 'pilaf',
    'naan', 'roti', 'chapati', 'paratha', 'dosa', 'idli', 'vada',
    'samosa', 'pakora', 'bhaji', 'tikka', 'tandoori', 'korma',
    'paneer', 'aloo', 'gobi', 'palak', 'chana', 'rajma', 'chole',
    'raita', 'chutney', 'pickle', 'papad', 'khichdi', 'upma',
    'halwa', 'ladoo', 'barfi', 'gulab jamun', 'jalebi', 'kheer',
    'lassi', 'chai', 'masala chai'
]


def is_indian_query(query):
    """Check if query contains Indian food keywords"""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in INDIAN_KEYWORDS)
