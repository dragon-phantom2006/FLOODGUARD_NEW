# API and data flow

### Telemetry
`POST /api/v1/telemetry`

Headers: `X-Device-Key`

Body fields: `sensor_id`, `water_level_m`, optional `switch_level` (integer 0–4), `pressure_kpa`, `battery_v`, optional GPS, optional device timestamp. `switch_level` is authoritative when provided: 0 = Normal, 1 = Tide Alert, 2 = Yellow Level, 3 = Orange Level, 4 = Red Level. Older devices without it continue using configured water thresholds.

The response includes the stored reading, current status, and an alert record only when severity rises. The endpoint is designed for an actual ESP32/edge client.

### Direct admin warning
`POST /api/v1/admin/warnings/direct`
```json
{"mobile":"9876543210","title":"Flood warning","message":"Move to the designated safe location.","severity":"WARNING"}
```
This creates an in-app notification. If Twilio variables are configured, the notification service can also send SMS. Without a provider, it does not pretend SMS was sent.

### WebSocket
After login, the frontend connects to Socket.IO and sends its JWT in the auth payload. The server places the socket into an admin room or a location-aware member room. New alerts are pushed without page refresh.


### Current sensor status
Members can request `GET /api/v1/sensors/status/nearby?lat=...&lng=...` to retrieve the latest switch state for sensors inside their alert radius. The `sensor:status` Socket.IO event pushes live state changes, including a return to Normal. Admin dashboards receive the same current status inside the `telemetry:update` event.
