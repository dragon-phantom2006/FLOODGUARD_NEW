import { useEffect, useMemo, useState } from 'react';
import Layout from '../components/Layout';
import LiveMap from '../components/LiveMap';
import AlertCard from '../components/AlertCard';
import StatusPill from '../components/StatusPill';
import RedAlertModal from '../components/RedAlertModal';
import { useAuth } from '../contexts/AuthContext';
import API from '../services/api';
import { connectSocket } from '../services/socket';

const NORMAL_STATUS = {
  level: 0,
  label: 'Normal',
  message: 'No flood switch is active. Conditions are currently normal.',
  sensor_id: null,
  sensor_name: null,
};

export default function MemberDashboard() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [pos, setPos] = useState(null);
  const [notes, setNotes] = useState([]);
  const [sensorStatuses, setSensorStatuses] = useState({});
  const [showRedAlert, setShowRedAlert] = useState(false);

  const currentStatus = useMemo(() => {
    const values = Object.values(sensorStatuses);
    if (!values.length) return NORMAL_STATUS;
    return values.sort((a, b) => (b.level - a.level) || ((a.distance_km ?? Infinity) - (b.distance_km ?? Infinity)))[0];
  }, [sensorStatuses]);

  useEffect(() => {
    const savedLat = Number(user?.latitude);
    const savedLng = Number(user?.longitude);

    if (user?.latitude != null && user?.longitude != null && Number.isFinite(savedLat) && Number.isFinite(savedLng)) {
      setPos({ lat: savedLat, lng: savedLng });
    } else {
      navigator.geolocation?.getCurrentPosition(
        (position) => {
          const next = { lat: position.coords.latitude, lng: position.coords.longitude };
          setPos(next);
          API.put('/member/profile/location', {
            latitude: next.lat,
            longitude: next.lng,
          }).catch(() => {});
        },
        () => setPos(null),
      );
    }

    API.get('/member/dashboard')
      .then((response) => setNotes(response.data.notifications || []))
      .catch(() => setNotes([]));

    const socket = connectSocket(localStorage.getItem('floodguard_token'));

    socket.on('sensor:status', (status) => {
      if (!status?.sensor_id) return;
      setSensorStatuses((previous) => ({
        ...previous,
        [status.sensor_id]: status,
      }));
    });

    socket.on('notification:new', () => {
      const lat = Number(user?.latitude);
      const lng = Number(user?.longitude);
      if (user?.latitude != null && user?.longitude != null && Number.isFinite(lat) && Number.isFinite(lng)) {
        API.get('/alerts/nearby', { params: { lat, lng } })
          .then((response) => setAlerts(response.data.alerts || []))
          .catch(() => {});
      }
    });

    return () => socket.disconnect();
  }, [user]);

  useEffect(() => {
    if (!pos) return;
    const params = { lat: pos.lat, lng: pos.lng };

    API.get('/alerts/nearby', { params })
      .then((response) => setAlerts(response.data.alerts || []))
      .catch(() => setAlerts([]));

    API.get('/safe-locations/nearest', { params: { ...params, limit: 6 } })
      .then((response) => setLocations(response.data.locations || []))
      .catch(() => setLocations([]));

    API.get('/sensors/status/nearby', { params })
      .then((response) => {
        const statuses = response.data.statuses || [];
        setSensorStatuses(Object.fromEntries(statuses.map((status) => [status.sensor_id, status])));
      })
      .catch(() => setSensorStatuses({}));
  }, [pos]);

  useEffect(() => {
    if (currentStatus.level === 4) {
      setShowRedAlert(true);
    } else {
      setShowRedAlert(false);
    }
  }, [currentStatus.level]);

  return (
    <Layout>
      <section className="hero-strip">
        <div>
          <span className="eyebrow">YOUR LOCAL RISK VIEW</span>
          <h2>Stay informed, stay ready.</h2>
          <p>Live alerts are pushed from registered flood sensors near your location.</p>
        </div>
        <div className="live-badge">
          <span className="live-dot" /> LIVE
        </div>
      </section>

      <section className={`current-status-card status-level-${currentStatus.level || 0}`} aria-live="polite">
        <div className="current-status-copy">
          <span className="eyebrow">LIVE SWITCH STATUS</span>
          <h2>{currentStatus.label || 'Normal'}</h2>
          <p>{currentStatus.sensor_name ? `Sensor: ${currentStatus.sensor_name}` : currentStatus.message || NORMAL_STATUS.message}</p>
        </div>
        <div className="current-status-meta">
          <StatusPill level={currentStatus.level || 0} />
          <span>{currentStatus.sensor_id || 'Awaiting nearby sensor reading'}</span>
        </div>
      </section>

      <div className="dashboard-grid">
        <section>
          <div className="section-head">
            <div>
              <span className="eyebrow">MAP GUIDANCE</span>
              <h2>Nearby sensors &amp; safe locations</h2>
            </div>
            <span className="muted">{pos ? 'Location active' : 'Location not available'}</span>
          </div>

          <LiveMap alerts={alerts} sensors={Object.values(sensorStatuses)} locations={locations} userLocation={pos} />
        </section>

        <section>
          <div className="section-head">
            <div>
              <span className="eyebrow">ALERT FEED</span>
              <h2>Local warnings</h2>
            </div>
          </div>

          {alerts.length ? (
            alerts.map((alert) => <AlertCard key={alert.id} a={alert} />)
          ) : (
            <div className="empty">No live alerts in your current radius.</div>
          )}

          <div className="section-head mt">
            <div>
              <span className="eyebrow">NOTIFICATIONS</span>
              <h2>Direct messages</h2>
            </div>
          </div>

          {notes.slice(0, 5).map((note) => (
            <div className="notice" key={note.id}>
              <b>{note.title}</b>
              <p>{note.message}</p>
            </div>
          ))}
        </section>
      </div>

      <RedAlertModal open={showRedAlert} onClose={() => setShowRedAlert(false)} />
    </Layout>
  );
}
