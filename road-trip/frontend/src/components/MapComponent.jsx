import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';

// Fix per le icone di default di Leaflet in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Componente interno per centrare la mappa automaticamente sul percorso
function MapUpdater({ geometry }) {
  const map = useMap();
  useEffect(() => {
    if (geometry && geometry.length > 0) {
      const bounds = L.latLngBounds(geometry.map(coord => [coord[1], coord[0]]));
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [geometry, map]);
  return null;
}

const createIcon = (color) => new L.Icon({
  iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const icons = {
  stop: createIcon('black'),
  poi: createIcon('green'),
  hotel: createIcon('blue'),
  restaurant: createIcon('red')
};

export default function MapComponent({ itinerary }) {
  if (!itinerary || !itinerary.geometry) {
    return (
      <div className="flex items-center justify-center bg-gray-100 text-gray-400 rounded-xl border-2 border-dashed border-gray-300" style={{ height: '500px' }}>
        Genera un itinerario per visualizzare la mappa
      </div>
    );
  }

  // OpenRouteService restituisce [long, lat], Leaflet vuole [lat, long]
  const positions = itinerary.geometry.map(coord => [coord[1], coord[0]]);

  return (
    <div style={{ height: '500px', width: '100%' }} className="rounded-xl overflow-hidden shadow-lg border border-gray-200">
      <MapContainer 
        center={positions[0]} 
        zoom={6} 
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
        />
        
        <Polyline positions={positions} color="#4f46e5" weight={5} opacity={0.7} />
        <MapUpdater geometry={itinerary.geometry} />

        {itinerary.giorni.map((giorno, gIdx) => (
          <div key={`day-group-${gIdx}`}>
            {/* Tappa del giorno */}
            {giorno.lat && giorno.lon && (
              <Marker position={[giorno.lat, giorno.lon]} icon={icons.stop}>
                <Popup>
                  <div className="font-bold text-sm">Giorno {giorno.giorno}: {giorno.citta_tappa}</div>
                </Popup>
              </Marker>
            )}

            {/* Punti di Interesse */}
            {giorno.poi?.map((p, i) => p.lat && p.lon && (
              <Marker key={`poi-${gIdx}-${i}`} position={[p.lat, p.lon]} icon={icons.poi}>
                <Popup><div className="text-xs font-bold">{p.name}</div></Popup>
              </Marker>
            ))}

            {/* Hotel */}
            {giorno.hotel?.map((h, i) => h.lat && h.lon && (
              <Marker key={`hotel-${gIdx}-${i}`} position={[h.lat, h.lon]} icon={icons.hotel}>
                <Popup><div className="text-xs font-bold text-blue-600">Alloggio: {h.name}</div></Popup>
              </Marker>
            ))}

            {/* Ristoranti */}
            {giorno.ristoranti?.map((r, i) => r.lat && r.lon && (
              <Marker key={`rest-${gIdx}-${i}`} position={[r.lat, r.lon]} icon={icons.restaurant}>
                <Popup><div className="text-xs font-bold text-red-600">Ristorante: {r.name}</div></Popup>
              </Marker>
            ))}
          </div>
        ))}
      </MapContainer>
    </div>
  );
}