/**
 * AUDIENCE BADMINTON LIVE DOM UPDATER
 */
window.AudienceBadminton = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elSetsA = document.getElementById('aud-badminton-sets-a');
    if (elSetsA) elSetsA.textContent = score.sets_team_a || 0;

    const elSetsB = document.getElementById('aud-badminton-sets-b');
    if (elSetsB) elSetsB.textContent = score.sets_team_b || 0;

    const curSet = (score.set_scores && score.set_scores.length > 0) ? score.set_scores[score.set_scores.length - 1] : { team_a: 0, team_b: 0 };

    const elPtsA = document.getElementById('aud-badminton-pts-a');
    if (elPtsA) {
      elPtsA.innerHTML = `${curSet.team_a || 0} ${score.server !== 'team_b' ? '<span class="server-shuttle" title="Serving" id="aud-badminton-server-a">🏸</span>' : ''}`;
    }

    const elPtsB = document.getElementById('aud-badminton-pts-b');
    if (elPtsB) {
      elPtsB.innerHTML = `${score.server === 'team_b' ? '<span class="server-shuttle" title="Serving" id="aud-badminton-server-b">🏸</span>' : ''} ${curSet.team_b || 0}`;
    }

    const elSetInfo = document.getElementById('aud-badminton-set-info');
    if (elSetInfo) {
      elSetInfo.textContent = `Set ${score.current_set || 1} (Target: ${score.points_to_win_set || 21} pts)`;
    }

    const elDeuce = document.getElementById('aud-badminton-deuce-badge');
    if (elDeuce) {
      if (score.in_deuce) elDeuce.classList.remove('d-none');
      else elDeuce.classList.add('d-none');
    }
  }
};
