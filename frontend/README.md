# Switch configuration Wizard (Frontend MVP)

This is a lightweight, intuitive web interface designed to guide users through the automatic switch configuration process.

## Tech Stack Decision: React + Vite

We have chosen **React (Vite)** over other alternatives (like HTMX or plain JS) for the following reasons:

1. **Structured State Management**: The configuration process is a 5-step wizard. Managing the state of each device, their ports, and the global job status across multiple views is significantly cleaner with React's component-based state.
2. **Real-Time Dashboards**: Step 5 (Execution) requires live polling and reactive updates to the status table. React's virtual DOM and hooks make this efficient and easy to maintain.
3. **Developer Experience**: Vite provides a modern, lighting-fast build system that is easy to deploy as a static site from the Raspberry Pi.
4. **Maintenance**: As a "long-term" baseline tool, using a standard framework like React ensures better maintainability and extensibility than custom vanilla JS or server-side fragment swapping for this specific complex workflow.

## Features
- **Intuitive Wizard**: 5 clear steps from Job creation to Report download.
- **Immediate Validation**: CSV errors and port conflicts are shown instantly.
- **Deep Visibility**: Live run status with per-device event logs.
- **Premium Design**: Dark mode with glassmorphism for a high-end feel.

## Local Development
1. Ensure the backend is running at `http://localhost:8000`.
2. Run `npm install`.
3. Run `npm run dev`.
