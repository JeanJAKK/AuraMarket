/* MarketHub — Live Shopping (Sprint 2)
 * Minimal WebRTC P2P broadcast using Odoo as a simple signaling relay.
 */

(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function safeParseInt(value, fallback) {
    var n = parseInt(value, 10);
    return Number.isFinite(n) ? n : fallback;
  }

  function randomId() {
    try {
      if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
      }
    } catch (e) {
      // ignore
    }
    return (
      "id-" +
      Math.random().toString(16).slice(2) +
      "-" +
      Date.now().toString(16)
    );
  }

  // Odoo `type='json'` routes use JSON-RPC over HTTP.
  async function postJson(url, params) {
    var response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      cache: "no-store",
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: params || {},
        id: Date.now(),
      }),
    });

    var data;
    try {
      data = await response.json();
    } catch (e) {
      throw {
        message: "Invalid JSON response",
        status: response.status,
      };
    }

    if (!response.ok) {
      if (data && data.error) {
        throw data.error;
      }
      throw {
        message: "HTTP error",
        status: response.status,
      };
    }

    if (data && data.error) {
      throw data.error;
    }
    return data && Object.prototype.hasOwnProperty.call(data, "result")
      ? data.result
      : data;
  }

  function showVideo(videoEl, placeholderEl) {
    if (placeholderEl) placeholderEl.style.display = "none";
    if (videoEl) videoEl.style.display = "block";
  }

  function hideVideo(videoEl, placeholderEl) {
    if (videoEl) videoEl.style.display = "none";
    if (placeholderEl) placeholderEl.style.display = "flex";
  }

  function ensurePlaceholderMessageEl(placeholderEl) {
    if (!placeholderEl) return null;
    var el = placeholderEl.querySelector("[data-live-msg='1']");
    if (el) return el;

    // Reuse the existing message paragraph from the template if present.
    el = placeholderEl.querySelector("p.text-white-50");
    if (el) {
      el.setAttribute("data-live-msg", "1");
      return el;
    }

    el = document.createElement("p");
    el.setAttribute("data-live-msg", "1");
    el.className = "text-white-50";
    placeholderEl.appendChild(el);
    return el;
  }

  function showPlaceholderMessage(placeholderEl, message) {
    var msgEl = ensurePlaceholderMessageEl(placeholderEl);
    if (!msgEl) return;
    msgEl.textContent = message || "";
  }

  function attachStreamToVideo(videoEl, stream) {
    if (!videoEl || !stream) return;

    // Help autoplay policies across browsers
    try {
      videoEl.autoplay = true;
      videoEl.muted = true;
      videoEl.playsInline = true;
      videoEl.setAttribute("autoplay", "autoplay");
      videoEl.setAttribute("muted", "muted");
      videoEl.setAttribute("playsinline", "playsinline");
      videoEl.setAttribute("webkit-playsinline", "webkit-playsinline");
    } catch (e) {
      // ignore
    }

    try {
      videoEl.srcObject = stream;
    } catch (e) {
      // Old/edge browsers (deprecated but safer fallback)
      try {
        videoEl.src = window.URL.createObjectURL(stream);
      } catch (e2) {
        // ignore
      }
    }

    videoEl.play().catch(function () {
      // ignore
    });
  }

  async function getLocalStreamWithFallback() {
    // Some browsers reject the whole call if audio is denied/unavailable.
    try {
      return await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
    } catch (e) {
      try {
        return await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      } catch (e2) {
        throw e2;
      }
    }
  }

  function humanizeGetUserMediaError(err) {
    var name = err && err.name ? String(err.name) : "";
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      return "Accès caméra refusé par le navigateur.";
    }
    if (name === "NotFoundError" || name === "DevicesNotFoundError") {
      return "Aucune caméra trouvée sur cet appareil.";
    }
    if (name === "NotReadableError" || name === "TrackStartError") {
      return "Caméra déjà utilisée par une autre application.";
    }
    if (
      name === "OverconstrainedError" ||
      name === "ConstraintNotSatisfiedError"
    ) {
      return "Contraintes caméra non satisfaites (essayez un autre périphérique).";
    }
    if (name) return "Erreur caméra: " + name;
    return "Impossible d'accéder à la caméra.";
  }

  function createPeerConnection() {
    return new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });
  }

  function isLive(status) {
    return status === "live";
  }

  function isNearTop(scrollEl, thresholdPx) {
    if (!scrollEl) return true;
    var threshold = typeof thresholdPx === "number" ? thresholdPx : 40;
    return scrollEl.scrollTop <= threshold;
  }

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    var configEl = $("marketplace-live-config");
    if (!configEl) return;

    var liveId = safeParseInt(configEl.dataset.liveId, 0);
    var liveStatus = (configEl.dataset.liveStatus || "").trim();
    var broadcasterId = (configEl.dataset.broadcasterId || "").trim();
    var isBroadcaster = (configEl.dataset.isBroadcaster || "0") === "1";

    if (!liveId || !broadcasterId) return;

    var placeholderEl = $("video-placeholder");
    var videoEl = $("remote-video");

    var startBtn = $("marketplace-webrtc-start");
    var stopBtn = $("marketplace-webrtc-stop");

    var csrfToken = (configEl.dataset.csrfToken || "").trim();

    // Live sidebar DOM (comments + stats)
    var viewerCountEl = $("viewer-count");
    var likeCountEl = $("live-like-count");
    var orderCountEl = $("live-order-count");
    var statusBadgeEl = $("live-status-badge");

    var commentsFeedEl = $("comments-feed");
    var commentsBottomEl = $("comments-bottom");
    var commentFormEl = $("comment-form");
    var commentInputEl = $("comment-input");

    var lastCommentId = 0;
    var lastReactionId = safeParseInt(configEl.dataset.lastReactionId, 0);
    var lastOrderId = safeParseInt(configEl.dataset.lastOrderId, 0);
    var updatesInFlight = false;
    var updatesTimer = null;

    var commentAuthorStyleText = null;
    var commentContentStyleText = null;

    var clientId;
    if (isBroadcaster) {
      clientId = broadcasterId;
    } else {
      var storageKey = "marketplace.live." + liveId + ".client_id";
      try {
        clientId = localStorage.getItem(storageKey);
        if (!clientId) {
          clientId = "viewer-" + randomId();
          localStorage.setItem(storageKey, clientId);
        }
      } catch (e) {
        clientId = "viewer-" + randomId();
      }
    }

    function placeholderMessageForStatus(status) {
      if (status === "scheduled") return "Ce live n'a pas encore commence";
      if (status === "ended") return "Ce live est termine";
      if (status === "live") return "Connexion au stream en cours...";
      return status ? String(status) : "";
    }

    function updateStatusBadge(status) {
      if (!statusBadgeEl) return;
      status = status ? String(status).trim() : "";

      statusBadgeEl.classList.remove("bg-danger");
      statusBadgeEl.classList.remove("bg-secondary");
      if (isLive(status)) {
        statusBadgeEl.classList.add("bg-danger");
        statusBadgeEl.textContent = "● EN DIRECT";
      } else {
        statusBadgeEl.classList.add("bg-secondary");
        if (status === "scheduled") {
          statusBadgeEl.textContent = "Programme";
        } else if (status === "ended") {
          statusBadgeEl.textContent = "Terminé";
        } else {
          statusBadgeEl.textContent = status;
        }
      }
    }

    function updatePlaceholderForStatus(status) {
      if (!placeholderEl) return;
      showPlaceholderMessage(
        placeholderEl,
        placeholderMessageForStatus(status),
      );
    }

    function computeLastCommentIdFromDom() {
      if (!commentsFeedEl) return 0;
      var nodes = commentsFeedEl.querySelectorAll("[data-comment-id]");
      var maxId = 0;
      for (var i = 0; i < nodes.length; i++) {
        var id = safeParseInt(nodes[i].getAttribute("data-comment-id"), 0);
        if (id > maxId) maxId = id;
      }
      return maxId;
    }

    function captureExistingCommentStyles() {
      if (!commentsFeedEl) return;
      if (!commentAuthorStyleText) {
        var authorEl = commentsFeedEl.querySelector(".live-comment-author");
        if (authorEl)
          commentAuthorStyleText = authorEl.getAttribute("style") || null;
      }
      if (!commentContentStyleText) {
        var bubbleEl = commentsFeedEl.querySelector(".live-comment-bubble");
        if (bubbleEl && bubbleEl.children && bubbleEl.children[1]) {
          commentContentStyleText =
            bubbleEl.children[1].getAttribute("style") || null;
        }
      }
    }

    function setNumberText(el, value) {
      if (!el) return;
      if (typeof value === "number" && Number.isFinite(value)) {
        el.textContent = String(value);
      }
    }

    function isNearBottom(scrollEl, thresholdPx) {
      if (!scrollEl) return true;
      var threshold = typeof thresholdPx === "number" ? thresholdPx : 40;
      return (
        scrollEl.scrollHeight - scrollEl.scrollTop - scrollEl.clientHeight <=
        threshold
      );
    }

    function createCommentNode(comment) {
      if (!comment) return null;
      var id =
        typeof comment.id === "number"
          ? comment.id
          : safeParseInt(comment.id, 0);
      if (!id) return null;

      var partnerName = (comment.partner_name || "").trim();
      var content = String(comment.content || "");

      var item = document.createElement("div");
      item.className = "live-comment-item";
      item.setAttribute("data-comment-id", String(id));

      var avatar = document.createElement("div");
      avatar.className = "live-comment-avatar";
      var initial = partnerName ? partnerName.charAt(0) : "U";
      avatar.textContent = initial.toUpperCase();
      item.appendChild(avatar);

      var bubble = document.createElement("div");
      bubble.className = "live-comment-bubble";

      var author = document.createElement("div");
      author.className = "live-comment-author";
      if (commentAuthorStyleText) {
        author.setAttribute("style", commentAuthorStyleText);
      } else {
        author.style.fontSize = "11px";
        author.style.fontWeight = "700";
      }
      author.textContent = partnerName;
      bubble.appendChild(author);

      var text = document.createElement("div");
      if (commentContentStyleText) {
        text.setAttribute("style", commentContentStyleText);
      } else {
        text.style.fontSize = "13px";
      }
      text.textContent = content;
      bubble.appendChild(text);

      item.appendChild(bubble);
      return item;
    }

    function appendNewComments(comments) {
      if (!commentsFeedEl || !comments || !comments.length) return;

      var shouldScroll = isNearBottom(commentsFeedEl, 60);

      for (var i = 0; i < comments.length; i++) {
        var node = createCommentNode(comments[i]);
        if (!node) continue;

        var id = safeParseInt(node.getAttribute("data-comment-id"), 0);
        if (id && id <= lastCommentId) continue;

        if (
          commentsBottomEl &&
          commentsBottomEl.parentNode === commentsFeedEl
        ) {
          commentsFeedEl.insertBefore(node, commentsBottomEl);
        } else {
          commentsFeedEl.appendChild(node);
        }
        lastCommentId = Math.max(lastCommentId, id);
      }

      if (shouldScroll) {
        commentsFeedEl.scrollTop = commentsFeedEl.scrollHeight;
      }
    }

    function spawnFloatingReaction(type) {
      var zone = $("live-video-zone");
      if (!zone) return;

      var emojis = { like: "❤", fire: "🔥", clap: "👏" };
      var el = document.createElement("div");
      el.className = "floating-heart";
      el.textContent = emojis[type] || emojis.like;

      // Small randomness so reactions feel alive.
      el.style.right = String(20 + Math.floor(Math.random() * 90)) + "px";
      el.style.bottom = String(80 + Math.floor(Math.random() * 60)) + "px";

      zone.appendChild(el);
      setTimeout(function () {
        try {
          el.remove();
        } catch (e) {
          // ignore
        }
      }, 2200);
    }

    function renderIncomingReactions(reactions) {
      if (!reactions || !reactions.length) return;

      for (var i = 0; i < reactions.length; i++) {
        var r = reactions[i] || {};
        var id = typeof r.id === "number" ? r.id : safeParseInt(r.id || 0, 0);
        if (!id || id <= lastReactionId) continue;

        spawnFloatingReaction((r.type || "like").trim());
        lastReactionId = Math.max(lastReactionId, id);
      }
    }

    var orderNotifTimer = null;

    function ensureOrderNotificationEl() {
      var zone = $("live-video-zone");
      if (!zone) return null;

      var existing = $("live-order-notification");
      if (existing) return existing;

      var wrap = document.createElement("div");
      wrap.id = "live-order-notification";
      wrap.style.position = "absolute";
      wrap.style.top = "64px";
      wrap.style.left = "50%";
      wrap.style.transform = "translateX(-50%)";
      wrap.style.zIndex = "15";
      wrap.style.display = "none";

      var inner = document.createElement("div");
      inner.id = "live-order-notification-text";
      inner.className = "badge bg-success bg-opacity-75 px-3 py-2";
      inner.style.fontSize = "13px";
      inner.style.borderRadius = "999px";
      wrap.appendChild(inner);

      zone.appendChild(wrap);
      return wrap;
    }

    function showOrderNotification(message) {
      var wrap = ensureOrderNotificationEl();
      if (!wrap) return;
      var textEl = $("live-order-notification-text");
      if (!textEl) return;

      textEl.textContent = message || "";
      wrap.style.display = "block";

      if (orderNotifTimer) clearTimeout(orderNotifTimer);
      orderNotifTimer = setTimeout(function () {
        wrap.style.display = "none";
      }, 4000);
    }

    function formatFcfa(amount) {
      var n = Number(amount || 0);
      if (!Number.isFinite(n)) n = 0;
      try {
        return Math.round(n).toLocaleString("fr-FR") + " FCFA";
      } catch (e) {
        return Math.round(n) + " FCFA";
      }
    }

    function renderIncomingOrders(orders) {
      if (!orders || !orders.length) return;

      for (var i = 0; i < orders.length; i++) {
        var o = orders[i] || {};
        var id = typeof o.id === "number" ? o.id : safeParseInt(o.id || 0, 0);
        if (!id || id <= lastOrderId) continue;

        var buyer = (o.buyer_name || "").trim() || "Quelqu'un";
        var productName = (o.product_name || "").trim();
        var amountText =
          o.amount_total && Number(o.amount_total) > 0
            ? " — " + formatFcfa(o.amount_total) + " !"
            : "";

        var message = buyer + " vient d'acheter";
        if (productName) message += " " + productName;
        message += amountText;

        showOrderNotification(message);
        lastOrderId = Math.max(lastOrderId, id);
      }
    }

    async function pollLiveUpdates() {
      if (updatesInFlight) return;
      updatesInFlight = true;
      try {
        var data = await postJson("/live/" + liveId + "/updates", {
          after_comment_id: lastCommentId,
          after_reaction_id: lastReactionId,
          after_order_id: lastOrderId,
          client_id: clientId,
          limit: 50,
        });

        if (data && data.live) {
          var newStatus = (data.live.status || "").trim();
          if (newStatus && newStatus !== liveStatus) {
            liveStatus = newStatus;
            try {
              configEl.dataset.liveStatus = newStatus;
            } catch (e) {
              // ignore
            }
            updateStatusBadge(newStatus);
            updatePlaceholderForStatus(newStatus);
          }

          setNumberText(viewerCountEl, data.live.viewer_count);
          setNumberText(likeCountEl, data.live.like_count);
          setNumberText(orderCountEl, data.live.order_count);
        }

        appendNewComments(data && data.comments ? data.comments : []);

        renderIncomingReactions(data && data.reactions ? data.reactions : []);
        renderIncomingOrders(data && data.orders ? data.orders : []);

        // If the live just started while the page is open, auto-connect viewers.
        if (!isBroadcaster && !viewerPc && isLive(liveStatus)) {
          startViewer();
        }
      } catch (e) {
        // retry later
      } finally {
        updatesInFlight = false;
      }
    }

    function startUpdatesPolling() {
      if (updatesTimer) return;
      updatesTimer = setInterval(pollLiveUpdates, 1000);
      pollLiveUpdates();
    }

    function setupCommentFormAjax() {
      if (!commentFormEl || !commentInputEl) return;
      if (!window.fetch || !csrfToken) return;

      commentFormEl.addEventListener("submit", async function (ev) {
        var content = (commentInputEl.value || "").trim();
        ev.preventDefault();

        if (!content) return;

        var submitBtn = commentFormEl.querySelector("button[type='submit']");
        if (submitBtn) submitBtn.disabled = true;

        try {
          var data = await postJson("/live/" + liveId + "/comment/json", {
            content: content,
            csrf_token: csrfToken,
          });

          if (data && data.status === "ok" && data.comment) {
            commentInputEl.value = "";
            appendNewComments([data.comment]);
            if (data.live) {
              setNumberText(likeCountEl, data.live.like_count);
              setNumberText(orderCountEl, data.live.order_count);
            }
          } else {
            // Fallback to regular form submit (full page reload)
            commentFormEl.submit();
          }
        } catch (e) {
          try {
            commentFormEl.submit();
          } catch (e2) {
            // ignore
          }
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    function setupReactionOptimisticCounter() {
      if (!likeCountEl) return;
      // Only optimistic-update when the user is logged in (same condition as the comment form).
      if (!commentFormEl) return;

      var reactionsEl = document.querySelector(".live-reactions");
      if (!reactionsEl) return;

      reactionsEl.addEventListener("click", function (ev) {
        var btn =
          ev.target && ev.target.closest ? ev.target.closest("button") : null;
        if (!btn) return;
        var onclick = (btn.getAttribute("onclick") || "").toLowerCase();
        if (onclick.indexOf("sendreaction") === -1) return;

        var current = safeParseInt(likeCountEl.textContent, null);
        if (current === null) return;
        likeCountEl.textContent = String(current + 1);
      });
    }

    // Init live sidebar state
    lastCommentId = computeLastCommentIdFromDom();
    captureExistingCommentStyles();
    updateStatusBadge(liveStatus);
    updatePlaceholderForStatus(liveStatus);

    var lastSignalId = 0;
    var pollInFlight = false;
    var pollTimer = null;

    var viewerPc = null;
    var viewerPendingIce = [];

    var localStream = null;
    var broadcasterPcs = new Map();
    var broadcasterPendingIce = new Map();

    async function signal(receiver, kind, payload) {
      return postJson("/live/" + liveId + "/webrtc/signal", {
        sender: clientId,
        receiver: receiver,
        kind: kind,
        payload: payload || {},
      });
    }

    async function pollSignals() {
      if (pollInFlight) return;
      pollInFlight = true;
      try {
        var data = await postJson("/live/" + liveId + "/webrtc/poll", {
          receiver: clientId,
          after_id: lastSignalId,
          limit: 50,
        });

        var messages = data && data.messages ? data.messages : [];
        for (var i = 0; i < messages.length; i++) {
          var msg = messages[i];
          if (msg && typeof msg.id === "number")
            lastSignalId = Math.max(lastSignalId, msg.id);
          await handleSignalMessage(msg);
        }
      } catch (e) {
        // retry later
      } finally {
        pollInFlight = false;
      }
    }

    function startPolling() {
      if (pollTimer) return;
      pollTimer = setInterval(pollSignals, 1000);
      pollSignals();
    }

    function stopPolling() {
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    }

    async function handleSignalMessage(msg) {
      if (!msg || !msg.kind) return;

      if (!isBroadcaster) {
        if (!viewerPc) return;
        if (msg.kind === "answer" && msg.payload && msg.payload.sdp) {
          if (!viewerPc.currentRemoteDescription) {
            await viewerPc.setRemoteDescription(msg.payload);
            while (viewerPendingIce.length) {
              var cand = viewerPendingIce.shift();
              try {
                await viewerPc.addIceCandidate(cand);
              } catch (e) {
                // ignore
              }
            }
          }
        } else if (msg.kind === "ice" && msg.payload && msg.payload.candidate) {
          var ice = new RTCIceCandidate(msg.payload);
          if (viewerPc.currentRemoteDescription) {
            try {
              await viewerPc.addIceCandidate(ice);
            } catch (e) {
              // ignore
            }
          } else {
            viewerPendingIce.push(ice);
          }
        }
        return;
      }

      // Broadcaster side
      var sender = (msg.sender || "").trim();
      if (!sender) return;

      if (msg.kind === "offer" && msg.payload && msg.payload.sdp) {
        if (!localStream) return;
        if (broadcasterPcs.has(sender)) return;

        var pc = createPeerConnection();
        broadcasterPcs.set(sender, pc);

        pc.onicecandidate = function (ev) {
          if (ev.candidate) {
            signal(sender, "ice", ev.candidate);
          }
        };

        pc.onconnectionstatechange = function () {
          if (
            pc.connectionState === "failed" ||
            pc.connectionState === "disconnected" ||
            pc.connectionState === "closed"
          ) {
            try {
              pc.close();
            } catch (e) {}
            broadcasterPcs.delete(sender);
            broadcasterPendingIce.delete(sender);
          }
        };

        localStream.getTracks().forEach(function (track) {
          pc.addTrack(track, localStream);
        });

        await pc.setRemoteDescription(msg.payload);
        var answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        await signal(sender, "answer", pc.localDescription);

        var pending = broadcasterPendingIce.get(sender) || [];
        broadcasterPendingIce.delete(sender);
        for (var i = 0; i < pending.length; i++) {
          try {
            await pc.addIceCandidate(pending[i]);
          } catch (e) {
            // ignore
          }
        }
      } else if (msg.kind === "ice" && msg.payload && msg.payload.candidate) {
        var targetPc = broadcasterPcs.get(sender);
        var targetIce = new RTCIceCandidate(msg.payload);

        if (targetPc && targetPc.currentRemoteDescription) {
          try {
            await targetPc.addIceCandidate(targetIce);
          } catch (e) {
            // ignore
          }
        } else {
          var queue = broadcasterPendingIce.get(sender) || [];
          queue.push(targetIce);
          broadcasterPendingIce.set(sender, queue);
        }
      }
    }

    async function startViewer() {
      if (!isLive(liveStatus)) return;
      if (!window.RTCPeerConnection) return;

      viewerPc = createPeerConnection();

      viewerPc.ontrack = function (ev) {
        if (!videoEl) return;
        var stream = ev.streams && ev.streams[0] ? ev.streams[0] : null;
        if (stream) {
          videoEl.srcObject = stream;
          // allow autoplay; user can click video to unmute
          videoEl.muted = true;
          showVideo(videoEl, placeholderEl);
          videoEl.play().catch(function () {});
        }
      };

      viewerPc.onicecandidate = function (ev) {
        if (ev.candidate) {
          signal(broadcasterId, "ice", ev.candidate);
        }
      };

      // Receive-only
      viewerPc.addTransceiver("video", { direction: "recvonly" });
      viewerPc.addTransceiver("audio", { direction: "recvonly" });

      var offer = await viewerPc.createOffer();
      await viewerPc.setLocalDescription(offer);
      await signal(broadcasterId, "offer", viewerPc.localDescription);

      startPolling();

      if (videoEl) {
        videoEl.addEventListener(
          "click",
          function () {
            if (videoEl.muted) {
              videoEl.muted = false;
              videoEl.play().catch(function () {});
            }
          },
          { once: true },
        );
      }
    }

    async function startBroadcaster() {
      if (!isLive(liveStatus)) {
        showPlaceholderMessage(
          placeholderEl,
          "Veuillez démarrer le live avant d'activer la caméra.",
        );
        return;
      }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia)
        return;
      if (!window.RTCPeerConnection) return;

      if (startBtn) startBtn.disabled = true;

      try {
        localStream = await getLocalStreamWithFallback();
      } catch (e) {
        console.error("[marketplace.live] getUserMedia failed", e);
        showPlaceholderMessage(placeholderEl, humanizeGetUserMediaError(e));
        if (startBtn) startBtn.disabled = false;
        hideVideo(videoEl, placeholderEl);
        return;
      } finally {
        if (startBtn) startBtn.disabled = false;
      }

      if (videoEl) {
        attachStreamToVideo(videoEl, localStream);
        showPlaceholderMessage(placeholderEl, "");
        showVideo(videoEl, placeholderEl);
      }

      if (startBtn) startBtn.style.display = "none";
      if (stopBtn) stopBtn.style.display = "inline-block";

      startPolling();
    }

    function stopBroadcaster() {
      try {
        broadcasterPcs.forEach(function (pc) {
          try {
            pc.close();
          } catch (e) {}
        });
      } catch (e) {
        // ignore
      }
      broadcasterPcs.clear();
      broadcasterPendingIce.clear();

      if (localStream) {
        localStream.getTracks().forEach(function (t) {
          try {
            t.stop();
          } catch (e) {}
        });
        localStream = null;
      }

      if (videoEl) {
        try {
          videoEl.srcObject = null;
        } catch (e) {}
      }

      if (startBtn) startBtn.style.display = "inline-block";
      if (stopBtn) stopBtn.style.display = "none";

      stopPolling();
      hideVideo(videoEl, placeholderEl);
      showPlaceholderMessage(placeholderEl, "");
    }

    // Featured product refresh (simple polling)
    var lastFeaturedId = null;
    var lastFeaturedName = null;
    var lastSpecial = null;
    var lastList = null;

    async function refreshFeatured() {
      try {
        var data = await postJson("/live/" + liveId + "/featured", {});
        var banner = $("live-featured-banner");
        var nameEl = $("live-featured-name");
        var priceEl = $("live-featured-price");
        var buyEl = $("live-featured-buy");

        if (!banner || !nameEl || !priceEl) return;

        if (!data || !data.featured) {
          banner.style.display = "none";
          lastFeaturedId = null;
          lastSpecial = null;
          lastList = null;
          return;
        }

        var product = data.product || {};
        var pid = product.id || null;
        var sp = Number(product.special_price || 0);
        var lp = Number(product.list_price || 0);

        if (pid === lastFeaturedId && sp === lastSpecial && lp === lastList) {
          return;
        }

        lastFeaturedId = pid;
        lastFeaturedName = product.name || "";
        lastSpecial = sp;
        lastList = lp;

        banner.style.display = "flex";

        nameEl.textContent = product.name || "";

        // Price rendering (safe DOM)
        while (priceEl.firstChild) priceEl.removeChild(priceEl.firstChild);

        if (sp && sp > 0) {
          priceEl.appendChild(document.createTextNode(sp + " FCFA "));

          var strike = document.createElement("span");
          strike.id = "live-featured-strike";
          strike.className =
            "text-muted text-decoration-line-through small ms-2";
          strike.textContent = lp + " FCFA";
          priceEl.appendChild(strike);
        } else {
          priceEl.textContent = lp + " FCFA";
        }

        if (buyEl && pid) {
          buyEl.setAttribute("href", "/marketplace/cart/add/" + pid);
        }
      } catch (e) {
        // ignore
      }
    }

    function setupBuyModal() {
      var buyEl = $("live-featured-buy");
      if (!buyEl) return;

      var modalEl = $("live-buy-modal");
      if (!modalEl) return;

      var nameEl = $("live-buy-product-name");
      var priceEl = $("live-buy-product-price");
      var qtyEl = $("live-buy-qty");
      var confirmEl = $("live-buy-confirm");

      var successEl = $("live-buy-success");
      var errorEl = $("live-buy-error");

      function resetAlerts() {
        if (successEl) {
          successEl.classList.add("d-none");
          successEl.textContent = "";
        }
        if (errorEl) {
          errorEl.classList.add("d-none");
          errorEl.textContent = "";
        }
      }

      function showError(message) {
        if (!errorEl) return;
        errorEl.textContent = message || "Erreur pendant l'achat.";
        errorEl.classList.remove("d-none");
      }

      function showSuccess(message) {
        if (!successEl) return;
        successEl.textContent = message || "Commande confirmée !";
        successEl.classList.remove("d-none");
      }

      function openModal() {
        try {
          if (window.bootstrap && window.bootstrap.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
            return true;
          }
        } catch (e) {
          // ignore
        }
        return false;
      }

      function closeModal() {
        try {
          if (window.bootstrap && window.bootstrap.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
            return;
          }
        } catch (e) {
          // ignore
        }
      }

      buyEl.addEventListener("click", function (ev) {
        if (!lastFeaturedId) return;
        if (!window.fetch) return;

        ev.preventDefault();

        resetAlerts();
        if (qtyEl) qtyEl.value = "1";

        if (nameEl) nameEl.textContent = lastFeaturedName || "";
        if (priceEl) {
          if (lastSpecial && Number(lastSpecial) > 0) {
            priceEl.textContent =
              formatFcfa(lastSpecial) +
              " (au lieu de " +
              formatFcfa(lastList) +
              ")";
          } else {
            priceEl.textContent = formatFcfa(lastList);
          }
        }

        // If bootstrap is not available, keep the old flow (cart add).
        if (!openModal()) {
          window.location.href =
            buyEl.getAttribute("href") || "/marketplace/cart";
        }
      });

      if (confirmEl) {
        confirmEl.addEventListener("click", async function () {
          resetAlerts();

          if (!lastFeaturedId) {
            showError("Aucun produit en vedette.");
            return;
          }

          var qty = 1;
          if (qtyEl) {
            qty = safeParseInt(qtyEl.value || 1, 1);
          }
          qty = Math.max(1, Math.min(qty, 99));

          confirmEl.disabled = true;
          try {
            var res = await postJson("/live/" + liveId + "/buy", {
              product_id: lastFeaturedId,
              qty: qty,
              csrf_token: csrfToken,
            });

            if (!res || res.status !== "ok") {
              var code = res && res.code ? String(res.code) : "buy_failed";
              throw new Error(code);
            }

            showSuccess("Commande confirmée !");

            // Local feedback immediately (others will see it via polling).
            if (res.order && res.order.product_name) {
              showOrderNotification(
                "Vous venez d'acheter " +
                  res.order.product_name +
                  " — " +
                  formatFcfa(res.order.amount_total) +
                  " !",
              );
            }

            setTimeout(function () {
              closeModal();
            }, 900);
          } catch (e) {
            showError("Impossible de finaliser l'achat. Réessayez.");
          } finally {
            confirmEl.disabled = false;
          }
        });
      }
    }

    // Start
    refreshFeatured();
    setInterval(refreshFeatured, 3000);

    setupBuyModal();

    setupCommentFormAjax();
    setupReactionOptimisticCounter();
    startUpdatesPolling();

    if (isBroadcaster) {
      if (startBtn) {
        startBtn.addEventListener("click", function () {
          startBroadcaster();
        });
      }
      if (stopBtn) {
        stopBtn.addEventListener("click", function () {
          stopBroadcaster();
        });
      }

      // If vendor is not broadcasting, keep placeholder visible
      hideVideo(videoEl, placeholderEl);
      return;
    }

    startViewer();
  });

  onReady(function () {
    var dashConfigEl = $("marketplace-live-vendor-dashboard-config");
    if (!dashConfigEl) return;

    var liveId = safeParseInt(dashConfigEl.dataset.liveId, 0);
    if (!liveId) return;

    var csrfToken = (dashConfigEl.dataset.csrfToken || "").trim();
    var liveStatus = (dashConfigEl.dataset.liveStatus || "").trim();

    var statusBadgeEl = $("vendor-live-status-badge");
    var viewersEl = $("stat-viewers");
    var likesEl = $("stat-likes");
    var ordersEl = $("stat-orders");
    var revenueEl = $("stat-revenue");

    var feedEl = $("vendor-comments-feed");
    var emptyEl = $("vendor-comments-empty");

    var ordersFeedEl = $("vendor-orders-feed");
    var ordersEmptyEl = $("vendor-orders-empty");

    var startFormEl = $("vendor-live-start-form");
    var endFormEl = $("vendor-live-end-form");

    var lastCommentId = 0;
    var lastOrderId = safeParseInt(dashConfigEl.dataset.lastOrderId, 0);
    var lastReactionId = safeParseInt(dashConfigEl.dataset.lastReactionId, 0);
    var updatesInFlight = false;
    var updatesTimer = null;

    var avatarStyleText = null;
    var bubbleClassText = "bg-light rounded p-2 flex-fill";
    var authorClassText = "fw-bold";
    var authorStyleText = "font-size:11px;";
    var contentStyleText = "font-size:13px;";
    var avatarTextStyleText = null;

    function setNumberText(el, value) {
      if (!el) return;
      if (typeof value === "number" && Number.isFinite(value)) {
        el.textContent = String(value);
      }
    }

    function setMoneyText(el, value) {
      if (!el) return;
      if (typeof value === "number" && Number.isFinite(value)) {
        try {
          el.textContent = Math.round(value).toLocaleString("fr-FR") + " FCFA";
        } catch (e) {
          el.textContent = Math.round(value) + " FCFA";
        }
      }
    }

    function updateStatusBadge(status) {
      if (!statusBadgeEl) return;
      status = status ? String(status).trim() : "";

      statusBadgeEl.classList.remove("bg-danger");
      statusBadgeEl.classList.remove("bg-secondary");
      if (isLive(status)) {
        statusBadgeEl.classList.add("bg-danger");
        statusBadgeEl.textContent = "● EN DIRECT";
      } else if (status === "scheduled") {
        statusBadgeEl.classList.add("bg-secondary");
        statusBadgeEl.textContent = "Programme";
      } else if (status === "ended") {
        statusBadgeEl.classList.add("bg-secondary");
        statusBadgeEl.textContent = "Terminé";
      } else if (status) {
        statusBadgeEl.classList.add("bg-secondary");
        statusBadgeEl.textContent = status;
      }
    }

    function computeLastCommentIdFromDom() {
      if (!feedEl) return 0;
      var nodes = feedEl.querySelectorAll("[data-comment-id]");
      var maxId = 0;
      for (var i = 0; i < nodes.length; i++) {
        var id = safeParseInt(nodes[i].getAttribute("data-comment-id"), 0);
        if (id > maxId) maxId = id;
      }
      return maxId;
    }

    function computeLastOrderIdFromDom() {
      if (!ordersFeedEl) return 0;
      var nodes = ordersFeedEl.querySelectorAll("[data-order-id]");
      var maxId = 0;
      for (var i = 0; i < nodes.length; i++) {
        var id = safeParseInt(nodes[i].getAttribute("data-order-id"), 0);
        if (id > maxId) maxId = id;
      }
      return maxId;
    }

    function captureExistingCommentStyles() {
      if (!feedEl) return;
      var item = feedEl.querySelector("[data-comment-id]");
      if (!item) return;

      var avatarEl =
        item.children && item.children[0] ? item.children[0] : null;
      var bubbleEl =
        item.children && item.children[1] ? item.children[1] : null;
      var authorEl =
        bubbleEl && bubbleEl.children && bubbleEl.children[0]
          ? bubbleEl.children[0]
          : null;
      var contentEl =
        bubbleEl && bubbleEl.children && bubbleEl.children[1]
          ? bubbleEl.children[1]
          : null;

      if (avatarEl) {
        avatarStyleText = avatarEl.getAttribute("style") || null;
        avatarTextStyleText = avatarEl.getAttribute("style") || null;
      }
      if (bubbleEl) {
        bubbleClassText = bubbleEl.className || bubbleClassText;
      }
      if (authorEl) {
        authorClassText = authorEl.className || authorClassText;
        authorStyleText = authorEl.getAttribute("style") || authorStyleText;
      }
      if (contentEl) {
        contentStyleText = contentEl.getAttribute("style") || contentStyleText;
      }
    }

    function createDashboardCommentNode(comment) {
      if (!comment) return null;
      var id =
        typeof comment.id === "number"
          ? comment.id
          : safeParseInt(comment.id, 0);
      if (!id) return null;

      var partnerName = (comment.partner_name || "").trim();
      var content = String(comment.content || "");

      var row = document.createElement("div");
      row.className = "d-flex gap-2 mb-2";
      row.setAttribute("data-comment-id", String(id));

      var avatar = document.createElement("div");
      if (avatarStyleText) {
        avatar.setAttribute("style", avatarStyleText);
      } else {
        avatar.style.width = "28px";
        avatar.style.height = "28px";
        avatar.style.borderRadius = "50%";
        avatar.style.display = "flex";
        avatar.style.alignItems = "center";
        avatar.style.justifyContent = "center";
        avatar.style.fontSize = "11px";
        avatar.style.fontWeight = "700";
        avatar.style.flexShrink = "0";
      }
      var initial = partnerName ? partnerName.charAt(0) : "U";
      avatar.textContent = initial.toUpperCase();
      row.appendChild(avatar);

      var bubble = document.createElement("div");
      bubble.className = bubbleClassText;

      var author = document.createElement("div");
      author.className = authorClassText;
      if (authorStyleText) author.setAttribute("style", authorStyleText);
      author.textContent = partnerName;
      bubble.appendChild(author);

      var text = document.createElement("div");
      if (contentStyleText) text.setAttribute("style", contentStyleText);
      text.textContent = content;
      bubble.appendChild(text);

      row.appendChild(bubble);
      return row;
    }

    function prependNewComments(comments) {
      if (!feedEl || !comments || !comments.length) return;

      if (emptyEl) {
        try {
          emptyEl.remove();
        } catch (e) {
          // ignore
        }
        emptyEl = null;
      }

      var keepTop = isNearTop(feedEl, 60);

      // Dashboard shows newest first; insert in reverse so newest ends up on top.
      for (var i = comments.length - 1; i >= 0; i--) {
        var node = createDashboardCommentNode(comments[i]);
        if (!node) continue;

        var id = safeParseInt(node.getAttribute("data-comment-id"), 0);
        if (id && id <= lastCommentId) continue;

        if (feedEl.firstChild) {
          feedEl.insertBefore(node, feedEl.firstChild);
        } else {
          feedEl.appendChild(node);
        }
        lastCommentId = Math.max(lastCommentId, id);
      }

      if (keepTop) {
        feedEl.scrollTop = 0;
      }
    }

    function formatFcfa(amount) {
      var n = Number(amount || 0);
      if (!Number.isFinite(n)) n = 0;
      try {
        return Math.round(n).toLocaleString("fr-FR") + " FCFA";
      } catch (e) {
        return Math.round(n) + " FCFA";
      }
    }

    function createDashboardOrderNode(order) {
      if (!order) return null;
      var id =
        typeof order.id === "number"
          ? order.id
          : safeParseInt(order.id || 0, 0);
      if (!id) return null;

      var buyer = (order.buyer_name || "").trim() || "Client";
      var productName = (order.product_name || "").trim();
      var amountText = formatFcfa(order.amount_total || 0);

      var row = document.createElement("div");
      row.className =
        "d-flex justify-content-between align-items-start py-2 border-bottom";
      row.setAttribute("data-order-id", String(id));

      var left = document.createElement("div");

      var buyerEl = document.createElement("div");
      buyerEl.className = "fw-bold";
      buyerEl.style.fontSize = "13px";
      buyerEl.textContent = buyer;
      left.appendChild(buyerEl);

      if (productName) {
        var productEl = document.createElement("div");
        productEl.className = "text-muted small";
        productEl.textContent = productName;
        left.appendChild(productEl);
      }

      var right = document.createElement("div");
      right.className = "fw-bold text-success";
      right.textContent = amountText;

      row.appendChild(left);
      row.appendChild(right);
      return row;
    }

    function prependNewOrders(orders) {
      if (!ordersFeedEl || !orders || !orders.length) return;

      if (ordersEmptyEl) {
        try {
          ordersEmptyEl.remove();
        } catch (e) {
          // ignore
        }
        ordersEmptyEl = null;
      }

      var keepTop = isNearTop(ordersFeedEl, 60);

      // Newest on top.
      for (var i = orders.length - 1; i >= 0; i--) {
        var node = createDashboardOrderNode(orders[i]);
        if (!node) continue;

        var id = safeParseInt(node.getAttribute("data-order-id"), 0);
        if (id && id <= lastOrderId) continue;

        if (ordersFeedEl.firstChild) {
          ordersFeedEl.insertBefore(node, ordersFeedEl.firstChild);
        } else {
          ordersFeedEl.appendChild(node);
        }
        lastOrderId = Math.max(lastOrderId, id);
      }

      if (keepTop) {
        ordersFeedEl.scrollTop = 0;
      }
    }

    async function pollLiveUpdates() {
      if (updatesInFlight) return;
      updatesInFlight = true;
      try {
        var data = await postJson("/live/" + liveId + "/updates", {
          after_comment_id: lastCommentId,
          after_order_id: lastOrderId,
          after_reaction_id: lastReactionId,
          limit: 50,
        });

        if (data && data.live) {
          var newStatus = (data.live.status || "").trim();
          if (newStatus && newStatus !== liveStatus) {
            liveStatus = newStatus;
            try {
              dashConfigEl.dataset.liveStatus = newStatus;
            } catch (e) {
              // ignore
            }
            updateStatusBadge(newStatus);
          }

          setNumberText(viewersEl, data.live.viewer_count);
          setNumberText(likesEl, data.live.like_count);
          setNumberText(ordersEl, data.live.order_count);
          setMoneyText(revenueEl, data.live.revenue_total);
        }

        prependNewComments(data && data.comments ? data.comments : []);
        prependNewOrders(data && data.orders ? data.orders : []);

        var reactions = data && data.reactions ? data.reactions : [];
        for (var i = 0; i < reactions.length; i++) {
          var rid =
            typeof reactions[i].id === "number"
              ? reactions[i].id
              : safeParseInt(reactions[i].id || 0, 0);
          if (rid) lastReactionId = Math.max(lastReactionId, rid);
        }
      } catch (e) {
        // retry later
      } finally {
        updatesInFlight = false;
      }
    }

    function startUpdatesPolling() {
      if (updatesTimer) return;
      updatesTimer = setInterval(pollLiveUpdates, 1000);
      pollLiveUpdates();
    }

    function interceptLiveActions() {
      function extractCsrfTokenFromForm(formEl) {
        if (!formEl) return csrfToken;
        var input = formEl.querySelector("input[name='csrf_token']");
        var token = input && input.value ? String(input.value).trim() : "";
        return token || csrfToken;
      }

      if (startFormEl) {
        startFormEl.addEventListener("submit", async function (ev) {
          ev.preventDefault();

          try {
            var token = extractCsrfTokenFromForm(startFormEl);
            var res = await postJson(
              "/my/vendor/live/" + liveId + "/start/json",
              {
                csrf_token: token,
              },
            );
            if (!res || res.status !== "ok") {
              throw new Error("start_live_failed");
            }
            window.location.href = "/my/vendor/live/" + liveId + "/dashboard";
          } catch (e) {
            try {
              startFormEl.submit();
            } catch (e2) {
              // ignore
            }
          }
        });
      }

      if (endFormEl) {
        endFormEl.addEventListener("submit", async function (ev) {
          ev.preventDefault();

          try {
            var token = extractCsrfTokenFromForm(endFormEl);
            var res = await postJson(
              "/my/vendor/live/" + liveId + "/end/json",
              {
                csrf_token: token,
              },
            );
            if (!res || res.status !== "ok") {
              throw new Error("end_live_failed");
            }
            window.location.href = "/my/vendor/live/" + liveId + "/dashboard";
          } catch (e) {
            try {
              endFormEl.submit();
            } catch (e2) {
              // ignore
            }
          }
        });
      }
    }

    // Init
    lastCommentId = computeLastCommentIdFromDom();
    lastOrderId = Math.max(lastOrderId, computeLastOrderIdFromDom());
    captureExistingCommentStyles();
    updateStatusBadge(liveStatus);
    interceptLiveActions();
    startUpdatesPolling();
  });
})();
