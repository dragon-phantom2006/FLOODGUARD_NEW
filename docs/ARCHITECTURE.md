# Architecture

## Request path
1. Hardware captures water level/pressure and reads four bottom-to-top switches (when switch telemetry is supplied, that switch state determines the displayed level).
2. ESP32 posts telemetry over the local Wi-Fi network to Flask.
3. Flask authenticates the sensor using `X-Device-Key` and validates the schema.
4. Telemetry, including optional `switch_level`, is stored as an immutable reading.
5. If `switch_level` is supplied, it determines the current level (0–4); otherwise, the legacy four configured water thresholds are used.
6. A rising severity creates an alert record; repeated telemetry at the same level does not create duplicate alerts.
7. Admin sockets receive `telemetry:update` with the current status. Nearby member sockets receive `sensor:status` updates, including a return to Normal.
8. Alert notifications are sent to members inside the alert radius.
9. The alert can be forwarded to a central webhook simultaneously.
10. Members can query nearest registered safe locations and receive route guidance.

## Frontend -> backend map
- Login: `frontend/src/services/api.js` -> `POST /api/v1/auth/login`
- Current user: `GET /api/v1/auth/me`
- Member dashboard: `GET /api/v1/member/dashboard`
- Nearby alerts: `GET /api/v1/alerts/nearby`
- Current nearby switch statuses: `GET /api/v1/sensors/status/nearby`
- Safe locations: `GET /api/v1/safe-locations/nearest`
- Admin sensors: `GET/POST/PATCH /api/v1/admin/sensors`
- Admin safe locations: `GET/POST/PATCH /api/v1/admin/safe-locations`
- Admin warning by phone: `POST /api/v1/admin/warnings/direct`
- Live updates: Socket.IO events `telemetry:update`, `sensor:status`, `notification:new`

## Role boundary
Admin-only endpoints require JWT + `admin` role. Member endpoints cannot manage sensors, safe locations, direct warnings, or view all residents.
