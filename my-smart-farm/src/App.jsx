import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { 
  getFirestore, 
  collection, 
  addDoc, 
  onSnapshot, 
  query, 
  doc, 
  updateDoc,
  deleteDoc,
  serverTimestamp 
} from 'firebase/firestore';
import { 
  getAuth, 
  signInAnonymously, 
  onAuthStateChanged,
  signInWithCustomToken 
} from 'firebase/auth';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import { 
  Sprout, 
  Thermometer, 
  Droplets, 
  Sun, 
  Database, 
  Plus, 
  Trash2, 
  Activity,
  History,
  LayoutDashboard
} from 'lucide-react';

// Firebase configuration using environment variables
const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'smart-farm-v1';

export default function App() {
  const [user, setUser] = useState(null);
  const [plants, setPlants] = useState([]);
  const [logs, setLogs] = useState([]);
  const [view, setView] = useState('dashboard'); // 'dashboard', 'plants', 'logs'
  const [newPlant, setNewPlant] = useState({ name: '', type: '', plantingDate: new Date().toISOString().split('T')[0] });
  const [loading, setLoading] = useState(true);

  // Auth initialization
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
          await signInWithCustomToken(auth, __initial_auth_token);
        } else {
          await signInAnonymously(auth);
        }
      } catch (error) {
        console.error("Auth error:", error);
      }
    };
    initAuth();
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  // Fetch Plants & Logs
  useEffect(() => {
    if (!user) return;

    const plantsRef = collection(db, 'artifacts', appId, 'public', 'data', 'plants');
    const logsRef = collection(db, 'artifacts', appId, 'public', 'data', 'logs');

    const unsubPlants = onSnapshot(plantsRef, (snapshot) => {
      const plantList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setPlants(plantList);
    }, (err) => console.error("Firestore error:", err));

    const unsubLogs = onSnapshot(logsRef, (snapshot) => {
      const logList = snapshot.docs.map(doc => ({ 
        id: doc.id, 
        ...doc.data(),
        timestamp: doc.data().timestamp?.toDate().toLocaleString() || 'N/A'
      }));
      // Sort in memory by date descending
      setLogs(logList.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
    }, (err) => console.error("Firestore error:", err));

    return () => {
      unsubPlants();
      unsubLogs();
    };
  }, [user]);

  const addPlant = async (e) => {
    e.preventDefault();
    if (!user || !newPlant.name) return;
    try {
      await addDoc(collection(db, 'artifacts', appId, 'public', 'data', 'plants'), {
        ...newPlant,
        createdAt: serverTimestamp()
      });
      setNewPlant({ name: '', type: '', plantingDate: new Date().toISOString().split('T')[0] });
    } catch (err) {
      console.error(err);
    }
  };

  const deletePlant = async (id) => {
    try {
      await deleteDoc(doc(db, 'artifacts', appId, 'public', 'data', 'plants', id));
    } catch (err) {
      console.error(err);
    }
  };

  // Mock data for the chart if logs are empty
  const chartData = logs.slice(0, 10).reverse().map(log => ({
    time: log.timestamp.split(',')[1],
    temp: log.temperature,
    humidity: log.humidity
  }));

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <div className="animate-spin text-emerald-600"><Activity size={48} /></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {/* Sidebar / Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t flex justify-around p-4 md:relative md:border-t-0 md:border-r md:w-64 md:flex-col md:justify-start md:space-y-4 z-10">
        <div className="hidden md:block p-6 mb-4">
          <div className="flex items-center gap-2 text-emerald-600 font-bold text-xl">
            <Sprout /> <span>SmartFarm</span>
          </div>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest">Growth Tracker</p>
        </div>
        
        <button 
          onClick={() => setView('dashboard')}
          className={`flex items-center gap-3 p-3 rounded-xl transition-all ${view === 'dashboard' ? 'bg-emerald-50 text-emerald-600 shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}
        >
          <LayoutDashboard size={20} /> <span className="text-sm font-medium">Dashboard</span>
        </button>
        <button 
          onClick={() => setView('plants')}
          className={`flex items-center gap-3 p-3 rounded-xl transition-all ${view === 'plants' ? 'bg-emerald-50 text-emerald-600 shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}
        >
          <Sprout size={20} /> <span className="text-sm font-medium">My Plants</span>
        </button>
        <button 
          onClick={() => setView('logs')}
          className={`flex items-center gap-3 p-3 rounded-xl transition-all ${view === 'logs' ? 'bg-emerald-50 text-emerald-600 shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}
        >
          <History size={20} /> <span className="text-sm font-medium">Activity Logs</span>
        </button>

        <div className="hidden md:mt-auto md:block p-4 bg-emerald-900 text-white rounded-2xl m-4">
          <p className="text-xs opacity-75">Current User ID:</p>
          <p className="text-[10px] truncate font-mono">{user?.uid}</p>
        </div>
      </nav>

      <main className="md:ml-64 p-6 pb-24 md:pb-6">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold capitalize">{view}</h1>
          <div className="flex items-center gap-4">
            <div className="bg-white p-2 px-4 rounded-full shadow-sm border flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-xs font-medium text-slate-600">Pi 5 Online</span>
            </div>
          </div>
        </header>

        {/* Dashboard View */}
        {view === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-blue-50 text-blue-500 rounded-2xl"><Thermometer /></div>
                  <span className="text-xs font-bold text-slate-400">TEMPERATURE</span>
                </div>
                <h3 className="text-3xl font-bold">{logs[0]?.temperature || '--'}°C</h3>
                <p className="text-xs text-slate-400 mt-2">Latest update from Pi 5</p>
              </div>
              <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-sky-50 text-sky-500 rounded-2xl"><Droplets /></div>
                  <span className="text-xs font-bold text-slate-400">HUMIDITY</span>
                </div>
                <h3 className="text-3xl font-bold">{logs[0]?.humidity || '--'}%</h3>
                <p className="text-xs text-slate-400 mt-2">Optimal range 60-80%</p>
              </div>
              <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-amber-50 text-amber-500 rounded-2xl"><Sun /></div>
                  <span className="text-xs font-bold text-slate-400">LIGHT INTENSITY</span>
                </div>
                <h3 className="text-3xl font-bold">{logs[0]?.light || '--'} lx</h3>
                <p className="text-xs text-slate-400 mt-2">Real-time light exposure</p>
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
              <h3 className="font-bold mb-6 flex items-center gap-2"><Activity size={18}/> Environment History</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="time" hide />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                    <Legend />
                    <Line type="monotone" dataKey="temp" stroke="#3b82f6" strokeWidth={3} dot={false} name="Temperature (°C)" />
                    <Line type="monotone" dataKey="humidity" stroke="#0ea5e9" strokeWidth={3} dot={false} name="Humidity (%)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Plants View */}
        {view === 'plants' && (
          <div className="space-y-6">
            <form onSubmit={addPlant} className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px]">
                <label className="text-xs font-bold text-slate-400 block mb-2">PLANT NAME</label>
                <input 
                  type="text" 
                  value={newPlant.name}
                  onChange={(e) => setNewPlant({...newPlant, name: e.target.value})}
                  className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="e.g. Thai Basil"
                />
              </div>
              <div className="flex-1 min-w-[200px]">
                <label className="text-xs font-bold text-slate-400 block mb-2">PLANT TYPE</label>
                <input 
                  type="text" 
                  value={newPlant.type}
                  onChange={(e) => setNewPlant({...newPlant, type: e.target.value})}
                  className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="e.g. Herb"
                />
              </div>
              <button type="submit" className="bg-emerald-600 text-white p-3 px-6 rounded-xl font-bold flex items-center gap-2 hover:bg-emerald-700 shadow-lg shadow-emerald-200 transition-all">
                <Plus size={20}/> Add Plant
              </button>
            </form>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {plants.map(plant => (
                <div key={plant.id} className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 group relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => deletePlant(plant.id)} className="text-rose-500 hover:bg-rose-50 p-2 rounded-lg"><Trash2 size={18}/></button>
                  </div>
                  <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mb-4">
                    <Sprout size={32} />
                  </div>
                  <h3 className="text-xl font-bold mb-1">{plant.name}</h3>
                  <p className="text-slate-400 text-sm mb-4">{plant.type || 'Standard Type'}</p>
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-500 bg-slate-50 p-2 px-3 rounded-lg w-fit">
                    <History size={14}/> Planted on: {plant.plantingDate}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Logs View */}
        {view === 'logs' && (
          <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    <th className="p-4 text-xs font-bold text-slate-400 uppercase">Timestamp</th>
                    <th className="p-4 text-xs font-bold text-slate-400 uppercase text-blue-500">Temp</th>
                    <th className="p-4 text-xs font-bold text-slate-400 uppercase text-sky-500">Humidity</th>
                    <th className="p-4 text-xs font-bold text-slate-400 uppercase text-amber-500">Light</th>
                    <th className="p-4 text-xs font-bold text-slate-400 uppercase">Device</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.map(log => (
                    <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                      <td className="p-4 text-sm font-medium">{log.timestamp}</td>
                      <td className="p-4 text-sm font-bold">{log.temperature}°C</td>
                      <td className="p-4 text-sm font-bold">{log.humidity}%</td>
                      <td className="p-4 text-sm font-bold">{log.light} lx</td>
                      <td className="p-4"><span className="text-[10px] bg-slate-100 p-1 px-2 rounded-full font-mono">PI_5_NODE_01</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {logs.length === 0 && (
                <div className="p-12 text-center text-slate-400">
                  <Database size={48} className="mx-auto mb-4 opacity-20"/>
                  <p>No log data received yet from Raspberry Pi.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}