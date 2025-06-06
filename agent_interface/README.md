# Agent Interface

This is the agent interface component of the Testing Agent project. It provides the core functionality for automated testing and interaction with web applications.

## Features

- Automated web testing
- Browser automation
- Test case generation
- Result analysis and reporting
- API integration with web interface

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running the Agent

### Windows
```bash
run.bat
```

### Unix-based Systems
```bash
chmod +x run.sh
./run.sh
```

## API Endpoints

The agent interface exposes the following endpoints:

- `POST /api/test/run` - Run a new test
- `GET /api/test/status` - Get test status
- `GET /api/test/results` - Get test results
- `POST /api/test/configure` - Configure test parameters

## Configuration

The agent can be configured through the `.env` file or through the web interface. Key configuration options include:

- Browser type
- Test timeout
- API keys
- Logging level
- Output directory

## Logging

Logs are stored in the `logs/` directory with the following structure:
- `test_runs/` - Individual test run logs
- `errors/` - Error logs
- `reports/` - Test reports

## Integration with Web Interface

The agent interface communicates with the web interface through a REST API. The web interface can:
- Start and stop tests
- Monitor test progress
- View test results
- Configure test parameters

## Development

To contribute to the agent interface:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This component is licensed under the MIT License - see the LICENSE file for details. 