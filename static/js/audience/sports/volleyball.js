/**
 * AUDIENCE VOLLEYBALL LIVE DOM UPDATER
 */
window.AudienceVolleyball = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elSetsA = document.getElementById('aud-sets-a');
    if (elSetsA) elSetsA.textContent = score.sets_team_a || 0;

    const elSetsB = document.getElementById('aud-sets-b');
    if (elSetsB) elSetsB.textContent = score.sets_team_b || 0;

    const curSet = (score.set_scores && score.set_scores.length > 0) ? score.set_scores[score.set_scores.length - 1] : { team_a: 0, team_b: 0 };

    const elPtsA = document.getElementById('aud-pts-a');
    if (elPtsA) {
      elPtsA.innerHTML = `${curSet.team_a || 0} ${score.server !== 'team_b' ? '<span class="server-indicator" title="Serving" id="aud-server-a">🏐</span>' : ''}`;
    }

    const elPtsB = document.getElementById('aud-pts-b');
    if (elPtsB) {
      elPtsB.innerHTML = `${score.server === 'team_b' ? '<span class="server-indicator" title="Serving" id="aud-server-b">🏐</span>' : ''} ${curSet.team_b || 0}`;
    }

    const elSetInfo = document.getElementById('aud-set-info');
    if (elSetInfo) {
      elSetInfo.textContent = `Set ${score.current_set || 1} (Target: ${score.points_to_win_set || 25} pts)`;
    }

    const elDeuce = document.getElementById('aud-deuce-badge');
    if (elDeuce) {
      if (score.in_deuce) elDeuce.classList.remove('d-none');
      else elDeuce.classList.add('d-none');
    }
  }
};
