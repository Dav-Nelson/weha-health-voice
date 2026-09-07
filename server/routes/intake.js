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

router.post('/turn', upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'Audio file is required' });
  }

  try {
    const language = req.body.language || 'en';
    const sessionId = req.body.sessionId;
    const existingFields = req.body.existingFields ? JSON.parse(req.body.existingFields) : {};
    const lat = req.body.lat ? parseFloat(req.body.lat) : null;
    const lng = req.body.lng ? parseFloat(req.body.lng) : null;

    if (!sessionId) {
      return res.status(400).json({ error: 'sessionId is required' });
    }

    const pipelineBaseUrl = getPipelineUrl();

    const transcribeForm = new FormData();
    const audioBlob = new Blob([req.file.buffer], { type: req.file.mimetype });
    transcribeForm.append('file', audioBlob, req.file.originalname || 'audio.wav');

    const transcribeResponse = await axios.post(
      `${pipelineBaseUrl}/transcribe?language=${language}&model=auto`,
      transcribeForm,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 45000 }
    );

    const transcript = transcribeResponse.data.text || '';
    if (!transcript.trim()) {
      return res.status(422).json({ error: 'Could not understand the audio. Please try again.' });
    }

    const intakeResponse = await axios.post(`${pipelineBaseUrl}/intake/process`, {
      transcript,
      language,
      existing_fields: existingFields,
      session_id: sessionId,
      lat,
      lng
    }, { timeout: 45000 });

    const result = intakeResponse.data;

    if (result.status === 'complete') {
      await pool.query(
        `INSERT INTO triage_records (session_id, language, fields, urgency, matched_signs, guidance, status, updated_at)
         VALUES ($1, $2, $3, $4, $5, $6, 'complete', NOW())
         ON CONFLICT (session_id) DO UPDATE SET
           fields = $3, urgency = $4, matched_signs = $5, guidance = $6, status = 'complete', updated_at = NOW()`,
        [sessionId, language, result.fields, result.urgency, JSON.stringify(result.matched_signs), result.guidance]
      );
    } else {
      await pool.query(
        `INSERT INTO triage_records (session_id, language, fields, status, updated_at)
         VALUES ($1, $2, $3, 'in_progress', NOW())
         ON CONFLICT (session_id) DO UPDATE SET
           fields = $3, status = 'in_progress', updated_at = NOW()`,
        [sessionId, language, result.fields]
      );
    }

    return res.json({
      success: true,
      transcript,
      transcription_engine: transcribeResponse.data.engine || 'unknown',
      ...result
    });

  } catch (error) {
    console.error('Intake turn failure:', error.response?.data || error.message);
    return res.status(500).json({ error: 'Intake processing failed', message: error.message });
  }
});

router.get('/:sessionId', async (req, res) => {
  try {
    const { sessionId } = req.params;
    const result = await pool.query(
      'SELECT * FROM triage_records WHERE session_id = $1',
      [sessionId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Session not found' });
    }
    return res.json({ success: true, record: result.rows[0] });
  } catch (error) {
    console.error('Intake fetch failure:', error.message);
    return res.status(500).json({ error: 'Failed to fetch session', message: error.message });
  }
});

module.exports = router;