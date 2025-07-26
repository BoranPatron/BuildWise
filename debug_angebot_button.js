// Debug-Skript für "Angebot abgeben" Button
console.log('🔧 Debug-Skript für Angebot abgeben Button geladen');

// Funktion zum Testen des Button-Klicks
function testAngebotButton() {
  console.log('🔧 Teste Angebot abgeben Button...');
  
  // Prüfe ob TradeDetailsModal vorhanden ist
  const tradeDetailsModal = document.querySelector('[data-testid="trade-details-modal"]');
  console.log('🔧 TradeDetailsModal gefunden:', !!tradeDetailsModal);
  
  // Prüfe ob Button vorhanden ist
  const angebotButton = document.querySelector('button[onclick*="handleSubmitQuote"]');
  console.log('🔧 Angebot Button gefunden:', !!angebotButton);
  
  // Prüfe alle Buttons mit "Angebot" Text
  const allButtons = document.querySelectorAll('button');
  const angebotButtons = Array.from(allButtons).filter(btn => 
    btn.textContent?.includes('Angebot') || 
    btn.textContent?.includes('angebot')
  );
  console.log('🔧 Alle Angebot-Buttons gefunden:', angebotButtons.length);
  angebotButtons.forEach((btn, index) => {
    console.log(`🔧 Button ${index}:`, btn.textContent, btn.onclick);
  });
  
  // Prüfe React-Komponenten
  console.log('🔧 React-Komponenten Status:');
  console.log('🔧 - showTradeDetailsModal:', window.showTradeDetailsModal);
  console.log('🔧 - showCostEstimateForm:', window.showCostEstimateForm);
  console.log('🔧 - selectedTradeForCostEstimate:', window.selectedTradeForCostEstimate);
  
  return {
    tradeDetailsModal: !!tradeDetailsModal,
    angebotButton: !!angebotButton,
    angebotButtons: angebotButtons.length
  };
}

// Funktion zum Simulieren eines Button-Klicks
function simulateAngebotButtonClick() {
  console.log('🔧 Simuliere Angebot Button Klick...');
  
  const angebotButtons = document.querySelectorAll('button');
  const angebotButton = Array.from(angebotButtons).find(btn => 
    btn.textContent?.includes('Angebot abgeben')
  );
  
  if (angebotButton) {
    console.log('🔧 Button gefunden, simuliere Klick...');
    angebotButton.click();
    return true;
  } else {
    console.log('❌ Angebot Button nicht gefunden');
    return false;
  }
}

// Event-Listener für Debugging
document.addEventListener('click', (e) => {
  if (e.target.textContent?.includes('Angebot abgeben')) {
    console.log('🔧 Angebot abgeben Button geklickt!');
    console.log('🔧 Event Target:', e.target);
    console.log('🔧 Event:', e);
  }
});

// Debug-Funktionen global verfügbar machen
window.testAngebotButton = testAngebotButton;
window.simulateAngebotButtonClick = simulateAngebotButtonClick;

console.log('🔧 Debug-Funktionen verfügbar:');
console.log('🔧 - testAngebotButton()');
console.log('🔧 - simulateAngebotButtonClick()'); 