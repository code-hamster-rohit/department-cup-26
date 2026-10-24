/**
 * ADMIN BADMINTON SCORING CONTROLS - Department Cup 2026
 * Handles 5-Event Mixed Team Match, rally points, deuce, golden point cap (21),
 * server rotation, late arrival advantage, and event progression.
 */
window.AdminBadminton = (function() {
  let _sendAction = null;
  let currentActiveEventId = 'bs';

  function init(sendAction) {
    _sendAction = sendAction;

    // 1. Points (+1 / -1)
    document.querySelectorAll('.sport-admin-badminton .btn-point-action').forEach(btn => {
      btn.addEventListener('click', function() {
        if (btn.disabled) return;
        const team = btn.dataset.team;
        const delta = parseInt(btn.dataset.delta, 10);
        _sendAction({
          type: 'point',
          team: team,
          delta: delta
        });
      });
    });

    // 2. Swap Server
    const btnSwapServer = document.getElementById('btn-swap-server');
    if (btnSwapServer) {
      btnSwapServer.addEventListener('click', function() {
        _sendAction({ type: 'swap_server' });
      });
    }

    // 3. Switch Event Tabs
    document.querySelectorAll('.sport-admin-badminton .event-nav-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        const evId = btn.dataset.eventId;
        if (evId) {
          currentActiveEventId = evId;
          _sendAction({ type: 'switch_event', event_id: evId });
        }
      });
    });

    // 4. Start Next Set
    const btnNextSet = document.getElementById('btn-start-next-set');
    if (btnNextSet) {
      btnNextSet.addEventListener('click', function() {
        _sendAction({ type: 'start_next_set' });
      });
    }

    // 5. Start Next Event
    const btnNextEvent = document.getElementById('btn-start-next-event');
    if (btnNextEvent) {
      btnNextEvent.addEventListener('click', function() {
        _sendAction({ type: 'start_next_event' });
      });
    }

    // 6. Finish / Award Set
    const btnConcludeSet = document.getElementById('btn-conclude-set');
    if (btnConcludeSet) {
      btnConcludeSet.addEventListener('click', function() {
        if (confirm("Conclude current set and award to leading team?")) {
          _sendAction({ type: 'end_set' });
        }
      });
    }

    // 7. Finalize Tie / Conclude Match Modal
    const btnFinalizeTie = document.getElementById('btn-finalize-tie');
    if (btnFinalizeTie) {
      btnFinalizeTie.addEventListener('click', function() {
        const modal = document.getElementById('conclude-match-modal') || document.getElementById('modal-conclude-match');
        if (modal) modal.classList.remove('d-none');
      });
    }

    // 8. Late Arrival Penalty Modal
    const modalLate = document.getElementById('modal-late-arrival');
    const btnOpenLate = document.getElementById('btn-late-arrival-tool');
    const btnCloseLate = document.getElementById('btn-close-late-modal');
    const btnCancelLate = document.getElementById('btn-cancel-late-modal');

    function closeLateModal() {
      if (modalLate) modalLate.classList.add('d-none');
    }

    if (btnOpenLate && modalLate) {
      btnOpenLate.addEventListener('click', () => modalLate.classList.remove('d-none'));
    }
    if (btnCloseLate) btnCloseLate.addEventListener('click', closeLateModal);
    if (btnCancelLate) btnCancelLate.addEventListener('click', closeLateModal);

    if (modalLate) {
      modalLate.addEventListener('click', function(e) {
        if (e.target === modalLate) closeLateModal();
      });
    }

    document.querySelectorAll('.btn-late-action').forEach(btn => {
      btn.addEventListener('click', function() {
        const advTeam = btn.dataset.team;
        if (confirm(`Apply Rule 5: Award 2-point opening set advantage to ${advTeam.toUpperCase()}?`)) {
          _sendAction({ type: 'late_arrival_penalty', advantaged_team: advTeam });
          closeLateModal();
        }
      });
    });

    // 9. Event Lineup Declaration Modal
    const modalLineup = document.getElementById('modal-event-lineup');
    const btnOpenLineup = document.getElementById('btn-open-lineup-modal');
    const btnCloseLineup = document.getElementById('btn-close-lineup-modal');
    const btnCancelLineup = document.getElementById('btn-cancel-lineup');
    const formLineup = document.getElementById('form-event-lineup');

    function closeLineupModal() {
      if (modalLineup) modalLineup.classList.add('d-none');
    }

    if (btnOpenLineup && modalLineup) {
      btnOpenLineup.addEventListener('click', () => modalLineup.classList.remove('d-none'));
    }
    if (btnCloseLineup) btnCloseLineup.addEventListener('click', closeLineupModal);
    if (btnCancelLineup) btnCancelLineup.addEventListener('click', closeLineupModal);

    if (modalLineup) {
      modalLineup.addEventListener('click', function(e) {
        if (e.target === modalLineup) closeLineupModal();
      });
    }

    // Universal Escape key listener for modals
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closeLateModal();
        closeLineupModal();
      }
    });

    if (formLineup) {
      formLineup.addEventListener('submit', function(e) {
        e.preventDefault();
        const plA = document.getElementById('input-ev-players-a').value.trim();
        const plB = document.getElementById('input-ev-players-b').value.trim();
        _sendAction({
          type: 'update_event_players',
          event_id: currentActiveEventId,
          players_a: plA,
          players_b: plB
        });
        closeLineupModal();
      });
    }
  }

  function updateState(match) {
    if (!match || !match.score) return;
    const score = match.score;
    const teamAAbbr = (match.team_a && match.team_a.abbr) || 'AMSC';
    const teamBAbbr = (match.team_b && match.team_b.abbr) || 'PPE';

    // 1. Overall Tie Events Won
    const elEventsA = document.getElementById('admin-events-a');
    if (elEventsA) elEventsA.textContent = score.events_team_a || 0;
    const elEventsB = document.getElementById('admin-events-b');
    if (elEventsB) elEventsB.textContent = score.events_team_b || 0;

    // 2. Active Event Identification
    currentActiveEventId = score.active_event_id || 'bs';
    const events = score.events || [];
    let curEvent = events.find(e => e.id === currentActiveEventId) || events[0] || {};

    // 3. Update Top Header Stadium Board Text
    const elTopStadiumText = document.getElementById('admin-current-score-text');
    if (elTopStadiumText) {
      const curSet = (curEvent.set_scores && curEvent.set_scores.length > 0)
        ? curEvent.set_scores[curEvent.set_scores.length - 1]
        : { team_a: 0, team_b: 0 };
      
      elTopStadiumText.textContent = 
        `${teamAAbbr} ${score.events_team_a || 0} - ${score.events_team_b || 0} ${teamBAbbr} ` +
        `(${curEvent.short_name || 'BS'} Set ${curEvent.current_set || 1}: ${curSet.team_a || 0} - ${curSet.team_b || 0})`;
    }

    // 4. Update 5-Event Navigation Tabs
    events.forEach(ev => {
      const btn = document.getElementById(`btn-event-nav-${ev.id}`);
      if (!btn) return;

      if (ev.id === currentActiveEventId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }

      if (ev.status === 'completed') {
        btn.classList.add('completed');
      } else {
        btn.classList.remove('completed');
      }

      const statusTag = btn.querySelector('.event-status-tag');
      if (statusTag) {
        if (ev.status === 'completed') {
          const wAbbr = ev.winner === 'team_a' ? teamAAbbr : teamBAbbr;
          statusTag.className = 'event-status-tag done';
          statusTag.innerHTML = `<i class="fa-solid fa-check"></i> ${wAbbr} (${ev.sets_a}-${ev.sets_b})`;
        } else if (ev.id === currentActiveEventId && ev.status === 'in_progress') {
          statusTag.className = 'event-status-tag live';
          statusTag.innerHTML = `<span class="pulse-dot"></span> LIVE`;
        } else {
          statusTag.className = 'event-status-tag upcoming';
          statusTag.textContent = 'Upcoming';
        }
      }

      const scoreText = btn.querySelector('.event-nav-score');
      if (scoreText) {
        if (ev.status === 'completed') {
          scoreText.textContent = `${ev.sets_a} - ${ev.sets_b} sets`;
        } else if (ev.set_scores && ev.set_scores.length > 0) {
          const lastS = ev.set_scores[ev.set_scores.length - 1];
          scoreText.textContent = `Set ${ev.current_set}: ${lastS.team_a}-${lastS.team_b}`;
        }
      }
    });

    // 5. Active Event Heading & Lineups
    const elEvName = document.getElementById('display-ev-name');
    if (elEvName) elEvName.textContent = curEvent.name || "Boys' Singles";
    const elEvShort = document.getElementById('display-ev-short');
    if (elEvShort) elEvShort.textContent = curEvent.short_name || "BS";

    const elModalEvName = document.getElementById('modal-ev-name-title');
    if (elModalEvName) elModalEvName.textContent = curEvent.name || '';
    const elModalEvShort = document.getElementById('modal-ev-short-title');
    if (elModalEvShort) elModalEvShort.textContent = curEvent.short_name || '';

    const elPlayersA = document.getElementById('display-players-a');
    if (elPlayersA) elPlayersA.textContent = curEvent.players_a || 'Athlete(s) Pending';
    const elPlayersB = document.getElementById('display-players-b');
    if (elPlayersB) elPlayersB.textContent = curEvent.players_b || 'Athlete(s) Pending';

    const inputPlA = document.getElementById('input-ev-players-a');
    if (inputPlA) inputPlA.value = curEvent.players_a || '';
    const inputPlB = document.getElementById('input-ev-players-b');
    if (inputPlB) inputPlB.value = curEvent.players_b || '';

    // 6. Server Badge
    const elServerBox = document.getElementById('badge-server');
    if (elServerBox) {
      const sTeam = curEvent.server === 'team_b' ? teamBAbbr : teamAAbbr;
      elServerBox.innerHTML = `🏸 Serving: <strong>${sTeam}</strong>`;
    }

    // 7. Active Event Sets Counter
    const elSetsA = document.getElementById('admin-sets-a');
    if (elSetsA) elSetsA.textContent = curEvent.sets_a || 0;
    const elSetsB = document.getElementById('admin-sets-b');
    if (elSetsB) elSetsB.textContent = curEvent.sets_b || 0;

    // 8. Current Set Points
    const setScores = curEvent.set_scores || [];
    const curSetIdx = Math.max(0, (curEvent.current_set || 1) - 1);
    const curSet = setScores[curSetIdx] || { team_a: 0, team_b: 0, completed: false };

    const elPtsA = document.getElementById('display-pts-a');
    if (elPtsA) elPtsA.textContent = curSet.team_a || 0;
    const elPtsB = document.getElementById('display-pts-b');
    if (elPtsB) elPtsB.textContent = curSet.team_b || 0;

    // 9. Set Indicators
    const elBadgeSet = document.getElementById('badge-current-set');
    if (elBadgeSet) elBadgeSet.textContent = curEvent.current_set || 1;
    const elCapA = document.getElementById('caption-set-num-a');
    if (elCapA) elCapA.textContent = curEvent.current_set || 1;
    const elCapB = document.getElementById('caption-set-num-b');
    if (elCapB) elCapB.textContent = curEvent.current_set || 1;

    // 10. Deuce / Golden Point Banner
    const elDeuceBanner = document.getElementById('badminton-deuce-banner');
    const elDeuceText = document.getElementById('deuce-banner-text');
    if (elDeuceBanner && elDeuceText) {
      if (curEvent.in_deuce) {
        elDeuceBanner.classList.remove('d-none');
        if (curSet.team_a === 20 && curSet.team_b === 20) {
          elDeuceText.textContent = "⚡ 20–20 REACHED: GOLDEN POINT CAP! First team to 21 points wins the set immediately!";
        } else {
          elDeuceText.textContent = "🔥 DEUCE AT 14–14 ACTIVE: Must win by a margin of 2 points! (Cap at 21)";
        }
      } else {
        elDeuceBanner.classList.add('d-none');
      }
    }

    // 11. Set Completed Banner
    const elSetBanner = document.getElementById('set-completed-banner');
    const elSetWonTitle = document.getElementById('set-won-title');
    const elSetWonDesc = document.getElementById('set-won-desc');
    const elNextSetNum = document.getElementById('btn-next-set-num');

    if (elSetBanner) {
      if (curSet.completed && curEvent.status !== 'completed') {
        elSetBanner.classList.remove('d-none');
        const wAbbr = curSet.winner === 'team_a' ? teamAAbbr : teamBAbbr;
        if (elSetWonTitle) elSetWonTitle.textContent = `SET ${curSet.set} COMPLETED!`;
        if (elSetWonDesc) elSetWonDesc.textContent = `${wAbbr} won Set ${curSet.set} (${curSet.team_a} - ${curSet.team_b}).`;
        if (elNextSetNum) elNextSetNum.textContent = (curEvent.current_set || 1) + 1;
      } else {
        elSetBanner.classList.add('d-none');
      }
    }

    // 12. Event Completed Banner
    const elEvBanner = document.getElementById('event-completed-banner');
    const elEvWonTitle = document.getElementById('event-won-title');
    const elEvWonDesc = document.getElementById('event-won-desc');

    if (elEvBanner) {
      if (curEvent.status === 'completed') {
        elEvBanner.classList.remove('d-none');
        const wAbbr = curEvent.winner === 'team_a' ? teamAAbbr : teamBAbbr;
        if (elEvWonTitle) elEvWonTitle.textContent = `${curEvent.name.toUpperCase()} WON!`;
        if (elEvWonDesc) elEvWonDesc.textContent = `${wAbbr} won 2 sets (${curEvent.sets_a} - ${curEvent.sets_b}).`;
      } else {
        elEvBanner.classList.add('d-none');
      }
    }

    // 13. Disable "+1 Point" Buttons if current set or event is completed
    const btnPointA = document.getElementById('btn-point-a');
    const btnPointB = document.getElementById('btn-point-b');
    const isLocked = Boolean(curSet.completed || curEvent.status === 'completed' || match.status === 'completed');

    if (btnPointA) {
      btnPointA.disabled = isLocked;
      btnPointA.style.opacity = isLocked ? '0.45' : '1';
    }
    if (btnPointB) {
      btnPointB.disabled = isLocked;
      btnPointB.style.opacity = isLocked ? '0.45' : '1';
    }

    // 14. Set History Chips
    const elHistory = document.getElementById('set-history-container');
    if (elHistory && curEvent.set_scores) {
      elHistory.innerHTML = curEvent.set_scores.map(s => {
        const cls = s.completed ? 'done' : '';
        const wTag = (s.completed && s.winner) ? `<strong>(${s.winner === 'team_a' ? teamAAbbr : teamBAbbr})</strong>` : '';
        return `<span class="set-history-chip ${cls}">Set ${s.set}: ${s.team_a} - ${s.team_b} ${wTag}</span>`;
      }).join('');
    }
  }

  return {
    init: init,
    updateState: updateState
  };
})();
