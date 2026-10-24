/**
 * AUDIENCE BASKETBALL SHOOTOUT LIVE DOM UPDATER
 */
window.AudienceBasketball = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elA = document.getElementById('aud-bb-pts-a');
    if (elA) elA.textContent = score.score_team_a || 0;

    const elB = document.getElementById('aud-bb-pts-b');
    if (elB) elB.textContent = score.score_team_b || 0;

    const elRem = document.getElementById('aud-bb-remaining');
    if (elRem) {
      elRem.textContent = `Remaining Shots: ${score.remaining_shots_a || 0} (${match.team_a.abbr}) · ${score.remaining_shots_b || 0} (${match.team_b.abbr})`;
    }
  }
};
