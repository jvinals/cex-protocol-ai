# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

CEX Protocol AI is a full-stack application with a React frontend and FastAPI backend. The project is in early stages with a minimal React frontend setup and a planned FastAPI backend structure.

## Architecture

### Frontend (React + Vite)
- **Location**: `frontend/`
- **Technology**: React 19.1.1 with Vite 7.1.2
- **Language**: JavaScript with JSX (no TypeScript yet despite type dependencies)
- **Structure**: Standard Vite React application with minimal setup

### Backend (FastAPI)
- **Location**: `backend/`
- **Technology**: FastAPI (planned - only virtual environment exists currently)
- **Language**: Python 3.12+
- **Status**: Virtual environment created but no source code implemented yet

## Common Development Commands

### Frontend Commands
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Preview production build
npm run preview
```

### Backend Commands (when implemented)
```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (when requirements.txt is created)
pip install -r requirements.txt

# Run development server (expected on http://localhost:8000)
python main.py  # When main.py is implemented

# Or with uvicorn directly
uvicorn main:app --reload  # When main.py exists
```

### Testing Commands
Currently no testing framework is configured. Future implementation expected to include:
- Frontend: Vitest or Jest for React components
- Backend: pytest for Python tests

## Development Environment Setup

### Prerequisites
- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Git

### First-time Setup
1. Clone the repository
2. Set up frontend:
   ```bash
   cd frontend
   npm install
   ```
3. Set up backend (when implemented):
   ```bash
   cd backend
   source venv/bin/activate
   # Install dependencies when available
   ```

## Code Structure Notes

### Frontend Structure
- Standard Vite React setup with default template files
- Main entry point: `src/main.jsx`
- App component: `src/App.jsx`
- CSS files: `src/App.css`, `src/index.css`
- ESLint configured with React-specific rules

### ESLint Configuration
- Uses modern ESLint flat config format
- Configured for React with hooks and refresh plugins
- Custom rule for unused variables with pattern `^[A-Z_]`

### Planned API Endpoints (from README)
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/test` - Test endpoint

## Important Notes for Development

1. **Backend Implementation Pending**: The backend directory only contains a virtual environment. All FastAPI code needs to be implemented.

2. **TypeScript Ready**: Despite using JSX files, TypeScript dependencies are installed, suggesting future TypeScript migration is planned.

3. **CORS Configuration**: README mentions CORS will be enabled for frontend-backend communication.

4. **Virtual Environment**: Backend uses Python virtual environment managed with `uv` tool.

5. **Development Ports**:
   - Frontend: http://localhost:5173 (Vite default)
   - Backend: http://localhost:8000 (FastAPI default)

## Project Status

- ✅ Frontend: Basic React setup complete
- ⏳ Backend: Virtual environment created, source code pending
- ⏳ Testing: Not yet configured
- ⏳ CI/CD: Not yet configured
- ⏳ Documentation: Basic README exists

## Git Workflow

Standard Git workflow with feature branches:
```bash
git checkout -b feature/amazing-feature
git commit -m 'Add some amazing feature'
git push origin feature/amazing-feature
# Open Pull Request
```
