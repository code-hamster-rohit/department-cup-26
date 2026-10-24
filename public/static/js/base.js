/**
 * Base JavaScript utilities: Global WebSocket client, notifications, and helpers.
 */

window.App = {
  ws: null,
  reconnectAttempts: 0,
  maxReconnectDelay: 5000,
  pingInterval: null,
  pollInterval: null,
  pollMode: false,
  wsConsecutiveFailures: 0,
  maxWsFailuresBeforePoll: 3,
  lastPollUpdateAt: '',

  initGlobalWS() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;

    const indicator = document.getElementById('global-live-indicator');

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('⚡ Connected to Global Live Stream WebSocket');
        this.reconnectAttempts = 0;
        if (indicator) {
          indicator.classList.remove('offline');
          indicator.querySelector('.status-text').textContent = 'LIVE NETWORK';
        }
        
        // Start ping heartbeat
        if (this.pingInterval) clearInterval(this.pingInterval);
        this.pingInterval = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send('ping');
          }
        }, 15000);
      };

      this.ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const payload = JSON.parse(event.data);
          this.handleGlobalEvent(payload);
        } catch (e) {
          console.warn('WS message parsing error:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('WS disconnected. Reconnecting...');
        if (indicator) {
          indicator.classList.add('offline');
          indicator.querySelector('.status-text').textContent = 'RECONNECTING...';
        }
        if (this.pingInterval) clearInterval(this.pingInterval);
        
        this.wsConsecutiveFailures++;
        if (this.wsConsecutiveFailures >= this.maxWsFailuresBeforePoll && !this.pollMode) {
          console.log('WebSocket unavailable (serverless env detected). Switching to HTTP polling.');
          this.initPollingFallback();
          return;
        }

        const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
        this.reconnectAttempts++;
        setTimeout(() => this.initGlobalWS(), delay);
      };

      this.ws.onerror = (err) => {
        console.error('WS Error:', err);
      };
    } catch (e) {
      console.error('Failed opening WebSocket:', e);
      this.wsConsecutiveFailures++;
      if (this.wsConsecutiveFailures >= this.maxWsFailuresBeforePoll && !this.pollMode) {
        this.initPollingFallback();
      }
    }
  },

  handleGlobalEvent(payload) {
    console.log('Global Live Event:', payload.event, payload);
    
    // Dispatch custom browser event so any view can react
    const customEvent = new CustomEvent('deptcup:matchupdate', { detail: payload });
    window.dispatchEvent(customEvent);

    if (payload.event === 'LIVE_REACTION' && payload.data) {
      this.spawnFadingReaction(payload.data.content, payload.data.sender);
    } else if (payload.event === 'MATCH_CREATED') {
      this.showToast(`New Match Created: ${payload.data.team_a.abbr} vs ${payload.data.team_b.abbr} (${payload.data.sport_name})`, 'info');
    } else if (payload.event === 'MATCH_STARTED') {
      this.showToast(`Match LIVE: ${payload.data.team_a.abbr} vs ${payload.data.team_b.abbr}!`, 'live');
    } else if (payload.event === 'MATCH_COMPLETED') {
      this.showToast(`Match Concluded! ${payload.data.result || ''}`, 'success');
    }
  },

  spawnFadingReaction(content, sender = "Audience") {
    const container = document.getElementById('fading-reactions-container');
    if (!container) return;

    const el = document.createElement('div');
    el.className = 'floating-reaction';

    // Check if content consists only of emojis or short emoji combo
    const emojiRegex = /^(\p{Emoji_Presentation}|\p{Extended_Pictographic}|\s)+$/u;
    const isEmojiOnly = emojiRegex.test(content) && content.length <= 12;

    if (isEmojiOnly) {
      el.classList.add('is-emoji');
      el.textContent = content;
    } else {
      el.classList.add('is-text');
      const senderText = (sender && sender !== 'Audience') ? sender.split(' ')[0] : 'Crowd';
      el.innerHTML = `
        <span class="reaction-sender">${this.escapeHtml(senderText)}</span>
        <span class="reaction-content">${this.escapeHtml(content)}</span>
      `;
    }

    // Randomized bottom horizontal position (10% to 85% width)
    const leftPercent = 10 + Math.random() * 75;
    el.style.left = `${leftPercent}%`;

    // Dynamic random rotational sway & drift offsets for organic physics
    const rotMid = (Math.random() * 12 - 6).toFixed(1) + 'deg';
    const rotEnd = (Math.random() * 16 - 8).toFixed(1) + 'deg';
    const drift1 = (Math.random() * 30 - 15).toFixed(0) + 'px';
    const drift2 = (Math.random() * 40 - 20).toFixed(0) + 'px';
    const drift3 = (Math.random() * 50 - 25).toFixed(0) + 'px';

    el.style.setProperty('--rot-mid', rotMid);
    el.style.setProperty('--rot-end', rotEnd);
    el.style.setProperty('--drift-1', drift1);
    el.style.setProperty('--drift-2', drift2);
    el.style.setProperty('--drift-3', drift3);

    container.appendChild(el);

    // Self cleanup upon animation completion
    el.addEventListener('animationend', () => {
      el.remove();
    });
  },

  sendReaction(matchId, content, senderName = null) {
    if (!content || !matchId) return;
    const text = content.trim().substring(0, 60);
    if (!text) return;

    let sender = senderName;
    if (!sender) {
      const nameEl = document.querySelector('.user-name') || document.getElementById('dest-user-name');
      sender = (nameEl && nameEl.textContent.trim()) ? nameEl.textContent.trim() : 'Audience';
    }

    // 1. Zero-latency transmission via WebSocket
    let wsSent = false;
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify({
          type: 'REACTION',
          match_id: matchId,
          content: text,
          sender: sender
        }));
        wsSent = true;
      } catch (err) {
        console.warn('WS reaction send failed:', err);
      }
    }

    // 2. Fallback REST POST if WebSocket is disconnected/reconnecting
    if (!wsSent) {
      fetch(`/api/match/${matchId}/react`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, sender: sender })
      }).catch(err => console.warn('Reaction REST fallback failed:', err));
    }
  },

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-circle-info';
    let iconColor = '#3b82f6';
    if (type === 'live') { icon = 'fa-satellite-dish'; iconColor = '#ef4444'; }
    else if (type === 'success') { icon = 'fa-trophy'; iconColor = '#10b981'; }
    else if (type === 'warning') { icon = 'fa-triangle-exclamation'; iconColor = '#f59e0b'; }

    toast.innerHTML = `
      <i class="fa-solid ${icon}" style="color: ${iconColor}; font-size: 1.1rem;"></i>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  // =========================================================================
  // HTTP POLLING FALLBACK (for Vercel / serverless where WebSockets fail)
  // =========================================================================
  initPollingFallback() {
    if (this.pollMode) return;
    this.pollMode = true;
    console.log('📡 HTTP Polling mode activated (3s interval)');

    const indicator = document.getElementById('global-live-indicator');
    if (indicator) {
      indicator.classList.remove('offline');
      indicator.querySelector('.status-text').textContent = 'LIVE (POLLING)';
    }

    // Determine active match ID from URL or page data
    const urlParams = new URLSearchParams(window.location.search);
    const matchId = urlParams.get('match')
      || document.querySelector('[data-match-id]')?.getAttribute('data-match-id');

    if (matchId) {
      this.startMatchPolling(matchId);
    } else {
      this.startActiveMatchesPolling();
    }
  },

  startMatchPolling(matchId) {
    if (this.pollInterval) clearInterval(this.pollInterval);

    const doPoll = async () => {
      try {
        const res = await fetch(`/api/match/${matchId}/poll?since=${encodeURIComponent(this.lastPollUpdateAt)}&_t=${Date.now()}`, { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();

        if (data.updated_at && data.updated_at !== this.lastPollUpdateAt) {
          this.lastPollUpdateAt = data.updated_at;

          // Synthesize SCORE_UPDATED event for the existing index.js listener
          const latestComm = data.commentary && data.commentary.length > 0
            ? data.commentary[data.commentary.length - 1]
            : null;

          this.handleGlobalEvent({
            event: 'SCORE_UPDATED',
            match_id: matchId,
            data: {
              score: data.score,
              commentary: latestComm,
              status: data.status,
              result: data.result
            }
          });
        }

        // If match completed, stop polling
        if (data.status === 'completed') {
          clearInterval(this.pollInterval);
          this.handleGlobalEvent({
            event: 'MATCH_COMPLETED',
            match_id: matchId,
            data: { result: data.result }
          });
        }
      } catch (err) {
        console.warn('Poll error:', err);
      }
    };

    doPoll();
    this.pollInterval = setInterval(doPoll, 1500);
  },

  startActiveMatchesPolling() {
    if (this.pollInterval) clearInterval(this.pollInterval);

    const doPoll = async () => {
      try {
        const res = await fetch('/api/matches/active/poll');
        if (!res.ok) return;
        const data = await res.json();
        if (data.matches && data.matches.length > 0) {
          // Found a live match, switch to match-specific polling
          const liveMatch = data.matches.find(m => m.status === 'live') || data.matches[0];
          clearInterval(this.pollInterval);
          window.location.href = `/?match=${liveMatch.id}`;
        }
      } catch (err) {
        console.warn('Active matches poll error:', err);
      }
    };

    doPoll();
    this.pollInterval = setInterval(doPoll, 5000);
  }
};

// Global Google GIS Credential Response Handler
window.handleGoogleCredentialResponse = async function(response) {
  if (!response || !response.credential) return;
  try {
    const res = await fetch('/api/auth/google/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential })
    });
    const data = await res.json();
    if (data.success) {
      if (data.is_admin) {
        // Present Administrator with Destination Choice Modal
        const modal = document.getElementById('admin-destination-modal');
        const nameEl = document.getElementById('dest-user-name');
        const emailEl = document.getElementById('dest-user-email');
        if (nameEl) nameEl.textContent = data.user.name;
        if (emailEl) emailEl.textContent = data.user.email;
        if (modal) modal.classList.add('open');
      } else {
        window.App.showToast(`Signed in as ${data.user.name} (Audience Viewer)`, 'info');
        setTimeout(() => window.location.reload(), 500);
      }
    } else {
      alert('Sign in failed: ' + (data.detail || 'Authentication error'));
    }
  } catch (err) {
    console.error('Google auth error:', err);
    alert('Failed to authenticate with Google: ' + err.message);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.initGlobalWS();

  // Dismiss button on Admin Destination Modal
  const dismissBtn = document.getElementById('btn-dismiss-dest-modal');
  if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
      const modal = document.getElementById('admin-destination-modal');
      if (modal) modal.classList.remove('open');
      window.location.reload();
    });
  }

  // Open View Choice modal for verified admins
  const openViewChoiceBtn = document.getElementById('btn-open-view-choice');
  const stripChooseBtn = document.getElementById('btn-strip-choose-view');
  const openDestModal = () => {
    const modal = document.getElementById('admin-destination-modal');
    if (modal) modal.classList.add('open');
  };
  if (openViewChoiceBtn) openViewChoiceBtn.addEventListener('click', openDestModal);
  if (stripChooseBtn) stripChooseBtn.addEventListener('click', openDestModal);

  // Single Sign-In Button Enforcement:
  // If GIS fails to render an iframe within 1.5s, reveal fallback button so user is never stranded
  const fallbackBtn = document.getElementById('btn-google-fallback');
  const gateFallbackBtn = document.getElementById('btn-gate-google-signin');
  const gSigninDiv = document.querySelector('.g_id_signin');
  if ((fallbackBtn || gateFallbackBtn) && gSigninDiv) {
    setTimeout(() => {
      const hasIframe = gSigninDiv.querySelector('iframe');
      if (!hasIframe) {
        if (fallbackBtn) {
          fallbackBtn.classList.remove('d-none');
          fallbackBtn.style.display = 'inline-flex';
        }
        if (gateFallbackBtn) {
          gateFallbackBtn.classList.remove('d-none');
          gateFallbackBtn.style.display = 'inline-flex';
        }
      } else {
        if (fallbackBtn) {
          fallbackBtn.classList.add('d-none');
          fallbackBtn.style.display = 'none';
        }
        if (gateFallbackBtn) {
          gateFallbackBtn.classList.add('d-none');
          gateFallbackBtn.style.display = 'none';
        }
      }
    }, 1500);
  }
});
