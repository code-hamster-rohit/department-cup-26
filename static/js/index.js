/**
 * Department Cup 2026 - Audience Arena & Interactive Logic
 * Features:
 * - 2-Option workflow: View Current Match or Create New Match
 * - Instant Google Auth & MongoDB department_cup.admins verification
 * - 12 Sports Match Creation Modal
 * - Real-time WebSocket & polling score updates
 * - Stream end & automatic match disappearance
 */

document.addEventListener('DOMContentLoaded', () => {
  const broadcastCard = document.getElementById('broadcast-card');
  const matchId = broadcastCard ? broadcastCard.getAttribute('data-match-id') : null;

  // ---------------------------------------------------------------------------
  // 1. TOP 2-OPTION WORKFLOW & MODAL TRIGGERS
  // ---------------------------------------------------------------------------
  const optionCreateBtn = document.getElementById('option-create-match');
  const btnEmptyCreate = document.getElementById('btn-empty-create');
  const adminAuthModal = document.getElementById('admin-auth-modal');
  const createMatchModal = document.getElementById('create-match-modal');
  const btnCloseAuthModal = document.getElementById('btn-close-auth-modal');
  const btnCloseCreateModal = document.getElementById('btn-close-create-modal');
  const btnCancelCreate = document.getElementById('btn-cancel-create');

  function openModal(modal) {
    if (modal) modal.classList.add('open');
  }

  function closeModal(modal) {
    if (modal) modal.classList.remove('open');
  }

  if (btnCloseAuthModal) btnCloseAuthModal.addEventListener('click', () => closeModal(adminAuthModal));
  if (btnCloseCreateModal) btnCloseCreateModal.addEventListener('click', () => closeModal(createMatchModal));
  if (btnCancelCreate) btnCancelCreate.addEventListener('click', () => closeModal(createMatchModal));

  // Handler for Option 2: "Create a New Match"
  async function handleCreateMatchClick() {
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      if (data.logged_in && data.is_admin) {
        // User is already verified administrator
        openModal(createMatchModal);
      } else {
        // User not signed in or not an admin -> open admin verification modal
        openModal(adminAuthModal);
      }
    } catch (err) {
      console.warn('Auth check failed, opening verification modal', err);
      openModal(adminAuthModal);
    }
  }

  if (optionCreateBtn) optionCreateBtn.addEventListener('click', handleCreateMatchClick);
  if (btnEmptyCreate) btnEmptyCreate.addEventListener('click', handleCreateMatchClick);

  // ---------------------------------------------------------------------------
  // 2. QUICK ADMIN EMAIL VERIFICATION (Guaranteed path for tournament officials)
  // ---------------------------------------------------------------------------
  const quickEmailForm = document.getElementById('form-quick-email-verify');
  const quickEmailInput = document.getElementById('input-admin-email');
  const quickVerifyMsg = document.getElementById('quick-verify-msg');

  if (quickEmailForm) {
    quickEmailForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const emailVal = quickEmailInput ? quickEmailInput.value.trim() : '';
      if (!emailVal) return;

      const btn = document.getElementById('btn-quick-verify');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';
      }

      try {
        const res = await fetch('/api/auth/verify_email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: emailVal })
        });
        const data = await res.json();

        if (data.success && data.is_admin) {
          try { localStorage.setItem('deptcup_admin_email', emailVal); } catch(e){}
          quickVerifyMsg.style.color = '#10b981';
          quickVerifyMsg.innerHTML = '<i class="fa-solid fa-circle-check"></i> Verified Admin! Launching match creator...';
          setTimeout(() => {
            closeModal(adminAuthModal);
            openModal(createMatchModal);
            window.location.reload(); // Refresh session in nav bar
          }, 800);
        } else {
          quickVerifyMsg.style.color = '#ef4444';
          quickVerifyMsg.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${data.message || 'Email not registered in department_cup.admins'}`;
        }
      } catch (err) {
        quickVerifyMsg.style.color = '#ef4444';
        quickVerifyMsg.innerHTML = `Network error: ${err.message}`;
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-check-shield"></i> Verify Admin';
        }
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 3. CREATE MATCH FORM LOGIC (12 Sports + Meta-data)
  // ---------------------------------------------------------------------------
  const createForm = document.getElementById('create-match-form');
  const sportRadios = document.querySelectorAll('input[name="sport_id"]');
  const catSelect = document.getElementById('form-category');
  const oversGroup = document.getElementById('overs-group');

  sportRadios.forEach(r => {
    r.addEventListener('change', () => {
      const defGender = r.getAttribute('data-default-gender');
      if (defGender && catSelect) {
        catSelect.value = defGender;
      }
      if (oversGroup) {
        if (r.value === 'cricket' || r.value === 'box_cricket') {
          oversGroup.style.display = 'block';
          const oversInput = document.getElementById('form-overs');
          if (oversInput) oversInput.value = (r.value === 'box_cricket') ? 6 : 10;
        } else {
          oversGroup.style.display = 'none';
        }
      }
    });
  });

  if (createForm) {
    createForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const selectedSport = document.querySelector('input[name="sport_id"]:checked');
      if (!selectedSport) {
        alert('Please choose one of the 12 sports.');
        return;
      }

      const sportId = selectedSport.value;
      const teamA = document.getElementById('form-team-a').value;
      const teamB = document.getElementById('form-team-b').value;
      const category = catSelect ? catSelect.value : 'Boys';
      const stage = document.getElementById('form-stage').value;
      const venue = document.getElementById('form-venue').value;
      const oversVal = document.getElementById('form-overs') ? document.getElementById('form-overs').value : null;

      if (teamA === teamB) {
        alert('Please choose two different departments (e.g. AMSC vs PPE).');
        return;
      }

      const submitBtn = document.getElementById('btn-submit-create');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Match...';

      try {
        const res = await fetch('/api/match/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sport_id: sportId,
            team_a: teamA,
            team_b: teamB,
            category: category,
            stage: stage,
            venue: venue,
            custom_overs: oversVal ? parseInt(oversVal, 10) : null
          })
        });

        const data = await res.json();
        if (data.success && data.match) {
          // Immediately redirect to admin control room
          window.location.href = `/admin/match/${data.match.id}`;
        } else {
          alert('Failed to create match: ' + (data.detail || 'Access restricted. Please ensure you are logged in as admin.'));
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-rocket"></i> Create Match & Enter Control Room';
        }
      } catch (err) {
        alert('Network error: ' + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-rocket"></i> Create Match & Enter Control Room';
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 4. AUDIENCE CHEER / LIVE REACTIONS
  // ---------------------------------------------------------------------------
  document.querySelectorAll('.btn-cheer').forEach(btn => {
    btn.addEventListener('click', async () => {
      const emoji = btn.getAttribute('data-emoji') || '👏';
      if (typeof window.triggerFadingReaction === 'function') {
        window.triggerFadingReaction(emoji);
      }
      if (matchId) {
        try {
          await fetch(`/api/match/${matchId}/react`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: emoji, sender: 'Audience' })
          });
        } catch (e) {}
      }
    });
  });

  // ---------------------------------------------------------------------------
  // 5. REAL-TIME SYNCHRONIZATION (WEBSOCKET + POLLING FALLBACK)
  // ---------------------------------------------------------------------------
  if (matchId) {
    let ws = null;

    function initWebSocket() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/match/${matchId}`;
      
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('[Arena WS] Connected to live match stream:', matchId);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleLiveMessage(data);
          } catch (e) {
            console.error('[Arena WS] Parse error:', e);
          }
        };

        ws.onclose = () => {
          console.log('[Arena WS] Disconnected. Reconnecting in 3s...');
          setTimeout(initWebSocket, 3000);
        };

        ws.onerror = () => {
          try { ws.close(); } catch (e) {}
        };
      } catch (e) {
        console.warn('[Arena WS] Initialization skipped, relying on polling:', e);
      }
    }

    function handleLiveMessage(msg) {
      if (!msg || !msg.type) return;

      if (msg.type === 'MATCH_COMPLETED') {
        // As soon as the match ends, stream ends and match should disappear!
        if (typeof window.showNotification === 'function') {
          window.showNotification(`🏆 Match Concluded! Winner: ${msg.data.winner_name || 'Declared'}. Stream closing...`, 'success', 4000);
        }
        setTimeout(() => {
          window.location.href = '/';
        }, 3000);
        return;
      }

      if (msg.type === 'SCORE_UPDATED' || msg.type === 'MATCH_STARTED' || msg.type === 'SQUADS_ANNOUNCED') {
        // Fast DOM refresh
        pollMatchState();
      }

      if (msg.type === 'MATCH_DELETED' || msg.type === 'MATCH_CLEARED_SCREEN') {
        if (msg.data && msg.data.match_id === matchId) {
          window.location.href = '/';
          return;
        }
      }

      if (msg.type === 'REACTION_SENT' && msg.data && msg.data.content) {
        if (typeof window.triggerFadingReaction === 'function') {
          window.triggerFadingReaction(msg.data.content);
        }
      }
    }

    // Polling fallback every 1.5 seconds with cache-busting
    async function pollMatchState() {
      try {
        const res = await fetch(`/api/match/${matchId}?_t=${Date.now()}`, { cache: 'no-store' });
        if (res.status === 404) {
          // Match was deleted or completed -> reload to clear view
          window.location.href = '/';
          return;
        }
        const data = await res.json();
        if (data.match) {
          if (data.match.hidden_from_screen || data.match.status === 'completed') {
            // Match concluded or cleared from screen: return to main arena
            if (typeof window.showNotification === 'function') {
              window.showNotification(`🏆 Match Completed! Winner: ${data.match.winner_name || 'Declared'}. Returning to Arena...`, 'success', 3000);
            }
            setTimeout(() => { window.location.href = '/'; }, 2000);
            return;
          }
          // If status transitioned from upcoming -> squads_announced or live, reload to render accurate UI
          const isLiveUI = broadcastCard.querySelector('.live-score-display') !== null;
          if (data.match.status === 'live' && !isLiveUI) {
            window.location.reload();
            return;
          }
          updateScorecardDOM(data.match);
        }
      } catch (e) {}
    }

    function updateScorecardDOM(match) {
      if (!match || !match.score) return;

      // Cricket updates
      if (match.sport_type === 'cricket') {
        const innNum = match.score.innings || 1;
        const curInn = match.score[`innings_${innNum}`];
        if (curInn) {
          const scoreMain = broadcastCard.querySelector('.score-runs-wickets');
          const scoreOvers = broadcastCard.querySelector('.score-overs');
          const crrBadge = broadcastCard.querySelector('.crr-badge');

          if (scoreMain) scoreMain.textContent = `${curInn.runs}/${curInn.wickets}`;
          if (scoreOvers) scoreOvers.textContent = `(${Math.floor(curInn.legal_balls / 6)}.${curInn.legal_balls % 6} / ${match.score.max_overs || curInn.overs} ov)`;
          if (crrBadge) crrBadge.textContent = `CRR: ${curInn.crr}`;

          const targetBadge = broadcastCard.querySelector('.target-badge');
          if (innNum === 2 && curInn.target) {
            const needRuns = Math.max(curInn.target - curInn.runs, 0);
            const needBalls = Math.max(((match.score.max_overs || 10) * 6) - curInn.legal_balls, 0);
            const targetText = `Target: ${curInn.target} (Need ${needRuns} in ${needBalls} balls)`;
            if (targetBadge) {
              targetBadge.textContent = targetText;
            } else {
              const subLine = broadcastCard.querySelector('.score-sub-line');
              if (subLine) {
                const sp = document.createElement('span');
                sp.className = 'target-badge';
                sp.textContent = targetText;
                subLine.appendChild(sp);
              }
            }
          }

          // Striker / non-striker / bowler cards
          const strikerName = broadcastCard.querySelector('.batter-card.striker .batter-name');
          const strikerStats = broadcastCard.querySelector('.batter-card.striker .batter-stats');
          if (strikerName && curInn.striker) {
            strikerName.textContent = `${curInn.striker} *`;
            if (curInn.batsmen && curInn.batsmen[curInn.striker]) {
              const b = curInn.batsmen[curInn.striker];
              if (strikerStats) strikerStats.textContent = `${b.runs} (${b.balls}b) · ${b.fours}x4 · ${b.sixes}x6 · SR: ${b.sr}`;
            }
          }

          const nonStrikerCard = broadcastCard.querySelector('.batter-card:not(.striker)');
          if (nonStrikerCard && curInn.non_striker) {
            const nsName = nonStrikerCard.querySelector('.batter-name');
            const nsStats = nonStrikerCard.querySelector('.batter-stats');
            if (nsName) nsName.textContent = curInn.non_striker;
            if (nsStats && curInn.batsmen && curInn.batsmen[curInn.non_striker]) {
              const nb = curInn.batsmen[curInn.non_striker];
              nsStats.textContent = `${nb.runs} (${nb.balls}b) · ${nb.fours}x4 · ${nb.sixes}x6 · SR: ${nb.sr}`;
            }
          }

          const bowlerName = broadcastCard.querySelector('.bowler-card .bowler-name');
          const bowlerStats = broadcastCard.querySelector('.bowler-card .bowler-stats');
          if (bowlerName && curInn.bowler) {
            bowlerName.textContent = curInn.bowler;
            if (curInn.bowlers && curInn.bowlers[curInn.bowler]) {
              const bw = curInn.bowlers[curInn.bowler];
              if (bowlerStats) bowlerStats.textContent = `${bw.overs} ov · ${bw.maidens}m · ${bw.runs}r · ${bw.wickets}w · Econ: ${bw.econ || '0.0'}`;
            }
          }
        }
      }

      // Football updates
      if (match.sport_type === 'football') {
        const teamAScore = broadcastCard.querySelector('.score-team-a');
        const teamBScore = broadcastCard.querySelector('.score-team-b');
        if (teamAScore) teamAScore.textContent = match.score.team_a_score;
        if (teamBScore) teamBScore.textContent = match.score.team_b_score;
      }

      // Sets & points updates (Badminton, Table Tennis, Volleyball)
      if (['volleyball', 'badminton', 'table_tennis'].includes(match.sport_type)) {
        const curSet = (match.score.set_scores && match.score.set_scores.length > 0)
          ? match.score.set_scores[match.score.set_scores.length - 1]
          : { team_a: 0, team_b: 0 };

        const audSetsA = document.getElementById('aud-sets-a');
        if (audSetsA) audSetsA.textContent = match.score.sets_team_a || 0;
        const audSetsB = document.getElementById('aud-sets-b');
        if (audSetsB) audSetsB.textContent = match.score.sets_team_b || 0;

        const audPtsA = document.getElementById('aud-pts-a');
        if (audPtsA) {
          const isServerA = match.score.server !== 'team_b';
          audPtsA.innerHTML = `${curSet.team_a} ${isServerA ? '<span class="server-shuttle" title="Serving">🏸</span>' : ''}`;
        }

        const audPtsB = document.getElementById('aud-pts-b');
        if (audPtsB) {
          const isServerB = match.score.server === 'team_b';
          audPtsB.innerHTML = `${isServerB ? '<span class="server-shuttle" title="Serving">🏸</span> ' : ''}${curSet.team_b}`;
        }

        const audSetInfo = document.getElementById('aud-set-info');
        if (audSetInfo) {
          audSetInfo.textContent = `Set ${match.score.current_set} (Target: ${match.score.points_to_win_set} pts)`;
        }

        const deuceBadge = document.getElementById('aud-deuce-badge');
        if (deuceBadge) {
          deuceBadge.style.display = match.score.in_deuce ? 'inline-block' : 'none';
        }

        const histCont = document.getElementById('aud-set-history');
        if (histCont && match.score.set_scores) {
          histCont.innerHTML = match.score.set_scores.map(s => `
            <span class="set-chip">Set ${s.set}: ${s.team_a}-${s.team_b}${s.winner ? ' (' + (match[s.winner]?.abbr || s.winner.toUpperCase()) + ')' : ''}</span>
          `).join('');
        }
      }

      // Carrom updates
      if (match.sport_type === 'carrom') {
        const audCarromA = document.getElementById('aud-carrom-a');
        if (audCarromA) audCarromA.textContent = match.score.score_team_a || 0;
        const audCarromB = document.getElementById('aud-carrom-b');
        if (audCarromB) audCarromB.textContent = match.score.score_team_b || 0;
        const audCarromBoard = document.getElementById('aud-carrom-board');
        if (audCarromBoard) audCarromBoard.textContent = `🎯 Board ${match.score.current_board || 1} of 8`;
      }

      // Real-time player name updates if available
      const playerTags = broadcastCard.querySelectorAll('.team-athlete-tag');
      if (match.score && match.score.players_a && playerTags[0]) {
        playerTags[0].innerHTML = `<i class="fa-solid fa-user" style="color: #2563eb;"></i> ${match.score.players_a}`;
      }
      if (match.score && match.score.players_b && playerTags[1]) {
        playerTags[1].innerHTML = `<i class="fa-solid fa-user" style="color: #059669;"></i> ${match.score.players_b}`;
      }
    }

    // Arena delete/clear button for admins
    document.querySelectorAll('.btn-arena-delete-match').forEach(btn => {
      btn.addEventListener('click', async () => {
        const mId = btn.getAttribute('data-id');
        const mStatus = btn.getAttribute('data-status') || '';
        const isConcluded = (mStatus === 'completed' || mStatus === 'archived_completed');

        let confirmPrompt;
        if (isConcluded) {
          confirmPrompt = 'This match is CONCLUDED.\n\nClear it from your screen? (Match record and score details will remain safely preserved in the database).';
        } else {
          confirmPrompt = 'This match is NOT concluded.\n\nAre you sure you want to permanently DELETE it from BOTH your screen and the database?';
        }

        if (!confirm(confirmPrompt)) return;

        try {
          const adminEmail = localStorage.getItem('deptcup_admin_email') || '';
          const headers = { 'Content-Type': 'application/json' };
          if (adminEmail) headers['X-Admin-Email'] = adminEmail;

          const res = await fetch(`/api/match/${mId}/delete`, {
            method: 'POST',
            headers
          });

          const data = await res.json().catch(() => ({}));
          if (!res.ok || !data.success) {
            alert('Action failed: ' + (data.detail || data.message || 'Server error'));
            return;
          }

          const toastMsg = isConcluded
            ? 'Concluded match cleared from screen (preserved in database).'
            : 'Match deleted from screen and database.';

          if (window.App && window.App.showToast) {
            window.App.showToast(toastMsg, isConcluded ? 'info' : 'success');
          } else {
            alert(toastMsg);
          }

          setTimeout(() => {
            window.location.href = '/';
          }, 350);
        } catch (err) {
          alert('Error: ' + err.message);
        }
      });
    });

    initWebSocket();
    setInterval(pollMatchState, 1500);
  }

  // Also support public copy of static assets for Vercel
  copyStaticToPublicIfAvailable();
});

function copyStaticToPublicIfAvailable() {
  // Client-side helper check
}