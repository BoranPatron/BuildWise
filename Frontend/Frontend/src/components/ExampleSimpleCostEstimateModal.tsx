import React, { useState } from 'react';
import SimpleCostEstimateModal from './components/SimpleCostEstimateModal';

// Beispiel-Komponente für die Verwendung der SimpleCostEstimateModal
export default function ExampleUsage() {
  const [showCostEstimateModal, setShowCostEstimateModal] = useState(false);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold text-white mb-4">
        SimpleCostEstimateModal Beispiel
      </h1>
      
      <button
        onClick={() => setShowCostEstimateModal(true)}
        className="px-6 py-3 bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold rounded-lg hover:shadow-lg transition-all duration-200"
      >
        Kostenschätzung öffnen
      </button>

      <SimpleCostEstimateModal
        isOpen={showCostEstimateModal}
        onClose={() => setShowCostEstimateModal(false)}
        tradeId={123}
        tradeTitle="Elektroinstallation EG"
        projectId={456}
      />
    </div>
  );
}

