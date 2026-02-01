import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, AlertOctagon, Activity, FileText, CheckCircle, XCircle, Clock, Terminal, LogOut } from 'lucide-react';
import LandingPage from './component/LandingPage';

// --- MOCK DATA (Replace with API calls later) ---
const INITIAL_JOBS = [
  { id: 1, company: 'Google', role: 'Frontend Intern', match: 95, status: 'SUBMITTED', time: '10:42 AM' },
  { id: 2, company: 'Netflix', role: 'UI Engineer', match: 88, status: 'FAILED', time: '10:44 AM' },
  { id: 3, company: 'Spotify', role: 'Web Developer', match: 92, status: 'APPLYING', time: '10:45 AM' },
  { id: 4, company: 'Amazon', role: 'SDE I', match: 74, status: 'QUEUED', time: '-' },
  { id: 5, company: 'Meta', role: 'React Dev', match: 81, status: 'QUEUED', time: '-' },
];

const INITIAL_LOGS = [
  { time: '10:42:10', type: 'info', msg: 'Job search initiated. Found 30 candidates.' },
  { time: '10:42:15', type: 'success', msg: 'Application to Google submitted successfully.' },
  { time: '10:44:02', type: 'error', msg: 'Netflix API returned 500. Retrying in 5s...' },
  { time: '10:45:00', type: 'info', msg: 'Generating cover letter for Spotify...' },
];

