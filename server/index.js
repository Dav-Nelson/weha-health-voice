const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

require('./db/index');

const app = express();
const PORT = process.env.PORT || 5000;

app.set('trust proxy', 1);

app.use(helmet());

const explicitAllowedOrigins = [
  'https://healthbridge-africa.vercel.app',
  'http://localhost:3000'
];

app.use(cors({
  origin: (origin, callback) => {
    if (!origin || explicitAllowedOrigins.includes(origin) || origin.endsWith('.vercel.app')) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '1mb' }));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests. Please wait a few minutes and try again.' }
});

const aiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'AI request limit reached. Please wait a few minutes and try again.' }
});

app.use(limiter);

app.head('/health', (req, res) => res.status(200).end());
app.get('/health', (req, res) => res.status(200).json({ status: 'ok' }));

app.use('/api/health', require('./routes/health'));
app.use('/api/voice', aiLimiter, require('./routes/voice'));
app.use('/api/intake', aiLimiter, require('./routes/intake'));

app.get('/', (req, res) => {
  res.json({
    message: 'Weha Health API is running',
    version: '1.0.0',
    status: 'ok'
  });
});

app.listen(PORT, () => {
  console.log(`Weha Health server running on port ${PORT}`);
});

module.exports = app;