import { useState } from 'react';
import UserProfile from './components/UserProfile';
import Chat from './components/Chat';
import ItineraryViewer from './components/ItineraryViewer';

function App() {
  const [userProfile, setUserProfile] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);

  return (
    <div className="flex h-screen w-full bg-white overflow-hidden font-sans">
      
      {/* PANNELLO SINISTRO (Chat & Profilo) */}
      <div className="w-full md:w-[400px] flex flex-col border-r border-gray-200 bg-white shrink-0">
        <UserProfile profile={userProfile} />
        <Chat setProfileUpdates={setUserProfile} setChatMessages={setChatMessages} />
      </div>

      {/* PANNELLO DESTRO (Itinerario) */}
      <div className="flex-1 bg-slate-50 overflow-y-auto hidden md:block">
        <ItineraryViewer chatMessages={chatMessages} />
      </div>
      
    </div>
  );
}

export default App;
