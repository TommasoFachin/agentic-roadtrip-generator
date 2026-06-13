import React from 'react';

const DayCard = ({ day }) => {
  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-8 border border-gray-100 hover:shadow-xl transition-shadow duration-300">
      {/* Header / Immagine Città */}
      <div className="relative h-48 sm:h-64 bg-gray-200">
        {day.immagine_url ? (
          <img 
            src={day.immagine_url} 
            alt={day.citta_tappa} 
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-5xl opacity-50">📷</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent"></div>
        <div className="absolute bottom-4 left-4 right-4 text-white">
          <div className="flex items-center space-x-2 text-sm font-medium text-blue-300 mb-1">
            <span>📅</span>
            <span>Giorno {day.giorno} • {day.data}</span>
          </div>
          <h2 className="text-3xl font-bold">{day.citta_tappa}</h2>
        </div>
      </div>

      {/* Info Tappa */}
      <div className="p-6">
        <div className="flex flex-wrap gap-4 mb-6 pb-6 border-b border-gray-100 text-sm text-gray-600">
          <div className="flex items-center space-x-2 bg-blue-50 px-3 py-1.5 rounded-full text-blue-700">
            <span>🚗</span>
            <span className="font-semibold">{day.distanza_km} km</span>
          </div>
          <div className="flex items-center space-x-2 bg-blue-50 px-3 py-1.5 rounded-full text-blue-700">
            <span>⏱️</span>
            <span>{day.durata_ore} ore di guida</span>
          </div>
          <div className="flex items-center space-x-2 text-gray-500">
            <span>Partenza: {day.ora_partenza}</span>
            <span>•</span>
            <span>Arrivo stimato: {day.ora_arrivo}</span>
          </div>
        </div>

        {/* POI - Punti di Interesse */}
        {day.poi && day.poi.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center mb-3">
              <span className="mr-2 text-xl">📍</span> 
              Cosa visitare
            </h3>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {day.poi.map((p, idx) => (
                <li key={idx} className="flex flex-col bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <span className="font-medium text-gray-800">{p.name || p.nome}</span>
                  <span className="text-xs text-gray-500 capitalize">{p.kind ? p.kind.split(',')[0].replace('_', ' ') : 'Punto di interesse'}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Eventi */}
        {day.eventi && day.eventi.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center mb-3">
              <span className="mr-2 text-xl">🎵</span> 
              Eventi Serali
            </h3>
            <ul className="space-y-2">
              {day.eventi.map((e, idx) => (
                <li key={idx} className="flex items-center bg-purple-50 p-3 rounded-lg text-sm text-purple-900 border border-purple-100">
                  <span className="font-semibold">{e.name || e.nome}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Hotel */}
        {day.hotel && day.hotel.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center mb-3">
              <span className="mr-2 text-xl">🛏️</span> 
              Dove dormire
            </h3>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {day.hotel.map((h, idx) => (
                <li key={idx} className="flex flex-col bg-emerald-50 p-3 rounded-lg border border-emerald-100">
                  <div className="flex justify-between items-start">
                    <span className="font-medium text-gray-800">{h.name || h.nome}</span>
                    {h.rate && (
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">⭐ {h.rate}</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Ristoranti */}
        {day.ristoranti && day.ristoranti.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 flex items-center mb-3">
              <span className="mr-2 text-xl">🍴</span> 
              Dove mangiare
            </h3>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {day.ristoranti.map((r, idx) => (
                <li key={idx} className="flex flex-col bg-orange-50 p-3 rounded-lg border border-orange-100">
                  <div className="flex justify-between items-start">
                    <span className="font-medium text-gray-800">{r.name || r.nome}</span>
                    {r.rate && (
                      <span className="text-xs font-bold text-orange-700 bg-orange-100 px-1.5 py-0.5 rounded">⭐ {r.rate}</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default DayCard;