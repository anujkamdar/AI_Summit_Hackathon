import express from 'express';
import mongoose from 'mongoose';
import dotenv from 'dotenv';
import cors from 'cors';

dotenv.config();

const app = express();
const PORT = 4000;

// Middleware
app.use(cors());  // Enable CORS for all origins
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// MongoDB Connection
const connectDB = async () => {
  try {
    await mongoose.connect("mongodb+srv://anujkamdar2006_db_user:UlaKG5HA8btbBmvm@sandboxportal.gsimmxy.mongodb.net/agno");
    console.log('✅ MongoDB Atlas connected successfully');
  } catch (error) {
    console.error('❌ MongoDB connection error:', error);
    process.exit(1);
  }
};

// ==================== SCHEMAS ====================

// Job Schema
const jobSchema = new mongoose.Schema({
  title: { type: String, required: true },
  company: { type: String, required: true },
  location: { type: String, required: true },
  type: { type: String, required: true }, // Full-time, Part-time, Contract
  salary: { type: String, required: true },
  description: { type: String, required: true },
  requiredSkills: [{ type: String }],
  visa_sponsorship: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now }
});

const Job = mongoose.model('Job', jobSchema);

// Application Schema
const applicationSchema = new mongoose.Schema({
  jobId: { type: mongoose.Schema.Types.ObjectId, ref: 'Job', required: true },
  applicantName: { type: String, required: true },
  applicantEmail: { type: String, default: '' },
  resumeText: { type: String, required: true },
  coverLetter: { type: String, required: true },
  matchScore: { type: Number, default: 0 },
  status: { type: String, default: 'pending' }, // pending, reviewed, accepted, rejected
  source: { type: String, default: 'manual' }, // manual, auto-apply-agent
  timestamp: { type: Date, default: Date.now }
});

const Application = mongoose.model('Application', applicationSchema);

// ==================== CHAOS MODE HELPER ====================
let chaosConfig = {
  enabled: true,
  failureRate: 0.2  // 20% failure rate
};

const chaosMode = () => {
  if (!chaosConfig.enabled) return null;
  
  if (Math.random() < chaosConfig.failureRate) {
    const errors = [
      { status: 500, message: 'Internal Server Error - Service temporarily unavailable', retryable: true },
      { status: 429, message: 'Too Many Requests - Rate limit exceeded', retryable: true },
      { status: 503, message: 'Service Unavailable - Database connection lost', retryable: true },
      { status: 502, message: 'Bad Gateway - Upstream server error', retryable: true }
    ];
    return errors[Math.floor(Math.random() * errors.length)];
  }
  return null;
};

// ==================== CHAOS MODE CONFIG ENDPOINTS ====================

// GET /api/chaos - Get current chaos mode config
app.get('/api/chaos', (req, res) => {
  res.json({
    success: true,
    config: chaosConfig
  });
});

// POST /api/chaos - Update chaos mode config
app.post('/api/chaos', (req, res) => {
  const { enabled, failureRate } = req.body;
  
  if (typeof enabled === 'boolean') {
    chaosConfig.enabled = enabled;
  }
  if (typeof failureRate === 'number' && failureRate >= 0 && failureRate <= 1) {
    chaosConfig.failureRate = failureRate;
  }
  
  res.json({
    success: true,
    message: 'Chaos mode config updated',
    config: chaosConfig
  });
});

// ==================== API ENDPOINTS ====================

// GET /api/jobs - Return all job listings
app.get('/api/jobs', async (req, res) => {
  try {
    const jobs = await Job.find().sort({ createdAt: -1 });
    res.json({
      success: true,
      count: jobs.length,
      data: jobs
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch jobs',
      message: error.message
    });
  }
});

