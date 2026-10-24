/**
 * AUDIENCE FOOTBALL LIVE DOM UPDATER
 * Updates football scores, period badges, and events on live broadcasts.
 */
window.AudienceFootball = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elA = document.getElementById('aud-fb-score-a');
    if (elA) elA.textContent = score.team_a_score || 0;

    const elB = document.getElementById('aud-fb-score-b');
    if (elB) elB.textContent = score.team_b_score || 0;

    const elPeriod = document.getElementById('aud-fb-period');
    if (elPeriod) elPeriod.textContent = score.period_label || `Half ${score.half || 1}`;
  }
};
