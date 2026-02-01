import React, { useState } from 'react';
import Galaxy from './Galaxy';
import { Rocket, LogIn, UserPlus, Upload, X } from 'lucide-react';
import './LandingPage.css';

export default function LandingPage({ onLogin }) {
    const [showAuthModal, setShowAuthModal] = useState(false);
    const [authMode, setAuthMode] = useState('signin'); // 'signin' or 'signup'
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        resume: null,
        work_authorization: '',
        location_preference: '',
        remote_preference: '',
        start_date: '',
        relocation: '',
        salary_expectation: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const API_BASE_URL = 'http://localhost:8000';

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            setFormData(prev => ({ ...prev, resume: file }));
            setError('');
        } else {
            setError('Please upload a PDF file');
        }
    };

    const handleSignIn = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/signin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Sign in failed');
            }

            // Store token
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_email', data.user.email);

            // Call onLogin callback
            if (onLogin) {
                onLogin(data);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSignUp = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (!formData.resume) {
            setError('Please upload your resume');
            setLoading(false);
            return;
        }

        try {
            const formDataToSend = new FormData();
            formDataToSend.append('email', formData.email);
            formDataToSend.append('password', formData.password);
            formDataToSend.append('resume', formData.resume);

            // Add optional FAQ answers if provided
            if (formData.work_authorization) formDataToSend.append('work_authorization', formData.work_authorization);
            if (formData.location_preference) formDataToSend.append('location_preference', formData.location_preference);
            if (formData.remote_preference) formDataToSend.append('remote_preference', formData.remote_preference);
            if (formData.start_date) formDataToSend.append('start_date', formData.start_date);
            if (formData.relocation) formDataToSend.append('relocation', formData.relocation);
            if (formData.salary_expectation) formDataToSend.append('salary_expectation', formData.salary_expectation);

            const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
                method: 'POST',
                body: formDataToSend
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Sign up failed');
            }

            // Store token
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_email', data.user.email);

            // Call onLogin callback
            if (onLogin) {
                onLogin(data);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="landing-page">
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

            {/* Content Overlay */}
            <div className="content-overlay">
                {/* Hero Section */}
                <div className="hero-section">
                    <div className="hero-content">
                        <div className="badge-pill">
                            <div className="badge-lines"></div>
                            AI-Powered Applications
                        </div>
                        <h1 className="hero-title">
                            Land your dream job,
                            <br />
                            young padawan.
                        </h1>

                        <div className="cta-buttons">
                            <button
                                className="cta-button primary"
                                onClick={() => {
                                    setAuthMode('signup');
                                    setShowAuthModal(true);
                                }}
                            >
                                Get Started
                            </button>
                            <button
                                className="cta-button secondary"
                                onClick={() => {
                                    setAuthMode('signin');
                                    setShowAuthModal(true);
                                }}
                            >
                                Learn More
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Auth Modal */}
            {showAuthModal && (
                <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <button
                            className="modal-close"
                            onClick={() => setShowAuthModal(false)}
                        >
                            <X size={24} />
                        </button>

                        <div className="modal-header">
                            <h2>{authMode === 'signin' ? 'Welcome Back' : 'Create Account'}</h2>
                            <p>{authMode === 'signin' ? 'Sign in to continue' : 'Start your automated job search'}</p>
                        </div>

                        {error && (
                            <div className="error-message">
                                {error}
                            </div>
                        )}

                        <form onSubmit={authMode === 'signin' ? handleSignIn : handleSignUp}>
                            <div className="form-group">
                                <label>Email</label>
                                <input
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleInputChange}
                                    required
                                    placeholder="your.email@example.com"
                                />
                            </div>

                            <div className="form-group">
                                <label>Password</label>
                                <input
                                    type="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleInputChange}
                                    required
                                    placeholder="••••••••"
                                    minLength={6}
                                />
                            </div>

                            {authMode === 'signup' && (
                                <>
                                    <div className="form-group">
                                        <label>Resume (PDF) *</label>
                                        <div className="file-upload">
                                            <input
                                                type="file"
                                                id="resume"
                                                accept=".pdf"
                                                onChange={handleFileChange}
                                                required
                                            />
                                            <label htmlFor="resume" className="file-upload-label">
                                                <Upload size={20} />
                                                {formData.resume ? formData.resume.name : 'Choose PDF file'}
                                            </label>
                                        </div>
                                    </div>

                                    <div className="faq-section">
                                        <h3>Optional: Help us find better matches</h3>

                                        <div className="form-group">
                                            <label>Work Authorization</label>
                                            <input
                                                type="text"
                                                name="work_authorization"
                                                value={formData.work_authorization}
                                                onChange={handleInputChange}
                                                placeholder="e.g., US Citizen, Work Visa, etc."
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label>Location Preference</label>
                                            <input
                                                type="text"
                                                name="location_preference"
                                                value={formData.location_preference}
                                                onChange={handleInputChange}
                                                placeholder="e.g., San Francisco, New York"
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label>Remote Preference</label>
                                            <select
                                                name="remote_preference"
                                                value={formData.remote_preference}
                                                onChange={handleInputChange}
                                            >
                                                <option value="">Select...</option>
                                                <option value="Remote Only">Remote Only</option>
                                                <option value="Hybrid">Hybrid</option>
                                                <option value="On-site">On-site</option>
                                                <option value="Any">Any</option>
                                            </select>
                                        </div>

                                        <div className="form-group">
                                            <label>Earliest Start Date</label>
                                            <input
                                                type="date"
                                                name="start_date"
                                                value={formData.start_date}
                                                onChange={handleInputChange}
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label>Willing to Relocate?</label>
                                            <select
                                                name="relocation"
                                                value={formData.relocation}
                                                onChange={handleInputChange}
                                            >
                                                <option value="">Select...</option>
                                                <option value="Yes">Yes</option>
                                                <option value="No">No</option>
                                                <option value="Maybe">Maybe</option>
                                            </select>
                                        </div>

                                        <div className="form-group">
                                            <label>Salary Expectation</label>
                                            <input
                                                type="text"
                                                name="salary_expectation"
                                                value={formData.salary_expectation}
                                                onChange={handleInputChange}
                                                placeholder="e.g., $80,000 - $100,000"
                                            />
                                        </div>
                                    </div>
                                </>
                            )}

                            <button
                                type="submit"
                                className="submit-button"
                                disabled={loading}
                            >
                                {loading ? 'Processing...' : (authMode === 'signin' ? 'Sign In' : 'Create Account')}
                            </button>
                        </form>

                        <div className="modal-footer">
                            {authMode === 'signin' ? (
                                <p>
                                    Don't have an account?{' '}
                                    <button onClick={() => setAuthMode('signup')}>Sign up</button>
                                </p>
                            ) : (
                                <p>
                                    Already have an account?{' '}
                                    <button onClick={() => setAuthMode('signin')}>Sign in</button>
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
