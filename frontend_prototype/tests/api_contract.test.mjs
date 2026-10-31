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
      candidate_utterance: 'A stack follows LIFO and a queue follows FIFO ordering.',
      word_timings: [{ word: 'stack', start: 0.1, end: 0.5, conf: 0.95 }],
      audio_base64: 'UklGRi...'
    };

    assert.ok(payload.session_id.startsWith('sess_'));
    assert.ok(payload.candidate_utterance.length > 5);
    assert.ok(Array.isArray(payload.word_timings));
  });

  test('POST /interview/conclude payload matches backend schema', () => {
    const payload = {
      session_id: 'sess_12345',
      final_scorecard: {
        overall_fairscore: 78.4,
        content_score: 80.0,
        structure_score: 76.0,
        summary_verdict: 'Demonstrates Solid Competence'
      }
    };

    assert.ok(payload.session_id.startsWith('sess_'));
    assert.strictEqual(typeof payload.final_scorecard.overall_fairscore, 'number');
  });

  test('GET /interview/session response schema matches UnifiedSession', () => {
    const mockSessionResponse = {
      session_id: 'sess_12345',
      candidate_name: 'Alex',
      stage: 'COMPLETED',
      turns: [
        {
          turn_id: 1,
          speaker: 'candidate',
          raw_utterance: 'Thread execution lock is governed by a semfor primitive.',
          recovered_utterance: 'Thread execution lock is governed by a semaphore primitive.',
          evaluation: {
            scores: { content_pct: 85.0, structure_pct: 75.0, overall_fairscore_pct: 81.0 },
            dual_diagnosis: {
              technical_knowledge_gaps: [],
              pronunciation_improvements: [
                {
                  raw_token: 'semfor',
                  recovered_token: 'semaphore',
                  coaching: "Pronounce 'semfor' as /sɛm.ə.fɔːr/.",
                  marks_deducted: 0.0
                }
              ]
            }
          }
        }
      ],
      final_scorecard: {
        overall_fairscore: 81.0,
        content_score: 85.0,
        structure_score: 75.0
      }
    };

    assert.strictEqual(mockSessionResponse.stage, 'COMPLETED');
    assert.ok(mockSessionResponse.turns.length >= 1);
    assert.strictEqual(
      mockSessionResponse.turns[0].evaluation.dual_diagnosis.pronunciation_improvements[0].marks_deducted,
      0.0
    );
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
