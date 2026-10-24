/**
 * Administrator Center & Scorer Control Room interactive logic.
 */

document.addEventListener('DOMContentLoaded', () => {
  // -------------------------------------------------------------
  // 1. ADMIN DASHBOARD: CREATE MATCH MODAL
  // -------------------------------------------------------------
  const btnOpenCreate = document.getElementById('btn-open-create-match');
  const btnEmptyStart = document.getElementById('btn-empty-start');
  const createModal = document.getElementById('create-match-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnCancelModal = document.getElementById('btn-cancel-modal');
  const createForm = document.getElementById('create-match-form');

  function openCreateModal() {
    if (createModal) createModal.classList.add('open');
  }

  function closeCreateModal() {
    if (createModal) createModal.classList.remove('open');
  }

  if (btnOpenCreate) btnOpenCreate.addEventListener('click', openCreateModal);
  if (btnEmptyStart) btnEmptyStart.addEventListener('click', openCreateModal);
  if (btnCloseModal) btnCloseModal.addEventListener('click', closeCreateModal);
  if (btnCancelModal) btnCancelModal.addEventListener('click', closeCreateModal);

  const sportSelect = document.getElementById('form-sport');
  const catSelect = document.getElementById('form-category');
  if (sportSelect && catSelect) {
    sportSelect.addEventListener('change', () => {
      const selectedOpt = sportSelect.options[sportSelect.selectedIndex];
      const defGender = selectedOpt ? selectedOpt.getAttribute('data-default-gender') : null;
      if (defGender) {
        catSelect.value = defGender;
      }
    });
  }

  if (createForm) {
    createForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const sportId = document.getElementById('form-sport').value;
      const categoryVal = document.getElementById('form-category') ? document.getElementById('form-category').value : '';
      const teamA = document.getElementById('form-team-a').value;
      const teamB = document.getElementById('form-team-b').value;
      const venue = document.getElementById('form-venue').value;
      const stage = document.getElementById('form-stage').value;
      const dayVal = document.getElementById('form-day') ? document.getElementById('form-day').value : 'Day 1';
      const schedDateVal = document.getElementById('form-sched-date') ? document.getElementById('form-sched-date').value : '';
      const oversVal = document.getElementById('form-overs').value;

      if (teamA === teamB) {
        alert('Please choose two different departments.');
        return;
      }

      const submitBtn = document.getElementById('btn-submit-match');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating...';

      try {
        const res = await fetch('/api/match/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sport_id: sportId,
            category: categoryVal,
            team_a: teamA,
            team_b: teamB,
            venue: venue,
            stage: stage,
            day_label: dayVal,
            scheduled_date: schedDateVal,
            custom_overs: oversVal ? parseInt(oversVal, 10) : null
          })
        });

        const data = await res.json();
        if (data.success && data.match) {
          window.location.href = `/admin/match/${data.match.id}`;
        } else {
          alert('Error: ' + (data.detail || 'Failed creating match'));
          submitBtn.disabled = false;
        }
      } catch (err) {
        alert('Network error: ' + err.message);
        submitBtn.disabled = false;
      }
    });
  }

  // Delete match handler
  document.querySelectorAll('.btn-delete-match').forEach(btn => {
    btn.addEventListener('click', async () => {
      const matchId = btn.getAttribute('data-id');
      if (!confirm('Are you sure you want to delete/reset this match?')) return;

      try {
        const res = await fetch(`/api/match/${matchId}/delete`, { method: 'POST' });
        if (res.ok) {
          const card = document.getElementById(`match-card-${matchId}`);
          if (card) card.remove();
          window.App.showToast('Match removed successfully.', 'info');
        }
      } catch (err) {
        alert('Error deleting match: ' + err.message);
      }
    });
  });

  // -------------------------------------------------------------
  // 2. MATCH CONTROL ROOM (STEP 2: SQUADS & TOSS)
  // -------------------------------------------------------------
  const root = document.querySelector('.control-room-root');
  if (!root) return;

  const matchId = root.getAttribute('data-match-id');
  const sportType = root.getAttribute('data-sport-type');

  const btnStartMatchLive = document.getElementById('btn-start-match-live');

  if (btnStartMatchLive) {
    btnStartMatchLive.addEventListener('click', async () => {
      if (!confirm('Commence match and start live scoring?')) return;
      try {
        btnStartMatchLive.disabled = true;
        const tossWinner = document.getElementById('toss-winner-select')?.value;
        const tossDecision = document.getElementById('toss-decision-select')?.value;
        const playersA = document.getElementById('input-players-a')?.value.trim() || '';
        const playersB = document.getElementById('input-players-b')?.value.trim() || '';

        // Save players and toss
        await fetch(`/api/match/${matchId}/players`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            players_a: playersA,
            players_b: playersB,
            toss_winner: tossWinner,
            toss_decision: tossDecision
          })
        });

        const res = await fetch(`/api/match/${matchId}/start`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          window.App.showToast('Match is now LIVE! Scorer unlocked.', 'live');
          setTimeout(() => window.location.reload(), 500);
        } else {
          alert('Error starting match: ' + (data.detail || ''));
          btnStartMatchLive.disabled = false;
        }
      } catch (err) {
        alert('Error starting match: ' + err.message);
        btnStartMatchLive.disabled = false;
      }
    });
  }

  // Interactive View Tabs (Lineups & Toss vs Scorer Cockpit)
  const tabSquads = document.getElementById('tab-btn-squads');
  const tabScorer = document.getElementById('tab-btn-scorer');
  const squadsSection = document.getElementById('squads-section');
  const scorerSection = document.getElementById('live-scorer-section');

  if (tabSquads && tabScorer) {
    tabSquads.addEventListener('click', () => {
      tabSquads.classList.add('active');
      tabScorer.classList.remove('active');
      if (squadsSection) squadsSection.classList.remove('d-none');
      if (scorerSection) scorerSection.classList.add('d-none');
    });
    tabScorer.addEventListener('click', () => {
      tabScorer.classList.add('active');
      tabSquads.classList.remove('active');
      if (squadsSection) squadsSection.classList.add('d-none');
      if (scorerSection) scorerSection.classList.remove('d-none');
    });
  }

  // Visual Toss Cards synchronization
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

  // Rotate Strike button
  const btnRotateStrike = document.getElementById('btn-rotate-strike');
  if (btnRotateStrike) {
    btnRotateStrike.addEventListener('click', () => {
      const s1 = document.getElementById('select-striker');
      const s2 = document.getElementById('select-non-striker');
      if (s1 && s2) {
        const temp = s1.value;
        s1.value = s2.value;
        s2.value = temp;
        if (window.App && window.App.showToast) {
          window.App.showToast(`Strike rotated: ${s1.value} now facing`, 'info');
        }
      }
    });
  }

  // -------------------------------------------------------------
  // 3. LIVE SCORER KEYPAD ACTIONS
  // -------------------------------------------------------------
  async function sendScoreAction(action) {
    try {
      const res = await fetch(`/api/match/${matchId}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action)
      });
      const data = await res.json();
      if (data.success) {
        updateControlRoomUI(data.match);
      } else {
        alert('Error: ' + (data.detail || 'Action rejected'));
      }
    } catch (err) {
      console.error('Score action error:', err);
    }
  }

  function getCricketContext() {
    return {
      striker: document.getElementById('select-striker')?.value,
      non_striker: document.getElementById('select-non-striker')?.value,
      bowler: document.getElementById('select-bowler')?.value
    };
  }

  // Runs buttons
  document.querySelectorAll('.btn-run').forEach(btn => {
    btn.addEventListener('click', () => {
      const runs = parseInt(btn.getAttribute('data-runs'), 10);
      const ctx = getCricketContext();
      sendScoreAction({ type: 'run', runs: runs, ...ctx });
    });
  });

  // Extras
  const btnWide = document.getElementById('btn-wide');
  const btnNoball = document.getElementById('btn-noball');
  const btnBye = document.getElementById('btn-bye');
  const btnLegbye = document.getElementById('btn-legbye');

  if (btnWide) btnWide.addEventListener('click', () => sendScoreAction({ type: 'extra', extra_type: 'wide', runs: 1, ...getCricketContext() }));
  if (btnNoball) btnNoball.addEventListener('click', () => sendScoreAction({ type: 'extra', extra_type: 'no_ball', runs: 1, ...getCricketContext() }));
  if (btnBye) btnBye.addEventListener('click', () => sendScoreAction({ type: 'extra', extra_type: 'bye', runs: 1, ...getCricketContext() }));
  if (btnLegbye) btnLegbye.addEventListener('click', () => sendScoreAction({ type: 'extra', extra_type: 'leg_bye', runs: 1, ...getCricketContext() }));

  // Wickets
  document.querySelectorAll('.wicket-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const dismissal = btn.getAttribute('data-dismissal');
      if (!dismissal) return;
      const ctx = getCricketContext();
      const newBatter = prompt(`New batsman to replace ${ctx.striker}:`, '');
      sendScoreAction({ type: 'wicket', dismissal: dismissal, new_batsman: newBatter, ...ctx });
    });
  });

  // Dead ball (Box cricket)
  const btnDeadBall = document.getElementById('btn-box-dead-ball');
  const btnDeadBallPenalty = document.getElementById('btn-box-dead-ball-penalty');
  if (btnDeadBall) btnDeadBall.addEventListener('click', () => sendScoreAction({ type: 'dead_ball', is_special_dead_ball_penalty: false, ...getCricketContext() }));
  if (btnDeadBallPenalty) btnDeadBallPenalty.addEventListener('click', () => sendScoreAction({ type: 'dead_ball', is_special_dead_ball_penalty: true, ...getCricketContext() }));

  // Switch Innings
  const btnSwitchInn = document.getElementById('btn-switch-innings');
  if (btnSwitchInn) {
    btnSwitchInn.addEventListener('click', () => {
      if (confirm('Conclude 1st Innings and switch to 2nd Innings (Target will be set)?')) {
        sendScoreAction({ type: 'switch_innings' });
      }
    });
  }

  // Football Goals & Cards & Match Statistics
  document.querySelectorAll('.btn-fb-goal').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const player = prompt('Goal scorer name:', 'Player') || 'Player';
      const assist = prompt('Assist provider name (optional):', '') || '';
      const min = prompt('Minute (e.g. 23\'):', '23\'') || '23\'';
      sendScoreAction({ type: 'goal', team: team, player: player, assist: assist, minute: min });
    });
  });

  document.querySelectorAll('.btn-fb-card').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const card = btn.getAttribute('data-card');
      const player = prompt('Card recipient player name:', 'Player') || 'Player';
      sendScoreAction({ type: 'card', team: team, player: player, card_color: card });
    });
  });

  // Fast Match Stats +1 buttons (SofaScore style)
  document.querySelectorAll('.btn-fb-stat').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const statKey = btn.getAttribute('data-stat');
      sendScoreAction({ type: 'stat', team: team, stat_key: statKey, delta: 1 });
    });
  });

  // Football Period / Half Switch
  document.querySelectorAll('.btn-fb-period').forEach(btn => {
    btn.addEventListener('click', () => {
      const half = parseInt(btn.getAttribute('data-half'), 10);
      sendScoreAction({ type: 'update_half', half: half });
    });
  });

  // Girls Penalty Shootout Kicks
  document.querySelectorAll('.btn-shootout-kick').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const result = btn.getAttribute('data-result');
      const player = prompt('Penalty taker name:', 'Shooter') || 'Shooter';
      sendScoreAction({ type: 'kick', team: team, result: result, player: player });
    });
  });

  // Tactile Point Scoring (+1 / -1) for Set-Based Sports (Badminton, Table Tennis, Volleyball)
  document.querySelectorAll('.btn-point-action').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const delta = parseInt(btn.getAttribute('data-delta') || '1', 10);
      sendScoreAction({ type: 'point', team: team, delta: delta });
    });
  });

  // Switch Server
  const btnSwapServer = document.getElementById('btn-swap-server');
  if (btnSwapServer) {
    btnSwapServer.addEventListener('click', () => {
      sendScoreAction({ type: 'swap_server' });
    });
  }

  // Finish Set
  const btnConcludeSet = document.getElementById('btn-conclude-set');
  if (btnConcludeSet) {
    btnConcludeSet.addEventListener('click', () => {
      if (confirm('Conclude the current set and move to next set?')) {
        sendScoreAction({ type: 'end_set' });
      }
    });
  }

  // Volleyball Timeout
  document.querySelectorAll('.btn-vb-timeout').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      sendScoreAction({ type: 'timeout', team: team });
    });
  });

  // Carrom Points & Boards
  document.querySelectorAll('.btn-carrom-add').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const pts = parseInt(btn.getAttribute('data-pts') || '1', 10);
      sendScoreAction({ type: 'points', team: team, delta: pts });
    });
  });

  const btnNextCarromBoard = document.getElementById('btn-next-carrom-board');
  if (btnNextCarromBoard) {
    btnNextCarromBoard.addEventListener('click', () => {
      if (confirm('Conclude this board and record cumulative score?')) {
        sendScoreAction({ type: 'end_board' });
      }
    });
  }

  // Tug of War
  document.querySelectorAll('.btn-tow-win').forEach(btn => {
    btn.addEventListener('click', () => {
      const winner = btn.getAttribute('data-winner');
      const dur = prompt('Pull duration in seconds (optional, e.g. 45s):', '45s') || '45s';
      sendScoreAction({ type: 'pull_won', winner: winner, duration: dur });
    });
  });

  // Athletics attempt form (World Athletics Field Scoring)
  const athForm = document.getElementById('form-athletics-attempt');
  if (athForm) {
    athForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const bib = document.getElementById('ath-bib')?.value || '';
      const name = document.getElementById('ath-name').value;
      const dept = document.getElementById('ath-dept').value;
      const attemptType = document.getElementById('ath-attempt-type').value;
      const isFoul = document.getElementById('ath-foul')?.checked;
      const distInput = document.getElementById('ath-dist').value;
      const dist = isFoul ? 0.0 : (parseFloat(distInput) || 0.0);

      sendScoreAction({
        type: 'attempt',
        bib: bib,
        name: name,
        department: dept,
        attempt_type: attemptType,
        distance: dist,
        foul: isFoul
      });
      document.getElementById('ath-dist').value = '';
      if (document.getElementById('ath-foul')) document.getElementById('ath-foul').checked = false;
    });
  }

  // Basketball shootout (Individual Shooter Tracking)
  document.querySelectorAll('.btn-bb-shot').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const zone = parseInt(btn.getAttribute('data-zone'), 10);
      const success = btn.getAttribute('data-success') === 'true';
      const shooterSelect = document.getElementById(team === 'team_a' ? 'select-bb-shooter-a' : 'select-bb-shooter-b');
      const shooter = (shooterSelect ? shooterSelect.value : '') || 'Shooter';
      sendScoreAction({ type: 'shot', team: team, zone: zone, success: success, player: shooter });
    });
  });


  // Undo button
  const btnUndo = document.getElementById('btn-undo-action');
  if (btnUndo) {
    btnUndo.addEventListener('click', async () => {
      try {
        const res = await fetch(`/api/match/${matchId}/undo`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          window.App.showToast('Last action undone.', 'info');
          setTimeout(() => window.location.reload(), 400);
        } else {
          alert('Undo failed: ' + (data.detail || ''));
        }
      } catch (err) {
        alert('Undo error: ' + err.message);
      }
    });
  }

  // Custom commentary broadcast
  const commForm = document.getElementById('form-custom-commentary');
  if (commForm) {
    commForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = document.getElementById('custom-comment-text');
      const text = input.value.trim();
      if (!text) return;
      sendScoreAction({ type: 'commentary_note', commentary: text, ...getCricketContext() });
      input.value = '';
    });
  }

  // Conclude match modal & declare winner
  const concludeModal = document.getElementById('conclude-match-modal');
  const btnCloseConclude = document.getElementById('btn-close-conclude-modal');
  const btnCancelConclude = document.getElementById('btn-cancel-conclude');
  const concludeForm = document.getElementById('form-conclude-match');

  document.querySelectorAll('.btn-trigger-conclude, #btn-open-conclude, #btn-top-conclude, #btn-conclude-match-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      if (concludeModal) {
        concludeModal.classList.add('open');
        concludeModal.classList.remove('d-none');
      }
    });
  });

  if (btnCloseConclude) {
    btnCloseConclude.addEventListener('click', () => {
      if (concludeModal) concludeModal.classList.remove('open');
    });
  }
  if (btnCancelConclude) {
    btnCancelConclude.addEventListener('click', () => {
      if (concludeModal) concludeModal.classList.remove('open');
    });
  }

  if (concludeForm) {
    concludeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const winner = document.getElementById('conclude-winner').value;
      const summary = document.getElementById('conclude-summary').value;
      const motm = document.getElementById('conclude-motm') ? document.getElementById('conclude-motm').value : '';

      const submitBtn = concludeForm.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving Result...';
      }

      try {
        const res = await fetch(`/api/match/${matchId}/end`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            winner: winner,
            result_summary: summary,
            player_of_the_match: motm
          })
        });
        const data = await res.json();
        if (data.success) {
          alert('🏆 Match Concluded! Winner declared and live stream ended. The match has disappeared from the live arena.');
          window.location.href = '/admin';
        } else {
          alert('Failed to end match: ' + (data.detail || 'Error'));
          if (submitBtn) submitBtn.disabled = false;
        }
      } catch (err) {
        alert('Network error: ' + err.message);
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  function updateControlRoomUI(match) {
    // Fast update of live score banner
    const scoreText = document.getElementById('admin-current-score-text');
    if (scoreText) {
      if (match.sport_type === 'cricket') {
        const inn = match.score.innings === 1 ? match.score.innings_1 : match.score.innings_2;
        scoreText.textContent = `${match[inn.team].abbr} ${inn.runs}/${inn.wickets} (${inn.overs} ov)`;
      } else if (match.sport_type === 'football') {
        scoreText.textContent = `${match.team_a.abbr} ${match.score.team_a_score} : ${match.score.team_b_score} ${match.team_b.abbr}`;
      } else if (match.sport_type === 'penalty_shootout') {
        scoreText.textContent = `${match.team_a.abbr} ${match.score.team_a_score} : ${match.score.team_b_score} ${match.team_b.abbr} (PK)`;
      } else if (['volleyball', 'badminton', 'table_tennis'].includes(match.sport_type)) {
        const curSet = (match.score.set_scores && match.score.set_scores.length > 0) ? match.score.set_scores[match.score.set_scores.length - 1] : { team_a: 0, team_b: 0 };
        scoreText.textContent = `${match.team_a.abbr} ${match.score.sets_team_a || 0} : ${match.score.sets_team_b || 0} ${match.team_b.abbr} (Set ${match.score.current_set}: ${curSet.team_a}-${curSet.team_b})`;

        const ptsA = document.getElementById('display-pts-a');
        if (ptsA) ptsA.textContent = curSet.team_a;
        const ptsB = document.getElementById('display-pts-b');
        if (ptsB) ptsB.textContent = curSet.team_b;

        const setsA = document.getElementById('admin-sets-a');
        if (setsA) setsA.textContent = match.score.sets_team_a || 0;
        const setsB = document.getElementById('admin-sets-b');
        if (setsB) setsB.textContent = match.score.sets_team_b || 0;

        const badgeSet = document.getElementById('badge-current-set');
        if (badgeSet) badgeSet.textContent = match.score.current_set;

        const badgeServer = document.getElementById('badge-server');
        if (badgeServer) {
          const sTeam = match.score.server === 'team_b' ? match.team_b.abbr : match.team_a.abbr;
          badgeServer.textContent = `🏸 Serving: ${sTeam}`;
        }

        const histCont = document.getElementById('set-history-container');
        if (histCont && match.score.set_scores) {
          histCont.innerHTML = '<span style="font-weight: 700;">Set Breakdown: </span>' + 
            match.score.set_scores.map(s => `<span class="badge" style="background: rgba(0,0,0,0.06); color: var(--text-main); font-weight: 700; margin-left: 0.35rem;">Set ${s.set}: ${s.team_a}-${s.team_b}${s.winner ? ' (' + match[s.winner].abbr + ')' : ''}</span>`).join('');
        }
      } else if (match.sport_type === 'carrom') {
        scoreText.textContent = `${match.team_a.abbr} ${match.score.score_team_a || 0} : ${match.score.score_team_b || 0} ${match.team_b.abbr} (Board ${match.score.current_board || 1})`;
        const carromA = document.getElementById('display-carrom-a');
        if (carromA) carromA.textContent = match.score.score_team_a || 0;
        const carromB = document.getElementById('display-carrom-b');
        if (carromB) carromB.textContent = match.score.score_team_b || 0;
        const boardEl = document.getElementById('admin-current-board');
        if (boardEl) boardEl.textContent = match.score.current_board || 1;
      }
    }

    // Period display for football
    const periodDisplay = document.getElementById('admin-current-period-display');
    if (periodDisplay && match.score && match.score.period_label) {
      periodDisplay.textContent = match.score.period_label;
    }

    // Free hit banner
    const freeHitBanner = document.getElementById('admin-freehit-banner');
    if (freeHitBanner) {
      freeHitBanner.classList.toggle('d-none', !match.score.is_free_hit);
      freeHitBanner.style.display = match.score.is_free_hit ? 'flex' : 'none';
    }

  }

  // Admin Directory Modal
  const btnOpenAdmins = document.getElementById('btn-open-admins-modal');
  const modalAdmins = document.getElementById('admins-directory-modal');
  const btnCloseAdmins = document.getElementById('btn-close-admins-modal');
  const formAddAdmin = document.getElementById('form-add-admin');
  const adminsListContainer = document.getElementById('admins-list-container');

  async function loadAdminsList() {
    if (!adminsListContainer) return;
    adminsListContainer.innerHTML = '<div style="color: var(--text-dim); font-size: 0.85rem;"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>';
    try {
      const res = await fetch('/api/admins');
      const data = await res.json();
      if (data.admins && data.admins.length > 0) {
        adminsListContainer.innerHTML = data.admins.map((adm, i) => `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.85rem;">
            <span><i class="fa-solid fa-circle-check" style="color: #10b981; font-size: 0.75rem; margin-right: 0.4rem;"></i> ${adm}</span>
            <span class="badge badge-admin" style="font-size: 0.6rem;">ADMIN</span>
          </div>
        `).join('');
      } else {
        adminsListContainer.innerHTML = '<div style="color: var(--text-dim); font-size: 0.85rem;">No admins registered yet.</div>';
      }
    } catch (e) {
      adminsListContainer.innerHTML = `<div style="color: #ef4444; font-size: 0.85rem;">Failed to load admins: ${e.message}</div>`;
    }
  }

  if (btnOpenAdmins) {
    btnOpenAdmins.addEventListener('click', () => {
      if (modalAdmins) modalAdmins.classList.add('open');
      loadAdminsList();
    });
  }

  if (btnCloseAdmins) {
    btnCloseAdmins.addEventListener('click', () => {
      if (modalAdmins) modalAdmins.classList.remove('open');
    });
  }

  if (formAddAdmin) {
    formAddAdmin.addEventListener('submit', async (e) => {
      e.preventDefault();
      const input = document.getElementById('new-admin-email');
      const email = input.value.trim();
      if (!email) return;

      try {
        const res = await fetch('/api/admins/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: email })
        });
        const data = await res.json();
        if (data.success) {
          window.App.showToast(`Admin '${email}' added to MongoDB!`, 'success');
          input.value = '';
          loadAdminsList();
        } else {
          alert('Failed to add admin');
        }
      } catch (err) {
        alert('Error adding admin: ' + err.message);
      }
    });
  }
});
