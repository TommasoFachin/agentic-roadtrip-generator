import React, { useState } from 'react';
import DayCard from './DayCard';

// Riceve lo storico messaggi come prop (array di stringhe) dal componente genitore (App.jsx o layout)
const ItineraryViewer = ({ chatMessages }) => {
  const [loading, setLoading] = useState(false);
  const [itinerary, setItinerary] = useState(null);
  const [error, setError] = useState(null);
  const [loadingStep, setLoadingStep] = useState("");
  const [showBudgetForm, setShowBudgetForm] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState("nessuno");

  const startPlanning = () => {
    // Controllo sicurezza: assicuriamoci ci siano messaggi
    if (!chatMessages || chatMessages.length === 0) {
      setError("Non hai ancora inserito le informazioni in chat!");
      return;
    }
    setShowBudgetForm(true);
  };

  const confirmPlanning = async () => {
    setShowBudgetForm(false);
    setLoading(true);
    setError(null);
    setItinerary(null);

    try {
      // 1. Uniamo i messaggi della chat in un unico testo
      const testoCompleto = chatMessages.join(" ");

      // 2. Chiamata all'agente LLM per interpretare la richiesta
      setLoadingStep("L'Intelligenza Artificiale sta leggendo la tua richiesta...");
      const llmResponse = await fetch("http://127.0.0.1:8000/interpreta-richiesta", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ testo: testoCompleto })
      });

      if (!llmResponse.ok) throw new Error("Errore durante l'interpretazione dei dati.");
      const tripRequest = await llmResponse.json();

      // Aggiungiamo la scelta del budget prima di inviare al planner
      tripRequest.budget_hotel_cibo = selectedBudget;

      // 3. Chiamata al Planner (Routing, POI, Eventi)
      setLoadingStep("Calcolo del percorso, ricerca POI ed eventi in corso...");
      const plannerResponse = await fetch("http://127.0.0.1:8000/genera-itinerario", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tripRequest)
      });

      const data = await plannerResponse.json();

      if (!plannerResponse.ok || data.errore) {
        throw new Error(data.errore ? `${data.errore}: ${data.dettagli.motivo}` : "Errore nella generazione dell'itinerario.");
      }

      // Tutto è andato a buon fine, salviamo l'itinerario!
      setItinerary(data.itinerario);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4 flex flex-col h-full overflow-y-auto">
      
      {/* Header / Bottone Iniziale */}
      {!showBudgetForm && !loading && !itinerary && (
        <div className="mb-8 flex flex-col items-center justify-center bg-white p-8 rounded-2xl shadow-sm border border-gray-100 text-center">
          <div className="text-5xl mb-4">🗺️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Pronto per partire?</h2>
          <p className="text-gray-500 mb-6 max-w-md">
            Premi il bottone qui sotto. L'intelligenza artificiale analizzerà la nostra conversazione e costruirà l'itinerario perfetto per te.
          </p>
          
          <button
            onClick={startPlanning}
            className="flex items-center justify-center px-8 py-3 rounded-full font-semibold text-white transition-all duration-300 shadow-md hover:shadow-lg bg-blue-600 hover:bg-blue-700 hover:-translate-y-1"
          >
            Pianifica il mio viaggio
          </button>
        </div>
      )}

      {/* Form Selezione Budget */}
      {showBudgetForm && (
        <div className="mb-8 flex flex-col items-center justify-center bg-white p-8 rounded-2xl shadow-sm border border-gray-100 text-center transition-all">
          <div className="text-4xl mb-4">🛏️ 🍴</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Dove vuoi dormire e mangiare?</h2>
          <p className="text-gray-500 mb-6 max-w-md">
            Scegli il tuo budget per ricevere consigli personalizzati su hotel e ristoranti per ogni tappa.
          </p>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8 w-full max-w-2xl">
            <button 
              onClick={() => setSelectedBudget("nessuno")}
              className={`p-4 rounded-xl border-2 transition-all ${selectedBudget === "nessuno" ? "border-blue-500 bg-blue-50" : "border-gray-100 hover:border-blue-200"}`}
            >
              <span className="block text-2xl mb-2">❌</span>
              <span className="font-medium text-gray-700 text-sm">No, grazie</span>
            </button>
            <button 
              onClick={() => setSelectedBudget("economico")}
              className={`p-4 rounded-xl border-2 transition-all ${selectedBudget === "economico" ? "border-emerald-500 bg-emerald-50" : "border-gray-100 hover:border-emerald-200"}`}
            >
              <span className="block text-2xl mb-2">💸</span>
              <span className="font-medium text-gray-700 text-sm">Economico</span>
            </button>
            <button 
              onClick={() => setSelectedBudget("medio")}
              className={`p-4 rounded-xl border-2 transition-all ${selectedBudget === "medio" ? "border-amber-500 bg-amber-50" : "border-gray-100 hover:border-amber-200"}`}
            >
              <span className="block text-2xl mb-2">💰</span>
              <span className="font-medium text-gray-700 text-sm">Medio</span>
            </button>
            <button 
              onClick={() => setSelectedBudget("alto")}
              className={`p-4 rounded-xl border-2 transition-all ${selectedBudget === "alto" ? "border-purple-500 bg-purple-50" : "border-gray-100 hover:border-purple-200"}`}
            >
              <span className="block text-2xl mb-2">💎</span>
              <span className="font-medium text-gray-700 text-sm">Alto</span>
            </button>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => setShowBudgetForm(false)}
              className="px-6 py-3 rounded-full font-semibold text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              Annulla
            </button>
            <button
              onClick={confirmPlanning}
              className="flex items-center justify-center px-8 py-3 rounded-full font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-md hover:-translate-y-1 transition-all"
            >
              Conferma e Genera
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="mb-8 flex flex-col items-center justify-center bg-white p-8 rounded-2xl shadow-sm border border-gray-100 text-center">
          <svg className="animate-spin mb-4 h-10 w-10 text-blue-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Elaborazione in corso...</h2>
          <p className="text-blue-600 animate-pulse font-medium">{loadingStep}</p>
        </div>
      )}

      {/* Area Errori */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl flex items-start mb-8 border border-red-200">
          <span className="mr-3 mt-0.5 shrink-0 text-xl">⚠️</span>
          <p>{error}</p>
        </div>
      )}

      {/* Visualizzazione Itinerario (Step 5) */}
      {itinerary && itinerary.giorni && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Il tuo Itinerario</h2>
          {itinerary.giorni.map((day) => (
            <DayCard key={day.giorno} day={day} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ItineraryViewer;