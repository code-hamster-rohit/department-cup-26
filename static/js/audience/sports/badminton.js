/**
 * AUDIENCE BADMINTON LIVE DOM UPDATER - Department Cup 2026
 * Renders live updates for the 5-event Mixed Team Match, active court points,
 * deuce status, server indicator, and set breakdown.
 */
window.AudienceBadminton = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;
    const teamAAbbr = (match.team_a && match.team_a.abbr) || 'AMSC';
    const teamBAbbr = (match.team_b && match.team_b.abbr) || 'PPE';

    // 1. Overall Team Tie Event Victories
    const elEventsA = document.getElementById('aud-badminton-events-a');
    if (elEventsA) elEventsA.textContent = score.events_team_a || 0;
    const elEventsB = document.getElementById('aud-badminton-events-b');
    if (elEventsB) elEventsB.textContent = score.events_team_b || 0;

    // 2. Active Event Identification
    const activeEvId = score.active_event_id || 'bs';
    const events = score.events || [];
    let curEvent = events.find(e => e.id === activeEvId) || events[0] || {};

    const elEvName = document.getElementById('aud-badminton-ev-name');
    if (elEvName) elEvName.textContent = curEvent.name || "Boys' Singles";
    const elEvShort = document.getElementById('aud-badminton-ev-short');
    if (elEvShort) elEvShort.textContent = curEvent.short_name || "BS";

    const elPlayers = document.getElementById('aud-badminton-players');
    if (elPlayers) {
      if (curEvent.players_a || curEvent.players_b) {
        elPlayers.textContent = `${curEvent.players_a || 'TBD'} vs ${curEvent.players_b || 'TBD'}`;
      } else {
        elPlayers.textContent = '';
      }
    }

    // 3. Active Event Sets
    const elSetsA = document.getElementById('aud-badminton-sets-a');
    if (elSetsA) elSetsA.textContent = curEvent.sets_a || 0;
    const elSetsB = document.getElementById('aud-badminton-sets-b');
    if (elSetsB) elSetsB.textContent = curEvent.sets_b || 0;

    // 4. Current Set Points
    const setScores = curEvent.set_scores || [];
    const curSetIdx = Math.max(0, (curEvent.current_set || 1) - 1);
    const curSet = setScores[curSetIdx] || { team_a: 0, team_b: 0 };

    const elPtsA = document.getElementById('aud-badminton-pts-a');
    if (elPtsA) {
      const shuttleA = curEvent.server !== 'team_b' ? '<span class="server-shuttle" title="Serving" id="aud-badminton-server-a">🏸</span>' : '';
      elPtsA.innerHTML = `${curSet.team_a || 0} ${shuttleA}`;
    }

    const elPtsB = document.getElementById('aud-badminton-pts-b');
    if (elPtsB) {
      const shuttleB = curEvent.server === 'team_b' ? '<span class="server-shuttle" title="Serving" id="aud-badminton-server-b">🏸</span>' : '';
      elPtsB.innerHTML = `${shuttleB} ${curSet.team_b || 0}`;
    }

    // 5. Set Info & Deuce Alert
    const elCurSetNum = document.getElementById('aud-badminton-cur-set-num');
    if (elCurSetNum) elCurSetNum.textContent = curEvent.current_set || 1;

    const elDeuce = document.getElementById('aud-badminton-deuce-badge');
    if (elDeuce) {
      if (curEvent.in_deuce) {
        elDeuce.classList.remove('d-none');
        if (curSet.team_a === 20 && curSet.team_b === 20) {
          elDeuce.textContent = "⚡ GOLDEN POINT CAP (Next to 21 wins)";
        } else {
          elDeuce.textContent = "🔥 DEUCE (Win by 2)";
        }
      } else {
        elDeuce.classList.add('d-none');
      }
    }

    // 6. Set History Chips
    const elHistory = document.getElementById('aud-badminton-set-history');
    if (elHistory && curEvent.set_scores) {
      elHistory.innerHTML = curEvent.set_scores.map(s => {
        const wTag = (s.completed && s.winner) ? `<strong>(${s.winner === 'team_a' ? teamAAbbr : teamBAbbr})</strong>` : '';
        return `<span class="set-chip">Set ${s.set}: ${s.team_a}-${s.team_b} ${wTag}</span>`;
      }).join('');
    }

    // 7. Update 5 Events Audience Cards
    events.forEach(ev => {
      const card = document.getElementById(`aud-ev-card-${ev.id}`);
      if (!card) return;

      if (ev.id === activeEvId) {
        card.classList.add('active-card');
      } else {
        card.classList.remove('active-card');
      }

      if (ev.status === 'completed') {
        card.classList.add('completed-card');
      } else {
        card.classList.remove('completed-card');
      }

      const statusEl = card.querySelector('.card-ev-status');
      if (statusEl) {
        if (ev.status === 'completed') {
          const wAbbr = ev.winner === 'team_a' ? teamAAbbr : teamBAbbr;
          statusEl.innerHTML = `<span class="status-done">${wAbbr} Won (${ev.sets_a}-${ev.sets_b})</span>`;
        } else if (ev.id === activeEvId) {
          statusEl.innerHTML = `<span class="status-live">🔴 LIVE (${ev.sets_a}-${ev.sets_b})</span>`;
        } else {
          statusEl.innerHTML = `<span class="status-upcoming">Upcoming</span>`;
        }
      }

      const playersEl = card.querySelector('.card-ev-players');
      if (playersEl) {
        if (ev.players_a || ev.players_b) {
          playersEl.textContent = `${ev.players_a || 'TBD'} vs ${ev.players_b || 'TBD'}`;
        }
      }
    });
  }
};
