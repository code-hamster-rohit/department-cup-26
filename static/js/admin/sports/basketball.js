/**
 * ADMIN BASKETBALL SHOOTOUT SCORING CONTROLS
 */
window.AdminBasketball = {
  activeZoneA: 1,
  activeZoneB: 1,

  init: function(sendAction) {
    const self = this;

    // Zone selection buttons
    document.querySelectorAll('.bb-zone-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const team = btn.dataset.team;
        const zone = parseInt(btn.dataset.zone, 10);
        document.querySelectorAll(`.bb-zone-btn[data-team="${team}"]`).forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (team === 'team_a') self.activeZoneA = zone;
        else self.activeZoneB = zone;
      });
    });

    // Shot buttons
    document.querySelectorAll('.btn-bb-shot').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const team = btn.dataset.team;
        const success = btn.dataset.success === 'true';
        const zone = (btn.dataset.zone) ? parseInt(btn.dataset.zone, 10) : (team === 'team_a' ? self.activeZoneA : self.activeZoneB);

        const selectShooter = document.getElementById(team === 'team_a' ? 'select-bb-shooter-a' : 'select-bb-shooter-b');
        const inputShooter = document.getElementById(team === 'team_a' ? 'bb-shooter-a' : 'bb-shooter-b');

        let shooterName = 'Shooter';
        if (inputShooter && inputShooter.value.trim()) {
          shooterName = inputShooter.value.trim();
        } else if (selectShooter) {
          shooterName = selectShooter.value;
        }

        sendAction({
          type: 'shot',
          team: team,
          player: shooterName,
          zone: zone,
          success: success
        });
      });
    });
  },

  updateState: function(match) {
    // Basketball state updates
  }
};
