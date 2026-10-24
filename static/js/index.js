/**
 * Audience Arena Interactive Logic & Real-time DOM synchronization.
 */

document.addEventListener('DOMContentLoaded', () => {
  // =========================================================================
  // 1. Tab Switching (Live Arena, Scoresheet, Commentary, Lineups & Squads)
  // =========================================================================
  const tabBtns = document.querySelectorAll('.tab-btn, .match-tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  function switchTab(targetId) {
    if (!targetId) return;
    tabBtns.forEach(b => {
      if (b.getAttribute('data-tab') === targetId) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });
    tabPanes.forEach(p => {
      if (p.id === targetId) {
        p.classList.add('active');
      } else {
        p.classList.remove('active');
      }
    });
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      switchTab(targetId);
      // Persist tab selection in sessionStorage
      try {
        sessionStorage.setItem('active_match_tab', targetId);
      } catch (e) {}
    });
  });

  // Restore active tab from sessionStorage if available
  try {
    const savedTab = sessionStorage.getItem('active_match_tab');
    if (savedTab && document.getElementById(savedTab)) {
      switchTab(savedTab);
    }
  } catch (e) {}

  // =========================================================================
  // 2. Commentary Filter Chips
  // =========================================================================
  const commFilterChips = document.querySelectorAll('.comm-chip');
  commFilterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      commFilterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const filter = chip.getAttribute('data-filter') || 'all';

      const items = document.querySelectorAll('.commentary-item');
      items.forEach(item => {
        if (filter === 'all') {
          item.style.display = '';
        } else if (filter === 'boundary') {
          const isBnd = item.classList.contains('boundary') || 
                        item.textContent.includes('FOUR') || 
                        item.textContent.includes('SIX');
          item.style.display = isBnd ? '' : 'none';
        } else if (filter === 'wicket') {
          const isWkt = item.classList.contains('wicket') || 
                        item.textContent.includes('WICKET') || 
                        item.textContent.includes('OUT');
          item.style.display = isWkt ? '' : 'none';
        } else if (filter === 'free_hit') {
          const isFh = item.classList.contains('free_hit') || 
                       item.textContent.includes('FREE HIT') || 
                       item.textContent.includes('NO BALL');
          item.style.display = isFh ? '' : 'none';
        }
      });
    });
  });

  // =========================================================================
  // 3. Schedule Day Filters (Blank canvas view)
  // =========================================================================
  const dayFilterBtns = document.querySelectorAll('.btn-day-filter');
  const matchChips = document.querySelectorAll('.match-chip');

  dayFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      dayFilterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const selectedDay = btn.getAttribute('data-day');

      matchChips.forEach(chip => {
        const chipDay = chip.getAttribute('data-day') || 'Day 1';
        const chipStatus = chip.getAttribute('data-status');

        if (selectedDay === 'all') {
          chip.style.display = '';
        } else if (selectedDay === 'live') {
          chip.style.display = (chipStatus === 'live') ? '' : 'none';
        } else {
          chip.style.display = (chipDay === selectedDay) ? '' : 'none';
        }
      });
    });
  });

  // =========================================================================
  // 4. Real-time WebSocket Listeners & Broadcasters
  // =========================================================================
  window.addEventListener('deptcup:matchupdate', (e) => {
    const { event, match_id, data } = e.detail;
    console.log('Audience view reacting to:', event, data);

    const blankCanvas = document.getElementById('blank-canvas-section');
    const activeSection = document.getElementById('active-match-section');

    // If currently on blank canvas and a match is created or started, redirect
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
    if (!['boundary', 'wicket', 'free_hit', 'penalty', 'goal'].includes(type) &&
        !badge.includes('FOUR') && !badge.includes('SIX') && !badge.includes('WICKET') && !badge.includes('GOAL')) {
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

  // =========================================================================
  // 5. Dynamic Comprehensive Scorecard Live Refresh
  // =========================================================================
  async function refreshMatchData(matchId) {
    try {
      const res = await fetch(`/api/match/${matchId}`);
      if (!res.ok) return;
      const json = await res.json();
      const match = json.match;
      if (!match) return;

      // Update team score boxes
      const scoreA = document.getElementById('team-a-score-box');
      const scoreB = document.getElementById('team-b-score-box');

      // CRICKET / BOX CRICKET
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
        const crrBox = document.getElementById('crr-rrr-box');
        if (crrBox) {
          let crrHtml = `<span>CRR: <strong>${curInn.crr || '0.00'}</strong></span>`;
          if (match.score.innings === 2 && inn2.target) {
            const remRuns = inn2.target - inn2.runs;
            const remBalls = (match.score.max_overs * 6) - inn2.legal_balls;
            crrHtml += ` <span>Target: <strong>${inn2.target}</strong> (Need ${remRuns} in ${remBalls} balls)</span>`;
          }
          crrBox.innerHTML = crrHtml;
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
            <td class="text-right">${b.dots || 0}</td>
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

      // FOOTBALL
      } else if (match.sport_type === 'football') {
        if (scoreA) scoreA.textContent = match.score.team_a_score;
        if (scoreB) scoreB.textContent = match.score.team_b_score;
        const fbScoreA = document.getElementById('fb-score-a');
        const fbScoreB = document.getElementById('fb-score-b');
        if (fbScoreA) fbScoreA.textContent = match.score.team_a_score;
        if (fbScoreB) fbScoreB.textContent = match.score.team_b_score;

        // Update Football stats bars if present
        const stats = match.score.stats;
        if (stats) {
          const statsMap = [
            { key: 'shots', label: 'Total Shots' },
            { key: 'shots_on_target', label: 'Shots on Target' },
            { key: 'corners', label: 'Corner Kicks' },
            { key: 'fouls', label: 'Fouls' },
            { key: 'offsides', label: 'Offsides' },
            { key: 'yellow_cards', label: 'Yellow Cards' },
            { key: 'red_cards', label: 'Red Cards' }
          ];
          const statsTable = document.querySelector('.match-stats-table');
          if (statsTable) {
            let statsHtml = '';
            statsMap.forEach(item => {
              const valA = (stats.team_a && stats.team_a[item.key]) || 0;
              const valB = (stats.team_b && stats.team_b[item.key]) || 0;
              const total = valA + valB;
              const pctA = total > 0 ? Math.round((valA / total) * 100) : 50;
              const pctB = total > 0 ? Math.round((valB / total) * 100) : 50;

              statsHtml += `
                <div class="stat-row">
                  <div class="stat-header-row">
                    <span class="stat-val-a">${valA}</span>
                    <span class="stat-label">${item.label}</span>
                    <span class="stat-val-b">${valB}</span>
                  </div>
                  <div class="stat-bar-track">
                    <div class="stat-bar-fill-a" style="width: ${pctA}%;"></div>
                    <div class="stat-bar-fill-b" style="width: ${pctB}%;"></div>
                  </div>
                </div>
              `;
            });
            statsTable.innerHTML = statsHtml;
          }
        }

      // GIRLS PENALTY SHOOTOUT
      } else if (match.sport_type === 'penalty_shootout') {
        if (scoreA) scoreA.textContent = `${match.score.team_a_score} Goals`;
        if (scoreB) scoreB.textContent = `${match.score.team_b_score} Goals`;

      // VOLLEYBALL
      } else if (match.sport_type === 'volleyball') {
        if (scoreA) scoreA.textContent = `${match.score.sets_team_a} Sets`;
        if (scoreB) scoreB.textContent = `${match.score.sets_team_b} Sets`;

      // TUG OF WAR
      } else if (match.sport_type === 'tug_of_war') {
        if (scoreA) scoreA.textContent = `${match.score.pulls_team_a} Pulls`;
        if (scoreB) scoreB.textContent = `${match.score.pulls_team_b} Pulls`;

      // RACQUET & CARROM MULTI-DAY TIES
      } else if (['badminton', 'table_tennis', 'carrom'].includes(match.sport_type)) {
        if (scoreA) scoreA.innerHTML = `${match.score.events_won_a} <span class="team-overs-display">Events</span>`;
        if (scoreB) scoreB.innerHTML = `${match.score.events_won_b} <span class="team-overs-display">Events</span>`;
        const leadTitle = document.querySelector('.tie-lead-title');
        const leadSub = document.querySelector('.tie-lead-sub');
        if (leadTitle && match.score.lead_summary) leadTitle.textContent = match.score.lead_summary;
        if (leadSub && match.score.lead_detail) leadSub.textContent = match.score.lead_detail;

        if (match.score.events) {
          match.score.events.forEach((ev) => {
            const card = document.getElementById(`sub-event-${ev.id}`);
            if (card) {
              const setsVal = card.querySelector('.sets-val');
              if (setsVal) setsVal.textContent = `${ev.sets_a} - ${ev.sets_b}`;
              const pointsVal = card.querySelector('.points-val');
              if (pointsVal) pointsVal.textContent = `${ev.current_points_a} - ${ev.current_points_b}`;
            }
          });
        }

      // BASKETBALL SHOOTOUT
      } else if (match.sport_type === 'basketball_shootout') {
        if (scoreA) scoreA.textContent = `${match.score.score_team_a} Pts`;
        if (scoreB) scoreB.textContent = `${match.score.score_team_b} Pts`;
      }
    } catch (e) {
      console.warn('Silent refresh error:', e);
    }
  }

  // =========================================================================
  // 6. Crowd Reactions & Floating Cheers Interaction
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