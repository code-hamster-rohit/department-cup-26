/**
 * AUDIENCE CARROM LIVE DOM UPDATER
 */
window.AudienceCarrom = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elA = document.getElementById('aud-carrom-a');
    if (elA) elA.textContent = score.score_team_a || 0;

    const elB = document.getElementById('aud-carrom-b');
    if (elB) elB.textContent = score.score_team_b || 0;

    const elBoard = document.getElementById('aud-carrom-board');
    if (elBoard) elBoard.textContent = `🎯 Board ${score.current_board || 1} of 8`;
  }
};
