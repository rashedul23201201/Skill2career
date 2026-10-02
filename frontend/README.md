# SKILL2CAREER - Frontend Foundation

> **Bangladesh Job Preparation Ecosystem**  
> *Tagline:* Learn Today, Get Hired Tomorrow

---

## 1. Overview

The frontend is built using **React 19**, **Vite**, **Tailwind CSS v3**, **Axios**, and **React Router v7**. It features a centralized API service layer, authentication context/provider with local storage persistence, responsive layout components, and a dedicated design system palette.

---

## 2. Directory Structure

```text
frontend/
├── src/
│   ├── assets/              # Static media & imagery
│   │
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Navbar, Footer, ProtectedRoute
│   │   ├── forms/           # Button, Input
│   │   └── layout/          # Layout wrappers
│   │
│   ├── pages/               # Route page components
│   │   ├── Home.jsx         # Landing page & ecosystem overview
│   │   ├── Login.jsx        # User login form
│   │   ├── Register.jsx     # User registration with role selection
│   │   ├── Dashboard.jsx    # User dashboard foundation & health display
│   │   └── NotFound.jsx     # 404 handler
│   │
│   ├── layouts/             # App shell layouts
│   │   └── MainLayout.jsx   # Layout with Navbar & Footer
│   │
│   ├── services/            # Centralized API layer
│   │   ├── api.js           # Axios instance with auth interceptor
│   │   └── authService.js   # Auth endpoints service
│   │
│   ├── context/             # React context providers
│   │   └── AuthContext.jsx  # Authentication state & actions
│   │
│   ├── hooks/               # Custom hooks
│   │   └── useAuth.js       # Auth consumer hook
│   │
│   ├── routes/              # Routing configuration
│   │   └── AppRoutes.jsx    # React Router routes tree
│   │
│   ├── constants/           # Global constants & routes
│   │   └── index.js
│   │
│   ├── utils/               # Storage and formatting helpers
│   │   └── index.js
│   │
│   ├── App.jsx              # Main App component with providers
│   ├── index.css            # Tailwind directives and base typography
│   └── main.jsx             # React DOM root entry
│
├── public/                  # Public assets
├── .env.example             # Environment template
├── package.json             # NPM dependencies & scripts
├── tailwind.config.js       # Tailwind brand colors and typography
└── vite.config.js           # Vite build configuration
```

---

## 3. Brand Design System

### Color Palette

| Token | Hex Value | Usage |
|---|---|---|
| **Primary Navy** | `#0F172A` (`navy-900`) | Main text, dark headers, brand buttons |
| **Primary Emerald** | `#10B981` (`emerald-500`) | Accents, success states, CTA buttons |
| **Slate** | `#64748B` (`slate-500`) | Subtitles, muted copy, borders |
| **Background** | `#F8FAFC` (`brandBg`) | Main page background |
| **Amber** | `#F59E0B` (`amber-500`) | Warnings, pending states, company badge |
| **Crimson** | `#EF4444` (`crimson`) | Errors, alerts, danger actions |

### Typography

* **Headings:** `Plus Jakarta Sans`, `Inter`, sans-serif
* **Body:** `Inter`, sans-serif

---

## 4. Setup & Running Locally

### Install dependencies

```bash
cd frontend
npm install
```

### Environment configuration

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Default content:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Run development server

```bash
npm run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173).

### Production build

```bash
npm run build
npm run preview
```

---

## 5. Adding Future Services (Sprint Tickets)

To add new domain services without restructuring, create a new service file inside `src/services/` following the existing `authService.js` pattern:

```javascript
// src/services/courseService.js
import api from "./api";

export const courseService = {
  getCourses: () => api.get("/courses").then(res => res.data),
  getCourseById: (id) => api.get(`/courses/${id}`).then(res => res.data),
};

export default courseService;
```
