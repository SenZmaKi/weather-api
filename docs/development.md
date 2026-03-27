# Developer Guide

This guide covers everything you need to know to develop, contribute to, and extend the Weather API service.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Structure](#code-structure)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Code Style](#code-style)
- [Contributing](#contributing)
- [Common Tasks](#common-tasks)
- [Debugging](#debugging)

## Getting Started

### Prerequisites

- **Python 3.12+**: The project uses modern Python features
- **UV Package Manager**: For dependency management and virtual environments
- **Git**: For version control
- **OpenWeatherMap API Key**: Free tier available at [OpenWeatherMap](https://openweathermap.org/api)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SenZmaKi/weather-api.git
   cd weather-api
   ```

2. **Install UV (if not already installed):**
   ```bash
   pip install uv
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenWeatherMap API key
   ```

5. **Run the application:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## Development Environment

### Recommended Tools

- **IDE**: VS Code, PyCharm, or similar with Python support
- **Extensions** (for VS Code):
  - Python
  - Python Type Hint
  - autoDocstring
  - GitLens
  - REST Client

### Environment Configuration

The application uses environment variables for configuration. All settings are defined in `app/config.py`:

```python
class Settings(BaseSettings):
    # OpenWeatherMap API Configuration
    openweather_api_key: str
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    
    # Database Configuration  
    database_url: str = "sqlite+aiosqlite:///./weather.db"
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # CORS Configuration
    cors_origins: list[str] = ["*"]
```

### Development vs Production Settings

**Development (.env):**
```env
DEBUG=True
APP_HOST=127.0.0.1
APP_PORT=8000
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
RATE_LIMIT_PER_MINUTE=100
```

**Production:**
```env
DEBUG=False
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=["https://yourdomain.com"]
RATE_LIMIT_PER_MINUTE=60
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/weatherdb
```

## Code Structure

The project follows a clean architecture pattern:

```
weather-api/
├── app/
│   ├── api/                    # API layer
│   │   ├── endpoints.py        # Route handlers
│   │   └── schemas.py          # Pydantic models
│   ├── models/                 # Data layer
│   │   ├── database.py         # Database configuration
│   │   └── search_history.py   # SQLAlchemy models
│   ├── services/               # Business logic layer
│   │   └── weather_service.py  # External API integration
│   ├── config.py               # Application configuration
│   └── main.py                 # FastAPI application setup
├── static/                     # Frontend assets
│   ├── css/
│   ├── js/
│   └── favicon.ico
├── templates/                  # HTML templates
│   └── index.html
├── docs/                       # Documentation
└── tests/                      # Test files (to be added)
```

### Architecture Layers

1. **API Layer** (`app/api/`):
   - FastAPI route handlers
   - Request/response validation
   - HTTP error handling

2. **Service Layer** (`app/services/`):
   - Business logic
   - External API integration
   - Data transformation

3. **Data Layer** (`app/models/`):
   - Database models
   - Database configuration
   - Data access patterns

4. **Configuration** (`app/config.py`):
   - Environment-based settings
   - Application configuration

## Adding New Features

### 1. Adding a New API Endpoint

**Step 1: Define the response schema** in `app/api/schemas.py`:

```python
class NewFeatureResponse(BaseModel):
    """Schema for new feature response."""
    
    result: str
    timestamp: datetime
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

**Step 2: Add the endpoint** in `app/api/endpoints.py`:

```python
@router.get(
    "/new-feature",
    response_model=NewFeatureResponse,
    summary="New feature endpoint",
    description="Description of what this endpoint does",
)
async def new_feature_endpoint(
    param: str = Query(..., description="Parameter description"),
    db: AsyncSession = Depends(get_db),
) -> NewFeatureResponse:
    """
    Detailed docstring explaining the endpoint.
    
    Args:
        param: Description of the parameter
        db: Database session dependency
        
    Returns:
        NewFeatureResponse object
        
    Raises:
        HTTPException: If something goes wrong
    """
    try:
        # Your logic here
        result = f"Processed: {param}"
        
        return NewFeatureResponse(
            result=result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )
```

**Step 3: Add business logic** in `app/services/`:

```python
class NewFeatureService:
    """Service for new feature functionality."""
    
    def __init__(self) -> None:
        """Initialize the service."""
        self.settings = get_settings()
    
    async def process_data(self, data: str) -> Dict[str, Any]:
        """
        Process data for new feature.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data dictionary
            
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Your processing logic here
        return {"processed": data.upper()}
```

**Step 4: Add tests** (see Testing section)

**Step 5: Update documentation** in relevant markdown files

### 2. Adding Database Models

**Step 1: Define the model** in `app/models/`:

```python
# app/models/new_model.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.models.database import Base

class NewModel(Base):
    """Database model for new feature."""
    
    __tablename__ = "new_table"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<NewModel(id={self.id}, name='{self.name}')>"
```

**Step 2: Update the models init file**:

```python
# app/models/__init__.py
from .database import init_db, get_db, Base
from .search_history import SearchHistory
from .new_model import NewModel  # Add this line

__all__ = ["init_db", "get_db", "Base", "SearchHistory", "NewModel"]
```

**Step 3: Create migration** (if needed):

```python
# In development, the database schema is automatically created
# For production, you might want to add proper migrations
```

### 3. Adding Frontend Features

**Step 1: Add HTML structure** in `templates/index.html`:

```html
<!-- Add new tab -->
<button class="tab-btn" data-tab="new-feature">New Feature</button>

<!-- Add new form -->
<form id="new-feature-form" class="search-form">
    <input type="text" id="new-param" placeholder="Enter parameter" required>
    <button type="submit">Submit</button>
</form>

<!-- Add results container -->
<div id="new-feature-results" class="results-container hidden">
    <h3>New Feature Results</h3>
    <div id="new-feature-data"></div>
</div>
```

**Step 2: Add JavaScript functionality** in `static/js/app.js`:

```javascript
// Add event listener for new feature form
document.getElementById('new-feature-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const param = document.getElementById('new-param').value;
    
    if (!param.trim()) {
        showToast('Please enter a parameter', 'error');
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/new-feature?param=${encodeURIComponent(param)}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Request failed');
        }
        
        displayNewFeatureResults(data);
        showToast('New feature data retrieved successfully!', 'success');
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
});

// Function to display results
function displayNewFeatureResults(data) {
    const resultsContainer = document.getElementById('new-feature-results');
    const dataContainer = document.getElementById('new-feature-data');
    
    dataContainer.innerHTML = `
        <p><strong>Result:</strong> ${data.result}</p>
        <p><strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
    `;
    
    resultsContainer.classList.remove('hidden');
}
```

**Step 3: Add CSS styling** in `static/css/styles.css` if needed.

## Testing

### Running Tests

```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio httpx pytest-cov

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app tests/

# Run specific test file
uv run pytest tests/test_api.py

# Run with verbose output
uv run pytest -v
```

### Writing Tests

**Example API test** (`tests/test_api.py`):

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_weather_by_city():
    """Test getting weather by city name."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/weather?city=London")
    
    assert response.status_code == 200
    data = response.json()
    assert "temperature" in data
    assert "city" in data
    assert data["city"] == "London"

@pytest.mark.asyncio
async def test_get_weather_invalid_city():
    """Test getting weather with invalid city."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/weather?city=InvalidCityName123")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data

@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Weather API"
```

**Example service test** (`tests/test_weather_service.py`):

```python
import pytest
from unittest.mock import Mock, patch
from app.services.weather_service import WeatherService

@pytest.mark.asyncio
async def test_get_current_weather_by_city():
    """Test weather service city lookup."""
    service = WeatherService()
    
    # Mock the HTTP response
    mock_response_data = {
        "name": "London",
        "sys": {"country": "GB"},
        "coord": {"lat": 51.5074, "lon": -0.1278},
        "main": {
            "temp": 15.6,
            "feels_like": 14.2,
            "temp_min": 13.1,
            "temp_max": 18.3,
            "pressure": 1013,
            "humidity": 72
        },
        "weather": [{
            "main": "Clouds",
            "description": "scattered clouds",
            "icon": "03d"
        }],
        "wind": {"speed": 3.6, "deg": 230},
        "clouds": {"all": 40},
        "dt": 1704110400
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await service.get_current_weather_by_city("London")
        
        assert result["name"] == "London"
        assert result["main"]["temp"] == 15.6
```

### Test Configuration

Create `tests/conftest.py` for test configuration:

```python
import pytest
import os
from app.config import get_settings

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    os.environ["OPENWEATHER_API_KEY"] = "test_api_key"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    return get_settings()

@pytest.fixture
async def test_db():
    """Create test database."""
    from app.models import init_db
    await init_db()
```

## Code Style

### Python Style Guide

- Follow **PEP 8** for Python code style
- Use **type hints** for all functions and methods
- Write **docstrings** for all modules, classes, and functions
- Use **f-strings** for string formatting
- Maximum line length: **88 characters** (Black formatter)

### Code Formatting

```bash
# Install formatting tools
uv add --dev black isort mypy flake8

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy app/

# Linting
uv run flake8 app/
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

Install and use:
```bash
uv add --dev pre-commit
uv run pre-commit install
uv run pre-commit run --all-files
```

### Documentation Style

- Use **Google-style docstrings**
- Include **Args**, **Returns**, and **Raises** sections
- Write clear, concise descriptions
- Include **examples** where helpful

Example:
```python
async def get_weather_by_city(self, city: str) -> Dict[str, Any]:
    """
    Get current weather data by city name.

    This method fetches current weather conditions from the OpenWeatherMap API
    for the specified city. The response includes temperature, humidity, wind
    speed, and other meteorological data.

    Args:
        city: Name of the city to get weather for. Must be at least 2 characters.

    Returns:
        Dictionary containing weather data with the following structure:
        - name (str): City name
        - main (dict): Temperature and atmospheric data
        - weather (list): Weather conditions
        - wind (dict): Wind data
        - clouds (dict): Cloudiness data

    Raises:
        httpx.HTTPStatusError: If the API request fails (e.g., city not found).
        ValueError: If the city name is invalid.

    Example:
        >>> service = WeatherService()
        >>> weather = await service.get_weather_by_city("London")
        >>> print(weather["main"]["temp"])
        15.6
    """
```

## Contributing

### Contribution Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the code style guidelines
4. **Add tests** for your changes
5. **Run tests** to ensure nothing breaks
6. **Update documentation** if needed
7. **Commit your changes**: `git commit -m 'Add amazing feature'`
8. **Push to the branch**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

### Pull Request Guidelines

- **Write clear commit messages** describing what changed
- **Include tests** for new functionality
- **Update documentation** for API changes
- **Ensure all tests pass**
- **Keep changes focused** - one feature per PR
- **Link related issues** in the PR description

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add weather alerts endpoint
fix(service): handle API timeout errors
docs(readme): update installation instructions
test(api): add tests for forecast endpoint
```

## Common Tasks

### Adding Environment Variables

1. **Add to `app/config.py`**:
   ```python
   class Settings(BaseSettings):
       new_setting: str = "default_value"
   ```

2. **Add to `.env.example`**:
   ```env
   NEW_SETTING=example_value
   ```

3. **Update documentation** if the setting affects usage

### Database Operations

**Adding new columns:**
```python
# Add column to model
class SearchHistory(Base):
    new_field = Column(String(255), nullable=True)

# In development, restart the app to auto-create
# In production, create proper migration
```

**Querying data:**
```python
async def get_recent_searches(db: AsyncSession, limit: int = 10):
    """Get recent weather searches."""
    result = await db.execute(
        select(SearchHistory)
        .order_by(SearchHistory.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()
```

### Adding Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Create limiter
limiter = Limiter(key_func=get_remote_address)

# Apply to endpoint
@router.get("/limited-endpoint")
@limiter.limit("5/minute")
async def limited_endpoint(request: Request):
    return {"message": "Rate limited endpoint"}
```

## Debugging

### Common Issues

**1. Import Errors:**
```bash
# Ensure you're in the project directory and using UV
cd /path/to/weather-api
uv run python -m app.main
```

**2. Database Issues:**
```bash
# Delete and recreate database
rm weather.db
uv run uvicorn app.main:app --reload
```

**3. API Key Issues:**
```bash
# Check if API key is set
uv run python -c "from app.config import get_settings; print(get_settings().openweather_api_key)"
```

### Debug Mode

Enable debug mode in `.env`:
```env
DEBUG=True
```

This enables:
- Detailed error tracebacks
- Auto-reload on code changes
- More verbose logging

### Logging

Add logging to your code:
```python
import logging

logger = logging.getLogger(__name__)

# In your functions
logger.info(f"Processing weather request for city: {city}")
logger.error(f"API request failed: {error}")
```

Configure logging in `app/main.py`:
```python
import logging

if settings.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
```

### Testing API Endpoints

**Using httpx in Python:**
```python
import asyncio
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/weather?city=London")
        print(response.status_code)
        print(response.json())

asyncio.run(test_api())
```

**Using curl:**
```bash
# Test with verbose output
curl -v "http://localhost:8000/weather?city=London"

# Test with timing
curl -w "@curl-format.txt" "http://localhost:8000/weather?city=London"
```

Create `curl-format.txt`:
```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

This completes the comprehensive developer guide. It covers everything from basic setup to advanced debugging techniques, making it easy for new contributors to get started and for experienced developers to understand the codebase structure.