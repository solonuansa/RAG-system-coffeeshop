# Frontend - Coffee Shop RAG UI

Frontend chat berbasis Next.js untuk berinteraksi dengan backend RAG FastAPI.

## Tech Stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS 4
- Framer Motion
- React Markdown + Remark GFM

## Struktur Penting

```text
frontend/
  app/
    api/chat/route.ts   # proxy server-side ke backend FastAPI
    page.tsx            # halaman chat utama
  components/
    chat-shell.tsx
  lib/
    api.ts              # client helper ke /api/chat
  types/
    chat.ts
  .env.local.example
```

## Environment Variables

Buat file `frontend/.env.local`:

```env
BACKEND_API_URL=http://127.0.0.1:8000/api/chat
BACKEND_API_TOKEN=
```

Keterangan:
- `BACKEND_API_URL`: endpoint backend FastAPI.
- `BACKEND_API_TOKEN`: isi jika backend memakai `API_ACCESS_TOKEN`.

## Menjalankan Lokal

```bash
cd frontend
npm install
npm run dev
```

Akses di `http://localhost:3000`.

Alternatif port 3010:

```bash
npm run dev:3010
```

## Scripts

- `npm run dev` - jalankan dev server.
- `npm run dev:3010` - jalankan dev server di port 3010.
- `npm run build` - build production.
- `npm run start` - start hasil build.
- `npm run lint` - lint code.

## Cara Kerja Request

1. UI memanggil `POST /api/chat` (route handler Next.js).
2. `app/api/chat/route.ts` meneruskan request ke `BACKEND_API_URL`.
3. Jika ada token, route menambahkan header `Authorization: Bearer <token>`.
4. Response backend dikembalikan ke UI.

## Catatan Integrasi

Saat development, jalankan backend dulu dari root proyek:

```bash
uvicorn backend.web_api.main:app --reload
```
