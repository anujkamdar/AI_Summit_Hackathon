import React from 'react';
import { useNavigate } from 'react-router-dom';
import Galaxy from './Galaxy';
import './LandingPage.css';

export default function LandingPage() {
    const navigate = useNavigate();

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

                        {/* CTA Buttons */}
                        <div className="cta-buttons">
                            <button 
                                className="cta-button primary"
                                onClick={() => navigate('/auth?mode=signin')}
                            >
                                Sign In
                            </button>
                            <button 
                                className="cta-button secondary"
                                onClick={() => navigate('/auth?mode=register')}
                            >
                                Register
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
