# AI Job Applier - Job Scraper

A modular Python job scraping system that collects software/AI job postings from multiple sources (LinkedIn, Greenhouse, Lever) and stores them in a SQLite database.

## Features

- **Multi-source scraping**: Support for LinkedIn, Greenhouse, and Lever job boards
- **Modular architecture**: Easy to add new job boards
- **Database storage**: SQLite database for job persistence
- **Type hints**: Full type annotation for code clarity
- **Logging**: Comprehensive logging for debugging
- **Playwright support**: Dynamic website scraping with Playwright
- **BeautifulSoup parsing**: HTML parsing for job details

## Requirements

- Python 3.11+
- Playwright
- BeautifulSoup4
- Pydantic
- SQLAlchemy
- python-dotenv

## Project Structure

```
ai-job-applier/
├── scraper/
│   ├── base_scraper.py          # Abstract base class for scrapers
│   ├── linkedin_scraper.py       # LinkedIn job scraper
│   ├── greenhouse_scraper.py     # Greenhouse job board scraper
│   ├── lever_scraper.py          # Lever job board scraper
│   └── __init__.py
│
├── database/
│   ├── db.py                     # Database operations
│   ├── models.py                 # SQLAlchemy and Pydantic models
│   └── __init__.py
│
├── utils/
│   ├── config.py                 # Configuration management
│   └── __init__.py
│
├── run_scraper.py                # Main runner script
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore file
└── README.md                     # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   cd ai-job-applier
   ```

2. **Create a virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

Edit `.env` file to configure the scraper:

```env
# Database Configuration
HEADLESS_MODE=true              # Run browser in headless mode
SCRAPER_TIMEOUT=30000           # Timeout in milliseconds
SCRAPER_WAIT_TIME=5000          # Wait time between actions

# LinkedIn Configuration (optional)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
```

## Usage

### Run the scraper:

```bash
python run_scraper.py
```

This will:
1. Initialize the database
2. Scrape LinkedIn for "AI Engineer" jobs
3. Store found jobs in the database
4. Print statistics

### Search for different job titles:

To search for different keywords, edit `run_scraper.py` and modify the `run_linkedin_scraper()` call:

```python
total_saved += run_linkedin_scraper(keywords="Software Engineer", location="San Francisco")
```

### Use with Greenhouse/Lever boards:

Uncomment the Greenhouse/Lever section in `run_scraper.py` and provide the job board URL:

```python
total_saved += run_greenhouse_scraper(
    job_board_url="https://jobs.greenhouse.io/example"
)
```

## Database Schema

### Jobs Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| title | String | Job title |
| company | String | Company name |
| location | String | Job location |
| url | String | Job URL (unique) |
| description | Text | Job description |
| source | String | Data source (LinkedIn, Greenhouse, Lever) |
| scraped_at | DateTime | Scrape timestamp |

## Database Operations

The `database/db.py` module provides utility functions:

```python
from database import init_db, insert_job, get_all_jobs, get_db_stats

# Initialize database
init_db()

# Insert a job
insert_job(job_schema)

# Get all jobs
jobs = get_all_jobs()

# Get stats
stats = get_db_stats()
print(stats)  # {'total_jobs': 150, 'by_source': {'LinkedIn': 100, 'Greenhouse': 50}}
```

## Creating New Scrapers

To add a new scraper:

1. **Create a new scraper class** in `scraper/new_scraper.py`:

```python
from scraper.base_scraper import BaseScraper
from database.models import JobSchema

class NewScraper(BaseScraper):
    def __init__(self):
        super().__init__("NewSource")
    
    def search_jobs(self, keywords: str, location: str = "", **kwargs):
        # Implement scraping logic
        pass
    
    def parse_job_card(self, html: str):
        # Parse HTML and return JobSchema
        pass
    
    def close(self):
        # Cleanup resources
        pass
```

2. **Add to imports** in `scraper/__init__.py`

3. **Use in run_scraper.py**:

```python
from scraper import NewScraper

scraper = NewScraper()
jobs = scraper.search_jobs(keywords="AI Engineer")
```

## Logging

Logs are written to both console and `scraper.log` file. Adjust log level in `.env`:

```env
LOG_LEVEL=DEBUG    # More detailed logging
```

## Job Model

Jobs are validated using Pydantic `JobSchema`:

```python
from database.models import JobSchema

job = JobSchema(
    title="AI Engineer",
    company="Google",
    location="Mountain View, CA",
    url="https://example.com/job/123",
    description="We are hiring...",
    source="LinkedIn"
)
```

## Error Handling

The scraper includes comprehensive error handling:

- Database connection failures
- Network timeouts
- HTML parsing errors
- Job validation errors

All errors are logged to both console and log file.

## Performance Tips

1. **Increase scroll limit** in LinkedIn scraper for more results
2. **Parallel scraping**: Run multiple scrapers in separate processes
3. **Database indexing**: URLs are indexed for faster lookups
4. **Headless mode**: Already enabled by default for faster execution

## Common Issues

### Issue: LinkedIn page not loading
**Solution**: Ensure headless mode is false and check network connection

### Issue: No jobs found
**Solution**: Check job board URL and search keywords

### Issue: Duplicate jobs
**Solution**: Jobs are checked against URLs before insertion

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! To add support for new job boards:

1. Create a new scraper class inheriting from `BaseScraper`
2. Implement required methods
3. Test with sample data
4. Submit a pull request

## Support

For issues or questions, please open an issue on GitHub.

## Future Enhancements

- [ ] Job filtering and search
- [ ] Email notifications for new jobs
- [ ] Job application tracking
- [ ] Duplicate detection
- [ ] Job salary extraction
- [ ] Skill matching
- [ ] REST API for job queries
- [ ] Web UI dashboard

---

Happy scraping! 🚀