// POST /api/apply-job - Submit job application with CHAOS MODE and retry info (for auto-apply agent)
app.post('/api/apply-job', async (req, res) => {
  try {
    // CHAOS MODE: Random failure based on config
    const chaos = chaosMode();
    if (chaos) {
      return res.status(chaos.status).json({
        success: false,
        error: chaos.message,
        chaos: true,
        retryable: chaos.retryable,
        retryAfter: Math.floor(Math.random() * 3) + 1 // Suggest retry after 1-3 seconds
      });
    }

    const { jobId, applicantName, applicantEmail, resumeText, coverLetter, matchScore } = req.body;

    // Validation
    if (!jobId || !applicantName || !coverLetter) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        required: ['jobId', 'applicantName', 'coverLetter'],
        optional: ['applicantEmail', 'resumeText', 'matchScore']
      });
    }

    // Check if job exists
    const job = await Job.findById(jobId);
    if (!job) {
      return res.status(404).json({
        success: false,
        error: 'Job not found',
        retryable: false
      });
    }

    // Check for duplicate application
    const existingApplication = await Application.findOne({ 
      jobId, 
      applicantName 
    });
    
    if (existingApplication) {
      return res.status(409).json({
        success: false,
        error: 'Duplicate application - already applied to this job',
        applicationId: existingApplication._id,
        retryable: false
      });
    }

    // Create application
    const application = new Application({
      jobId,
      applicantName,
      applicantEmail: applicantEmail || '',
      resumeText: resumeText || 'Resume provided via auto-apply agent',
      coverLetter,
      matchScore: matchScore || 0,
      status: 'pending',
      source: 'auto-apply-agent'
    });

    await application.save();

    // Return receipt
    res.status(201).json({
      success: true,
      message: 'Application submitted successfully',
      receipt: {
        applicationId: application._id,
        jobId: jobId,
        jobTitle: job.title,
        company: job.company,
        applicantName: application.applicantName,
        submittedAt: application.timestamp,
        status: application.status,
        matchScore: matchScore
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to submit application',
      message: error.message,
      retryable: true
    });
  }
});

// GET /api/applied-jobs - Get all applied jobs with full details
app.get('/api/applied-jobs', async (req, res) => {
  try {
    const { applicantName, applicantEmail, status } = req.query;
    
    // Build filter
    const filter = {};
    if (applicantName) filter.applicantName = applicantName;
    if (applicantEmail) filter.applicantEmail = applicantEmail;
    if (status) filter.status = status;
    
    const applications = await Application.find(filter)
      .populate('jobId', 'title company location type salary requiredSkills visa_sponsorship description')
      .sort({ timestamp: -1 });
    
    // Format response with full job details
    const appliedJobs = applications.map(app => ({
      applicationId: app._id,
      appliedAt: app.timestamp,
      status: app.status,
      applicantName: app.applicantName,
      applicantEmail: app.applicantEmail,
      coverLetterPreview: app.coverLetter ? app.coverLetter.substring(0, 200) + '...' : '',
      matchScore: app.matchScore || 0,
      source: app.source || 'manual',
      job: app.jobId ? {
        jobId: app.jobId._id,
        title: app.jobId.title,
        company: app.jobId.company,
        location: app.jobId.location,
        type: app.jobId.type,
        salary: app.jobId.salary,
        requiredSkills: app.jobId.requiredSkills,
        visa_sponsorship: app.jobId.visa_sponsorship
      } : null
    }));
    
    res.json({
      success: true,
      count: appliedJobs.length,
      data: appliedJobs
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch applied jobs',
      message: error.message
    });
  }
});

// GET /api/applications - Return all applications (legacy endpoint)
app.get('/api/applications', async (req, res) => {
  try {
    const applications = await Application.find()
      .populate('jobId', 'title company location')
      .sort({ timestamp: -1 });
    
    res.json({
      success: true,
      count: applications.length,
      data: applications
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch applications',
      message: error.message
    });
  }
});

