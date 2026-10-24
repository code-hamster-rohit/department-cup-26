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

  const btnAnnounceSquads = document.getElementById('btn-announce-squads');
  const btnStartMatchLive = document.getElementById('btn-start-match-live');

  function extractSquadFromTextarea(textareaId) {
    const el = document.getElementById(textareaId);
    if (!el) return null;
    const text = el.value.trim();
    if (!text) return { playing: [], substitutes: [] };
    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    const playing = lines.map(line => {
      const isCaptain = /\(c\)/i.test(line);
      const cleanName = line.replace(/\(c\)/i, '').trim();
      return {
        name: cleanName,
        role: isCaptain ? 'Captain' : 'Player',
        is_captain: isCaptain,
        student_id: ''
      };
    });
    return { playing, substitutes: [] };
  }

  if (btnAnnounceSquads) {
    btnAnnounceSquads.addEventListener('click', async () => {
      const tossWinner = document.getElementById('toss-winner-select').value;
      const tossDecision = document.getElementById('toss-decision-select').value;
      const squadA = extractSquadFromTextarea('squad-team-a-input') || {};
      const squadB = extractSquadFromTextarea('squad-team-b-input') || {};

      try {
        btnAnnounceSquads.disabled = true;
        const res = await fetch(`/api/match/${matchId}/squads`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            squad_a: squadA,
            squad_b: squadB,
            toss_winner: tossWinner,
            toss_decision: tossDecision
          })
        });
        const data = await res.json();
        if (data.success) {
          window.App.showToast('Squads & Toss confirmed! Visible on audience view.', 'success');
          setTimeout(() => window.location.reload(), 500);
        } else {
          alert('Failed announcing squads: ' + (data.detail || ''));
          btnAnnounceSquads.disabled = false;
        }
      } catch (err) {
        alert('Error: ' + err.message);
        btnAnnounceSquads.disabled = false;
      }
    });
  }

  if (btnStartMatchLive) {
    btnStartMatchLive.addEventListener('click', async () => {
      if (!confirm('Commence match and start live streaming to audience view?')) return;
      try {
        btnStartMatchLive.disabled = true;
        // Auto-save entered squads and toss before commencing
        const tossWinner = document.getElementById('toss-winner-select')?.value;
        const tossDecision = document.getElementById('toss-decision-select')?.value;
        const squadA = extractSquadFromTextarea('squad-team-a-input') || {};
        const squadB = extractSquadFromTextarea('squad-team-b-input') || {};

        if (tossWinner && tossDecision) {
          await fetch(`/api/match/${matchId}/squads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              squad_a: squadA,
              squad_b: squadB,
              toss_winner: tossWinner,
              toss_decision: tossDecision
            })
          });
        }

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

  // Volleyball Points & Timeouts
  document.querySelectorAll('.btn-vb-point').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      sendScoreAction({ type: 'point', team: team });
    });
  });

  document.querySelectorAll('.btn-vb-timeout').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      sendScoreAction({ type: 'timeout', team: team });
    });
  });

  // Racquet / Carrom Points
  document.querySelectorAll('.btn-racquet-point').forEach(btn => {
    btn.addEventListener('click', () => {
      const team = btn.getAttribute('data-team');
      const evIdx = parseInt(btn.getAttribute('data-ev-idx') || '0', 10);
      sendScoreAction({ type: 'point', team: team, event_index: evIdx });
    });
  });

  // Activate specific rubber to score live
  document.querySelectorAll('.btn-activate-rubber').forEach(btn => {
    btn.addEventListener('click', () => {
      const evIdx = parseInt(btn.getAttribute('data-ev-idx') || '0', 10);
      sendScoreAction({ type: 'activate_event', event_index: evIdx });
    });
  });

  // Pause tie until next scheduled day
  const btnPauseTie = document.getElementById('btn-pause-tie-day');
  if (btnPauseTie) {
    btnPauseTie.addEventListener('click', () => {
      const note = prompt('Enter note for pause (e.g. Day 1 complete. Tie resumes on Day 2 with Boys Doubles):', 'Day 1 rubbers completed. Tie resumes on scheduled day.') || 'Tie paused.';
      sendScoreAction({ type: 'pause_tie', note: note });
    });
  }

  // Quick direct result logger modal
  const modalQuickRes = document.getElementById('modal-quick-result');
  const btnCloseQuickRes = document.getElementById('btn-close-quick-res');
  const btnCancelQuickRes = document.getElementById('btn-cancel-quick-res');
  const formQuickRes = document.getElementById('form-quick-result');

  function closeQuickResModal() {
    if (modalQuickRes) modalQuickRes.classList.add('d-none');
  }
  if (btnCloseQuickRes) btnCloseQuickRes.addEventListener('click', closeQuickResModal);
  if (btnCancelQuickRes) btnCancelQuickRes.addEventListener('click', closeQuickResModal);

  document.querySelectorAll('.btn-quick-result-trigger').forEach(btn => {
    btn.addEventListener('click', () => {
      const evIdx = btn.getAttribute('data-ev-idx');
      const evName = btn.getAttribute('data-ev-name');
      document.getElementById('quick-res-idx').value = evIdx;
      const label = document.getElementById('quick-res-event-label');
      if (label) label.textContent = `Logging official result for Rubber ${(parseInt(evIdx, 10) + 1)}: ${evName}`;
      if (modalQuickRes) modalQuickRes.classList.remove('d-none');
    });
  });

  if (formQuickRes) {
    formQuickRes.addEventListener('submit', (e) => {
      e.preventDefault();
      const evIdx = parseInt(document.getElementById('quick-res-idx').value, 10);
      const winner = document.getElementById('quick-res-winner').value;
      const setsA = parseInt(document.getElementById('quick-res-sets-a').value, 10);
      const setsB = parseInt(document.getElementById('quick-res-sets-b').value, 10);
      
      const s1 = document.getElementById('quick-res-set1').value.trim();
      const s2 = document.getElementById('quick-res-set2').value.trim();
      const s3 = document.getElementById('quick-res-set3').value.trim();

      const setHistory = [];
      [s1, s2, s3].forEach(st => {
        if (st && st.includes('-')) {
          const parts = st.split('-');
          setHistory.push({ a: parseInt(parts[0], 10) || 0, b: parseInt(parts[1], 10) || 0 });
        }
      });

      sendScoreAction({
        type: 'record_event_result',
        event_index: evIdx,
        winner: winner,
        sets_a: setsA,
        sets_b: setsB,
        set_history: setHistory
      });

      closeQuickResModal();
    });
  }

  // Edit rubber day and athletes metadata modal
  const modalRubberMeta = document.getElementById('modal-rubber-meta');
  const btnCloseRubberMeta = document.getElementById('btn-close-rubber-meta');
  const btnCancelRubberMeta = document.getElementById('btn-cancel-rubber-meta');
  const formRubberMeta = document.getElementById('form-rubber-meta');

  function closeRubberMetaModal() {
    if (modalRubberMeta) modalRubberMeta.classList.add('d-none');
  }
  if (btnCloseRubberMeta) btnCloseRubberMeta.addEventListener('click', closeRubberMetaModal);
  if (btnCancelRubberMeta) btnCancelRubberMeta.addEventListener('click', closeRubberMetaModal);

  document.querySelectorAll('.btn-edit-rubber-meta').forEach(btn => {
    btn.addEventListener('click', () => {
      const evIdx = btn.getAttribute('data-ev-idx');
      const evDay = btn.getAttribute('data-ev-day') || 'Day 1';
      const pA = btn.getAttribute('data-players-a') || '';
      const pB = btn.getAttribute('data-players-b') || '';

      document.getElementById('rubber-meta-idx').value = evIdx;
      document.getElementById('rubber-meta-day').value = evDay;
      document.getElementById('rubber-meta-players-a').value = pA;
      document.getElementById('rubber-meta-players-b').value = pB;

      if (modalRubberMeta) modalRubberMeta.classList.remove('d-none');
    });
  });

  if (formRubberMeta) {
    formRubberMeta.addEventListener('submit', (e) => {
      e.preventDefault();
      const evIdx = parseInt(document.getElementById('rubber-meta-idx').value, 10);
      const dayVal = document.getElementById('rubber-meta-day').value;
      const statusVal = document.getElementById('rubber-meta-status').value;
      const pA = document.getElementById('rubber-meta-players-a').value.trim();
      const pB = document.getElementById('rubber-meta-players-b').value.trim();

      sendScoreAction({
        type: 'update_event_meta',
        event_index: evIdx,
        day_label: dayVal,
        status: statusVal,
        players_a: pA,
        players_b: pB
      });

      closeRubberMetaModal();
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

  // Carrom Board Modal Handlers (AICF Standard)
  const modalCarrom = document.getElementById('modal-carrom-board');
  const btnCloseCarrom = document.getElementById('btn-close-carrom-board');
  const btnCancelCarrom = document.getElementById('btn-cancel-carrom-board');
  const formCarrom = document.getElementById('form-carrom-board');

  function closeCarromModal() {
    if (modalCarrom) modalCarrom.classList.add('d-none');
  }
  if (btnCloseCarrom) btnCloseCarrom.addEventListener('click', closeCarromModal);
  if (btnCancelCarrom) btnCancelCarrom.addEventListener('click', closeCarromModal);

  document.querySelectorAll('.btn-carrom-board-trigger').forEach(btn => {
    btn.addEventListener('click', () => {
      const evIdx = btn.getAttribute('data-ev-idx') || '0';
      const rubIdxInput = document.getElementById('carrom-rubber-idx');
      if (rubIdxInput) rubIdxInput.value = evIdx;
      if (modalCarrom) modalCarrom.classList.remove('d-none');
    });
  });

  if (formCarrom) {
    formCarrom.addEventListener('submit', (e) => {
      e.preventDefault();
      const evIdx = parseInt(document.getElementById('carrom-rubber-idx').value || '0', 10);
      const boardNum = parseInt(document.getElementById('carrom-board-num').value || '1', 10);
      const winner = document.getElementById('carrom-board-winner').value;
      const whitePts = parseInt(document.getElementById('carrom-white-pts').value || '0', 10);
      const blackPts = parseInt(document.getElementById('carrom-black-pts').value || '0', 10);
      const queen = document.getElementById('carrom-queen-covered').value;
      const netPts = parseInt(document.getElementById('carrom-net-pts').value || '1', 10);

      sendScoreAction({
        type: 'record_board',
        event_index: evIdx,
        board_num: boardNum,
        winner: winner,
        white_pts: whitePts,
        black_pts: blackPts,
        queen: queen,
        net_points: netPts
      });

      closeCarromModal();
      const nextBoardInput = document.getElementById('carrom-board-num');
      if (nextBoardInput) nextBoardInput.value = boardNum + 1;
    });
  }

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

  // Conclude match modal
  const btnConcludeModal = document.getElementById('btn-conclude-match-modal');
  const concludeModal = document.getElementById('conclude-match-modal');
  const btnCloseConclude = document.getElementById('btn-close-conclude-modal');
  const btnCancelConclude = document.getElementById('btn-cancel-conclude');
  const concludeForm = document.getElementById('form-conclude-match');

  if (btnConcludeModal) btnConcludeModal.addEventListener('click', () => concludeModal.classList.add('open'));
  if (btnCloseConclude) btnCloseConclude.addEventListener('click', () => concludeModal.classList.remove('open'));
  if (btnCancelConclude) btnCancelConclude.addEventListener('click', () => concludeModal.classList.remove('open'));

  if (concludeForm) {
    concludeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const winner = document.getElementById('conclude-winner').value;
      const summary = document.getElementById('conclude-summary').value;
      const motm = document.getElementById('conclude-motm').value;

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
          window.App.showToast('Match officially concluded!', 'success');
          setTimeout(() => window.location.reload(), 500);
        }
      } catch (err) {
        alert('Error concluding match: ' + err.message);
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
      } else if (match.sport_type === 'volleyball') {
        scoreText.textContent = `${match.team_a.abbr} ${match.score.sets_team_a} : ${match.score.sets_team_b} ${match.team_b.abbr} (Sets)`;
      } else if (match.sport_type === 'tug_of_war') {
        scoreText.textContent = `${match.team_a.abbr} ${match.score.pulls_team_a} : ${match.score.pulls_team_b} ${match.team_b.abbr} (Pulls)`;
      } else if (match.sport_type === 'basketball_shootout') {
        scoreText.textContent = `${match.team_a.abbr} ${match.score.score_team_a} : ${match.score.score_team_b} ${match.team_b.abbr} (Pts)`;
      } else if (['badminton', 'table_tennis', 'carrom'].includes(match.sport_type)) {
        scoreText.textContent = `${match.team_a.abbr} ${match.score.events_won_a} : ${match.score.events_won_b} ${match.team_b.abbr} (Events)`;
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

    // Prepend commentary item
    if (match.commentary && match.commentary.length > 0) {
      const latest = match.commentary[match.commentary.length - 1];
      const feed = document.getElementById('admin-commentary-feed');
      if (feed) {
        const item = document.createElement('div');
        item.className = `commentary-item ${latest.type}`;
        item.style.padding = '0.6rem';
        item.innerHTML = `
          <div class="comm-ball" style="font-size: 0.85rem;">${latest.ball}</div>
          <div class="comm-text-group">
            ${latest.badge ? `<span class="comm-badge" style="background: rgba(255,255,255,0.08); font-size: 0.62rem;">${latest.badge}</span>` : ''}
            <div class="comm-text" style="font-size: 0.82rem;">${latest.text}</div>
          </div>
        `;
        feed.insertBefore(item, feed.firstChild);
      }
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
