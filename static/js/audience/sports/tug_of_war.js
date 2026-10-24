/**
 * AUDIENCE TUG OF WAR LIVE DOM UPDATER
 */
window.AudienceTugOfWar = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elA = document.getElementById('aud-tow-pulls-a');
    if (elA) elA.textContent = score.pulls_team_a || 0;

    const elB = document.getElementById('aud-tow-pulls-b');
    if (elB) elB.textContent = score.pulls_team_b || 0;

    const elPull = document.getElementById('aud-tow-pull-info');
    if (elPull) elPull.textContent = `Best of 3 Pulls · Pull ${score.current_pull || 1}`;
  }
};
