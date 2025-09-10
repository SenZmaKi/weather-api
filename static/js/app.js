const API_BASE = '/weather';

// DOM Elements
const tabButtons = document.querySelectorAll('.tab-btn');
const searchForms = document.querySelectorAll('.search-form');
const cityForm = document.getElementById('city-form');
const coordinatesForm = document.getElementById('coordinates-form');
const forecastForm = document.getElementById('forecast-form');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const weatherDisplay = document.getElementById('weather-display');
const forecastDisplay = document.getElementById('forecast-display');
const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history-btn');

// Tab switching
tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // Update active states
        tabButtons.forEach(b => b.classList.remove('active'));
        searchForms.forEach(f => f.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(`${tab}-form`).classList.add('active');
        
        // Hide displays when switching tabs
        weatherDisplay.classList.add('hidden');
        forecastDisplay.classList.add('hidden');
        error.classList.add('hidden');
    });
});

// City search form
cityForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const city = document.getElementById('city-input').value.trim();
    if (city) {
        await fetchWeather({ city });
    }
});

// Coordinates search form
coordinatesForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const lat = parseFloat(document.getElementById('lat-input').value);
    const lon = parseFloat(document.getElementById('lon-input').value);
    await fetchWeather({ lat, lon });
});

// Forecast form
forecastForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const city = document.getElementById('forecast-city-input').value.trim();
    const days = document.getElementById('days-select').value;
    if (city) {
        await fetchForecast(city, days);
    }
});

// Clear history button
clearHistoryBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear all search history?')) {
        await clearHistory();
    }
});

// Fetch current weather
async function fetchWeather(params) {
    showLoading();
    hideError();
    hideDisplays();
    
    try {
        const queryParams = new URLSearchParams();
        if (params.city) {
            queryParams.append('city', params.city);
        } else {
            queryParams.append('lat', params.lat);
            queryParams.append('lon', params.lon);
        }
        
        const response = await fetch(`${API_BASE}?${queryParams}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Error: ${response.status}`);
        }
        
        const data = await response.json();
        displayWeather(data);
        await loadHistory();
    } catch (err) {
        showError(err.message);
    } finally {
        hideLoading();
    }
}

// Fetch weather forecast
async function fetchForecast(city, days) {
    showLoading();
    hideError();
    hideDisplays();
    
    try {
        const response = await fetch(`${API_BASE}/forecast?city=${encodeURIComponent(city)}&days=${days}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Error: ${response.status}`);
        }
        
        const data = await response.json();
        displayForecast(data);
        await loadHistory();
    } catch (err) {
        showError(err.message);
    } finally {
        hideLoading();
    }
}

// Display current weather
function displayWeather(data) {
    document.getElementById('location-name').textContent = 
        data.city ? `${data.city}, ${data.country}` : `${data.latitude}, ${data.longitude}`;
    document.getElementById('weather-time').textContent = 
        new Date(data.timestamp).toLocaleString();
    document.getElementById('temp-value').textContent = Math.round(data.temperature);
    document.getElementById('weather-icon').src = 
        `https://openweathermap.org/img/wn/${data.weather_icon}@2x.png`;
    document.getElementById('weather-desc').textContent = data.weather_description;
    document.getElementById('feels-like').textContent = 
        `Feels like ${Math.round(data.feels_like)}°C`;
    document.getElementById('humidity').textContent = `${data.humidity}%`;
    document.getElementById('wind-speed').textContent = `${data.wind_speed} m/s`;
    document.getElementById('pressure').textContent = `${data.pressure} hPa`;
    document.getElementById('clouds').textContent = `${data.clouds}%`;
    
    weatherDisplay.classList.remove('hidden');
}

// Display forecast
function displayForecast(data) {
    document.getElementById('forecast-location').textContent = 
        `${data.city}, ${data.country} - ${data.days_requested} Day${data.days_requested > 1 ? 's' : ''} Forecast`;
    
    const forecastCards = document.getElementById('forecast-cards');
    forecastCards.innerHTML = '';
    
    // Group forecast by day
    const dailyForecasts = {};
    data.forecast.forEach(item => {
        const date = new Date(item.datetime).toLocaleDateString();
        if (!dailyForecasts[date]) {
            dailyForecasts[date] = [];
        }
        dailyForecasts[date].push(item);
    });
    
    // Display each forecast item
    data.forecast.forEach(item => {
        const card = createForecastCard(item);
        forecastCards.appendChild(card);
    });
    
    forecastDisplay.classList.remove('hidden');
}

// Create forecast card element
function createForecastCard(item) {
    const card = document.createElement('div');
    card.className = 'forecast-card';
    
    const datetime = new Date(item.datetime);
    const date = datetime.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const time = datetime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    card.innerHTML = `
        <div class="forecast-date">${date}</div>
        <div class="forecast-time">${time}</div>
        <div class="forecast-icon">
            <img src="https://openweathermap.org/img/wn/${item.weather_icon}@2x.png" alt="${item.weather}">
        </div>
        <div class="forecast-temp">${Math.round(item.temperature)}°C</div>
        <div class="forecast-desc">${item.weather_description}</div>
    `;
    
    return card;
}

// Load search history
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history?limit=10`);
        const data = await response.json();
        
        if (data.items && data.items.length > 0) {
            displayHistory(data.items);
        } else {
            historyList.innerHTML = '<p class="no-history">No search history yet</p>';
        }
    } catch (err) {
        console.error('Failed to load history:', err);
    }
}

// Display search history
function displayHistory(items) {
    historyList.innerHTML = '';
    
    items.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const datetime = new Date(item.timestamp);
        const location = item.city || `${item.latitude}, ${item.longitude}`;
        
        historyItem.innerHTML = `
            <div class="history-item-header">
                <span class="history-type">${item.search_type}</span>
                <span class="history-time">${datetime.toLocaleString()}</span>
            </div>
            <div class="history-location">${location}</div>
        `;
        
        // Make history items clickable
        historyItem.addEventListener('click', () => {
            if (item.search_type === 'forecast' && item.city) {
                document.getElementById('forecast-city-input').value = item.city;
                document.getElementById('days-select').value = item.forecast_days || 5;
                tabButtons[2].click(); // Switch to forecast tab
            } else if (item.city) {
                document.getElementById('city-input').value = item.city;
                tabButtons[0].click(); // Switch to city tab
            } else if (item.latitude && item.longitude) {
                document.getElementById('lat-input').value = item.latitude;
                document.getElementById('lon-input').value = item.longitude;
                tabButtons[1].click(); // Switch to coordinates tab
            }
        });
        
        historyList.appendChild(historyItem);
    });
}

// Clear search history
async function clearHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            historyList.innerHTML = '<p class="no-history">No search history yet</p>';
        }
    } catch (err) {
        showError('Failed to clear history');
    }
}

// Helper functions
function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function showError(message) {
    error.textContent = message;
    error.classList.remove('hidden');
}

function hideError() {
    error.classList.add('hidden');
}

function hideDisplays() {
    weatherDisplay.classList.add('hidden');
    forecastDisplay.classList.add('hidden');
}

// Load history on page load
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});