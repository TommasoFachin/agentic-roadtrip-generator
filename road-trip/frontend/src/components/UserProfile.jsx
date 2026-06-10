export default function UserProfile({ profile }) {
  return (
    <div className="p-4 bg-slate-800 text-white shadow-md z-10 shrink-0">
      <h2 className="text-lg font-semibold mb-2">Il tuo Profilo</h2>
      
      {!profile ? (
        <p className="text-sm text-slate-400">Inizia a chattare per aggiornare le preferenze di viaggio.</p>
      ) : (
        <div className="space-y-2 text-sm">
          {profile.luogo_partenza && (
            <p><span className="font-semibold text-indigo-300">Partenza:</span> {profile.luogo_partenza}</p>
          )}
          {profile.luogo_destinazione && (
            <p><span className="font-semibold text-indigo-300">Destinazione:</span> {profile.luogo_destinazione}</p>
          )}
          {profile.interessi_poi?.length > 0 && (
            <p><span className="font-semibold text-indigo-300">Interessi:</span> {profile.interessi_poi.join(", ")}</p>
          )}
          {profile.interessi_eventi?.length > 0 && (
            <p><span className="font-semibold text-indigo-300">Eventi:</span> {profile.interessi_eventi.join(", ")}</p>
          )}
          {profile.tappe_obbligatorie?.length > 0 && (
            <p><span className="font-semibold text-indigo-300">Tappe:</span> {profile.tappe_obbligatorie.join(", ")}</p>
          )}
          {profile.preferenze_viaggio?.length > 0 && (
            <p><span className="font-semibold text-indigo-300">Preferenze:</span> {profile.preferenze_viaggio.join(", ")}</p>
          )}
        </div>
      )}
    </div>
  );
}