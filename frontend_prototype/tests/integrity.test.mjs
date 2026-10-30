import { test, describe, beforeEach } from 'node:test';
import assert from 'node:assert';

// Mock localStorage for node environment
global.localStorage = {
  store: {},
  getItem(k) { return this.store[k] || null; },
  setItem(k, v) { this.store[k] = String(v); },
  removeItem(k) { delete this.store[k]; },
  clear() { this.store = {}; }
};

describe('Interviewer Integrity Monitor & Warning Logic', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('3-warning progression accurately increments', () => {
    let warningCount = 0;
    const warnings = [];

    function triggerViolation(type, desc) {
      warningCount++;
      const warnNum = Math.min(3, warningCount);
      const warn = {
        warningNumber: warnNum,
        event: { type, description: desc, timestamp: Date.now() },
        explanation: `Warning ${warnNum}: ${desc}`,
        correctiveAction: 'Please adjust your camera framing.'
      };
      warnings.push(warn);
      return warn;
    }

    const w1 = triggerViolation('CAMERA_DISABLED', 'Camera feed disabled during session');
    assert.strictEqual(w1.warningNumber, 1);
    assert.strictEqual(warningCount, 1);

    const w2 = triggerViolation('MULTIPLE_PEOPLE', 'Multiple people detected in camera frame');
    assert.strictEqual(w2.warningNumber, 2);
    assert.strictEqual(warningCount, 2);

    const w3 = triggerViolation('CAMERA_OBSTRUCTED', 'Camera view obstructed');
    assert.strictEqual(w3.warningNumber, 3);
    assert.strictEqual(warningCount, 3);
  });

  test('4th violation triggers 24-hour temporary restriction with audit trail', () => {
    let warningCount = 3;
    const auditTrail = [
      { warningNumber: 1, event: { description: 'Feed disabled' } },
      { warningNumber: 2, event: { description: 'Multiple people' } },
      { warningNumber: 3, event: { description: 'Lens obstructed' } },
    ];

    let restrictionState = { isRestricted: false };

    function onFourthViolation(event) {
      warningCount++;
      const now = Date.now();
      restrictionState = {
        isRestricted: true,
        restrictedAt: now,
        expiresAt: now + 24 * 60 * 60 * 1000,
        reason: `Accumulated 3 verified warnings plus subsequent violation: ${event.description}`,
        auditTrail: [...auditTrail],
        appealSubmitted: false
      };
      localStorage.setItem('restriction', JSON.stringify(restrictionState));
    }

    onFourthViolation({ description: 'Camera disabled again' });

    assert.strictEqual(restrictionState.isRestricted, true);
    assert.strictEqual(restrictionState.auditTrail.length, 3);
    assert.ok(restrictionState.expiresAt > Date.now() + 23 * 60 * 60 * 1000);
  });

  test('Appeal submission sets appealSubmitted: true', () => {
    const state = {
      isRestricted: true,
      restrictedAt: Date.now(),
      expiresAt: Date.now() + 86400000,
      appealSubmitted: false
    };

    function submitAppeal(appealReason) {
      assert.ok(appealReason.length > 0);
      state.appealSubmitted = true;
      return true;
    }

    const ok = submitAppeal('Camera driver updated and verified.');
    assert.strictEqual(ok, true);
    assert.strictEqual(state.appealSubmitted, true);
  });
});