// POST /seed - Seed database with 50 dummy jobs
app.post('/seed', async (req, res) => {
  try {
    // Clear existing data
    await Job.deleteMany({});
    await Application.deleteMany({});

    // Generate 50 realistic dummy jobs
    const companies = [
      'Google', 'Meta', 'Amazon', 'Microsoft', 'Apple', 'Netflix', 
      'Tesla', 'Spotify', 'Adobe', 'Salesforce', 'Oracle', 'IBM',
      'Stripe', 'Airbnb', 'Uber', 'Lyft', 'Twitter', 'LinkedIn',
      'Dropbox', 'Slack', 'Zoom', 'Shopify', 'Square', 'PayPal'
    ];

    const roles = [
      'Software Engineer', 'Senior Software Engineer', 'Staff Engineer',
      'Frontend Developer', 'Backend Developer', 'Full Stack Developer',
      'DevOps Engineer', 'Data Scientist', 'ML Engineer', 'Product Manager',
      'Engineering Manager', 'Solutions Architect', 'QA Engineer',
      'Security Engineer', 'Platform Engineer', 'Site Reliability Engineer',
      'Mobile Developer', 'Cloud Engineer', 'AI Research Scientist',
      'Technical Lead', 'Principal Engineer', 'Data Engineer'
    ];

    const locations = [
      'Remote', 'San Francisco, CA', 'New York, NY', 'Seattle, WA',
      'Austin, TX', 'Boston, MA', 'Los Angeles, CA', 'Chicago, IL',
      'Denver, CO', 'Atlanta, GA', 'Remote (US)', 'Remote (Global)',
      'London, UK', 'Toronto, Canada', 'Berlin, Germany', 'Singapore'
    ];

    const types = ['Full-time', 'Full-time', 'Full-time', 'Contract', 'Part-time'];

    const skillSets = [
      ['JavaScript', 'React', 'Node.js', 'MongoDB'],
      ['Python', 'Django', 'PostgreSQL', 'AWS'],
      ['Java', 'Spring Boot', 'MySQL', 'Kubernetes'],
      ['TypeScript', 'Vue.js', 'GraphQL', 'Docker'],
      ['Go', 'Microservices', 'Redis', 'gRPC'],
      ['Python', 'TensorFlow', 'PyTorch', 'Pandas'],
      ['C++', 'System Design', 'Linux', 'Performance'],
      ['React Native', 'iOS', 'Android', 'Firebase'],
      ['Kubernetes', 'Terraform', 'CI/CD', 'Jenkins'],
      ['AWS', 'Azure', 'GCP', 'Cloud Architecture']
    ];

    const dummyJobs = [];

    for (let i = 0; i < 50; i++) {
      const company = companies[Math.floor(Math.random() * companies.length)];
      const role = roles[Math.floor(Math.random() * roles.length)];
      const location = locations[Math.floor(Math.random() * locations.length)];
      const type = types[Math.floor(Math.random() * types.length)];
      const skills = skillSets[Math.floor(Math.random() * skillSets.length)];
      const salary = `$${Math.floor(Math.random() * 150 + 80)}k - $${Math.floor(Math.random() * 100 + 150)}k`;
      const visaSponsorship = Math.random() > 0.4; // 60% offer visa sponsorship

      dummyJobs.push({
        title: role,
        company: company,
        location: location,
        type: type,
        salary: salary,
        description: `We are seeking a talented ${role} to join our ${company} team in ${location}. You will work on cutting-edge projects, collaborate with world-class engineers, and have the opportunity to make a significant impact. This is a ${type.toLowerCase()} position with competitive compensation and benefits.`,
        requiredSkills: skills,
        visa_sponsorship: visaSponsorship
      });
    }

    await Job.insertMany(dummyJobs);

    res.json({
      success: true,
      message: '✅ Database seeded successfully',
      jobsCreated: 50
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to seed database',
      message: error.message
    });
  }
});

// ==================== FRONTEND VIEW ====================

