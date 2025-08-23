# CEX Protocol AI

A full-stack application with React frontend and FastAPI backend for CEX Protocol AI.

## Project Structure

```
cex-protocol-ai/
├── frontend/          # React + Vite frontend
├── backend/           # FastAPI backend
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Git

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:5173`

### Backend Setup

```bash
cd backend
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
# Install dependencies (already done with uv)
python main.py
```

The backend will run on `http://localhost:8000`

## Development

### Frontend
- Built with React + TypeScript
- Vite for fast development and building
- ESLint for code quality

### Backend
- Built with FastAPI
- Python virtual environment with uv
- CORS enabled for frontend communication

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/test` - Test endpoint

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is private and proprietary.
