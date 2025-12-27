# 🃏 pkr.img

A real-time poker chip tracking web app.  
Players upload photos of their chip stacks, the system calculates payouts, and the host instantly sees results on a live dashboard.

Built with **Next.js + FastAPI + SQLAlchemy**.

---

## 🚀 Features

- **Create & Join Parties**
  - Host creates a party and automatically becomes the first player
  - Players join via party code
- **Live Host Dashboard**
  - See who has joined and who has submitted
  - End game and generate payouts
- **Player Uploads**
  - Each player uploads a photo of their chip stack
  - Multiple submissions allowed — only the latest counts
- **Automatic Settlement**
  - Computes P&L for each player
  - Generates minimal Venmo payment graph
- **Role-aware UI**
  - Same upload page for host & players
  - Upload page automatically redirects:
    - Host → Host Dashboard
    - Player → Party Dashboard

---

## 🧠 System Architecture
Frontend: Next.js (App Router)
Backend: FastAPI + SQLAlchemy
Database: SQLite (MVP)
Vision: Future YOLO-based chip recognition


---

## 🗺️ User Flow

### 1. Home
Choose:
- **Host a Game**
- **Join a Game**

### 2. Host Flow
Create Party → Host Dashboard → Upload Chips → End Game → Results

### 3. Player Flow
Join Party → Upload Chips → Party Dashboard → Results


---

## 🧩 Key Design Decisions

- **Host is also a Player**
  - Host is automatically registered as the first player
  - Host can upload chips just like everyone else
- **Role-aware Routing**
  - `localStorage` stores `role:{partyCode}` = `host | player`
  - Upload page redirects based on role
- **Live Updates**
  - Dashboards auto-refresh every 2 seconds

---

## 📁 Project Structure

pkr.img/\n
├── api/ # FastAPI backend\n
│ ├── main.py\n
│ ├── models.py\n
│ ├── db.py\n
│ └── uploads/\n
│\n
├── web/ # Next.js frontend\n
│ └── app/\n
│ ├── page.tsx\n
│ └── party/\n
│ └── [code]/\n
│ ├── host/page.tsx\n
│ ├── join/page.tsx\n
│ ├── upload/page.tsx\n
│ └── page.tsx # Party Dashboard\n

---

## ⚙️ Setup

### Backend

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```
### Frontend
cd web\n
npm install\n
npm run dev\n
Frontend: http://localhost:3000\n
API: http://127.0.0.1:8000\n

🧪 Quick Test\n
curl http://127.0.0.1:8000/health\n
Expected response:\n
{ "status": "ok" }\n

🛣️ Roadmap

 YOLO-based chip recognition

 Real-time WebSocket updates

 Authentication

 Persistent storage (Postgres)

 Multi-device host sync

 Production deployment

🧑‍💻 Author

Built by Tian Yi Yang

---
