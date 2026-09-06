const express = require('express');
const axios = require('axios');
const router = express.Router();
const multer = require('multer');
const pool = require('../db/index');

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }
});

const getPipelineUrl = () => process.env.AI_PIPELINE_URL || 'https://weha-health-voice-ai-pipeline.onrender.com';

const MAX_MESSAGE_LENGTH = 2000;

async function saveMessage(sessionId, role, content, language) {
  await pool.query(
    'INSERT INTO conversations (session_id, role, content, language) VALUES ($1, $2, $3, $4)',
    [sessionId, role, content, language || 'en']
  );
}

async function getHistory(sessionId, limit = 6) {
  const result = await pool.query(
    `SELECT role, content FROM (
       SELECT role, content, created_at FROM conversations
       WHERE session_id = $1 ORDER BY created_at DESC LIMIT $2
     ) AS recent ORDER BY created_at ASC`,
    [sessionId, limit]
  );
  return result.rows.map(r => ({ sender: r.role, text: r.content }));
}

// POST /api/voice/chat — full voice flow: audio -> transcribe -> RAG answer
router.post('/chat', upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'Audio file is required' });
  }
  try {
    const selectedLanguage = req.body.language || 'en';
    const sessionId = req.body.sessionId;

    if (!sessionId) {
      return res.status(400).json({ error: 'sessionId is required' });
    }

    const pipelineBaseUrl = getPipelineUrl();

    const transcribeForm = new FormData();
    const audioBlob = new Blob([req.file.buffer], { type: req.file.mimetype });
    transcribeForm.append('file', audioBlob, req.file.originalname || 'audio.wav');

    const transcribeResponse = await axios.post(
      `${pipelineBaseUrl}/transcribe?language=${selectedLanguage}`,
      transcribeForm,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 45000 }
    );

    const transcribedText = transcribeResponse.data.text || '';
    if (!transcribedText.trim()) {
      return res.status(422).json({ error: 'Could not understand the audio. Please try again.' });
    }

    if (transcribedText.length > MAX_MESSAGE_LENGTH) {
      return res.status(400).json({ error: 'Transcribed audio is too long. Please keep messages concise.' });
    }

    await saveMessage(sessionId, 'user', transcribedText, selectedLanguage);
    const history = await getHistory(sessionId);

    const askResponse = await axios.post(`${pipelineBaseUrl}/ask`, {
      question: transcribedText,
      language: selectedLanguage,
      history: history
    }, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 45000
    });

    const answer = askResponse.data.answer || '';
    await saveMessage(sessionId, 'bot', answer, selectedLanguage);

    return res.json({
      success: true,
      transcribed: transcribedText,
      response: answer,
      sources: askResponse.data.sources || [],
      disclaimer: 'This is not medical advice. Please see a doctor for diagnosis and treatment.'
    });
  } catch (error) {
    console.error('Voice chat failure:', error.response?.data || error.message);
    return res.status(500).json({ error: 'Voice chat failed', message: error.message });
  }
});

// POST /api/voice/text-chat — typed text flow with history
router.post('/text-chat', async (req, res) => {
  try {
    const { message, language, sessionId } = req.body;

    if (!message || !sessionId) {
      return res.status(400).json({ error: 'Message and sessionId are required' });
    }

    if (message.length > MAX_MESSAGE_LENGTH) {
      return res.status(400).json({ error: 'Message is too long. Please keep messages under 2000 characters.' });
    }

    await saveMessage(sessionId, 'user', message, language);
    const history = await getHistory(sessionId);

    const pipelineBaseUrl = getPipelineUrl();
    const response = await axios.post(`${pipelineBaseUrl}/ask`, {
      question: message,
      language: language || 'en',
      history: history
    }, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 45000
    });

    const answer = response.data.answer || '';
    await saveMessage(sessionId, 'bot', answer, language);

    return res.json({
      success: true,
      transcribed: message,
      response: answer,
      sources: response.data.sources || [],
      disclaimer: 'This is not medical advice. Please see a doctor for diagnosis and treatment.'
    });
  } catch (error) {
    console.error('Text chat failure:', error.response?.data || error.message);
    return res.status(500).json({ error: 'Text chat failed', message: error.message });
  }
});

// POST /api/voice/speak — text -> audio
router.post('/speak', async (req, res) => {
  try {
    const { text } = req.body;
    if (!text || text.length > MAX_MESSAGE_LENGTH) {
      return res.status(400).json({ error: 'Invalid or oversized text for speech synthesis.' });
    }

    const pipelineBaseUrl = getPipelineUrl();

    const pythonResponse = await axios.post(`${pipelineBaseUrl}/speak`, req.body, {
      headers: { 'Content-Type': 'application/json' },
      responseType: 'text',
      timeout: 45000
    });

    try {
      const jsonData = JSON.parse(pythonResponse.data);
      if (jsonData && jsonData.audio) {
        const audioBuffer = Buffer.from(jsonData.audio, 'base64');
        res.setHeader('Content-Type', 'audio/mpeg');
        res.setHeader('Content-Length', audioBuffer.length);
        return res.send(audioBuffer);
      }
    } catch (e) {
      // Not JSON — fall through to raw response
    }

    return res.send(Buffer.from(pythonResponse.data, 'binary'));

  } catch (error) {
    console.error('Voice proxy /speak failure:', error.response?.data || error.message);
    return res.status(500).json({
      error: 'Proxy text-to-speech generation failure',
      message: error.message
    });
  }
});

// GET /api/voice/history/:sessionId — fetch full conversation history
router.get('/history/:sessionId', async (req, res) => {
  try {
    const { sessionId } = req.params;
    if (!sessionId) {
      return res.status(400).json({ error: 'sessionId is required' });
    }

    const result = await pool.query(
      'SELECT role, content, language, created_at FROM conversations WHERE session_id = $1 ORDER BY created_at ASC',
      [sessionId]
    );

    return res.json({ success: true, messages: result.rows });
  } catch (error) {
    console.error('History fetch failure:', error.message);
    return res.status(500).json({ error: 'Failed to fetch history', message: error.message });
  }
});

// DELETE /api/voice/history/:sessionId — delete all messages for a session
router.delete('/history/:sessionId', async (req, res) => {
  try {
    const { sessionId } = req.params;
    if (!sessionId) {
      return res.status(400).json({ error: 'sessionId is required' });
    }

    const result = await pool.query(
      'DELETE FROM conversations WHERE session_id = $1',
      [sessionId]
    );

    return res.json({ success: true, deleted: result.rowCount });
  } catch (error) {
    console.error('History delete failure:', error.message);
    return res.status(500).json({ error: 'Failed to delete history', message: error.message });
  }
});

module.exports = router;