from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class WordTiming(BaseModel):
    word: str
    start: float
    end: float
    conf: Optional[float] = None
    corrected_from: Optional[str] = None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return {
            "word": self.word,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "conf": round(self.conf, 4) if self.conf is not None else None,
            "corrected_from": self.corrected_from
        }

class SuspiciousSpan(BaseModel):
    span_id: str
    start_idx: int
    end_idx: int
    t_start: float
    t_end: float
    original_text: str
    candidate_term: str
    avg_conf: float
    min_conf: float
    fuzzy_score: float
    phonetic_match: bool
    combined_score: float
    reason: str

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "start_idx": self.start_idx,
            "end_idx": self.end_idx,
            "t_start": round(self.t_start, 2),
            "t_end": round(self.t_end, 2),
            "original_text": self.original_text,
            "candidate_term": self.candidate_term,
            "avg_conf": round(self.avg_conf, 4),
            "min_conf": round(self.min_conf, 4),
            "fuzzy_score": round(self.fuzzy_score, 1),
            "phonetic_match": self.phonetic_match,
            "combined_score": round(self.combined_score, 1),
            "reason": self.reason
        }

class PassResult(BaseModel):
    pass_name: str
    text: str
    words: List[WordTiming]
    latency_sec: float
    hotwords_used: Optional[str] = None

class TwoPassTranscription(BaseModel):
    transcript: List[WordTiming]
    text: str
    pass_a: PassResult
    pass_b: PassResult
    candidate_terms: List[str] = Field(default_factory=list)
    audio_duration_sec: float
    language: str
    language_probability: float
    rtf: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def text_between(self, t_start: float, t_end: float) -> str:
        """Returns the space-joined text of words occurring between t_start and t_end."""
        words_in_range = [
            w.word.strip() for w in self.transcript
            if (w.end > t_start and w.start < t_end)
        ]
        return " ".join(words_in_range)

    def to_contract_dict(self) -> Dict[str, Any]:
        """Conforms directly to the IMAIRA-Fairscore hours 0-4 data contract."""
        return {
            "transcript": [w.model_dump() for w in self.transcript],
            "text": self.text,
            "audio_duration_sec": round(self.audio_duration_sec, 3),
            "language": self.language,
            "rtf": round(self.rtf, 4),
            "candidate_terms": self.candidate_terms
        }

class RecoveryAuditEntry(BaseModel):
    span_id: str
    t_start: float
    t_end: float
    original_text: str
    candidate_term: str
    redecoded_text: str
    decision: str  # "CORRECTED" | "ABSTAINED"
    reason: str
    original_conf: float
    recheck_conf: Optional[float] = None
    applied_correction: Optional[str] = None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "t_start": round(self.t_start, 2),
            "t_end": round(self.t_end, 2),
            "original_text": self.original_text,
            "candidate_term": self.candidate_term,
            "redecoded_text": self.redecoded_text,
            "decision": self.decision,
            "reason": self.reason,
            "original_conf": round(self.original_conf, 4),
            "recheck_conf": round(self.recheck_conf, 4) if self.recheck_conf is not None else None,
            "applied_correction": self.applied_correction
        }

class RecoveryResult(BaseModel):
    original_transcript: List[WordTiming]
    corrected_transcript: List[WordTiming]
    original_text: str
    corrected_text: str
    audit_log: List[RecoveryAuditEntry] = Field(default_factory=list)
    spans_detected: int = 0
    spans_corrected: int = 0
    spans_abstained: int = 0
    audio_duration_sec: float = 0.0
    recovery_latency_sec: float = 0.0

    def text_between(self, t_start: float, t_end: float) -> str:
        words_in_range = [
            w.word.strip() for w in self.corrected_transcript
            if (w.end > t_start and w.start < t_end)
        ]
        return " ".join(words_in_range)

    def to_contract_dict(self) -> Dict[str, Any]:
        return {
            "transcript": [w.model_dump() for w in self.corrected_transcript],
            "original_transcript": [w.model_dump() for w in self.original_transcript],
            "text": self.corrected_text,
            "original_text": self.original_text,
            "audit_log": [e.model_dump() for e in self.audit_log],
            "spans_detected": self.spans_detected,
            "spans_corrected": self.spans_corrected,
            "spans_abstained": self.spans_abstained,
            "audio_duration_sec": round(self.audio_duration_sec, 3),
            "recovery_latency_sec": round(self.recovery_latency_sec, 3)
        }

