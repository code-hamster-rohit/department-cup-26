/**
 * AUDIENCE ATHLETICS DISTANCE LIVE DOM UPDATER
 */
window.AudienceAthletics = {
  updateScore: function(match) {
    if (!match || !match.score) return;
    const score = match.score;
    const tbody = document.getElementById('aud-athletics-tbody');
    if (!tbody || !score.athletes) return;

    if (score.athletes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="padding: 2rem; text-align: center; color: var(--text-muted);">Awaiting first athlete throw / jump attempt...</td></tr>`;
      return;
    }

    tbody.innerHTML = score.athletes.map((a, idx) => {
      const rankBadge = (idx === 0) ? '🥇' : ((idx === 1) ? '🥈' : ((idx === 2) ? '🥉' : `${idx + 1}`));
      const atts = a.attempts || [];
      return `
        <tr style="border-bottom: 1px solid var(--border-subtle);">
          <td style="padding: 0.65rem 1rem; text-align: center; font-weight: 800;">${rankBadge}</td>
          <td style="padding: 0.65rem 1rem; font-weight: 700; color: var(--text-main);">${a.name}</td>
          <td style="padding: 0.65rem 1rem; text-align: center;"><span class="dept-badge ${a.department.toLowerCase()}">${a.department.toUpperCase()}</span></td>
          <td style="padding: 0.65rem 1rem; text-align: center; color: var(--text-muted);">${a.trial || '-'}</td>
          <td style="padding: 0.65rem 1rem; text-align: center;">${atts[0] || '-'}</td>
          <td style="padding: 0.65rem 1rem; text-align: center;">${atts[1] || '-'}</td>
          <td style="padding: 0.65rem 1rem; text-align: center;">${atts[2] || '-'}</td>
          <td style="padding: 0.65rem 1rem; text-align: center; font-weight: 900; color: #2563eb; font-size: 1rem;">${a.best || 0}m</td>
        </tr>
      `;
    }).join('');
  }
};
