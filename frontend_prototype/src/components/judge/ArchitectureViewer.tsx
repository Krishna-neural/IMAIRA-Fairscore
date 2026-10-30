import React, { useState, useEffect } from 'react';
import { Layers, X } from 'lucide-react';
import { apiService } from '../../services/apiService';

export const ArchitectureViewer: React.FC = () => {
  const [components, setComponents] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiService.fetchArchitecture();
        setComponents(data.components || []);
      } catch (err) {
        console.error('[Architecture] Error fetching components:', err);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-4">
      <div className="p-4 bg-white border border-slate-200 rounded-lg">
        <h3 className="text-base font-bold text-[#101C35]">
          10-Node Interactive System Architecture Pipeline
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Click on any architectural pipeline node to inspect input/output schemas, module implementation paths, and unit test coverage:
        </p>
      </div>

      <div className="space-y-2">
        {components.map((node, idx) => (
          <div
            key={node.id}
            onClick={() => setSelectedNode(node)}
            className="p-3.5 bg-white border border-slate-200 rounded-lg shadow-xs hover:border-[#2457A6] hover:shadow-sm cursor-pointer transition-all flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <span className="w-7 h-7 rounded-full bg-blue-50 text-blue-800 text-xs font-bold border border-blue-200 flex items-center justify-center">
                0{idx + 1}
              </span>
              <div>
                <h4 className="text-sm font-bold text-[#101C35]">{node.name}</h4>
                <div className="text-[11px] font-mono text-blue-700">{node.technology}</div>
                <p className="text-xs text-slate-500">{node.purpose}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                {node.category}
              </span>
              <button className="px-2.5 py-1 text-xs font-semibold bg-slate-50 hover:bg-slate-100 border border-slate-300 rounded text-slate-700">
                Inspect 🔍
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Node Detail Inspection Modal */}
      {selectedNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="w-full max-w-xl bg-white rounded-lg shadow-xl border border-slate-300 overflow-hidden">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-bold text-sm text-[#101C35]">
                {selectedNode.name} — Architecture Specification
              </h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 text-slate-400 hover:text-slate-700 rounded"
              >
                <X size={16} />
              </button>
            </div>

            <div className="p-5 space-y-3.5 text-xs text-slate-700 max-h-[75vh] overflow-y-auto">
              <div>
                <span className="font-bold text-blue-900 uppercase tracking-wide block mb-0.5">
                  Functional Purpose
                </span>
                <p className="text-sm text-slate-800">{selectedNode.purpose}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded font-mono">
                  <span className="font-bold text-slate-500 uppercase block text-[10px]">Input Schema</span>
                  <div className="text-slate-800 mt-1">{selectedNode.input}</div>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded font-mono">
                  <span className="font-bold text-slate-500 uppercase block text-[10px]">Output Schema</span>
                  <div className="text-slate-800 mt-1">{selectedNode.output}</div>
                </div>
              </div>

              <div>
                <span className="font-bold text-blue-900 uppercase tracking-wide block mb-0.5">
                  Technology Stack
                </span>
                <div className="font-mono text-slate-800">{selectedNode.technology}</div>
              </div>

              <div>
                <span className="font-bold text-blue-900 uppercase tracking-wide block mb-0.5">
                  Implementation Path
                </span>
                <div className="font-mono text-blue-700 font-bold">{selectedNode.implementation_file}</div>
              </div>

              <div>
                <span className="font-bold text-blue-900 uppercase tracking-wide block mb-0.5">
                  Associated API Endpoint
                </span>
                <div className="font-mono text-emerald-700 font-bold">{selectedNode.api_endpoint}</div>
              </div>

              <div>
                <span className="font-bold text-blue-900 uppercase tracking-wide block mb-0.5">
                  Test Verification
                </span>
                <div className="font-mono text-amber-800">{selectedNode.test_coverage}</div>
              </div>

              <div className="p-2.5 bg-amber-50 border border-amber-200 rounded text-amber-900">
                <span className="font-bold uppercase text-[10px] block mb-0.5">Known Limitation</span>
                <p>{selectedNode.limitations}</p>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSelectedNode(null)}
                className="px-3.5 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-semibold rounded"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
