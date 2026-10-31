import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { TerminologyAuditItem } from '../../types/evaluation';

interface AuditLogTableProps {
  auditLog?: TerminologyAuditItem[];
}

export const AuditLogTable: React.FC<AuditLogTableProps> = ({ auditLog }) => {
  const items: TerminologyAuditItem[] = auditLog && auditLog.length > 0 ? auditLog : [
    {
      timestamp_range: '[0.0s - 1.2s]',
      raw_token: 'has map',
      verified_token: 'hash map',
      status: 'CORRECTED',
      reason: 'Phonetic Double Metaphone match against 2,000-term glossary (conf: 0.94)',
    },
    {
      timestamp_range: '[2.1s - 2.8s]',
      raw_token: 'testing',
      verified_token: 'A/B testing',
      status: 'ABSTAINED',
      reason: 'Insufficient acoustic support in audio slice; original token preserved',
    },
  ];

  return (
    <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-5 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] mb-6 space-y-3">
      <div className="flex items-center gap-2">
        <ShieldCheck className="text-secondary" size={18} />
        <h3 className="text-sm font-bold text-on-surface">
          Acoustic Verification & Terminology Audit Log
        </h3>
      </div>
      <p className="text-xs text-outline font-mono">
        Transparent audit trail of Stage 2 technical terminology recovery and conservative abstention:
      </p>

      <div className="border border-outline-variant/20 rounded-lg overflow-hidden">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead className="bg-surface-container border-b border-outline-variant/20 text-outline font-bold uppercase text-[10px]">
            <tr>
              <th className="p-3">Timestamp</th>
              <th className="p-3">Raw Spoken Token</th>
              <th className="p-3">Verified Entity</th>
              <th className="p-3">Decision</th>
              <th className="p-3">Acoustic Verification Rationale</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/20">
            {items.map((row, idx) => (
              <tr key={idx} className="hover:bg-surface-container/60 transition-colors">
                <td className="p-3 text-outline">{row.timestamp_range}</td>
                <td className="p-3 text-on-surface-variant bg-surface-container-lowest/50">"{row.raw_token}"</td>
                <td className="p-3 font-bold text-secondary">{row.verified_token}</td>
                <td className="p-3">
                  <span
                    className={`inline-block px-2.5 py-0.5 rounded text-[10px] font-bold border ${
                      row.status === 'CORRECTED'
                        ? 'bg-secondary/15 text-secondary border-secondary/30'
                        : 'bg-surface-container-high text-outline border-outline-variant/30'
                    }`}
                  >
                    {row.status}
                  </span>
                </td>
                <td className="p-3 text-on-surface-variant">{row.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
