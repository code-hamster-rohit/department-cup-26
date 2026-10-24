/**
 * ADMIN VOLLEYBALL SCORING CONTROLS
 */
window.AdminVolleyball = {
  init: function(sendAction) {
    // 1. Points (+1 / -1)
    document.querySelectorAll('.sport-admin-volleyball .btn-point-action').forEach(function(btn) {
      btn.addEventListener('click', function() {
        sendAction({
          type: 'point',
          team: btn.dataset.team,
          delta: parseInt(btn.dataset.delta, 10)
        });
      });
    });

    // 2. Timeout
    document.querySelectorAll('.sport-admin-volleyball .btn-vb-timeout').forEach(function(btn) {
      btn.addEventListener('click', function() {
        sendAction({
          type: 'timeout',
          team: btn.dataset.team
        });
      });
    });

    // 3. Swap Server
    const btnSwapServer = document.querySelector('.sport-admin-volleyball #btn-swap-server');
    if (btnSwapServer) {
      btnSwapServer.addEventListener('click', function() {
        sendAction({ type: 'swap_server' });
      });
    }

    // 4. Conclude Set
    const btnConcludeSet = document.querySelector('.sport-admin-volleyball #btn-conclude-set');
    if (btnConcludeSet) {
      btnConcludeSet.addEventListener('click', function() {
        if (confirm("Finish current set and award to leading team?")) {
          sendAction({ type: 'end_set' });
        }
      });
    }
  },

  updateState: function(match) {
    if (!match || !match.score) return;
    const score = match.score;

    const elSetsA = document.querySelector('.sport-admin-volleyball #admin-sets-a');
    if (elSetsA) elSetsA.textContent = score.sets_team_a || 0;

    const elSetsB = document.querySelector('.sport-admin-volleyball #admin-sets-b');
    if (elSetsB) elSetsB.textContent = score.sets_team_b || 0;

    const curSet = (score.set_scores && score.set_scores.length > 0) ? score.set_scores[score.set_scores.length - 1] : { team_a: 0, team_b: 0 };

    const elPtsA = document.querySelector('.sport-admin-volleyball #display-pts-a');
    if (elPtsA) elPtsA.textContent = curSet.team_a || 0;

    const elPtsB = document.querySelector('.sport-admin-volleyball #display-pts-b');
    if (elPtsB) elPtsB.textContent = curSet.team_b || 0;

    const elBadgeSet = document.querySelector('.sport-admin-volleyball #badge-current-set');
    if (elBadgeSet) elBadgeSet.textContent = score.current_set || 1;

    const elBadgeServer = document.querySelector('.sport-admin-volleyball #badge-server');
    if (elBadgeServer) {
      const serverTeam = score.server === 'team_b' ? match.team_b.abbr : match.team_a.abbr;
      elBadgeServer.textContent = `🏐 Serving: ${serverTeam}`;
    }
  }
};
