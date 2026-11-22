
import React, { useEffect, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  Polyline
} from 'react-leaflet';
import L from 'leaflet';

const pinIcon = L.divIcon({
  className: 'sensor-pin-marker',
  html: '<span aria-label="Sensor location">🚩</span>',
  iconSize: [34, 38],
  iconAnchor: [17, 34],
});

// Custom icon for safe locations.
// Prevents Leaflet from requesting its default marker image.
const safeLocationIcon = L.divIcon({
  className: 'safe-location-marker',
  html: '<span aria-label="Safe location">🏠</span>',
  iconSize: [36, 40],
  iconAnchor: [18, 36],
});

// Custom icon for the user's current location.
const userLocationIcon = L.divIcon({
  className: 'user-location-marker',
  html: '<span aria-label="Your location">📍</span>',
  iconSize: [36, 40],
  iconAnchor: [18, 36],
});

const alertColors = {
  1: '#79D8F2', // light blue — Tide Alert
  2: '#F4D84A', // yellow
  3: '#F28C28', // orange
  4: '#E53935', // red
};

export default function LiveMap({
  alerts = [],
  sensors = [],
  locations = [],
  userLocation = null
}) {
  const [route, setRoute] = useState([]);

  const mappedSensors = sensors.length ? sensors : [];

  const center = userLocation
    ? [userLocation.lat, userLocation.lng]
    : mappedSensors[0]
      ? [mappedSensors[0].latitude, mappedSensors[0].longitude]
      : alerts[0]
        ? [alerts[0].latitude, alerts[0].longitude]
        : [22.72, 88.48];

  useEffect(() => {
    setRoute([]);
  }, [userLocation?.lat, userLocation?.lng]);

  async function getRoute(to) {
    if (!userLocation) return;

    const base =
      import.meta.env.VITE_ROUTING_BASE_URL ||
      'https://router.project-osrm.org';

    const url = `${base}/route/v1/driving/${userLocation.lng},${userLocation.lat};${to.longitude},${to.latitude}?overview=full&geometries=geojson`;

    const response = await fetch(url);
    const data = await response.json();

    setRoute(
      data.routes?.[0]?.geometry?.coordinates?.map(
        ([lng, lat]) => [lat, lng]
      ) || []
    );
  }

  return (
    <div className="map-wrap">
      <MapContainer
        key={`${center[0]}-${center[1]}`}
        center={center}
        zoom={13}
        scrollWheelZoom
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {mappedSensors.map((sensor) => {
          const level = Number(sensor.level || 0);
          const color = alertColors[level];

          return (
            <React.Fragment key={`sensor-${sensor.sensor_id}`}>
              {color && (
                <Circle
                  center={[
                    sensor.latitude,
                    sensor.longitude
                  ]}
                  radius={350}
                  pathOptions={{
                    color,
                    weight: 2,
                    opacity: 0.85,
                    fillColor: color,
                    fillOpacity: 0.22
                  }}
                />
              )}

              <Marker
                position={[
                  sensor.latitude,
                  sensor.longitude
                ]}
                icon={pinIcon}
              >
                <Popup>
                  <b>{sensor.name || sensor.sensor_name}</b>
                  <br />
                  {sensor.sensor_id}
                  <br />
                  <b>{sensor.label || 'Normal'}</b>
                  <br />
                  {sensor.water_level_m != null
                    ? `${sensor.water_level_m} m`
                    : 'Awaiting first telemetry reading'}
                </Popup>
              </Marker>
            </React.Fragment>
          );
        })}

        {/* Historical alert markers */}
        {!mappedSensors.length &&
          alerts.map((alert) => (
            <Marker
              key={`alert-${alert.id}`}
              position={[
                alert.latitude,
                alert.longitude
              ]}
              icon={pinIcon}
            >
              <Popup>
                <b>{alert.title}</b>
                <br />
                Level {alert.level}
                <br />
                {alert.water_level_m} m
              </Popup>
            </Marker>
          ))}

        {/* Safe location markers */}
        {locations.map((location) => (
          <Marker
            key={`location-${location.id}`}
            position={[
              location.latitude,
              location.longitude
            ]}
            icon={safeLocationIcon}
          >
            <Popup>
              <b>{location.name}</b>
              <br />
              {location.address}
              <br />
              {location.distance_km != null
                ? `${location.distance_km} km away`
                : ''}
              <br />
              <button onClick={() => getRoute(location)}>
                Guide me
              </button>
            </Popup>
          </Marker>
        ))}

        {/* User's current location */}
        {userLocation && (
          <Marker
            position={[
              userLocation.lat,
              userLocation.lng
            ]}
            icon={userLocationIcon}
          >
            <Popup>Your location</Popup>
          </Marker>
        )}

        {/* Navigation route */}
        {route.length > 1 && (
          <Polyline positions={route} />
        )}

      </MapContainer>
    </div>
  );
}
