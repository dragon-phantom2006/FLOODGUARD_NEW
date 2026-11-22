import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import LiveMap from '../components/LiveMap';
import StatusPill from '../components/StatusPill';
import RedAlertModal from '../components/RedAlertModal';
import API from '../services/api';
import { connectSocket } from '../services/socket';
import { formatTimeIST } from '../utils/dateTime';

export default function AdminDashboard() {
  const [sensors, setSensors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [latest, setLatest] = useState(null);
  const [showRedAlert, setShowRedAlert] = useState(false);

  useEffect(() => {
    Promise.all([API.get('/admin/sensors'), API.get('/admin/alerts')]).then(([sensorResponse, alertResponse]) => {
      setSensors(sensorResponse.data.sensors);
      setAlerts(alertResponse.data.alerts);
    });

    const socket = connectSocket(localStorage.getItem('floodguard_token'));
    socket.on('telemetry:update', (update) => {
      setLatest(update);
      setSensors((previous) => previous.map((sensor) => (
        sensor.sensor_id === update.sensor.sensor_id ? { ...sensor, ...update.sensor, level: update.status?.level ?? 0, label: update.status?.label || 'Normal', water_level_m: update.reading?.water_level_m } : sensor
      )));
      if (update.alert) setAlerts((previous) => [update.alert, ...previous]);
    });

    return () => socket.disconnect();
  }, []);

  useEffect(() => {
    if (latest?.status?.level === 4) {
      setShowRedAlert(true);
    } else if (latest?.status?.level != null) {
      setShowRedAlert(false);
    }
  }, [latest?.status?.level]);

  return (
    <Layout admin>
      <div className="kpi-grid">
        <div>
          <span>Registered sensors</span>
          <b>{sensors.length}</b>
        </div>
        <div>
          <span>Active alert records</span>
          <b>{alerts.length}</b>
        </div>
        <div>
          <span>Live pipeline</span>
          <b className="online">ONLINE</b>
        </div>
      </div>

      <div className="dashboard-grid">
        <section>
          <div className="section-head">
            <div>
              <span className="eyebrow">LIVE COMMAND MAP</span>
              <h2>Sensor network</h2>
            </div>
          </div>
          <LiveMap alerts={alerts.slice(0, 20)} sensors={sensors} locations={[]} />
        </section>

        <section>
          <div className="section-head">
            <div>
              <span className="eyebrow">INGESTION STREAM</span>
              <h2>Latest telemetry</h2>
            </div>
          </div>

          {latest ? (
            <div className="telemetry-card">
              <div>
                <StatusPill level={latest.status?.level ?? latest.alert?.level ?? 0} />
                <b>{latest.sensor.name}</b>
              </div>
              <div className="big-number">
                {latest.status?.label || (latest.status?.level === 0 ? 'Normal' : latest.reading.water_level_m)}
                <small>{latest.status?.label ? ' live status' : ' m water level'}</small>
              </div>
              <div className="metric-row">
                <span>Switch level: {latest.reading.switch_level ?? 'Not supplied'}</span>
                <span>Battery: {latest.reading.battery_v ?? '—'} V</span>
              </div>
            </div>
          ) : sensors.length ? (
            <div className="telemetry-card">
              <div>
                <StatusPill level={0} />
                <b>{sensors.length} registered sensor{sensors.length === 1 ? '' : 's'}</b>
              </div>
              <div className="big-number">Normal <small>initial status</small></div>
              <div className="metric-row"><span>Awaiting the first telemetry reading</span></div>
            </div>
          ) : (
            <div className="empty">No registered sensors yet.</div>
          )}

          <div className="section-head mt">
            <div>
              <span className="eyebrow">RECENT ALERTS</span>
              <h2>Event history</h2>
            </div>
          </div>
          {alerts.slice(0, 8).map((alert) => (
            <div className="event-row" key={alert.id}>
              <StatusPill level={alert.level} />
              <span>{alert.title}</span>
              <small>{formatTimeIST(alert.created_at)}</small>
            </div>
          ))}
        </section>
      </div>

      <RedAlertModal open={showRedAlert} onClose={() => setShowRedAlert(false)} />
    </Layout>
  );
}
