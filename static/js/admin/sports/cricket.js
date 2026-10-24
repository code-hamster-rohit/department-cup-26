/**
 * ADMIN CRICKET SCORING CONTROLS
 * Handles user interactions with keypad, strike rotation, extras, and wickets.
 */
window.AdminCricket = {
  getContext: function() {
    const selectStriker = document.getElementById('select-striker');
    const selectNonStriker = document.getElementById('select-non-striker');
    const selectBowler = document.getElementById('select-bowler');

    return {
      striker: selectStriker ? selectStriker.value : '',
      non_striker: selectNonStriker ? selectNonStriker.value : '',
      bowler: selectBowler ? selectBowler.value : ''
    };
  },

  init: function(sendAction) {
    const self = this;

    // 1. Swap Strike
    const btnSwap = document.getElementById('btn-rotate-strike');
    if (btnSwap) {
      btnSwap.addEventListener('click', function() {
        sendAction({ type: 'swap_strike', ...self.getContext() });
      });
    }

    // 2. Change Bowler
    const selectBowler = document.getElementById('select-bowler');
    if (selectBowler) {
      selectBowler.addEventListener('change', function() {
        sendAction({ type: 'change_bowler', bowler: selectBowler.value, ...self.getContext() });
      });
    }

    // 3. Runs Keypad
    document.querySelectorAll('.runs-keypad .btn-run').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const runs = parseInt(btn.dataset.runs, 10);
        sendAction({ type: runs in [4, 6] ? 'boundary' : 'run', runs: runs, ...self.getContext() });
      });
    });

    // 4. Extras Keypad
    const btnWide = document.getElementById('btn-wide');
    if (btnWide) btnWide.addEventListener('click', () => sendAction({ type: 'extra', extra_type: 'wide', runs: 1, ...self.getContext() }));

    const btnNoball = document.getElementById('btn-noball');
    if (btnNoball) btnNoball.addEventListener('click', () => sendAction({ type: 'extra', extra_type: 'no_ball', runs: 1, ...self.getContext() }));

    const btnBye = document.getElementById('btn-bye');
    if (btnBye) btnBye.addEventListener('click', () => sendAction({ type: 'extra', extra_type: 'bye', runs: 1, ...self.getContext() }));

    const btnLegbye = document.getElementById('btn-legbye');
    if (btnLegbye) btnLegbye.addEventListener('click', () => sendAction({ type: 'extra', extra_type: 'leg_bye', runs: 1, ...self.getContext() }));

    // 5. Wickets Keypad
    document.querySelectorAll('.wicket-keypad .wicket-btn').forEach(function(btn) {
      if (btn.disabled) return;
      btn.addEventListener('click', function() {
        const dis = btn.dataset.dismissal || 'bowled';
        sendAction({ type: 'wicket', dismissal: dis, ...self.getContext() });
      });
    });

    // 6. Dead Ball Actions
    const btnDeadBall = document.getElementById('btn-box-dead-ball');
    if (btnDeadBall) btnDeadBall.addEventListener('click', () => sendAction({ type: 'dead_ball', is_special_dead_ball_penalty: false, ...self.getContext() }));

    const btnDeadBallPenalty = document.getElementById('btn-box-dead-ball-penalty');
    if (btnDeadBallPenalty) btnDeadBallPenalty.addEventListener('click', () => sendAction({ type: 'dead_ball', is_special_dead_ball_penalty: true, ...self.getContext() }));

    // 7. Switch Innings
    const btnSwitchInnings = document.getElementById('btn-switch-innings');
    if (btnSwitchInnings) {
      btnSwitchInnings.addEventListener('click', function() {
        if (confirm("Conclude 1st innings and switch to 2nd innings?")) {
          sendAction({ type: 'switch_innings', ...self.getContext() });
        }
      });
    }
  },

  updateState: function(match) {
    if (!match || !match.score) return;
    const score = match.score;
    const innNum = score.innings || 1;
    const curInn = score[`innings_${innNum}`];
    if (!curInn) return;

    // Free hit banner
    const elFh = document.getElementById('admin-freehit-banner');
    if (elFh) {
      if (score.is_free_hit) elFh.classList.remove('d-none');
      else elFh.classList.add('d-none');
    }

    // Update striker selector value if not matching
    const selectStriker = document.getElementById('select-striker');
    if (selectStriker && curInn.striker && selectStriker.value !== curInn.striker) {
      selectStriker.value = curInn.striker;
    }

    // Update non-striker selector value
    const selectNonStriker = document.getElementById('select-non-striker');
    if (selectNonStriker && curInn.non_striker && selectNonStriker.value !== curInn.non_striker) {
      selectNonStriker.value = curInn.non_striker;
    }

    // Update bowler selector value
    const selectBowler = document.getElementById('select-bowler');
    if (selectBowler && curInn.bowler && selectBowler.value !== curInn.bowler) {
      selectBowler.value = curInn.bowler;
    }
  }
};
