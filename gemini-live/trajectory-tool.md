# Trajectory Tools – Research & Implementation Plan

Purpose: Add robust, safe, and observable trajectory motion to the Mobile ALOHA path using Gemini Live API tool calling. This plan consolidates multi‑agent recommendations into a concrete, implementation‑ready blueprint covering frontend (TypeScript/React), Python bridges (aiohttp), safety/observability, testing, rollout, and risks.

Last updated: 2025‑09‑09

---

## Repository Snapshot (for orientation)

Top‑level:
- `live-api-console/` – React dev app and Gemini Live client
  - `src/lib/genai-live-client.ts` – Live API session + tool plumbing
  - `src/components/aloha-control/ALOHAControl.tsx` – Robot UI + toolcall handler
  - `src/components/mac-control/MacControl.tsx` – Reference tool pattern (fire‑and‑forget)
- `bridges/` – aiohttp bridges to systems
  - `bridge_mac_control.py` – Reference CORS + JSON + immediate responses
  - `bridge_robot_mock.py` – Mock robot bridge (extend or parallel new bridge)
- `research/trajectory-tool-research.md` – Prior notes on desired tools
- `CRITICAL_LESSONS_GEMINI_LIVE_API.md` – Must‑follow patterns

---

## Guiding Principles (from hard‑won lessons)

- Always respond to tool calls immediately: send a minimal success payload back to Gemini, then perform side‑effects asynchronously via the bridge (fire‑and‑forget).
- Configure tools and systemInstruction before connecting to the Live API session.
- Explicitly tell the model that it has live video input; avoid any Python code generation paths in the browser.
- Keep responses to Gemini simple; update the UI separately with real bridge results.
- Prefer server‑side safety enforcement; mirror client pre‑checks for better UX and fewer rejected jobs.

---

## What We’re Adding

Two new trajectory tools exposed to Gemini via functionDeclarations:
1) `move_to_pose(arm_side, x, y, z, roll, pitch, yaw, moving_time=2.0, accel_time=0.5)`
2) `follow_cartesian_trajectory(arm_side, delta_x, delta_y, delta_z, delta_roll=0, delta_pitch=0, delta_yaw=0, moving_time=2.0, wp_period=0.02)`

Both use a time‑based motion profile and return immediately to Gemini while the bridge executes motions asynchronously.

---

## High‑Level Architecture Additions

- Frontend declares new tools, performs risk pre‑checks, responds to Gemini immediately, and asynchronously POSTs to the robot bridge.
- Bridge exposes REST endpoints to accept jobs, validates safety/velocity, queues per arm, drives hardware (Interbotix) or a mock driver, and emits telemetry via SSE.
- Observability provides job/status streams; reliability adds idempotency, watchdogs, timeouts, and stop/e‑stop paths.

---

## Frontend Plan (TypeScript/React)

Files to touch (descriptions only):
- `live-api-console/src/components/aloha-control/ALOHAControl.tsx`
  - Add functionDeclarations for both trajectory tools.
  - Add config‑before‑connect panel (Robot endpoint, Driver mode, Safety profile, Dry‑Run default).
  - Implement risk pre‑check (bounds, velocity estimate). If risky → immediate tool result `{requiresConfirmation:true}` and UI confirm flow.
  - Toolcall handler: for each call → push minimal toolResponse to Gemini, then fire‑and‑forget POST to bridge with `request_id` and optional `idempotencyKey`.
  - UX: controls for Move to Pose, Relative Trajectory, Dry‑Run toggle; Stop/E‑Stop buttons.
  - Telemetry: subscribe to SSE `/robot/telemetry` if present; fallback poll `/robot/state`.
- `live-api-console/src/lib/genai-live-client.ts`
  - No behavioral change other than ensuring config (tools + systemInstruction) is set before `connect()`.

FunctionDeclarations (schema‑like):

