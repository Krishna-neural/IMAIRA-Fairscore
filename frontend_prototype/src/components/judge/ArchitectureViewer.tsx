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
      <div className="p-5 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)]">
        <h3 className="text-sm font-bold text-on-surface">
          10-Node Interactive System Architecture Pipeline
        </h3>
        <p className="text-xs text-outline font-mono mt-0.5">
          Click on any architectural pipeline node to inspect input/output schemas, module implementation paths, and unit test coverage:
        </p>
      </div>

      <div className="space-y-2.5">
        {components.map((node, idx) => (
          <div
            key={node.id}
            onClick={() => setSelectedNode(node)}
            className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-sm hover:border-secondary/60 hover:bg-surface-container cursor-pointer transition-all flex items-center justify-between font-mono"
          >
            <div className="flex items-center gap-3">
              <span className="w-8 h-8 rounded-lg bg-surface-container-high text-secondary text-xs font-bold border border-outline-variant/30 flex items-center justify-center shrink-0">
                0{idx + 1}
              </span>
              <div>
                <h4 className="text-sm font-bold text-on-surface font-sans">{node.name}</h4>
                <div className="text-[11px] text-secondary font-mono">{node.technology}</div>
                <p className="text-xs text-outline font-sans">{node.purpose}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-mono bg-surface-container text-on-surface-variant border border-outline-variant/30">
                {node.category}
              </span>
              <button className="px-3 py-1 text-xs font-mono font-semibold bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant/40 rounded-lg text-primary transition-colors">
                Inspect 🔍
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Detail Modal */}
      {selectedNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-container-lowest/80 backdrop-blur-md animate-fadeIn">
          <div className="w-full max-w-2xl bg-surface-container-low border border-outline-variant/30 rounded-2xl shadow-[0_24px_60px_rgba(0,0,0,0.85)] p-6 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/20">
              <div className="flex items-center gap-2 text-secondary">
                <Layers size={18} />
                <h3 className="text-base font-bold text-on-surface font-sans">{selectedNode.name}</h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 text-outline hover:text-on-surface"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <span className="text-outline uppercase text-[10px] font-bold block">Purpose</span>
                <p className="text-on-surface font-sans leading-relaxed text-xs mt-0.5">{selectedNode.purpose}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20">
                  <span className="text-outline uppercase text-[10px] font-bold block">Input Schema</span>
                  <span className="text-primary text-[11px] block mt-0.5">{selectedNode.input}</span>
                </div>
                <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20">
                  <span className="text-outline uppercase text-[10px] font-bold block">Output Schema</span>
                  <span className="text-secondary text-[11px] block mt-0.5">{selectedNode.output}</span>
                </div>
              </div>

              <div>
                <span className="text-outline uppercase text-[10px] font-bold block">Implementation File</span>
                <span className="text-secondary text-[11px]">{selectedNode.implementation_file}</span>
              </div>

              <div>
                <span className="text-outline uppercase text-[10px] font-bold block">API Endpoint</span>
                <span className="text-primary text-[11px]">{selectedNode.api_endpoint}</span>
              </div>

              <div>
                <span className="text-outline uppercase text-[10px] font-bold block">Test Verification</span>
                <span className="text-tertiary text-[11px]">{selectedNode.test_coverage}</span>
              </div>

              {selectedNode.limitations && (
                <div className="p-3 bg-surface-container border border-amber-500/30 rounded-lg text-amber-300">
                  <span className="uppercase text-[10px] font-bold block">Operational Limitations</span>
                  <p className="text-[11px] mt-0.5 leading-relaxed font-sans">{selectedNode.limitations}</p>
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedNode(null)}
                className="px-4 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface text-xs font-mono font-semibold"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
