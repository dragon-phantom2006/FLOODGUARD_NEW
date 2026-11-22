import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import API from '../services/api';

export default function AdminSafeLocations() {
  const [items, setItems] = useState([]),
    [f, setF] = useState({
      name: '',
      address: '',
      latitude: '',
      longitude: '',
      capacity: ''
    });

  const load = () =>
    API.get('/admin/safe-locations').then(r => setItems(r.data.locations));

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const set = k => e =>
    setF({ ...f, [k]: e.target.value });

  async function add(e) {
    e.preventDefault();

    await API.post('/admin/safe-locations', {
      ...f,
      latitude: Number(f.latitude),
      longitude: Number(f.longitude),
      capacity: f.capacity ? Number(f.capacity) : null
    });

    setF({
      name: '',
      address: '',
      latitude: '',
      longitude: '',
      capacity: ''
    });

    load();
  }

  return (
    <Layout admin>
      <div className="two-col">
        <form className="panel" onSubmit={add}>
          <span className="eyebrow">EVACUATION NETWORK</span>
          <h2>Add real safe location</h2>
          <p className="muted">
            Only locations entered by your authority appear to members.
          </p>

          {Object.keys(f).map(k => (
            <label key={k}>
              {k}
              <input
                className="plain-input"
                value={f[k]}
                onChange={set(k)}
                required={k !== 'capacity'}
              />
            </label>
          ))}

          <button className="primary">
            Publish safe location
          </button>
        </form>

        <section className="panel">
          <span className="eyebrow">VERIFIED LOCATIONS</span>
          <h2>{items.length} locations</h2>

          {items.map(x => (
            <div className="location-row" key={x.id}>
              <b>{x.name}</b>
              <span>{x.address}</span>
              <small>
                {x.latitude}, {x.longitude} • capacity{' '}
                {x.capacity ?? 'not set'}
              </small>
            </div>
          ))}
        </section>
      </div>
    </Layout>
  );
}