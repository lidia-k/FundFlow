import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Results from './pages/Results';
import SaltRulesDashboard from './pages/SaltRulesDashboard';
import SaltRulesUpload from './pages/SaltRulesUpload';
import RuleSetDetails from './pages/RuleSetDetails';
import { Toaster } from '@/components/ui';

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/results/:sessionId" element={<Results />} />
          <Route path="/salt-rules" element={<SaltRulesDashboard />} />
          <Route path="/salt-rules/upload" element={<SaltRulesUpload />} />
          <Route path="/salt-rules/:ruleSetId" element={<RuleSetDetails />} />
        </Routes>
      </Layout>
      <Toaster />
    </div>
  );
}

export default App;