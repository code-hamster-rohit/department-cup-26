/**
 * ADMIN TUG OF WAR SCORING CONTROLS
 */
window.AdminTugOfWar = {
  init: function(sendAction) {
    document.querySelectorAll('.btn-tow-award, .btn-tow-win').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const winner = btn.dataset.team || btn.dataset.winner || 'team_a';
        const durInput = document.getElementById('tow-duration-input');
        const cAInput = document.getElementById('tow-cautions-a');
        const cBInput = document.getElementById('tow-cautions-b');

        sendAction({
          type: 'pull_win',
          winner: winner,
          duration: durInput ? durInput.value.trim() : '1m 15s',
          cautions_a: cAInput ? parseInt(cAInput.value, 10) : 0,
          cautions_b: cBInput ? parseInt(cBInput.value, 10) : 0
        });
      });
    });
  },

  updateState: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elPull = document.getElementById('admin-tow-cur-pull');
    if (elPull) elPull.textContent = score.current_pull || 1;
  }
};
