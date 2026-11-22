# FloodGuard — Real-Time Flood Monitoring & Community Alert Platform

A deployment-ready React + Flask + Socket.IO platform for live water-sensor telemetry, four-stage flood alerts, AI prediction integration, role-based admin/member dashboards, geospatial notifications, and nearest safe-location guidance.

## Core rule: no dummy data
The application does **not** seed fake telemetry, users, sensors, alerts, safe locations, or map markers. The database starts empty except for an optional bootstrap admin created from environment variables. Hardware telemetry is accepted only from registered sensors with their device key. A terminal simulator is provided strictly as a test client that sends real HTTP requests to the same ingestion endpoint.

## Architecture

`ESP32 / hardware -> LAN/Wi-Fi Flask ingest API -> validation -> database -> rule engine -> optional ML predictor -> Socket.IO -> Admin + nearby Members`

The same ingestion event can also be forwarded to `CENTRAL_WEBHOOK_URL` so a local deployment and central deployment receive the alert. If that variable is empty, the current Flask instance is the central application.

### Four-switch alert levels
The ESP32 sketch reads four physical switches in bottom-to-top order. The highest active switch determines the live state:
1. **No switch active — Normal**
2. **Bottom-most switch — Tide Alert**
3. **Second switch — Yellow Level**
4. **Third switch — Orange Level**
5. **Top-most switch — Red Level** (opens a dismissible red-alert popup on the member and admin dashboards)

If multiple switches are active together, the highest active switch wins. Devices that do not send `switch_level` remain compatible and continue to use the sensor's configured Level-1 to Level-4 water thresholds.

## Run locally

### Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.cli bootstrap-admin
python -m app
```
Backend: `http://127.0.0.1:5000`

### Frontend
```powershell
cd frontend
npm install
copy .env.example .env
npm run dev -- --host 0.0.0.0
```
Frontend: `http://localhost:5173`

For another device on the same Wi-Fi, set `VITE_API_BASE_URL` to the computer's LAN address, e.g. `http://192.168.1.20:5000`, and open the Vite LAN URL.

## Four-switch ESP32 hardware and LCD
The reference sketch uses these GPIOs in bottom-to-top order: GPIO 13 = Tide Alert, GPIO 14 = Yellow Level, GPIO 27 = Orange Level, and GPIO 26 = Red Level. Wire each switch between its GPIO and GND; the sketch uses `INPUT_PULLUP`, so a LOW reading means ON. When multiple switches are active, the highest active one wins.

A 16x2 I2C LCD is supported on SDA GPIO 21 and SCL GPIO 22 (default I2C address `0x27`; change to `0x3F` if needed). Install the `LiquidCrystal_I2C` Arduino library. The LCD shows Normal/Tide Alert/Yellow Level/Orange Level/Red Level and displays `EVACUATE NOW` at Red Level.

Before uploading, fill in the Wi-Fi name/password, API LAN URL, sensor ID, and device key placeholders in the sketch. Do not commit real credentials.

## Hardware on same Wi-Fi
The ESP32 sends JSON over HTTP to:
`POST http://<FLASK-LAN-IP>:5000/api/v1/telemetry`

Headers:
- `Content-Type: application/json`
- `X-Device-Key: <registered sensor device key>`

Payload example (replace with live readings):
```json
{
  "sensor_id": "YOUR_REGISTERED_SENSOR_ID",
  "water_level_m": 2.31,
  "switch_level": 2,
  "pressure_kpa": 51.4,
  "battery_v": 4.03,
  "latitude": 22.72,
  "longitude": 88.48,
  "captured_at": "2026-09-18T10:30:00Z"
}
```
The ESP32 should send its actual measured values; the backend never generates substitute telemetry.

## Terminal live-test client
After registering a sensor and obtaining its device key, run:
```powershell
cd backend
python scripts/simulate_telemetry.py --base-url http://127.0.0.1:5000 --sensor-id YOUR_SENSOR_ID --device-key YOUR_DEVICE_KEY
```
The script prompts for values and posts them to the real API. This is not database seeding or application dummy data; it is an external test client.

## Admin bootstrap
Set in `backend/.env`:
```env
BOOTSTRAP_ADMIN_MOBILE=9999999999
BOOTSTRAP_ADMIN_PASSWORD=change-me-now
BOOTSTRAP_ADMIN_NAME=System Admin
```
Then run `python -m app.cli bootstrap-admin`. Change the password before deployment.

## Safe-location workflow
Admins add real shelters/assembly points with name, coordinates, capacity and address. Member map requests `/api/v1/safe-locations/nearest?lat=...&lng=...&limit=5`; the backend calculates actual distance from the supplied coordinates. The frontend can request a walking route from a configurable OSRM-compatible routing service. No fictional safe locations are inserted.

## AI model integration
Put the eventual trained model under `backend/ml/models/` (for example `flood_predictor.joblib`) and set `MODEL_PATH` in `.env`. `backend/app/services/ml_service.py` loads it only when present. If absent, the API explicitly reports `not_loaded`; it never fabricates a prediction. The four-level deterministic safety alert still works from the physical sensor's configured thresholds.

## Production
- Use PostgreSQL via `DATABASE_URL`.
- Put Flask-SocketIO behind an appropriate production server/reverse proxy and configure CORS narrowly.
- Use HTTPS/WSS.
- Store device keys and JWT secrets in environment/secret management.
- Restrict telemetry endpoint to known sensor IDs/device keys and optionally network/VPN/firewall ranges.
- Configure `CENTRAL_WEBHOOK_URL` for local-to-central forwarding.
- Replace the public routing endpoint with an organization-managed routing service if required by operational policy.

## Project documentation
See `docs/ARCHITECTURE.md`, `docs/API_FLOW.md`, `docs/HARDWARE_WIFI.md`, and `docs/DEPLOYMENT.md`.


## Sensor management and map status enhancements
- Admins can delete a sensor from the active network. Deletion is a soft-delete (`active=false`) so historical telemetry and event-history records remain available for audit.
- Newly registered sensors are shown as **Normal** while awaiting their first telemetry reading.
- Registered sensors are shown on the map with a 📍 marker.
- A translucent 350 m alert circle is drawn around a sensor only while its current level is active: light blue (Tide Alert), yellow, orange, and red. The circle follows current sensor status rather than old alert-history entries.
- Member sensor status includes nearby registered sensors even before their first reading, so their initial state is Normal.
