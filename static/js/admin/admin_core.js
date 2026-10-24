/**
 * ADMIN CONTROL ROOM CORE MODULE - Department Cup 2026
 * Orchestrates match lifecycle (squads, toss, live scoring, undo, conclude, delete)
 * and dispatches keypad events to sport-specific controllers.
 */
window.AdminCore = (function() {
  let matchId = null;
  let sportType = null;
  let isTeamSport = false;
  let ws = null;

  function init() {
    const root = document.querySelector('.control-room-root');
    if (!root) return;

    matchId = root.dataset.matchId;
    sportType = root.dataset.sportType;
    isTeamSport = root.dataset.isTeamSport === 'true';

    initTabSwitcher();
    initLifecycleActions();
    initSportController();
    initWebSocket();
  }

  function initTabSwitcher() {
    const tabSquads = document.getElementById('tab-btn-squads');
    const tabScorer = document.getElementById('tab-btn-scorer');
    const viewSquads = document.getElementById('squads-section');
    const viewScorer = document.getElementById('live-scorer-section');

    if (tabSquads && tabScorer) {
      tabSquads.addEventListener('click', () => {
        tabSquads.classList.add('active');
        tabScorer.classList.remove('active');
        if (viewSquads) viewSquads.classList.remove('d-none');
        if (viewScorer) viewScorer.classList.add('d-none');
      });

      tabScorer.addEventListener('click', () => {
        tabScorer.classList.add('active');
        tabSquads.classList.remove('active');
        if (viewScorer) viewScorer.classList.remove('d-none');
        if (viewSquads) viewSquads.classList.add('d-none');
      });
    }

    // Toss visual cards sync
    document.querySelectorAll('.toss-choice-card').forEach(card => {
      card.addEventListener('click', () => {
        const val = card.getAttribute('data-value');
        const select = document.getElementById('toss-winner-select');
        if (select) select.value = val;
        document.querySelectorAll('.toss-choice-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
      });
    });

    document.querySelectorAll('.toss-dec-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.getAttribute('data-value');
        const select = document.getElementById('toss-decision-select');
        if (select) select.value = val;
        document.querySelectorAll('.toss-dec-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
      });
    });
  }

  function initLifecycleActions() {
    // 1. Announce Squads & Toss
    const btnAnnounce = document.getElementById('btn-announce-squads');
    if (btnAnnounce) {
      btnAnnounce.addEventListener('click', () => saveSquadsAndToss(false));
    }

    // 2. Start Match Live
    const btnStart = document.getElementById('btn-start-match-live');
    if (btnStart) {
      btnStart.addEventListener('click', () => saveSquadsAndToss(true));
    }

    // 3. Undo Last Action
    const btnUndo = document.getElementById('btn-undo-action');
    if (btnUndo) {
      btnUndo.addEventListener('click', async () => {
        if (!confirm("Undo last ball / point?")) return;
        try {
          const res = await fetch(`/api/match/${matchId}/undo`, { method: 'POST' });
          const data = await res.json();
          if (data.success) {
            window.location.reload();
          } else {
            alert(data.detail || "Failed to undo action.");
          }
        } catch (e) {
          alert("Error communicating with server.");
        }
      });
    }

    // 4. Conclude Match Modal
    const btnTopConclude = document.getElementById('btn-top-conclude');
    const btnModalConclude = document.getElementById('btn-conclude-match-modal');
    const modalFinish = document.getElementById('modal-conclude-match');

    function openFinishModal() {
      if (modalFinish) modalFinish.classList.remove('d-none');
    }

    if (btnTopConclude) btnTopConclude.addEventListener('click', openFinishModal);
    if (btnModalConclude) btnModalConclude.addEventListener('click', openFinishModal);

    const btnCloseModal = document.getElementById('btn-close-conclude-modal');
    if (btnCloseModal && modalFinish) {
      btnCloseModal.addEventListener('click', () => modalFinish.classList.add('d-none'));
    }

    const formFinish = document.getElementById('form-finish-match');
    if (formFinish) {
      formFinish.addEventListener('submit', async (e) => {
        e.preventDefault();
        const winner = document.getElementById('conclude-winner-select').value;
        const summary = document.getElementById('conclude-summary-input').value.trim();
        const motm = document.getElementById('conclude-motm-input') ? document.getElementById('conclude-motm-input').value.trim() : '';

        try {
          const res = await fetch(`/api/match/${matchId}/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              winner: winner,
              result_summary: summary || `${winner.toUpperCase()} won the match`,
              player_of_the_match: motm
            })
          });
          const data = await res.json();
          if (data.success) {
            alert("Match concluded successfully!");
            window.location.href = '/admin';
          } else {
            alert(data.detail || "Failed to end match.");
          }
        } catch (e) {
          alert("Error ending match.");
        }
      });
    }

    // 5. Delete or Clear Match
    document.querySelectorAll('.btn-delete-control-room').forEach(btn => {
      btn.addEventListener('click', async () => {
        const isConcluded = btn.dataset.status === 'completed';
        const msg = isConcluded
          ? "Clear concluded match from screen? (Historical records will remain in database)"
          : "PERMANENTLY DELETE match from database and screen? This cannot be undone!";
        if (!confirm(msg)) return;

        try {
          const res = await fetch(`/api/match/${matchId}/delete`, { method: 'POST' });
          const data = await res.json();
          if (data.success) {
            alert(data.message || "Match processed successfully.");
            window.location.href = '/admin';
          } else {
            alert(data.detail || "Failed to delete/clear match.");
          }
        } catch (e) {
          alert("Error deleting match.");
        }
      });
    });
  }

  async function saveSquadsAndToss(startLiveAfterwards) {
    const tossWinner = document.getElementById('toss-winner-select') ? document.getElementById('toss-winner-select').value : null;
    const tossDecision = document.getElementById('toss-decision-select') ? document.getElementById('toss-decision-select').value : null;

    let payload = {
      toss_winner: tossWinner,
      toss_decision: tossDecision
    };

    if (isTeamSport) {
      const txtA = document.getElementById('squad-team-a-input');
      const txtB = document.getElementById('squad-team-b-input');
      if (txtA && txtB) {
        payload.squad_a = parseSquadText(txtA.value);
        payload.squad_b = parseSquadText(txtB.value);
      }
    } else {
      const plA = document.getElementById('input-players-a');
      const plB = document.getElementById('input-players-b');
      if (plA) payload.players_a = plA.value.trim();
      if (plB) payload.players_b = plB.value.trim();
    }

    try {
      const res = await fetch(`/api/match/${matchId}/squads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!data.success) {
        alert(data.detail || "Failed to update squads.");
        return;
      }

      if (startLiveAfterwards) {
        const resStart = await fetch(`/api/match/${matchId}/start`, { method: 'POST' });
        const dataStart = await resStart.json();
        if (dataStart.success) {
          window.location.reload();
        } else {
          alert(dataStart.detail || "Failed to start live match.");
        }
      } else {
        alert("Lineups & Toss announced successfully!");
        window.location.reload();
      }
    } catch (e) {
      alert("Error saving squads and toss.");
    }
  }

  function parseSquadText(text) {
    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    const playing = [];
    let captain = null;

    lines.forEach(name => {
      const isC = name.toLowerCase().includes('(c)') || name.toLowerCase().includes('captain');
      const clean = name.replace(/\(c\)/i, '').replace(/captain/i, '').trim();
      if (clean) {
        playing.push({ name: clean, is_captain: isC, role: isC ? 'Captain' : 'Player' });
        if (isC) captain = clean;
      }
    });

    if (!captain && playing.length > 0) {
      playing[0].is_captain = true;
      playing[0].role = 'Captain';
      captain = playing[0].name;
    }

    return { playing: playing, substitutes: [], captain: captain };
  }

  async function sendAction(actionPayload) {
    try {
      const res = await fetch(`/api/match/${matchId}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(actionPayload)
      });
      const data = await res.json();
      if (data.success) {
        updateActiveSportState(data.match);
      } else {
        alert(data.detail || "Score action failed.");
      }
    } catch (e) {
      console.error("Action error:", e);
      alert("Error sending score action.");
    }
  }

  function initSportController() {
    if (sportType === 'cricket' && window.AdminCricket) {
      window.AdminCricket.init(sendAction);
    } else if (sportType === 'football' && window.AdminFootball) {
      window.AdminFootball.init(sendAction);
    } else if (sportType === 'volleyball' && window.AdminVolleyball) {
      window.AdminVolleyball.init(sendAction);
    } else if (sportType === 'badminton' && window.AdminBadminton) {
      window.AdminBadminton.init(sendAction);
    } else if (sportType === 'table_tennis' && window.AdminTableTennis) {
      window.AdminTableTennis.init(sendAction);
    } else if (sportType === 'carrom' && window.AdminCarrom) {
      window.AdminCarrom.init(sendAction);
    } else if (sportType === 'tug_of_war' && window.AdminTugOfWar) {
      window.AdminTugOfWar.init(sendAction);
    } else if (sportType === 'athletics_distance' && window.AdminAthletics) {
      window.AdminAthletics.init(sendAction);
    } else if (sportType === 'basketball_shootout' && window.AdminBasketball) {
      window.AdminBasketball.init(sendAction);
    }
  }

  function updateActiveSportState(match) {
    if (!match) return;
    if (sportType === 'cricket' && window.AdminCricket) {
      window.AdminCricket.updateState(match);
    } else if (sportType === 'football' && window.AdminFootball) {
      window.AdminFootball.updateState(match);
    } else if (sportType === 'volleyball' && window.AdminVolleyball) {
      window.AdminVolleyball.updateState(match);
    } else if (sportType === 'badminton' && window.AdminBadminton) {
      window.AdminBadminton.updateState(match);
    } else if (sportType === 'table_tennis' && window.AdminTableTennis) {
      window.AdminTableTennis.updateState(match);
    } else if (sportType === 'carrom' && window.AdminCarrom) {
      window.AdminCarrom.updateState(match);
    } else if (sportType === 'tug_of_war' && window.AdminTugOfWar) {
      window.AdminTugOfWar.updateState(match);
    }
  }

  function initWebSocket() {
    if (!matchId) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = function() {
        ws.send(JSON.stringify({ type: 'subscribe', match_id: matchId }));
      };
      ws.onmessage = function(event) {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === 'SCORE_UPDATED' && msg.data.match) {
            updateActiveSportState(msg.data.match);
          }
        } catch (e) {}
      };
    } catch (e) {}
  }

  return {
    init: init,
    sendAction: sendAction
  };
})();

document.addEventListener('DOMContentLoaded', function() {
  AdminCore.init();
});
