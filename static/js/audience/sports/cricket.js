/**
 * AUDIENCE CRICKET LIVE DOM UPDATER
 * Updates cricket scoreboard, pitch strip, and timeline on live WebSocket/polling broadcasts.
 */
window.AudienceCricket = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;
    const innNum = score.innings || 1;
    const curInn = score[`innings_${innNum}`];
    if (!curInn) return;

    // Runs & Wickets
    const elRuns = document.getElementById('aud-cricket-runs-wickets');
    if (elRuns) elRuns.textContent = `${curInn.runs}/${curInn.wickets}`;

    // Overs
    const elOvers = document.getElementById('aud-cricket-overs');
    if (elOvers) {
      const legal = curInn.legal_balls || 0;
      elOvers.textContent = `(${Math.floor(legal / 6)}.${legal % 6} / ${score.max_overs || 10} ov)`;
    }

    // CRR
    const elCrr = document.getElementById('aud-cricket-crr');
    if (elCrr) elCrr.textContent = `CRR: ${curInn.crr || '0.00'}`;

    // Free Hit banner
    const elFh = document.getElementById('aud-cricket-freehit');
    if (elFh) {
      if (score.is_free_hit) elFh.classList.remove('d-none');
      else elFh.classList.add('d-none');
    }

    // Striker
    const elStrikerName = document.getElementById('aud-striker-name');
    if (elStrikerName) elStrikerName.textContent = (curInn.striker || 'Batter 1') + ' *';
    const elStrikerStats = document.getElementById('aud-striker-stats');
    if (elStrikerStats && curInn.batsmen && curInn.batsmen[curInn.striker]) {
      const b = curInn.batsmen[curInn.striker];
      elStrikerStats.textContent = `${b.runs} (${b.balls}b) · ${b.fours}x4 · ${b.sixes}x6 · SR: ${b.sr}`;
    }

    // Non-striker
    const elNonStrikerName = document.getElementById('aud-non-striker-name');
    if (elNonStrikerName) elNonStrikerName.textContent = curInn.non_striker || 'Batter 2';
    const elNonStrikerStats = document.getElementById('aud-non-striker-stats');
    if (elNonStrikerStats && curInn.batsmen && curInn.batsmen[curInn.non_striker]) {
      const b = curInn.batsmen[curInn.non_striker];
      elNonStrikerStats.textContent = `${b.runs} (${b.balls}b)`;
    }

    // Bowler
    const elBowlerName = document.getElementById('aud-bowler-name');
    if (elBowlerName) elBowlerName.textContent = curInn.bowler || 'Bowler';
    const elBowlerStats = document.getElementById('aud-bowler-stats');
    if (elBowlerStats && curInn.bowlers && curInn.bowlers[curInn.bowler]) {
      const bw = curInn.bowlers[curInn.bowler];
      elBowlerStats.textContent = `${bw.overs} ov · ${bw.maidens}m · ${bw.runs}r · ${bw.wickets}w · Econ: ${bw.econ}`;
    }

    // Recent Timeline Chips
    const chipsContainer = document.getElementById('aud-timeline-chips');
    if (chipsContainer && curInn.timeline) {
      chipsContainer.innerHTML = curInn.timeline.slice(-12).map(b => {
        let cls = 'dot';
        if (b === '4') cls = 'four';
        else if (b === '6') cls = 'six';
        else if (b === 'W') cls = 'wicket';
        else if (b.includes('Wd') || b.includes('NB')) cls = 'extra';
        return `<span class="ball-chip ${cls}">${b}</span>`;
      }).join('');
    }
  }
};
