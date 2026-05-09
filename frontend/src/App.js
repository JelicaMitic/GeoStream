import { useEffect, useState, useRef, useCallback } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
  iconUrl: require("leaflet/dist/images/marker-icon.png"),
  shadowUrl: require("leaflet/dist/images/marker-shadow.png"),
});

function App() {
  const [drivers, setDrivers] = useState({});
  const ws = useRef(null);

  const connect = useCallback(() => {
    ws.current = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.current.onopen = () => console.log("WebSocket povezan!");

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setDrivers((prev) => ({
        ...prev,
        [data.driver_id]: {
          id: data.driver_id,
          name: data.driver_name,
          lat: data.latitude,
          lon: data.longitude,
        },
      }));
    };

    ws.current.onclose = () => {
      console.log("WebSocket zatvoren, pokušavam ponovo za 2s...");
      setTimeout(connect, 2000);
    };

    ws.current.onerror = (err) => {
      console.log("WebSocket greška:", err);
      ws.current.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  return (
    <div style={{ height: "100vh", width: "100vw" }}>
      <MapContainer
        center={[44.8176, 20.4569]}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap"
        />
        {Object.values(drivers).map((driver) => (
          <Marker key={driver.id} position={[driver.lat, driver.lon]}>
            <Popup>Vozač: {driver.name}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

export default App;
