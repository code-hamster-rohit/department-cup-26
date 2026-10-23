/**
 * Audience Arena Interactive Logic & Real-time DOM synchronization.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Tab Switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // Listen to live WebSocket broadcast events
  window.addEventListener('deptcup:matchupdate', (e) => {
    const { event, match_id, data } = e.detail;
    console.log('Audience view reacting to:', event, data);

    const blankCanvas = document.getElementById('blank-canvas-section');
    const activeSection = document.getElementById('active-match-section');

    // If currently on blank canvas and a match is created, refresh to display it!
    if (event === 'MATCH_CREATED' || event === 'MATCH_STARTED') {
      if (blankCanvas && (!activeSection || blankCanvas.style.display !== 'none')) {
        window.location.href = `/?match=${match_id}`;
        return;
      }
    }

    // If active match score updated, refresh match state or update live stats
    if (event === 'SCORE_UPDATED') {
      const urlParams = new URLSearchParams(window.location.search);
      const currentMatchId = urlParams.get('match');

      if (!currentMatchId || currentMatchId === match_id) {
        // Crex-style Pop-up Celebrations on boundaries, wickets, free hits, and goals
        if (data.commentary) {
          prependCommentary(data.commentary);
          if (data.commentary.badge) {
            triggerCrexAlert(data.commentary.badge, data.commentary.text, data.commentary.type);
          }
        }
        // Live DOM stats refresh
        refreshMatchData(match_id);
      }
    } else if (event === 'SQUADS_ANNOUNCED' || event === 'MATCH_COMPLETED') {
      setTimeout(() => window.location.reload(), 600);
    }
  });

  function triggerCrexAlert(badge, text, type) {
    // Only celebrate major events (Boundaries, Wickets, Free Hits, Goals)
    if (!['boundary', 'wicket', 'free_hit', 'penalty', 'goal'].includes(type) && !badge.includes('FOUR') && !badge.includes('SIX') && !badge.includes('WICKET')) {
      return;
    }

    const banner = document.createElement('div');
    let bannerType = type;
    if (badge.includes('FOUR') || badge.includes('SIX')) bannerType = 'boundary';
    if (badge.includes('WICKET')) bannerType = 'wicket';
    if (badge.includes('FREE HIT')) bannerType = 'free_hit';
    if (badge.includes('GOAL')) bannerType = 'goal';

    banner.className = `crex-alert-banner ${bannerType}`;
    banner.innerHTML = `
      <div class="crex-alert-badge">${badge}</div>
      <div class="crex-alert-text">${text}</div>
    `;
    document.body.appendChild(banner);

    setTimeout(() => {
      banner.classList.add('out');
      setTimeout(() => banner.remove(), 400);
    }, 2400);
  }

  function prependCommentary(comm) {
    const feeds = document.querySelectorAll('.commentary-feed');
    feeds.forEach(feed => {
      const item = document.createElement('div');
      item.className = `commentary-item ${comm.type} fade-in-comm`;
      item.innerHTML = `
        <div class="comm-ball">${comm.ball}</div>
        <div class="comm-text-group">
          ${comm.badge ? `<span class="comm-badge" style="background: rgba(255,255,255,0.08); color: #38bdf8;">${comm.badge}</span>` : ''}
          <div class="comm-text">${comm.text}</div>
          <div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 0.25rem;">${comm.time}</div>
        </div>
      `;
      feed.insertBefore(item, feed.firstChild);
    });
  }

  async function refreshMatchData(matchId) {
    try {
      const res = await fetch(`/api/match/${matchId}`);
      if (!res.ok) return;
      const json = await res.json();
      const match = json.match;
      
      // Update team score boxes
      const scoreA = document.getElementById('team-a-score-box');
      const scoreB = document.getElementById('team-b-score-box');
      
      if (match.sport_type === 'cricket') {
        const inn1 = match.score.innings_1;
        const inn2 = match.score.innings_2;
        const curInn = match.score.innings === 1 ? inn1 : inn2;
        
        if (scoreA) {
          if (inn1.team === 'team_a') {
            scoreA.innerHTML = `${inn1.runs}/${inn1.wickets} <span class="team-overs-display">(${inn1.overs} ov)</span>`;
          } else if (inn2.team === 'team_a') {
            scoreA.innerHTML = `${inn2.runs}/${inn2.wickets} <span class="team-overs-display">(${inn2.overs} ov)</span>`;
          }
        }
        if (scoreB) {
          if (inn1.team === 'team_b') {
            scoreB.innerHTML = `${inn1.runs}/${inn1.wickets} <span class="team-overs-display">(${inn1.overs} ov)</span>`;
          } else if (inn2.team === 'team_b') {
            scoreB.innerHTML = `${inn2.runs}/${inn2.wickets} <span class="team-overs-display">(${inn2.overs} ov)</span>`;
          }
        }

        // Update CRR and Target
        const oversFloat = Math.floor(curInn.legal_balls / 6) + (curInn.legal_balls % 6) / 6.0;
        const crr = oversFloat > 0 ? (curInn.runs / oversFloat).toFixed(2) : '0.00';
        const crrBox = document.getElementById('crr-rrr-box');
        if (crrBox) {
          crrBox.innerHTML = `<span>CRR: <strong>${crr}</strong></span>`;
          if (match.score.innings === 2 && inn2.target) {
            const remRuns = inn2.target - inn2.runs;
            const remBalls = (match.score.max_overs * 6) - inn2.legal_balls;
            crrBox.innerHTML += ` <span>Target: <strong>${inn2.target}</strong> (Need ${remRuns} in ${remBalls} balls)</span>`;
          }
        }

        // Update Free Hit indicator strip
        const statusStrip = document.getElementById('status-strip-text');
        if (statusStrip) {
          if (match.score.is_free_hit) {
            statusStrip.innerHTML = '<span class="badge badge-freehit" style="background: #f59e0b; color: #000; font-weight: 800;">🎯 FREE HIT IN PLAY</span>';
          } else if (match.score.is_powerplay) {
            statusStrip.innerHTML = '<span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #93c5fd;">⚡ POWERPLAY (Max 2 fielders outside)</span>';
          }
        }

        // Update Active Batsmen Table
        const bTableBody = document.querySelector('#batsmen-table tbody');
        if (bTableBody && curInn.batsmen) {
          let bHtml = '';
          if (curInn.striker && curInn.batsmen[curInn.striker]) {
            const s = curInn.batsmen[curInn.striker];
            bHtml += `<tr class="striker-active">
              <td><strong>${curInn.striker}</strong> *</td>
              <td class="text-right"><strong>${s.runs}</strong></td>
              <td class="text-right">${s.balls}</td>
              <td class="text-right">${s.fours}</td>
              <td class="text-right">${s.sixes}</td>
              <td class="text-right">${s.sr || '0.0'}</td>
            </tr>`;
          }
          if (curInn.non_striker && curInn.batsmen[curInn.non_striker]) {
            const ns = curInn.batsmen[curInn.non_striker];
            bHtml += `<tr>
              <td><strong>${curInn.non_striker}</strong></td>
              <td class="text-right"><strong>${ns.runs}</strong></td>
              <td class="text-right">${ns.balls}</td>
              <td class="text-right">${ns.fours}</td>
              <td class="text-right">${ns.sixes}</td>
              <td class="text-right">${ns.sr || '0.0'}</td>
            </tr>`;
          }
          if (bHtml) bTableBody.innerHTML = bHtml;
        }

        // Update Current Bowler Table
        const bowTableBody = document.querySelector('#bowler-table tbody');
        if (bowTableBody && curInn.bowler && curInn.bowlers && curInn.bowlers[curInn.bowler]) {
          const b = curInn.bowlers[curInn.bowler];
          bowTableBody.innerHTML = `<tr>
            <td><strong>${curInn.bowler}</strong></td>
            <td class="text-right">${b.overs} / 2.0</td>
            <td class="text-right">${b.maidens}</td>
            <td class="text-right">${b.runs}</td>
            <td class="text-right"><strong>${b.wickets}</strong></td>
            <td class="text-right">${b.econ || '0.0'}</td>
          </tr>`;
        }

        // Update Timeline Deliveries
        const timeline = document.getElementById('balls-timeline');
        if (timeline && curInn.timeline) {
          timeline.innerHTML = '';
          curInn.timeline.slice(-18).forEach(b => {
            const pill = document.createElement('span');
            let cls = 'ball-pill';
            if (b === '4') cls += ' four';
            else if (b === '6') cls += ' six';
            else if (b === 'W') cls += ' wicket';
            else if (b.includes('Wd')) cls += ' wide';
            else if (b.includes('NB')) cls += ' noball';
            pill.className = cls;
            pill.textContent = b;
            timeline.appendChild(pill);
          });
        }
      } else if (match.sport_type === 'football') {
        if (scoreA) scoreA.textContent = match.score.team_a_score;
        if (scoreB) scoreB.textContent = match.score.team_b_score;
        const fbScoreA = document.getElementById('fb-score-a');
        const fbScoreB = document.getElementById('fb-score-b');
        if (fbScoreA) fbScoreA.textContent = match.score.team_a_score;
        if (fbScoreB) fbScoreB.textContent = match.score.team_b_score;
      } else if (match.sport_type === 'penalty_shootout') {
        if (scoreA) scoreA.textContent = `${match.score.team_a_score} Goals`;
        if (scoreB) scoreB.textContent = `${match.score.team_b_score} Goals`;
      } else if (match.sport_type === 'volleyball') {
        if (scoreA) scoreA.textContent = `${match.score.sets_team_a} Sets`;
        if (scoreB) scoreB.textContent = `${match.score.sets_team_b} Sets`;
      }
    } catch (e) {
      console.warn('Silent refresh error:', e);
    }
  }

  // =========================================================================
  // Crowd Reactions & Floating Cheers Interaction
  // =========================================================================
  const dock = document.getElementById('crowd-reactions-dock');
  if (dock) {
    const matchId = dock.getAttribute('data-match-id');

    // Emoji reaction buttons
    const emojiBtns = dock.querySelectorAll('.btn-reaction-emoji');
    emojiBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const content = btn.getAttribute('data-content');
        if (content && window.App) {
          window.App.sendReaction(matchId, content);
        }
      });
    });

    // Preset department/sport chant buttons
    const chantBtns = dock.querySelectorAll('.btn-reaction-chant');
    chantBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const content = btn.getAttribute('data-content');
        if (content && window.App) {
          window.App.sendReaction(matchId, content);
        }
      });
    });

    // Custom cheer input form
    const form = document.getElementById('custom-reaction-form');
    const input = document.getElementById('custom-reaction-input');
    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (text && window.App) {
          window.App.sendReaction(matchId, text);
          input.value = '';
          input.blur();
        }
      });
    }
  }
});