```ts
const toolMoveToPose: FunctionDeclaration = {
  name: 'move_to_pose',
  description: 'Move end-effector to an absolute 6D pose (m, rad) using a time-based profile. You have live video input. Use tools only.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      arm_side: { type: Type.STRING, enum: ['left','right'] },
      x: { type: Type.NUMBER }, y: { type: Type.NUMBER }, z: { type: Type.NUMBER },
      roll: { type: Type.NUMBER }, pitch: { type: Type.NUMBER }, yaw: { type: Type.NUMBER },
      moving_time: { type: Type.NUMBER, description: 'seconds', default: 2.0 },
      accel_time: { type: Type.NUMBER, description: 'seconds', default: 0.5 },
      options: {
        type: Type.OBJECT,
        properties: {
          dryRun: { type: Type.BOOLEAN },
          idempotencyKey: { type: Type.STRING }
        }
      }
    },
    required: ['arm_side','x','y','z','roll','pitch','yaw']
  }
};

const toolFollowCartesianTrajectory: FunctionDeclaration = {
  name: 'follow_cartesian_trajectory',
  description: 'Follow a straight-line relative Cartesian trajectory (m, rad). Time-based profile. You have live video input. Use tools only.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      arm_side: { type: Type.STRING, enum: ['left','right'] },
      delta_x: { type: Type.NUMBER }, delta_y: { type: Type.NUMBER }, delta_z: { type: Type.NUMBER },
      delta_roll: { type: Type.NUMBER, default: 0 },
      delta_pitch: { type: Type.NUMBER, default: 0 },
      delta_yaw: { type: Type.NUMBER, default: 0 },
      moving_time: { type: Type.NUMBER, default: 2.0 },
      wp_period: { type: Type.NUMBER, description: 'seconds', default: 0.02 },
      options: {
        type: Type.OBJECT,
        properties: {
          dryRun: { type: Type.BOOLEAN },
          idempotencyKey: { type: Type.STRING }
        }
      }
    },
    required: ['arm_side','delta_x','delta_y','delta_z']
  }
};
```

System instruction (set before connect):

```text
You are connected to a Mobile ALOHA robot. You receive LIVE VIDEO input and CAN SEE the scene. Use the provided tool functions ONLY (no Python). Prefer smooth, safe trajectories; request confirmation for risky moves near workspace bounds.
```

Toolcall handler best practice:

```ts
// 1) Respond to Gemini immediately (minimal) to avoid stalls
responses.push({ name: call.name, id: call.id, response: { success: true, status: 'executed' }});

// 2) Fire-and-forget to the bridge; update UI from telemetry only
fetch(`${ROBOT_ENDPOINT}/robot/${call.name}`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ ...call.args, request_id, options })
}).catch(console.error);

client.sendToolResponse({ functionResponses: responses });
```

Environment flags (frontend):
- `REACT_APP_ROBOT_ENDPOINT` (default `http://localhost:8081`)
- `REACT_APP_ENABLE_TRAJECTORY_MODE=true|false`
- `REACT_APP_DEFAULT_DRY_RUN=true|false`

---

## Bridge Plan (aiohttp, Python 3.10+)

New/updated module(s) under `bridges/`:
- Option A: Extend `bridge_robot_mock.py` with endpoints + mock driver and add `bridge_robot_interbotix.py` for hardware.
- Option B: Create unified `bridge_robot.py` with `ROBOT_DRIVER=mock|interbotix` env flag.

Endpoints (prefix `/robot`, CORS enabled):
- `POST /move_to_pose`
- `POST /follow_cartesian_trajectory`
- `POST /stop` (soft stop active motion)
- `POST /e_stop` (hard stop; clear queue)
- `GET /state` (connection, driverMode, per‑arm pose, queue length, activeJobId, lastError, safetyProfile)
- `GET /telemetry` (SSE; job_started/job_progress/job_completed/job_failed/state/warning/e_stop)

Request envelope (example):

```json
{
  "arm_side": "right",
  "x": 0.32, "y": 0.10, "z": 0.18,
  "roll": 0.0, "pitch": 1.57, "yaw": 0.0,
  "moving_time": 2.0, "accel_time": 0.5,
  "options": { "dryRun": false, "idempotencyKey": "..." },
  "request_id": "..."
}
```

Immediate response envelope (never block):

```json
{
  "accepted": true,
  "queued": true,
  "jobId": "...",
  "dryRun": false,
  "safety": { "riskLevel": "low", "notes": [] },
  "message": "Queued",
  "requestId": "..."
}
```

