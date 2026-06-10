export default function Itinerary() {
  return (
    <div className="h-full flex flex-col justify-center items-center bg-slate-100 p-8 text-center">
      <div className="text-indigo-200 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-24 w-24 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      </div>
      <h1 className="text-3xl font-bold text-slate-700 mb-2">Pronto per partire?</h1>
      <p className="text-slate-500 max-w-md">Chatta con l'assistente a sinistra per definire le tue preferenze. L'itinerario del tuo road trip apparirà qui.</p>
    </div>
  );
}