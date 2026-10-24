/**
 * ADMIN FOOTBALL SCORING CONTROLS
 */
window.AdminFootball = {
  init: function(sendAction) {
    // 1. Goal Buttons
    document.querySelectorAll('.btn-fb-goal').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const team = btn.dataset.team;
        const player = prompt("Enter Goal Scorer Name:", "Player");
        if (player === null) return;
        const assist = prompt("Enter Assist Provider (Optional):", "");
        const minute = prompt("Enter Minute (e.g. 24'):", "25'");
        sendAction({
          type: 'goal',
          team: team,
          player: player.trim() || 'Player',
          assist: assist ? assist.trim() : '',
          minute: minute ? minute.trim() : "25'"
        });
      });
    });

    // 2. Card Buttons
    document.querySelectorAll('.btn-fb-card').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const team = btn.dataset.team;
        const color = btn.dataset.card;
        const player = prompt(`Enter Player Name receiving ${color.toUpperCase()} card:`, "Player");
        if (player === null) return;
        const minute = prompt("Enter Minute (e.g. 34'):", "30'");
        sendAction({
          type: 'card',
          team: team,
          card_color: color,
          player: player.trim() || 'Player',
          minute: minute ? minute.trim() : "30'"
        });
      });
    });

    // 3. Stats Buttons
    document.querySelectorAll('.btn-fb-stat').forEach(function(btn) {
      btn.addEventListener('click', function() {
        sendAction({
          type: 'stat',
          team: btn.dataset.team,
          stat_key: btn.dataset.stat,
          delta: 1
        });
      });
    });

    // 4. Period Switches
    document.querySelectorAll('.btn-fb-period').forEach(function(btn) {
      btn.addEventListener('click', function() {
        sendAction({
          type: 'update_half',
          half: parseInt(btn.dataset.half, 10)
        });
      });
    });

    // 5. Shootout Kicks
    document.querySelectorAll('.btn-shootout-kick').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const team = btn.dataset.team;
        const res = btn.dataset.result;
        const player = prompt("Enter Shooter Player Name:", "Shooter");
        if (player === null) return;
        sendAction({
          type: 'shootout_kick',
          team: team,
          result: res,
          player: player.trim() || 'Shooter'
        });
      });
    });
  },

  updateState: function(match) {
    if (!match || !match.score) return;
    const score = match.score;
    const elPeriod = document.getElementById('admin-current-period-display');
    if (elPeriod) {
      elPeriod.textContent = score.period_label || `Half ${score.half || 1}`;
    }
  }
};
