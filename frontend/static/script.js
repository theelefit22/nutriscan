document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchInput = document.getElementById('foodInput');
    const searchBtn = document.getElementById('searchBtn');
    const resultsSection = document.getElementById('resultsSection');
    const resultsList = document.getElementById('resultsList');

    // Modal Elements
    const modalOverlay = document.getElementById('modalOverlay');
    const closeModalBtn = document.getElementById('closeModal');
    const modalFoodName = document.getElementById('modalFoodName');
    const modalBrand = document.getElementById('modalBrand');
    const weightInput = document.getElementById('weightInput');
    const calculateBtn = document.getElementById('calculateBtn');
    const nutritionResults = document.getElementById('nutritionResults');

    // State
    let currentFdcId = null;

    // Search Handler
    function handleSearch() {
        const query = searchInput.value.trim();
        if (!query) return;

        searchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        // Hide previous results
        resultsSection.classList.add('hidden');
        resultsList.innerHTML = '';

        fetch(`/api/search?query=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                const foods = data.foods;
                if (!foods || foods.length === 0) {
                    alert('No foods found. Try a different term.');
                    return;
                }

                foods.forEach(food => {
                    const card = document.createElement('div');
                    card.className = 'food-card';
                    card.innerHTML = `
                        <h4>${food.description}</h4>
                        <div class="brand">${food.brandOwner || 'Generic'}</div>
                    `;
                    card.addEventListener('click', () => openModal(food));
                    resultsList.appendChild(card);
                });

                resultsSection.classList.remove('hidden');
            })
            .catch(err => {
                console.error(err);
                alert('Something went wrong searching.');
            })
            .finally(() => {
                searchBtn.textContent = 'Analyze';
            });
    }

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    searchBtn.addEventListener('click', handleSearch);

    // Modal Handling
    function openModal(food) {
        currentFdcId = food.fdcId;
        modalFoodName.textContent = food.description;
        modalBrand.textContent = food.brandOwner || 'Generic';
        weightInput.value = 100; // Reset weight
        nutritionResults.classList.add('hidden'); // Hide results until calculated

        modalOverlay.classList.remove('hidden');

        // Auto calculate for 100g on open? Optional. Let's wait for user user interactions or do it immediately.
        // Let's do it immediately for better UX
        calculateNutrition();
    }

    function closeModal() {
        modalOverlay.classList.add('hidden');
        currentFdcId = null;
    }

    closeModalBtn.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });

    // Calculate Handler
    function calculateNutrition() {
        if (!currentFdcId) return;

        const weight = parseFloat(weightInput.value);
        if (isNaN(weight) || weight <= 0) {
            alert('Please enter a valid weight');
            return;
        }

        calculateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fdcId: currentFdcId, weight: weight })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                updateNutritionUI(data.nutrients);
            })
            .catch(err => {
                console.error(err);
                alert('Error calculating nutrition');
            })
            .finally(() => {
                calculateBtn.textContent = 'Calculate';
            });
    }

    calculateBtn.addEventListener('click', calculateNutrition);

    function updateNutritionUI(nutrients) {
        // Update Values - Macros (using the new dictionary structure)
        // Access safely
        const getVal = (key) => nutrients[key] ? nutrients[key].amount : 0;
        const getPct = (key) => nutrients[key] && nutrients[key].percent ? nutrients[key].percent : 0;

        document.getElementById('valCalories').textContent = Math.round(getVal('Calories'));
        document.getElementById('valProtein').textContent = getVal('Protein').toFixed(1) + 'g';
        document.getElementById('valFat').textContent = getVal('Fat').toFixed(1) + 'g';
        document.getElementById('valCarbs').textContent = getVal('Carbs').toFixed(1) + 'g';

        // Update Percentages (of calories from macros)
        document.getElementById('pctProtein').textContent = getPct('Protein').toFixed(1) + '%';
        document.getElementById('pctFat').textContent = getPct('Fat').toFixed(1) + '%';
        document.getElementById('pctCarbs').textContent = getPct('Carbs').toFixed(1) + '%';

        // Update Bar
        const pPct = getPct('Protein');
        const fPct = getPct('Fat');
        const cPct = getPct('Carbs');

        if (pPct + fPct + cPct > 0) {
            document.getElementById('barProtein').style.width = `${pPct}%`;
            document.getElementById('barFat').style.width = `${fPct}%`;
            document.getElementById('barCarbs').style.width = `${cPct}%`;
        }

        // --- Render Detailed List ---
        const listContainer = document.getElementById('detailedList');
        listContainer.innerHTML = ''; // Clear previous

        // Define order of display
        const displayOrder = [
            "Dietary Fiber",
            "Cholesterol",
            "Na", "Ca", "Mg", "Fe", "Mn", "Zn", "Cu", "P", // Minerals
            "Vitamin A", "Vitamin C", "Vitamin E", "Vitamin K",
            "Vitamin B1", "Vitamin B2", "Niacin",
            "Carotene", "Retinol Equivalent"
        ];

        displayOrder.forEach(name => {
            const data = nutrients[name];
            if (data) {
                const row = document.createElement('div');
                row.className = 'nutrient-row';

                // Add unit checking
                let amount = data.amount;
                // Maybe format small numbers? keeping it simple for now

                row.innerHTML = `
                    <span class="nutrient-name">${name}</span>
                    <span class="nutrient-value">${amount}${data.unit}</span>
                `;
                listContainer.appendChild(row);
            }
        });

        nutritionResults.classList.remove('hidden');
    }
});
