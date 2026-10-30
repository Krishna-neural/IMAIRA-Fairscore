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
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs mb-6">
      <div className="flex items-center gap-2 mb-1">
        <ShieldCheck className="text-emerald-700" size={18} />
        <h3 className="text-base font-bold text-[#101C35]">
          Acoustic Verification & Terminology Audit Log
        </h3>
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Transparent audit trail of Stage 2 technical terminology recovery and conservative abstention:
      </p>

      <div className="border border-slate-200 rounded overflow-hidden">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-bold uppercase text-[10px]">
            <tr>
              <th className="p-2.5">Timestamp</th>
              <th className="p-2.5">Raw ASR Token</th>
              <th className="p-2.5">Verified Technical Term</th>
              <th className="p-2.5">Decision</th>
              <th className="p-2.5">Acoustic Verification Rationale</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50">
                <td className="p-2.5 font-mono text-slate-500">{row.timestamp_range}</td>
                <td className="p-2.5 font-mono text-slate-700 bg-slate-50">"{row.raw_token}"</td>
                <td className="p-2.5 font-bold text-slate-900">{row.verified_token}</td>
                <td className="p-2.5">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[10px] font-extrabold ${
                      row.status === 'CORRECTED'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                    }`}
                  >
                    {row.status}
                  </span>
                </td>
                <td className="p-2.5 text-slate-600">{row.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
