# Tech Stack

- **Frontend**: Next.js 15 + React 19 + Tailwind CSS + TypeScript
- **Backend**: FastAPI (Python 3.11) + SQLAlchemy 2.0
- **Database**: PostgreSQL 15 + Redis (caché/colas)
- **ComfyUI**: Python worker con GPU (RTX 5060 Ti)
- **Deployment**: Docker + Docker Compose

## Estructura

```
comfyui-web/
├── frontend/          # Next.js 15
│   ├── src/
│   │   ├── app/      # App Router
│   │   ├── components/
│   │   └── lib/
│   └── tailwind.config.js
├── backend/           # FastAPI
│   ├── api/
│   ├── models/
│   ├── services/
│   └── main.py
├── worker/           # ComfyUI worker
│   └── worker.py
└── docker-compose.yml
```

## API Endpoints

- `POST /api/jobs` - Crear job (imagen/video)
- `GET /api/jobs` - Listar jobs
- `GET /api/jobs/{id}` - Ver job
- `WS /ws/jobs` - WebSocket real-time
- `GET /api/stats` - Estadísticas