export default function App() {
  // State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userData, setUserData] = useState(null);
  const [jobs, setJobs] = useState(INITIAL_JOBS);
  const [logs, setLogs] = useState(INITIAL_LOGS);
  const [isRunning, setIsRunning] = useState(true); // The "Kill Switch" state
  const [stats, setStats] = useState({ total: 30, applied: 12, successRate: '92%' });
  
  // Check for existing authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const email = localStorage.getItem('user_email');
    if (token && email) {
      setIsAuthenticated(true);
      setUserData({ email });
    }
  }, []);

  const handleLogin = (data) => {
    setIsAuthenticated(true);
    setUserData(data.user);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_email');
    setIsAuthenticated(false);
    setUserData(null);
  };

  // Show landing page if not authenticated
  if (!isAuthenticated) {
    return <LandingPage onLogin={handleLogin} />;
  }
  
  const logsEndRef = useRef(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // --- POLLING EFFECT (Uncomment this when Backend is ready) ---
  /*
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [jobsRes, logsRes, statusRes] = await Promise.all([
           axios.get('/api/jobs/queue'),
           axios.get('/api/logs/latest'),
           axios.get('/api/status')
        ]);
        setJobs(jobsRes.data);
        setLogs(prev => [...prev, ...logsRes.data]); // Append new logs
        setStats(statusRes.data);
      } catch (err) { console.error("Polling failed", err); }
    }, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, []);
  */

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-6 font-mono selection:bg-indigo-500 selection:text-white">
      
      {/* HEADER & CONTROLS */}
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
            AutoApply Agent <span className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded ml-2">v1.0.0</span>
          </h1>
          <p className="text-slate-500 mt-1 text-sm">Autonomous Search & Application Pipeline {userData?.email && `• ${userData.email}`}</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-lg border border-slate-800">
            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className="text-sm font-semibold">{isRunning ? 'SYSTEM ACTIVE' : 'SYSTEM PAUSED'}</span>
          </div>
          
          {/* THE KILL SWITCH */}
          <button 
            onClick={() => setIsRunning(!isRunning)}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all ${
              isRunning 
              ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/50' 
              : 'bg-green-500/10 text-green-400 hover:bg-green-500/20 border border-green-500/50'
            }`}
          >
            {isRunning ? <><Pause size={18} /> EMERGENCY STOP</> : <><Play size={18} /> RESUME AGENT</>}
          </button>

          {/* LOGOUT BUTTON */}
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-300 border border-slate-700"
          >
            <LogOut size={18} /> Logout
          </button>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">
        
        {/* LEFT COLUMN: STATS & CONFIG (3 cols) */}
        <div className="col-span-3 flex flex-col gap-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 gap-4">
            <StatCard label="Jobs Found" value={stats.total} icon={<Activity size={20} className="text-blue-400"/>} />
            <StatCard label="Applications Sent" value={stats.applied} icon={<FileText size={20} className="text-purple-400"/>} />
            <StatCard label="Success Rate" value={stats.successRate} icon={<CheckCircle size={20} className="text-green-400"/>} />
          </div>

          {/* Policy Config Panel */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 flex-1">
            <h3 className="text-slate-400 font-semibold mb-4 flex items-center gap-2">
              <AlertOctagon size={16} /> Autonomy Policy
            </h3>
            <div className="space-y-4">
              <ConfigInput label="Max Applications / Day" value="50" />
              <ConfigInput label="Min Match Score" value="75%" />
              <ConfigInput label="Restricted Companies" value="Revature, Infosys" />
              
              <div className="mt-6 p-3 bg-indigo-500/10 border border-indigo-500/30 rounded text-xs text-indigo-300">
                Running in <strong>Safe Mode</strong>. Agent will verify all claims against "Student_Profile.json" before applying.
              </div>
            </div>
          </div>
        </div>

        {/* MIDDLE COLUMN: JOB QUEUE (6 cols) */}
        <div className="col-span-6 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/80 backdrop-blur">
            <h2 className="font-semibold flex items-center gap-2">
              <Clock size={18} className="text-slate-400"/> Execution Queue
            </h2>
            <span className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded">Live Feed</span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
            {jobs.map((job) => (
              <JobRow key={job.id} job={job} />
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: TERMINAL LOGS (3 cols) */}
        <div className="col-span-3 bg-black border border-slate-800 rounded-xl overflow-hidden flex flex-col font-mono text-xs">
          <div className="p-3 border-b border-slate-800 bg-slate-900/50 text-slate-400 flex items-center gap-2">
            <Terminal size={14} /> Agent Logs
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            {logs.map((log, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-slate-600 shrink-0">[{log.time}]</span>
                <span className={clsx({
                  'text-slate-300': log.type === 'info',
                  'text-green-400': log.type === 'success',
                  'text-red-400': log.type === 'error',
                  'text-yellow-400': log.type === 'warning',
                })}>
                  {log.type === 'error' ? '✖ ' : log.type === 'success' ? '✔ ' : '> '}
                  {log.msg}
                </span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>

      </div>
    </div>
  );
}

// --- SUB COMPONENTS ---

function StatCard({ label, value, icon }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
      <div>
        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider">{label}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
      </div>
      <div className="bg-slate-800/50 p-3 rounded-lg">{icon}</div>
    </div>
  );
}

function ConfigInput({ label, value }) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      <input 
        type="text" 
        defaultValue={value} 
        className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none transition-colors"
      />
    </div>
  );
}

function JobRow({ job }) {
  const statusColors = {
    QUEUED: 'bg-slate-800 text-slate-400 border-slate-700',
    APPLYING: 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse',
    SUBMITTED: 'bg-green-500/10 text-green-400 border-green-500/20',
    FAILED: 'bg-red-500/10 text-red-400 border-red-500/20',
  };

  return (
    <div className="flex items-center justify-between p-4 bg-slate-950/50 border border-slate-800/50 rounded-lg hover:border-slate-700 transition-all">
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
          job.match > 90 ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
        }`}>
          {job.match}
        </div>
        <div>
          <h4 className="font-bold text-slate-200">{job.role}</h4>
          <p className="text-sm text-slate-500">{job.company}</p>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className={`px-3 py-1 rounded-full text-xs font-bold border ${statusColors[job.status] || statusColors.QUEUED}`}>
          {job.status}
        </div>
        {job.status === 'FAILED' && <span className="text-xs text-red-500 font-mono">Retrying...</span>}
      </div>
    </div>
  );
}

function clsx(classes) {
  // Simple utility for conditional classes if you don't install the library
  // But strictly standard: return Object.keys(classes).filter(k => classes[k]).join(' ');
  return Object.entries(classes).filter(([k, v]) => v).map(([k]) => k).join(' ');
}