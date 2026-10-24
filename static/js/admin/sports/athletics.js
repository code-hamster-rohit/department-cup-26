/**
 * ADMIN ATHLETICS DISTANCE SCORING CONTROLS
 */
window.AdminAthletics = {
  init: function(sendAction) {
    const form = document.getElementById('form-athletics-attempt');
    if (form) {
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        const nameInput = document.getElementById('ath-name-input') || document.getElementById('ath-name');
        const deptSelect = document.getElementById('ath-dept-select') || document.getElementById('ath-dept');
        const bibInput = document.getElementById('ath-bib-input') || document.getElementById('ath-bib');
        const typeSelect = document.getElementById('ath-attempt-type');
        const distInput = document.getElementById('ath-distance-input') || document.getElementById('ath-dist');
        const foulBox = document.getElementById('ath-foul-checkbox') || document.getElementById('ath-foul');

        const isFoul = foulBox ? foulBox.checked : false;
        const dist = distInput ? parseFloat(distInput.value || 0) : 0;

        if (!isFoul && (!dist || dist <= 0)) {
          alert("Please enter a valid distance in meters, or check 'Foul Attempt'.");
          return;
        }

        sendAction({
          type: 'record_attempt',
          name: nameInput ? nameInput.value.trim() : 'Athlete',
          department: deptSelect ? deptSelect.value : 'AMSC',
          bib: bibInput ? bibInput.value.trim() : '',
          attempt_type: typeSelect ? typeSelect.value : 'official',
          distance: dist,
          is_foul: isFoul
        });

        // Reset inputs
        if (distInput) distInput.value = '';
        if (foulBox) foulBox.checked = false;
      });
    }
  },

  updateState: function(match) {
    // State is reflected in leaderboard
  }
};
