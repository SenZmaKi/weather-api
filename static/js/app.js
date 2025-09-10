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

// Toast notification system
function showToast(message, type = 'info') {
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Tab switching with smooth transitions
tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // Update active states with animation
        tabButtons.forEach(b => b.classList.remove('active'));
        searchForms.forEach(f => {
            f.classList.remove('active');
            f.style.animation = '';
        });
        
        btn.classList.add('active');
        const targetForm = document.getElementById(`${tab}-form`);
        targetForm.classList.add('active');
        targetForm.style.animation = 'slideIn 0.3s ease-out';
        
        // Hide displays when switching tabs
        weatherDisplay.classList.add('hidden');
        forecastDisplay.classList.add('hidden');
        error.classList.add('hidden');
    });
});

// Form validation
function validateCity(city) {
    if (!city || city.trim().length < 2) {
        showToast('Please enter a valid city name (at least 2 characters)', 'error');
        return false;
    }
    return true;
}

function validateCoordinates(lat, lon) {
    if (isNaN(lat) || isNaN(lon)) {
        showToast('Please enter valid numeric coordinates', 'error');
        return false;
    }
    if (lat < -90 || lat > 90) {
        showToast('Latitude must be between -90 and 90', 'error');
        return false;
    }
    if (lon < -180 || lon > 180) {
        showToast('Longitude must be between -180 and 180', 'error');
        return false;
    }
    return true;
}

// City search form with validation
cityForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const cityInput = document.getElementById('city-input');
    const city = cityInput.value.trim();
    
    if (validateCity(city)) {
        cityInput.blur(); // Remove focus for better mobile experience
        await fetchWeather({ city });
    }
});

// Coordinates search form with validation
coordinatesForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const latInput = document.getElementById('lat-input');
    const lonInput = document.getElementById('lon-input');
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);
    
    if (validateCoordinates(lat, lon)) {
        latInput.blur();
        lonInput.blur();
        await fetchWeather({ lat, lon });
    }
});

// Forecast form with validation
forecastForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const cityInput = document.getElementById('forecast-city-input');
    const city = cityInput.value.trim();
    const days = document.getElementById('days-select').value;
    
    if (validateCity(city)) {
        cityInput.blur();
        await fetchForecast(city, days);
    }
});

// Clear history button with confirmation
clearHistoryBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear all search history?')) {
        await clearHistory();
    }
});

// Fetch current weather with enhanced error handling
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
        showToast('Weather data loaded successfully', 'success');
        await loadHistory();
    } catch (err) {
        showError(err.message);
        showToast(err.message, 'error');
    } finally {
        hideLoading();
    }
}

// Fetch weather forecast with enhanced error handling
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
        showToast(`${days}-day forecast loaded for ${city}`, 'success');
        await loadHistory();
    } catch (err) {
        showError(err.message);
        showToast(err.message, 'error');
    } finally {
        hideLoading();
    }
}

// Display current weather
function displayWeather(data) {
    document.getElementById('location-name').textContent = 
        data.city ? `${data.city}, ${data.country}` : `${data.latitude.toFixed(2)}, ${data.longitude.toFixed(2)}`;
    document.getElementById('weather-time').textContent = 
        new Date(data.timestamp).toLocaleString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    
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

// Load search history with enhanced display
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history?limit=10`);
        const data = await response.json();
        
        if (data.items && data.items.length > 0) {
            displayHistory(data.items);
        } else {
            historyList.innerHTML = '<p class="no-history">No search history yet. Start by searching for weather!</p>';
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
        const location = item.city || `${item.latitude?.toFixed(2)}, ${item.longitude?.toFixed(2)}`;
        
        historyItem.innerHTML = `
            <div class="history-type">${item.search_type}</div>
            <div class="history-location">${location}</div>
            <div class="history-time">${datetime.toLocaleString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit' 
            })}</div>
        `;
        
        // Make history items clickable
        historyItem.addEventListener('click', () => {
            if (item.search_type === 'forecast' && item.city) {
                document.getElementById('forecast-city-input').value = item.city;
                document.getElementById('days-select').value = item.forecast_days || 5;
                tabButtons[2].click();
            } else if (item.city) {
                document.getElementById('city-input').value = item.city;
                tabButtons[0].click();
            } else if (item.latitude && item.longitude) {
                document.getElementById('lat-input').value = item.latitude;
                document.getElementById('lon-input').value = item.longitude;
                tabButtons[1].click();
            }
        });
        
        historyList.appendChild(historyItem);
    });
}

// Clear search history with enhanced feedback
async function clearHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const data = await response.json();
            historyList.innerHTML = '<p class="no-history">No search history yet. Start by searching for weather!</p>';
            showToast(`Successfully cleared ${data.deleted_count} history items`, 'success');
        }
    } catch (err) {
        showError('Failed to clear history');
        showToast('Failed to clear history', 'error');
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


// Theme management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Load history on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();
    
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Load search history
    loadHistory();
});