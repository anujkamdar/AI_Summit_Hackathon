import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import Galaxy from './Galaxy';
import './AuthPage.css';

const API_BASE_URL = 'http://localhost:8000';

export default function AuthPage() {
    const [searchParams] = useSearchParams();
    const initialMode = searchParams.get('mode') === 'register' ? 'register' : 'signin';
    const [mode, setMode] = useState(initialMode);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    // Sign In form state
    const [signInData, setSignInData] = useState({
        email: '',
        password: ''
    });

    // Register form state
    const [registerData, setRegisterData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        resume: null,
        work_authorization: '',
        location_preference: '',
        remote_preference: '',
        start_date: '',
        relocation: '',
        salary_expectation: ''
    });

    const handleSignIn = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const response = await axios.post(`${API_BASE_URL}/api/auth/signin`, {
                email: signInData.email,
                password: signInData.password
            });

            // Store token and user data
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('user', JSON.stringify(response.data.user));

            // Redirect to dashboard
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Sign in failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        // Validate passwords match
        if (registerData.password !== registerData.confirmPassword) {
            setError('Passwords do not match');
            setIsLoading(false);
            return;
        }

        // Validate resume is provided
        if (!registerData.resume) {
            setError('Please upload your resume');
            setIsLoading(false);
            return;
        }

        try {
            const formData = new FormData();
            formData.append('email', registerData.email);
            formData.append('password', registerData.password);
            formData.append('resume', registerData.resume);

            // Optional fields
            if (registerData.work_authorization) formData.append('work_authorization', registerData.work_authorization);
            if (registerData.location_preference) formData.append('location_preference', registerData.location_preference);
            if (registerData.remote_preference) formData.append('remote_preference', registerData.remote_preference);
            if (registerData.start_date) formData.append('start_date', registerData.start_date);
            if (registerData.relocation) formData.append('relocation', registerData.relocation);
            if (registerData.salary_expectation) formData.append('salary_expectation', registerData.salary_expectation);

            const response = await axios.post(`${API_BASE_URL}/api/auth/signup`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            // Store token and user data
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('user', JSON.stringify(response.data.user));

            // Redirect to dashboard
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            setRegisterData({ ...registerData, resume: file });
        } else {
            setError('Please upload a PDF file');
        }
    };

    return (
        <div className="auth-page">
            {/* Galaxy Background */}
            <div className="galaxy-background">
                <Galaxy
                    mouseRepulsion
                    mouseInteraction
                    density={1}
                    glowIntensity={0.3}
                    saturation={0}
                    hueShift={140}
                    twinkleIntensity={0.3}
                    rotationSpeed={0.1}
                    repulsionStrength={2}
                    autoCenterRepulsion={0}
                    starSpeed={0.5}
                    speed={1}
                />
            </div>

            {/* Content */}
            <div className="auth-content">
                <div className="auth-container">
                    {/* Back button */}
                    <button className="back-button" onClick={() => navigate('/')}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M19 12H5M12 19l-7-7 7-7" />
                        </svg>
                        Back
                    </button>

                    {/* Mode Toggle */}
                    <div className="auth-toggle">
                        <button
                            className={`toggle-btn ${mode === 'signin' ? 'active' : ''}`}
                            onClick={() => { setMode('signin'); setError(''); }}
                        >
                            Sign In
                        </button>
                        <button
                            className={`toggle-btn ${mode === 'register' ? 'active' : ''}`}
                            onClick={() => { setMode('register'); setError(''); }}
                        >
                            Register
                        </button>
                    </div>

                    {/* Error Message */}
                    {error && <div className="error-message">{error}</div>}

                    {/* Sign In Form */}
                    {mode === 'signin' && (
                        <form className="auth-form" onSubmit={handleSignIn}>
                            <h2 className="form-title">Welcome Back</h2>
                            <p className="form-subtitle">Sign in to continue your journey</p>

                            <div className="form-group">
                                <label>Email</label>
                                <input
                                    type="email"
                                    placeholder="Enter your email"
                                    value={signInData.email}
                                    onChange={(e) => setSignInData({ ...signInData, email: e.target.value })}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Password</label>
                                <input
                                    type="password"
                                    placeholder="Enter your password"
                                    value={signInData.password}
                                    onChange={(e) => setSignInData({ ...signInData, password: e.target.value })}
                                    required
                                />
                            </div>

                            <button type="submit" className="submit-btn" disabled={isLoading}>
                                {isLoading ? 'Signing in...' : 'Sign In'}
                            </button>
                        </form>
                    )}

                    {/* Register Form */}
                    {mode === 'register' && (
                        <form className="auth-form" onSubmit={handleRegister}>
                            <h2 className="form-title">Create Account</h2>
                            <p className="form-subtitle">Start your journey to landing your dream job</p>

                            <div className="form-section">
                                <h3>Account Details</h3>
                                <div className="form-group">
                                    <label>Email *</label>
                                    <input
                                        type="email"
                                        placeholder="Enter your email"
                                        value={registerData.email}
                                        onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                                        required
                                    />
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Password *</label>
                                        <input
                                            type="password"
                                            placeholder="Min 6 characters"
                                            value={registerData.password}
                                            onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                                            required
                                            minLength={6}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Confirm Password *</label>
                                        <input
                                            type="password"
                                            placeholder="Confirm password"
                                            value={registerData.confirmPassword}
                                            onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                                            required
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="form-section">
                                <h3>Resume *</h3>
                                <div className="file-upload">
                                    <input
                                        type="file"
                                        accept=".pdf"
                                        onChange={handleFileChange}
                                        id="resume-upload"
                                    />
                                    <label htmlFor="resume-upload" className="file-label">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                            <polyline points="17 8 12 3 7 8" />
                                            <line x1="12" y1="3" x2="12" y2="15" />
                                        </svg>
                                        {registerData.resume ? registerData.resume.name : 'Upload PDF Resume'}
                                    </label>
                                </div>
                            </div>

                            <div className="form-section">
                                <h3>Optional Information</h3>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Work Authorization</label>
                                        <input
                                            type="text"
                                            placeholder="e.g., Authorized to work in US"
                                            value={registerData.work_authorization}
                                            onChange={(e) => setRegisterData({ ...registerData, work_authorization: e.target.value })}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Location Preference</label>
                                        <input
                                            type="text"
                                            placeholder="e.g., San Francisco Bay Area"
                                            value={registerData.location_preference}
                                            onChange={(e) => setRegisterData({ ...registerData, location_preference: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Remote Preference</label>
                                        <select
                                            value={registerData.remote_preference}
                                            onChange={(e) => setRegisterData({ ...registerData, remote_preference: e.target.value })}
                                        >
                                            <option value="">Select preference</option>
                                            <option value="Remote">Remote</option>
                                            <option value="Hybrid">Hybrid</option>
                                            <option value="On-site">On-site</option>
                                            <option value="Flexible">Flexible</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Start Date</label>
                                        <input
                                            type="text"
                                            placeholder="e.g., June 2026"
                                            value={registerData.start_date}
                                            onChange={(e) => setRegisterData({ ...registerData, start_date: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Relocation</label>
                                        <select
                                            value={registerData.relocation}
                                            onChange={(e) => setRegisterData({ ...registerData, relocation: e.target.value })}
                                        >
                                            <option value="">Select option</option>
                                            <option value="Open to relocation">Open to relocation</option>
                                            <option value="Not open to relocation">Not open to relocation</option>
                                            <option value="Depends on location">Depends on location</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Salary Expectation</label>
                                        <input
                                            type="text"
                                            placeholder="e.g., $80k-$100k"
                                            value={registerData.salary_expectation}
                                            onChange={(e) => setRegisterData({ ...registerData, salary_expectation: e.target.value })}
                                        />
                                    </div>
                                </div>
                            </div>

                            <button type="submit" className="submit-btn" disabled={isLoading}>
                                {isLoading ? 'Creating account...' : 'Create Account'}
                            </button>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
