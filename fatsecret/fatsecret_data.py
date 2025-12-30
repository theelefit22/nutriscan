import os
import re
from fatsecret import Fatsecret
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Use environment variables for API keys
CONSUMER_KEY = os.environ.get("FATSECRET_CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("FATSECRET_CONSUMER_SECRET")

try:
    if CONSUMER_KEY and CONSUMER_SECRET:
        fs = Fatsecret(CONSUMER_KEY, CONSUMER_SECRET)
    else:
        fs = None
        print("Warning: FatSecret API keys not found in environment.")
except Exception as e:
    fs = None
    print(f"Error initializing Fatsecret API: {e}")

def search_fatsecret(query, max_results=15):
    """
    Search FatSecret for food items matching the query.
    """
    if not fs:
        return []
    
    try:
        results = fs.foods_search(query)
        formatted_results = []
        
        # FatSecret returns a list of foods
        if not results:
            return []
            
        for food in results[:max_results]:
            formatted_results.append({
                'fdcId': food['food_id'],
                'description': food['food_name'],
                'source': 'FatSecret',
                'dataType': food.get('food_type', 'Brand'),
                'brandOwner': food.get('brand_name', ''),
                'score': 100 # FatSecret's internal ranking is usually good
            })
        return formatted_results
    except Exception as e:
        print(f"Error searching FatSecret: {e}")
        return []

def get_fatsecret_nutrients(food_id, weight_grams=100):
    """
    Get detailed nutrients for a FatSecret food item.
    """
    if not fs:
        return None
    
    try:
        food = fs.food_get(food_id)
        if not food:
            return None
            
        # FatSecret provides "servings" which can be many things.
        # We need to find the one closest to 100g or the standard serving.
        servings = food.get('servings', {}).get('serving', [])
        if isinstance(servings, dict):
            servings = [servings]
            
        # Look for a metric serving (grams)
        selected_serving = None
        for s in servings:
            if s.get('metric_serving_unit') == 'g':
                selected_serving = s
                break
        
        if not selected_serving:
            selected_serving = servings[0] # Fallback to first
            
        # Scaling factor: weight_grams / metric_serving_amount
        metric_amount = float(selected_serving.get('metric_serving_amount', 100))
        scale_factor = weight_grams / metric_amount
        
        nutrients = {
            'Calories': {
                'amount': round(float(selected_serving.get('calories', 0)) * scale_factor, 2),
                'unit': 'kcal',
                'percent': 0
            },
            'Protein': {
                'amount': round(float(selected_serving.get('protein', 0)) * scale_factor, 2),
                'unit': 'g',
                'percent': 0
            },
            'Fat': {
                'amount': round(float(selected_serving.get('fat', 0)) * scale_factor, 2),
                'unit': 'g',
                'percent': 0
            },
            'Carbs': {
                'amount': round(float(selected_serving.get('carbohydrate', 0)) * scale_factor, 2),
                'unit': 'g',
                'percent': 0
            },
            'Dietary Fiber': {
                'amount': round(float(selected_serving.get('fiber', 0)) * scale_factor, 2),
                'unit': 'g'
            },
            'Cholesterol': {
                'amount': round(float(selected_serving.get('cholesterol', 0)) * scale_factor, 2),
                'unit': 'mg'
            },
            'Ca': {
                'amount': round(float(selected_serving.get('calcium', 0)) * scale_factor, 2),
                'unit': 'mg'
            },
            'Fe': {
                'amount': round(float(selected_serving.get('iron', 0)) * scale_factor, 2),
                'unit': 'mg'
            },
            'Na': {
                'amount': round(float(selected_serving.get('sodium', 0)) * scale_factor, 2),
                'unit': 'mg'
            }
        }
        
        # Calculate percentages
        total_cal = nutrients['Calories']['amount']
        if total_cal > 0:
            nutrients['Fat']['percent'] = round((nutrients['Fat']['amount'] * 9 / total_cal) * 100, 1)
            nutrients['Protein']['percent'] = round((nutrients['Protein']['amount'] * 4 / total_cal) * 100, 1)
            nutrients['Carbs']['percent'] = round((nutrients['Carbs']['amount'] * 4 / total_cal) * 100, 1)
            
        return nutrients
    except Exception as e:
        print(f"Error getting FatSecret details: {e}")
        return None