Safety policy (server‑side, mirrored client pre‑check):
- Hard workspace bounds (tune per hardware): `x:[0.15,0.65]`, `y:[-0.35,0.35]`, `z:[0.05,0.55]` (m).
- Orientation clamp: RPY to `[-π, π]`; optional per‑move orientation step caps.
- Velocity/accel caps: `linear ≤ 0.25 m/s`, `angular ≤ 0.8 rad/s` via distance/duration estimate.
- Temporal constraints: `moving_time ≥ accel_time*2`, `wp_period ≥ 0.01s`.
- Risk levels: `low`, `needs_confirmation` (near bounds/large deltas/short times), `blocked` (exceeds hard limits).
- Dry‑run mode: validate + simulate; emit completion quickly.

Queueing & lifecycle:
- `asyncio.Queue` per arm; single worker per arm; FIFO fairness.
- Jobs: `{ jobId, type, req, createdAt, state: queued|running|completed|failed|canceled, dryRun }`.
- Timeouts: `moving_time + guard`; on timeout → stop + `job_failed`.
- Idempotency: store recent `idempotencyKey → jobId` with TTL; on duplicates → 409 or same jobId.

Drivers:
- Mock: numeric simulation; periodic `job_progress` SSE with synthetic poses.
- Interbotix: enable time‑based profiles; use `set_ee_pose_components(...)` for pose; `set_ee_cartesian_trajectory(...)` (or waypoint loop) for straight‑line deltas.

Observability & logging:
- SSE stream for progress; heartbeat pings.
- JSON logs: ts, level, event, jobId, arm, tool, duration_ms, reqSummary, resultSummary.

Environment flags (bridge):
- `ROBOT_DRIVER=mock|interbotix`
- `ROBOT_ARMS=left,right`
- `SAFETY_PROFILE=strict|soft|custom`
- `BOUNDS_X="0.15,0.65"` (similar for Y/Z)
- `SPEED_CAP_LIN=0.25`, `SPEED_CAP_ANG=0.8`
- `DEFAULT_MOVING_TIME=2.0`, `DEFAULT_ACCEL_TIME=0.5`
- `SSE_HEARTBEAT_MS=10000`
- `CORS_ALLOW_ORIGINS=*` (or list)

Stop/e‑stop patterns:
- `/stop` attempts soft stop and preserves state.
- `/e_stop` halts immediately, clears queue, emits SSE `e_stop`; require explicit resume.

Error translation:
- Safety blocks → 200 with `{accepted:false, queued:false, safety:{riskLevel:'blocked'}, message:'...'}`.
- Idempotency replays → 409 with existing job state or 200 with `accepted:false` and link to job.
- 5xx for unexpected errors only (include `requestId`).

---

## Observability & Metrics

- Prefer SSE `/telemetry` for smooth progress; fallback poll `/state` if SSE unavailable.
- Minimal metrics (phase 1): counters (`jobs_queued/completed/failed`, `e_stops`, `blocked_by_safety`), durations (`job_duration_ms`).
- Optional: expose `/metrics` (Prometheus) in phase 2.

---

## Reliability Best Practices

- Idempotency everywhere: client sends `idempotencyKey`; server returns the same `jobId` on duplicates.
- Watchdogs: if motion active but no SSE progress for >2s, emit `warning` and consider timeout.
- Timeouts: `moving_time + 2s` guard; on hit → `/stop` and mark job failed.
- Backoff: client retries POST on transient 5xx up to 2 times with exponential backoff.

---

## Testing Plan

Python unit (pytest):
- Safety validators (bounds, velocity/accel, temporal constraints).
- Waypoint math: `ceil(moving_time/wp_period)+1`.
- Idempotency store behavior; queue worker serialization and cancellation.
- Error translation envelopes.

Python integration (aiohttp test client):
- POST `move_to_pose` (mock) → 200 accepted; observe SSE job_started → job_completed.
- `follow_cartesian_trajectory` with `dryRun:true` → completes quickly.
- `/e_stop` cancels active job; SSE `e_stop` + job_failed/canceled.
- Hardware offline path (driver=interbotix without hardware): `/state.connected=false`; POST returns `accepted:false`.

