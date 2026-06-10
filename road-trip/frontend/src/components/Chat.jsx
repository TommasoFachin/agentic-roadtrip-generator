import { useState, useRef, useEffect } from 'react';

export default function Chat({ setProfileUpdates, setChatMessages }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Ciao! Sono il tuo assistente di viaggio. Dimmi da dove parti, dove vuoi andare, in che date e quanti km al giorno vuoi fare." }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setInput('');
    setIsLoading(true);

    // Aggiorniamo lo storico dei messaggi globale (per il planner)
    if (setChatMessages) {
      setChatMessages(prev => [...prev, userMessage]);
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/chatbot/messaggio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messaggio: userMessage })
      });
      const data = await response.json();

      setMessages(prev => [...prev, { role: 'assistant', text: data.risposta }]);
      
      if (data.profilo_aggiornato) {
        setProfileUpdates(data.profilo_aggiornato);
      }
    } catch (error) {
      console.error("Errore API:", error);
      setMessages(prev => [...prev, { role: 'assistant', text: "Errore di connessione al server." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-3 rounded-2xl ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white border border-gray-200 text-slate-800 rounded-bl-none shadow-sm'}`}>
              {msg.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 text-slate-500 p-3 rounded-2xl rounded-bl-none shadow-sm flex space-x-1">
              <span className="animate-bounce">.</span><span className="animate-bounce delay-100">.</span><span className="animate-bounce delay-200">.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-200">
        <div className="flex space-x-2">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Scrivi all'assistente..." 
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
          <button 
            onClick={sendMessage}
            disabled={isLoading}
            className="bg-indigo-600 text-white px-4 py-2 rounded-full hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            Invia
          </button>
        </div>
      </div>
    </div>
  );
}