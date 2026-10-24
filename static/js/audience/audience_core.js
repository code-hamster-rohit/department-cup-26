/**
 * AUDIENCE CORE MODULE - Department Cup 2026
 * Handles live WebSocket streaming, HTTP polling fallback, flying cheer reactions,
 * tab switching, and sport-specific DOM dispatching.
 */
window.AudienceCore = (function() {
  let activeMatchId = null;
  let activeSportType = null;
  let ws = null;
  let pollInterval = null;

  function init() {
    const root = document.getElementById('audience-root') || document.getElementById('broadcast-card');
    if (!root) return;

    const bCard = document.getElementById('broadcast-card');
    if (bCard) {
      activeMatchId = bCard.dataset.matchId;
      activeSportType = bCard.dataset.sportType || 'cricket';
    }

    initTabs();
    initReactions();
    initLiveStream();
  }

  function initTabs() {
    const tabButtons = document.querySelectorAll('.arena-nav-tab');
    const tabPanes = document.querySelectorAll('.arena-tab-pane');

    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        tabButtons.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const target = btn.dataset.tab;
        const pane = document.getElementById(`pane-${target}`);
        if (pane) pane.classList.add('active');
      });
    });
  }

  function initReactions() {
    document.querySelectorAll('.btn-cheer').forEach(btn => {
      btn.addEventListener('click', () => {
        const emoji = btn.dataset.emoji || '🔥';
        if (activeMatchId && window.App && window.App.sendReaction) {
          window.App.sendReaction(activeMatchId, emoji);
        }
      });
    });
  }

  function initLiveStream() {
    if (!activeMatchId) return;

    // Connect WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = function() {
        console.log('[Audience WS] Connected');
        ws.send(JSON.stringify({ type: 'subscribe', match_id: activeMatchId }));
      };

      ws.onmessage = function(event) {
        try {
          const msg = JSON.parse(event.data);
          handleLiveBroadcast(msg);
        } catch (e) {
          console.error('[Audience WS] Parse error:', e);
        }
      };

      ws.onerror = function() {
        startPollingFallback();
      };

      ws.onclose = function() {
        startPollingFallback();
      };
    } catch (e) {
      startPollingFallback();
    }
  }

  function startPollingFallback() {
    if (pollInterval || !activeMatchId) return;
    console.log('[Audience] Starting HTTP polling fallback...');
    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/match/${activeMatchId}/poll`);
        if (res.ok) {
          const data = await res.json();
          dispatchSportUpdate(data);
        }
      } catch (e) {}
    }, 2500);
  }

  function handleLiveBroadcast(msg) {
    if (!msg) return;
    if (msg.event === 'LIVE_REACTION' && window.App && window.App.spawnFadingReaction) {
      window.App.spawnFadingReaction(msg.data.content, msg.data.sender);
      return;
    }

    if (msg.event === 'SCORE_UPDATED' || msg.event === 'MATCH_COMPLETED') {
      const matchData = msg.data.match || msg.data;
      dispatchSportUpdate(matchData);
    }
  }

  function dispatchSportUpdate(matchData) {
    if (!matchData) return;
    const stype = matchData.sport_type || activeSportType;

    if (stype === 'cricket' && window.AudienceCricket) {
      window.AudienceCricket.updateScore(matchData);
    } else if (stype === 'football' && window.AudienceFootball) {
      window.AudienceFootball.updateScore(matchData);
    } else if (stype === 'volleyball' && window.AudienceVolleyball) {
      window.AudienceVolleyball.updateScore(matchData);
    } else if (stype === 'badminton' && window.AudienceBadminton) {
      window.AudienceBadminton.updateScore(matchData);
    } else if (stype === 'table_tennis' && window.AudienceTableTennis) {
      window.AudienceTableTennis.updateScore(matchData);
    } else if (stype === 'carrom' && window.AudienceCarrom) {
      window.AudienceCarrom.updateScore(matchData);
    } else if (stype === 'tug_of_war' && window.AudienceTugOfWar) {
      window.AudienceTugOfWar.updateScore(matchData);
    } else if (stype === 'athletics_distance' && window.AudienceAthletics) {
      window.AudienceAthletics.updateScore(matchData);
    } else if (stype === 'basketball_shootout' && window.AudienceBasketball) {
      window.AudienceBasketball.updateScore(matchData);
    }
  }

  return {
    init: init,
    dispatchSportUpdate: dispatchSportUpdate
  };
})();

document.addEventListener('DOMContentLoaded', function() {
  AudienceCore.init();
});