TypeScript unit (vitest/jest):
- functionDeclaration schemas; risk pre‑check logic.
- Idempotency key generation; fetch helpers (timeouts/backoff).

E2E (mock):
- Spin dev server + mock bridge; automate UI actions; assert DOM shows progress from SSE.

On‑hardware checklist:
1) Home pose and clear workspace.
2) Center pose dry‑run → real motion.
3) Small relative trajectory (5cm) with wp_period=0.02.
4) Boundary approach → `needs_confirmation` flow.
5) `/stop` vs `/e_stop` behavior and recovery.
6) Long move timing/smoothness; telemetry sanity.

---

## Rollout & Migration

- Default to `ROBOT_DRIVER=mock`; UI banner: “Mock Mode”.
- Feature flags: `REACT_APP_ENABLE_TRAJECTORY_MODE`; toggle in settings.
- If bridge unreachable/offline: tool handler returns minimal result plus UI banner; suggest switching to mock.
- Documentation: README quickstart for robot bridge; update CRITICAL_LESSONS with trajectory notes (immediate responses, confirm flows).

---

## Risks & Mitigations

- Unsafe LLM suggestions → Strict server‑side safety, client warnings, confirmation gate, dry‑run default in early testing.
- UI/bridge desync → SSE with heartbeats; `/state` polling fallback; treat bridge state as source of truth.
- Duplicate toolcalls → Idempotency keys; dedupe store.
- Hardware/API variance → Driver abstraction; mock parity; env‑driven parameters.
- Process crashes → try/finally safe stop; watchdogs; clear queues on startup.

---

## Concrete Task Checklist (2–3 days)

Day 1
1) Frontend: add functionDeclarations + config‑before‑connect; basic handler with immediate toolResponse and POST.
2) Bridge: scaffold endpoints, mock driver, per‑arm queue, safety validators, SSE.

Day 2
3) Frontend: risk pre‑check + confirm modal; telemetry panel; Stop/E‑Stop.
4) Bridge: idempotency store, timeouts, watchdog, JSON logs; refine safety.

Day 3
5) Tests: unit (validators/idempotency/queue), integration (POST+SSE), E2E (mock UI).
6) Docs: README quickstart; CRITICAL_LESSONS addenda; enable feature flags.

Stretch (Week 1)
- Prometheus `/metrics`; richer 3D preview UI; per‑arm calibration; multi‑user sessions; auth on bridge.

---

## API Quick Reference (copy‑paste friendly)

POST `/robot/move_to_pose`

```jsonc
// Body
{ "arm_side":"right", "x":0.32, "y":0.10, "z":0.18,
  "roll":0, "pitch":1.57, "yaw":0,
  "moving_time":2.0, "accel_time":0.5,
  "options":{ "dryRun":false, "idempotencyKey":"..." },
  "request_id":"..." }

// 200 Response (immediate)
{ "accepted":true, "queued":true, "jobId":"...",
  "dryRun":false, "safety":{ "riskLevel":"low" },
  "message":"Queued", "requestId":"..." }
```

POST `/robot/follow_cartesian_trajectory`

```jsonc
{ "arm_side":"right", "delta_x":0.10, "delta_y":0, "delta_z":0,
  "delta_roll":0, "delta_pitch":0, "delta_yaw":0,
  "moving_time":2.0, "wp_period":0.02,
  "options":{ "dryRun":true },
  "request_id":"..." }
```

GET `/robot/state`

```json
{ "connected":true, "driverMode":"mock",
  "arms": { "right": {"x":0.30,"y":0.10,"z":0.20,"roll":0,"pitch":1.57,"yaw":0} },
  "queueLength":0, "activeJobId":null, "safetyProfile":{...} }
```

SSE `/robot/telemetry` – events: `job_started`, `job_progress`, `job_completed`, `job_failed`, `state`, `warning`, `e_stop`.

---

## Final Notes

Adhere strictly to immediate tool responses and keep model prompts simple. Treat the bridge as the source of truth for motion progress and state. Start in mock + dry‑run, then progressively enable real motions with confirmations near workspace limits.
