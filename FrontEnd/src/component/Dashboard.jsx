import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export default function Dashboard() {
    const [user, setUser] = useState(null);
    const [logs, setLogs] = useState([]);
    const [queue, setQueue] = useState([]);
    const [rankedJobs, setRankedJobs] = useState([]);
    const [status, setStatus] = useState({
        connected: false,
        agentStatus: 'idle',
        tasksCompleted: 0,
        tasksInProgress: 0,
        currentPhase: 'idle',
        uptime: '0h 0m'
    });
    const [progress, setProgress] = useState({
        stage: '',
        progress: 0,
        total: 0,
        percentage: 0
    });
    const [wsConnected, setWsConnected] = useState(false);
    const [isRunning, setIsRunning] = useState(false);
    const [maxJobs, setMaxJobs] = useState(10);
    const [autoApplyEnabled, setAutoApplyEnabled] = useState(true);
    const logsEndRef = useRef(null);
    const wsRef = useRef(null);
    const logIdRef = useRef(0);
    const navigate = useNavigate();

    // Auto-scroll logs to bottom
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    useEffect(() => {
        // Check if user is logged in
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');

        if (!token || !userData) {
            navigate('/auth');
            return;
        }

        try {
            setUser(JSON.parse(userData));
        } catch (e) {
            navigate('/auth');
        }
    }, [navigate]);

    // WebSocket connection for real-time updates
    useEffect(() => {
        if (!user) return;

        const token = localStorage.getItem('token');
        // Connect to WebSocket server
        const wsUrl = `ws://localhost:8000/ws/dashboard?token=${token}`;
        
        const connectWebSocket = () => {
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                setWsConnected(true);
                setStatus(prev => ({ ...prev, connected: true }));
                addLog('info', 'Connected to real-time server');
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            wsRef.current.onclose = () => {
                setWsConnected(false);
                setStatus(prev => ({ ...prev, connected: false }));
                addLog('warning', 'Disconnected from server. Reconnecting...');
                // Attempt to reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };

            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                addLog('error', 'Connection error occurred');
            };
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [user]);

    const handleWebSocketMessage = (data) => {
        switch (data.type) {
            case 'log':
                addLog(data.level || 'info', data.message, data.timestamp);
                break;
            case 'queue_update':
                setQueue(data.queue || []);
                break;
            case 'status_update':
                setStatus(prev => ({ ...prev, ...data.status }));
                if (data.status?.agentStatus === 'idle' || data.status?.agentStatus === 'error') {
                    setIsRunning(false);
                }
                if (data.status?.agentStatus === 'running') {
                    setIsRunning(true);
                }
                break;
            case 'job_update':
                if (data.action === 'ranked') {
                    setRankedJobs(prev => [...prev, data.job]);
                }
                break;
            case 'process_update':
                setProgress({
                    stage: data.stage,
                    progress: data.progress,
                    total: data.total,
                    percentage: data.percentage,
                    details: data.details
                });
                break;
            case 'task_started':
                addLog('info', `Task started: ${data.taskName}`);
                setStatus(prev => ({ ...prev, tasksInProgress: prev.tasksInProgress + 1 }));
                break;
            case 'task_completed':
                addLog('success', `Task completed: ${data.taskName}`);
                setStatus(prev => ({
                    ...prev,
                    tasksCompleted: prev.tasksCompleted + 1,
                    tasksInProgress: Math.max(0, prev.tasksInProgress - 1)
                }));
                break;
            default:
                break;
        }
    };

    const addLog = (level, message, timestamp = new Date().toISOString()) => {
        logIdRef.current += 1;
        setLogs(prev => [...prev.slice(-99), { level, message, timestamp, id: `log-${logIdRef.current}-${Date.now()}` }]);
    };

    const handleLogout = () => {
        if (wsRef.current) {
            wsRef.current.close();
        }
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/');
    };

    const clearLogs = () => {
        setLogs([]);
    };

    const getLogIcon = (level) => {
        switch (level) {
            case 'error':
                return '✕';
            case 'warning':
                return '⚠';
            case 'success':
                return '✓';
            default:
                return '●';
        }
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const getStatusColor = (agentStatus) => {
        switch (agentStatus) {
            case 'running':
                return 'status-running';
            case 'idle':
                return 'status-idle';
            case 'error':
                return 'status-error';
            default:
                return 'status-idle';
        }
    };

    const startAutoApply = async () => {
        if (isRunning) return;
        
        setIsRunning(true);
        setRankedJobs([]);
        setProgress({ stage: '', progress: 0, total: 0, percentage: 0 });
        
        const token = localStorage.getItem('token');
        
        try {
            const response = await fetch(`http://localhost:8000/api/auto-apply/start?max_jobs=${maxJobs}&auto_apply=${autoApplyEnabled}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                addLog('error', `Failed to start: ${error.detail || 'Unknown error'}`);
                setIsRunning(false);
            }
        } catch (error) {
            addLog('error', `Connection error: ${error.message}`);
            setIsRunning(false);
        }
    };

    const clearQueue = async () => {
        const token = localStorage.getItem('token');
        
        try {
            const response = await fetch('http://localhost:8000/api/auto-apply/queue/clear', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                setQueue([]);
                setRankedJobs([]);
            }
        } catch (error) {
            addLog('error', `Failed to clear queue: ${error.message}`);
        }
    };

    const getPhaseLabel = (phase) => {
        const labels = {
            'initializing': 'Initializing...',
            'ranking': 'Ranking Jobs',
            'queuing': 'Adding to Queue',
            'applying': 'Auto-Applying',
            'completed': 'Completed',
            'failed': 'Failed',
            'idle': 'Ready'
        };
        return labels[phase] || phase;
    };

    const getQueueStatusColor = (status) => {
        switch (status) {
            case 'SUBMITTED':
                return 'queue-submitted';
            case 'APPLYING':
                return 'queue-applying';
            case 'IN_PROGRESS':
                return 'queue-progress';
            case 'FAILED':
                return 'queue-failed';
            default:
                return 'queue-pending';
        }
    };

    if (!user) {
        return null;
    }

    return (
        <div className="dashboard-page">
            {/* Content */}
            <div className="dashboard-content">
                <div className="dashboard-header">
                    <div className="header-left">
                        <h1>Auto-Apply Dashboard</h1>
                        <span className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
                            <span className="status-dot"></span>
                            {wsConnected ? 'Live' : 'Disconnected'}
                        </span>
                    </div>
                    <div className="header-right">
                        <span className="user-info">{user.email}</span>
                        <button className="logout-btn" onClick={handleLogout}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                <polyline points="16 17 21 12 16 7" />
                                <line x1="21" y1="12" x2="9" y2="12" />
                            </svg>
                            Logout
                        </button>
                    </div>
                </div>

                {/* Auto-Apply Control Panel */}
                <div className="control-panel">
                    <div className="control-panel-left">
                        <div className="control-group">
                            <label>Max Jobs:</label>
                            <select 
                                value={maxJobs} 
                                onChange={(e) => setMaxJobs(Number(e.target.value))}
                                disabled={isRunning}
                            >
                                <option value={5}>5</option>
                                <option value={10}>10</option>
                                <option value={20}>20</option>
                                <option value={50}>50</option>
                            </select>
                        </div>
                        <div className="control-group">
                            <label className="checkbox-label">
                                <input 
                                    type="checkbox" 
                                    checked={autoApplyEnabled}
                                    onChange={(e) => setAutoApplyEnabled(e.target.checked)}
                                    disabled={isRunning}
                                />
                                Auto-Apply
                            </label>
                        </div>
                    </div>
                    <div className="control-panel-right">
                        <button 
                            className={`start-btn ${isRunning ? 'running' : ''}`}
                            onClick={startAutoApply}
                            disabled={isRunning || !wsConnected}
                        >
                            {isRunning ? (
                                <>
                                    <span className="spinner"></span>
                                    Running...
                                </>
                            ) : (
                                <>
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <polygon points="5 3 19 12 5 21 5 3" />
                                    </svg>
                                    Start Auto-Apply
                                </>
                            )}
                        </button>
                        <button 
                            className="clear-queue-btn"
                            onClick={clearQueue}
                            disabled={isRunning}
                        >
                            Clear Queue
                        </button>
                    </div>
                </div>

                {/* Progress Bar */}
                {progress.stage && progress.stage !== 'idle' && (
                    <div className="progress-section">
                        <div className="progress-header">
                            <span className="progress-stage">{getPhaseLabel(progress.stage)}</span>
                            <span className="progress-count">{progress.progress} / {progress.total}</span>
                        </div>
                        <div className="progress-bar-container">
                            <div 
                                className="progress-bar-fill"
                                style={{ width: `${progress.percentage}%` }}
                            ></div>
                        </div>
                        {progress.details?.message && (
                            <div className="progress-message">{progress.details.message}</div>
                        )}
                    </div>
                )}

                {/* Status Cards */}
                <div className="status-grid">
                    <div className="status-card">
                        <div className="status-card-header">
                            <span className="status-card-title">Agent Status</span>
                            <span className={`status-badge ${getStatusColor(status.agentStatus)}`}>
                                {status.agentStatus}
                            </span>
                        </div>
                        <div className="status-card-value">
                            <span className={`status-indicator ${getStatusColor(status.agentStatus)}`}></span>
                            <span className="phase-label">{getPhaseLabel(status.currentPhase || 'idle')}</span>
                        </div>
                    </div>

                    <div className="status-card">
                        <div className="status-card-header">
                            <span className="status-card-title">Jobs Applied</span>
                        </div>
                        <div className="status-card-value">{status.tasksCompleted}</div>
                    </div>

                    <div className="status-card">
                        <div className="status-card-header">
                            <span className="status-card-title">In Progress</span>
                        </div>
                        <div className="status-card-value">{status.tasksInProgress}</div>
                    </div>

                    <div className="status-card">
                        <div className="status-card-header">
                            <span className="status-card-title">Queue Size</span>
                        </div>
                        <div className="status-card-value">{queue.length}</div>
                    </div>
                </div>

                {/* Main Grid */}
                <div className="dashboard-grid">
                    {/* Live Logs Section */}
                    <div className="panel logs-panel">
                        <div className="panel-header">
                            <h2>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                    <polyline points="14 2 14 8 20 8" />
                                    <line x1="16" y1="13" x2="8" y2="13" />
                                    <line x1="16" y1="17" x2="8" y2="17" />
                                    <polyline points="10 9 9 9 8 9" />
                                </svg>
                                Live Logs
                            </h2>
                            <button className="clear-btn" onClick={clearLogs}>Clear</button>
                        </div>
                        <div className="logs-container">
                            {logs.length === 0 ? (
                                <div className="logs-empty">
                                    <span>No logs yet. Waiting for activity...</span>
                                </div>
                            ) : (
                                logs.map((log) => (
                                    <div key={log.id} className={`log-entry log-${log.level}`}>
                                        <span className="log-time">{formatTimestamp(log.timestamp)}</span>
                                        <span className="log-icon">{getLogIcon(log.level)}</span>
                                        <span className="log-message">{log.message}</span>
                                    </div>
                                ))
                            )}
                            <div ref={logsEndRef} />
                        </div>
                    </div>

                    {/* Queue Section */}
                    <div className="panel queue-panel">
                        <div className="panel-header">
                            <h2>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <line x1="8" y1="6" x2="21" y2="6" />
                                    <line x1="8" y1="12" x2="21" y2="12" />
                                    <line x1="8" y1="18" x2="21" y2="18" />
                                    <line x1="3" y1="6" x2="3.01" y2="6" />
                                    <line x1="3" y1="12" x2="3.01" y2="12" />
                                    <line x1="3" y1="18" x2="3.01" y2="18" />
                                </svg>
                                Job Queue
                            </h2>
                            <span className="queue-count">{queue.length} jobs</span>
                        </div>
                        <div className="queue-container">
                            {queue.length === 0 ? (
                                <div className="queue-empty">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                                        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                                    </svg>
                                    <span>No jobs in queue</span>
                                    <span className="queue-hint">Click "Start Auto-Apply" to find jobs</span>
                                </div>
                            ) : (
                                queue.map((job, index) => (
                                    <div key={job.id || index} className={`queue-item ${getQueueStatusColor(job.status)}`}>
                                        <div className="queue-item-header">
                                            <span className="queue-position">#{index + 1}</span>
                                            <span className={`queue-status ${getQueueStatusColor(job.status)}`}>
                                                {job.status || 'pending'}
                                            </span>
                                        </div>
                                        <div className="queue-item-name">{job.name || 'Unknown Job'}</div>
                                        {job.match_score && (
                                            <div className="queue-item-score">
                                                <span className="score-label">Match:</span>
                                                <span className="score-value">{job.match_score.toFixed(1)}%</span>
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
