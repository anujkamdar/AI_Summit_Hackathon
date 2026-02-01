import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export default function Dashboard() {
    const [user, setUser] = useState(null);
    const [logs, setLogs] = useState([]);
    const [queue, setQueue] = useState([]);
    const [status, setStatus] = useState({
        connected: false,
        agentStatus: 'idle',
        tasksCompleted: 0,
        tasksInProgress: 0,
        uptime: '0h 0m'
    });
    const [wsConnected, setWsConnected] = useState(false);
    const logsEndRef = useRef(null);
    const wsRef = useRef(null);
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
        setLogs(prev => [...prev.slice(-99), { level, message, timestamp, id: Date.now() }]);
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

    if (!user) {
        return null;
    }

    return (
        <div className="dashboard-page">
            {/* Content */}
            <div className="dashboard-content">
                <div className="dashboard-header">
                    <div className="header-left">
                        <h1>Dashboard</h1>
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
                        </div>
                    </div>

                    <div className="status-card">
                        <div className="status-card-header">
                            <span className="status-card-title">Tasks Completed</span>
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
                                Task Queue
                            </h2>
                            <span className="queue-count">{queue.length} tasks</span>
                        </div>
                        <div className="queue-container">
                            {queue.length === 0 ? (
                                <div className="queue-empty">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                        <circle cx="12" cy="12" r="10" />
                                        <path d="M16 16s-1.5-2-4-2-4 2-4 2" />
                                        <line x1="9" y1="9" x2="9.01" y2="9" />
                                        <line x1="15" y1="9" x2="15.01" y2="9" />
                                    </svg>
                                    <span>Queue is empty</span>
                                </div>
                            ) : (
                                queue.map((task, index) => (
                                    <div key={task.id || index} className={`queue-item ${task.status || 'pending'}`}>
                                        <div className="queue-item-header">
                                            <span className="queue-position">#{index + 1}</span>
                                            <span className={`queue-status ${task.status || 'pending'}`}>
                                                {task.status || 'pending'}
                                            </span>
                                        </div>
                                        <div className="queue-item-name">{task.name || 'Unnamed Task'}</div>
                                        {task.description && (
                                            <div className="queue-item-desc">{task.description}</div>
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
