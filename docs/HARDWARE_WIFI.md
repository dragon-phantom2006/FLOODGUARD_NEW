# Hardware on the same Wi-Fi

## Network model
The ESP32 and the computer running Flask must be reachable on the same LAN. Find the Flask computer's LAN IPv4 address (`ipconfig` on Windows). Example: `192.168.1.20`.

Run Flask on `0.0.0.0:5000`, then configure the ESP32 firmware with:
`http://192.168.1.20:5000/api/v1/telemetry`

Do not use `localhost` from the ESP32; `localhost` means the ESP32 itself.

## Firewall
Allow inbound TCP 5000 on the private network profile, or place Flask behind a local reverse proxy.

## Device authentication
Every sensor row has a generated device key. The ESP32 stores that key and sends it in `X-Device-Key`. The backend hashes the key in the database and never needs to store the raw key after registration. If lost, rotate the key from the admin UI/API.

## Offline resilience
The reference hardware architecture includes SD-card storage. The backend accepts timestamped readings, so firmware can buffer readings locally and upload them later. The server does not manufacture missing readings.


## Four-switch wiring and status display
The firmware reads four normally-open switches using ESP32 internal pull-ups. Connect one side of each switch to GND and the other side to the assigned GPIO:

| Physical position | ESP32 GPIO | Dashboard/LCD state |
| --- | ---: | --- |
| Bottom-most | 13 | Tide Alert |
| Second from bottom | 14 | Yellow Level |
| Third from bottom | 27 | Orange Level |
| Top-most | 26 | Red Level |

No active switch reports Normal. If more than one switch is active, the highest active switch determines the level. The firmware sends `switch_level` (0–4) in each telemetry request.

For a 16x2 I2C LCD, connect SDA to GPIO 21, SCL to GPIO 22, VCC to the appropriate board/LCD supply, and GND to GND. The sketch defaults to I2C address `0x27`; use `0x3F` if that is the detected backpack address. Install the `LiquidCrystal_I2C` library in Arduino IDE before compiling.

`switch_level` is stored with telemetry and the backend adds the column automatically when upgrading an older local database. The dashboard shows the highest-severity current state from nearby sensors. Reaching Red Level opens a dismissible evacuation popup.