// GET / - Serve HTML page with job listings
app.get('/', async (req, res) => {
  try {
    const jobs = await Job.find().sort({ createdAt: -1 });
    
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sandbox Job Portal</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
      min-height: 100vh;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      overflow: hidden;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
    }
    .header h1 {
      font-size: 2.5em;
      margin-bottom: 10px;
    }
    .header p {
      font-size: 1.1em;
      opacity: 0.9;
    }
    .stats {
      display: flex;
      justify-content: space-around;
      padding: 20px;
      background: #f8f9fa;
      border-bottom: 1px solid #dee2e6;
    }
    .stat {
      text-align: center;
    }
    .stat-value {
      font-size: 2em;
      font-weight: bold;
      color: #667eea;
    }
    .stat-label {
      color: #6c757d;
      font-size: 0.9em;
      margin-top: 5px;
    }
    .table-container {
      overflow-x: auto;
      padding: 20px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th {
      background: #667eea;
      color: white;
      padding: 15px;
      text-align: left;
      font-weight: 600;
      position: sticky;
      top: 0;
    }
    td {
      padding: 15px;
      border-bottom: 1px solid #dee2e6;
    }
    tr:hover {
      background: #f8f9fa;
    }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 0.85em;
      font-weight: 500;
    }
    .badge-remote {
      background: #d4edda;
      color: #155724;
    }
    .badge-onsite {
      background: #cce5ff;
      color: #004085;
    }
    .badge-visa {
      background: #fff3cd;
      color: #856404;
    }
    .skills {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .skill-tag {
      background: #e9ecef;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.8em;
      color: #495057;
    }
    .footer {
      text-align: center;
      padding: 20px;
      background: #f8f9fa;
      color: #6c757d;
      font-size: 0.9em;
    }
    .no-jobs {
      text-align: center;
      padding: 60px 20px;
      color: #6c757d;
    }
    .no-jobs h2 {
      margin-bottom: 20px;
    }
    .seed-btn {
      background: #667eea;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 6px;
      font-size: 1em;
      cursor: pointer;
      margin-top: 20px;
    }
    .seed-btn:hover {
      background: #5568d3;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🚀 Sandbox Job Portal</h1>
      <p>Hackathon Edition - AI Agent Testing Platform</p>
    </div>
    
    <div class="stats">
      <div class="stat">
        <div class="stat-value">${jobs.length}</div>
        <div class="stat-label">Total Jobs</div>
      </div>
      <div class="stat">
        <div class="stat-value">${jobs.filter(j => j.location.includes('Remote')).length}</div>
        <div class="stat-label">Remote Positions</div>
      </div>
      <div class="stat">
        <div class="stat-value">${jobs.filter(j => j.visa_sponsorship).length}</div>
        <div class="stat-label">Visa Sponsorship</div>
      </div>
    </div>

    ${jobs.length === 0 ? `
    <div class="no-jobs">
      <h2>No jobs available yet!</h2>
      <p>Click the button below to seed the database with 50 sample jobs.</p>
      <form method="POST" action="/seed">
        <button type="submit" class="seed-btn">Seed Database</button>
      </form>
    </div>
    ` : `
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Company</th>
            <th>Location</th>
            <th>Type</th>
            <th>Salary</th>
            <th>Skills</th>
            <th>Visa</th>
          </tr>
        </thead>
        <tbody>
          ${jobs.map(job => `
          <tr>
            <td><strong>${job.title}</strong></td>
            <td>${job.company}</td>
            <td>
              <span class="badge ${job.location.includes('Remote') ? 'badge-remote' : 'badge-onsite'}">
                ${job.location}
              </span>
            </td>
            <td>${job.type}</td>
            <td>${job.salary}</td>
            <td>
              <div class="skills">
                ${job.requiredSkills.slice(0, 3).map(skill => 
                  `<span class="skill-tag">${skill}</span>`
                ).join('')}
                ${job.requiredSkills.length > 3 ? `<span class="skill-tag">+${job.requiredSkills.length - 3}</span>` : ''}
              </div>
            </td>
            <td>
              ${job.visa_sponsorship ? '<span class="badge badge-visa">✓ Available</span>' : '✗'}
            </td>
          </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    `}

    <div class="footer">
      <p>🎯 Sandbox Job Portal API | Chaos Mode: ${chaosConfig.enabled ? `${chaosConfig.failureRate * 100}% Random Failures Enabled` : 'Disabled'}</p>
      <p>Built for Hackathon - AI Agent Testing Environment</p>
    </div>
  </div>
</body>
</html>
    `;

    res.send(html);
  } catch (error) {
    res.status(500).send(`
      <h1>Error loading jobs</h1>
      <p>${error.message}</p>
    `);
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    chaos: 'enabled',
    failureRate: '20%'
  });
});

// ==================== START SERVER ====================

const startServer = async () => {
  await connectDB();
  app.listen(PORT, () => {
    console.log(`\n🚀 Sandbox Job Portal Server Running`);
    console.log(`📍 Port: ${PORT}`);
    console.log(`🌐 Frontend: http://localhost:${PORT}`);
    console.log(`🔌 API: http://localhost:${PORT}/api/jobs`);
    console.log(`⚠️  CHAOS MODE: ${chaosConfig.enabled ? 'Enabled' : 'Disabled'} (${chaosConfig.failureRate * 100}% failure rate)`);
    console.log(`\n📝 API Endpoints:`);
    console.log(`   GET  /              - Frontend view`);
    console.log(`   GET  /api/jobs      - List all jobs`);
    console.log(`   POST /api/apply-job - Submit application (with chaos + retry)`);
    console.log(`   GET  /api/applied-jobs - View all applied jobs with details`);
    console.log(`   GET  /api/applications - View all applications (legacy)`);
    console.log(`   GET  /api/chaos     - Get chaos mode config`);
    console.log(`   POST /api/chaos     - Update chaos mode config`);
    console.log(`   POST /seed          - Seed 50 dummy jobs`);
    console.log(`   GET  /health        - Health check\n`);
  });
};

startServer();
