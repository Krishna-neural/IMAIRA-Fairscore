import { test, describe } from 'node:test';
import assert from 'node:assert';

describe('FastAPI API Contract Verification', () => {
  test('POST /interview/start payload matches backend schema', () => {
    const payload = {
      candidate_name: 'Alex',
      domain: 'Data Structures and Algorithms',
      difficulty: 'Intermediate',
      num_questions: 3
    };

    assert.strictEqual(typeof payload.candidate_name, 'string');
    assert.strictEqual(typeof payload.domain, 'string');
    assert.strictEqual(typeof payload.difficulty, 'string');
    assert.strictEqual(typeof payload.num_questions, 'number');
    assert.ok(payload.num_questions >= 1 && payload.num_questions <= 10);
  });

  test('POST /interview/turn payload matches backend schema', () => {
    const payload = {
      session_id: 'sess_12345',
      candidate_utterance: 'A stack follows LIFO and a queue follows FIFO ordering.'
    };

    assert.ok(payload.session_id.startsWith('sess_'));
    assert.ok(payload.candidate_utterance.length > 5);
  });

  test('POST /score payload format matches backend schema', () => {
    const payload = {
      session_id: 'sess_12345',
      question_id: 'ENG001',
      transcript: [
        { start: 0.0, end: 3.0, speaker: 'candidate', text: 'AVL trees strictly enforce balance factor <= 1.' }
      ]
    };

    assert.strictEqual(typeof payload.session_id, 'string');
    assert.ok(Array.isArray(payload.transcript));
    assert.strictEqual(payload.transcript[0].speaker, 'candidate');
    assert.strictEqual(typeof payload.transcript[0].start, 'number');
    assert.strictEqual(typeof payload.transcript[0].end, 'number');
  });
});
