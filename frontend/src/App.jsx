import { useState, useEffect } from 'react'
import { api } from './api'
import Step1Job from './components/Step1Job'
import Step2Import from './components/Step2Import'
import Step3Devices from './components/Step3Devices'
import Step4Preview from './components/Step4Preview'
import Step5Run from './components/Step5Run'

function App() {
  const [step, setStep] = useState(1);
  const [job, setJob] = useState(null);
  const [runId, setRunId] = useState(null);

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  const renderStep = () => {
    switch (step) {
      case 1: return <Step1Job onNext={(newJob) => { setJob(newJob); nextStep(); }} />;
      case 2: return <Step2Import jobId={job.id} onNext={nextStep} onPrev={prevStep} />;
      case 3: return <Step3Devices jobId={job.id} onNext={nextStep} onPrev={prevStep} />;
      case 4: return <Step4Preview jobId={job.id} onNext={nextStep} onPrev={prevStep} />;
      case 5: return <Step5Run jobId={job.id} onReset={() => { setStep(1); setJob(null); }} />;
      default: return <div>Unknown Step</div>;
    }
  };

  const steps = ["Job", "Import", "Ports", "Preview", "Run"];

  return (
    <div className="container">
      <header className="text-center mt-4">
        <h1>Wizard: Switch Baseline</h1>
        <p style={{ color: 'var(--text-muted)' }}>Automate your network deployments with ease.</p>
      </header>

      <div className="wizard-steps card mt-4" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', position: 'relative' }}>
          {steps.map((label, i) => (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2 }}>
              <div className={`step ${step === i + 1 ? 'active' : step > i + 1 ? 'completed' : ''}`}>
                {step > i + 1 ? '✓' : i + 1}
              </div>
              <span style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: step >= i + 1 ? 'var(--text-color)' : 'var(--text-muted)' }}>
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <main>
        {renderStep()}
      </main>
    </div >
  )
}

export default App
