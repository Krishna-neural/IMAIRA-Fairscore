import React, { useState } from 'react';
import { Navbar } from './components/common/Navbar';
import { LandingPage } from './pages/LandingPage';
import { SetupPage } from './pages/SetupPage';
import { InterviewPage } from './pages/InterviewPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { JudgeConsolePage } from './pages/JudgeConsolePage';
import { CandidateConfig } from './types/interview';
import { EvaluationResult } from './types/evaluation';
import { integrityMonitor } from './services/integrityMonitor';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'home' | 'setup' | 'interview' | 'evaluation' | 'judge'>('home');
  const [candidateConfig, setCandidateConfig] = useState<CandidateConfig>({
    name: 'Candidate',
    domain: 'Software and Computer Science Fundamentals',
    difficulty: 'Intermediate',
    numQuestions: 3,
  });
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null);

  const restriction = integrityMonitor.getRestrictionState();

  const handleStartSession = (config: CandidateConfig, stream: MediaStream | null) => {
    setCandidateConfig(config);
    setCameraStream(stream);
    setCurrentView('interview');
  };

  const handleFinishEvaluation = (result: EvaluationResult) => {
    setEvaluationResult(result);
    setCurrentView('evaluation');
  };

  return (
    <div className="min-h-screen bg-[#10131c] text-[#e0e2ef] font-sans flex flex-col selection:bg-primary-container selection:text-on-primary-container">
      <Navbar
        currentView={currentView}
        onNavigate={(view) => setCurrentView(view as any)}
        isRestricted={restriction.isRestricted}
      />

      <main className="flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 max-w-[1440px]">
        {currentView === 'home' && (
          <LandingPage
            onStartInterview={() => setCurrentView('setup')}
            onExploreJudge={() => setCurrentView('judge')}
          />
        )}

        {currentView === 'setup' && (
          <SetupPage
            onStartSession={handleStartSession}
            isRestricted={restriction.isRestricted}
          />
        )}

        {currentView === 'interview' && (
          <InterviewPage
            config={candidateConfig}
            initialCameraStream={cameraStream}
            onFinishEvaluation={handleFinishEvaluation}
          />
        )}

        {currentView === 'evaluation' && (
          <EvaluationPage
            result={evaluationResult}
            candidateName={candidateConfig.name}
            domain={candidateConfig.domain}
            onStartNew={() => setCurrentView('setup')}
            onExploreJudge={() => setCurrentView('judge')}
          />
        )}

        {currentView === 'judge' && <JudgeConsolePage />}
      </main>
    </div>
  );
};

export default App;
