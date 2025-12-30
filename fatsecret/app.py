from flask import Flask, render_template, request, jsonify
import fatsecret_data
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    # Only Search FatSecret
    fatsecret_results = fatsecret_data.search_fatsecret(query, max_results=20)
    
    return jsonify({'foods': fatsecret_results})

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

    fdc_id_str = str(fdc_id)
    
    # Use FatSecret data
    nutrients = fatsecret_data.get_fatsecret_nutrients(fdc_id_str, weight)
    if not nutrients:
        return jsonify({'error': 'FatSecret nutrition details not found'}), 404
    
    # Ideally we'd have the food name from the search result in the frontend
    # but for simplicity we'll just indicate it's from FatSecret or handle it generically.
    food_name = "Selected Food" 
    
    return jsonify({
        'food_name': food_name,
        'weight': weight,
        'nutrients': nutrients,
        'source': 'FatSecret'
    })

if __name__ == '__main__':
    # Try to inform the user if keys are missing
    if not fatsecret_data.CONSUMER_KEY:
        print("\nWARNING: FatSecret API keys are not set!")
        print("Please check your .env file.\n")
        
    app.run(debug=True, port=5001)
