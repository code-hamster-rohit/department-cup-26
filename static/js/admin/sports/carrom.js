/**
 * ADMIN CARROM SCORING CONTROLS
 */
window.AdminCarrom = {
  init: function(sendAction) {
    // Points buttons
    document.querySelectorAll('.btn-carrom-add').forEach(function(btn) {
      btn.addEventListener('click', function() {
        sendAction({
          type: 'points',
          team: btn.dataset.team,
          delta: parseInt(btn.dataset.delta || btn.dataset.pts || 1, 10)
        });
      });
    });

    // Next Board
    const btnNext = document.getElementById('btn-next-carrom-board');
    if (btnNext) {
      btnNext.addEventListener('click', function() {
        if (confirm("Conclude current board and proceed to next board?")) {
          sendAction({ type: 'end_board' });
        }
      });
    }
  },

  updateState: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elA = document.getElementById('admin-carrom-pts-a');
    if (elA) elA.textContent = score.score_team_a || 0;

    const elB = document.getElementById('admin-carrom-pts-b');
    if (elB) elB.textContent = score.score_team_b || 0;

    const elBoard = document.getElementById('admin-carrom-cur-board');
    if (elBoard) elBoard.textContent = score.current_board || 1;
  }
};
