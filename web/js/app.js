(function () {
  const PAGE = document.body.dataset.page;

  function $(selector, root) {
    return (root || document).querySelector(selector);
  }

  function $all(selector, root) {
    return Array.from((root || document).querySelectorAll(selector));
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function params() {
    return new URLSearchParams(window.location.search);
  }

  function param(name) {
    return params().get(name);
  }

  function formatCurrency(value) {
    const amount = Number(value || 0);
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2
    }).format(Number.isFinite(amount) ? amount : 0);
  }

  function formatDate(value) {
    if (!value) return "Unknown date";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Unknown date";
    return date.toLocaleDateString();
  }

  function progressPercent(current, goal) {
    const currentAmount = Number(current || 0);
    const goalAmount = Number(goal || 0);
    if (!goalAmount || goalAmount <= 0) return 0;
    return Math.max(0, Math.min(100, (currentAmount / goalAmount) * 100));
  }

  function progressMarkup(current, goal, live) {
    const pct = progressPercent(current, goal);
    return `
      <div class="progress-block">
        <div class="progress-track ${live ? "is-live" : ""}" aria-hidden="true">
          <div class="progress-fill" style="width: ${pct.toFixed(2)}%"></div>
        </div>
        <div class="progress-labels">
          <span>${formatCurrency(current)} raised</span>
          <span>${pct.toFixed(0)}%</span>
        </div>
      </div>
    `;
  }

  function setError(idOrElement, message) {
    const element = typeof idOrElement === "string" ? document.getElementById(idOrElement) : idOrElement;
    if (!element) return;
    element.textContent = message || "";
    element.classList.toggle("hidden", !message);
  }

  function setHtml(idOrElement, html) {
    const element = typeof idOrElement === "string" ? document.getElementById(idOrElement) : idOrElement;
    if (element) element.innerHTML = html;
  }

  function show(element, visible) {
    if (element) element.classList.toggle("hidden", !visible);
  }

  function setBusy(button, busy, busyText) {
    if (!button) return;
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }
    button.disabled = busy;
    button.textContent = busy ? busyText || "Working..." : button.dataset.originalText;
  }

  function getInfo(campaign) {
    return campaign && campaign.info ? campaign.info : {};
  }

  function campaignTitle(campaign) {
    return getInfo(campaign).title || "Untitled campaign";
  }

  function campaignOwner(campaign) {
    return getInfo(campaign).owner || {};
  }

  function userCanManage(campaign) {
    const payload = Auth.getPayload();
    if (!payload || !campaign) return false;
    const ownerId = Number(campaignOwner(campaign).userId);
    return Number(payload.sub) === ownerId || payload.role === "admin";
  }

  function isLoggedIn() {
    return Auth.hasValidToken();
  }

  function youtubeId(url) {
    if (!url) return "";
    try {
      const parsed = new URL(url);
      if (parsed.hostname.includes("youtu.be")) {
        return parsed.pathname.replace("/", "").split("/")[0];
      }
      if (parsed.hostname.includes("youtube.com")) {
        if (parsed.searchParams.get("v")) return parsed.searchParams.get("v");
        const match = parsed.pathname.match(/\/(embed|shorts)\/([^/?]+)/);
        return match ? match[2] : "";
      }
    } catch (error) {
      return "";
    }
    return "";
  }

  function campaignThumb(campaign) {
    const id = youtubeId(getInfo(campaign).videolink);
    if (id) {
      return `<img alt="" src="https://img.youtube.com/vi/${encodeURIComponent(id)}/hqdefault.jpg" loading="lazy">`;
    }
    return `
      <div class="fallback-thumb">
        <span class="material-symbols-outlined" aria-hidden="true">volunteer_activism</span>
      </div>
    `;
  }

  function videoMarkup(url) {
    const id = youtubeId(url);
    if (id) {
      return `<iframe class="video-frame" src="https://www.youtube.com/embed/${encodeURIComponent(id)}" title="Campaign video" allowfullscreen></iframe>`;
    }
    if (url) {
      return `<a class="video-link-panel" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">Open campaign video</a>`;
    }
    return `
      <div class="video-link-panel">
        <span class="material-symbols-outlined" aria-hidden="true">volunteer_activism</span>
      </div>
    `;
  }

  function campaignCard(campaign) {
    const id = Api.getCampaignId(campaign);
    const info = getInfo(campaign);
    const owner = campaignOwner(campaign);
    const open = campaign.isOpen !== false;
    return `
      <article class="campaign-card">
        <a class="campaign-thumb" href="campaign.html?id=${encodeURIComponent(id)}" aria-label="Open ${escapeHtml(campaignTitle(campaign))}">
          ${campaignThumb(campaign)}
        </a>
        <div class="campaign-body">
          ${progressMarkup(campaign.current, campaign.goal, false)}
          <div>
            <h3>${escapeHtml(campaignTitle(campaign))}</h3>
            <div class="campaign-meta">
              <span>${escapeHtml(owner.username || "Unknown owner")}</span>
              <span>${escapeHtml(formatDate(info.created))}</span>
            </div>
          </div>
          <div class="campaign-card-footer">
            <span class="badge ${open ? "badge-open" : "badge-closed"}">${open ? "Open" : "Closed"}</span>
            <a class="button button-secondary" href="campaign.html?id=${encodeURIComponent(id)}">
              <span class="material-symbols-outlined" aria-hidden="true">open_in_new</span>
              Open
            </a>
          </div>
        </div>
      </article>
    `;
  }

  function renderCampaignGrid(campaigns, target, emptyText) {
    if (!target) return;
    if (!campaigns || campaigns.length === 0) {
      target.innerHTML = `<div class="empty-state">${escapeHtml(emptyText || "No campaigns found.")}</div>`;
      return;
    }
    target.innerHTML = campaigns.map(campaignCard).join("");
  }

  function renderNav() {
    const mount = document.getElementById("site-nav");
    if (!mount) return;
    const payload = Auth.getPayload();
    const loggedIn = isLoggedIn();
    const username = loggedIn ? `User #${escapeHtml(payload.sub)}` : "";
    const currentSearch = param("q") || param("title") || "";

    mount.innerHTML = `
      <nav class="top-nav" aria-label="Main navigation">
        <div class="container top-nav-inner">
          <a class="brand" href="index.html" aria-label="No Refunds home">
            <span class="brand-mark">N</span>
            <span>No Refunds</span>
          </a>
          <form class="nav-search" id="navSearch">
            <span class="material-symbols-outlined" aria-hidden="true">search</span>
            <input name="q" value="${escapeHtml(currentSearch)}" placeholder="Search campaigns" autocomplete="off">
          </form>
          <div class="nav-actions">
            ${loggedIn ? `<span class="nav-user">${username}</span>` : ""}
            ${loggedIn ? `<a class="button button-action" href="create-campaign.html"><span class="material-symbols-outlined" aria-hidden="true">add</span>Start</a>` : ""}
            ${loggedIn ? `<button class="button button-secondary" id="logoutButton" type="button">Logout</button>` : `<a class="button button-secondary" href="login.html">Login</a>`}
          </div>
        </div>
      </nav>
    `;

    $("#navSearch", mount).addEventListener("submit", function (event) {
      event.preventDefault();
      const q = new FormData(event.currentTarget).get("q").toString().trim();
      window.location.href = q ? `index.html?q=${encodeURIComponent(q)}` : "index.html";
    });

    const logoutButton = $("#logoutButton", mount);
    if (logoutButton) {
      logoutButton.addEventListener("click", Auth.logout);
    }
  }

  async function initHome() {
    const grid = $("#campaignGrid");
    const error = $("#homeError");
    const pageLabel = $("#pageLabel");
    const prevButton = $("#prevPage");
    const nextButton = $("#nextPage");
    const homeSearch = $("#homeSearch");
    let page = Math.max(1, Number(param("page") || 1));
    const searchTerm = (param("q") || param("title") || "").trim();

    if (homeSearch && searchTerm) {
      homeSearch.elements.q.value = searchTerm;
    }

    async function load() {
      setError(error, "");
      grid.innerHTML = `<span class="loader">Loading campaigns</span>`;
      try {
        const data = searchTerm ? await Api.searchCampaigns(searchTerm) : await Api.listCampaigns(page);
        const campaigns = data.campaigns || [];
        renderCampaignGrid(campaigns, grid, searchTerm ? "No campaigns match that search." : "No campaigns are available yet.");
        pageLabel.textContent = searchTerm ? "Search results" : `Page ${page}`;
        prevButton.disabled = searchTerm || page <= 1;
        nextButton.disabled = Boolean(searchTerm) || campaigns.length < 6;
      } catch (requestError) {
        grid.innerHTML = "";
        setError(error, requestError.message);
      }
    }

    if (homeSearch) {
      homeSearch.addEventListener("submit", function (event) {
        event.preventDefault();
        const q = new FormData(homeSearch).get("q").toString().trim();
        window.location.href = q ? `index.html?q=${encodeURIComponent(q)}` : "index.html";
      });
    }

    prevButton.addEventListener("click", function () {
      if (page > 1) window.location.href = `index.html?page=${page - 1}`;
    });
    nextButton.addEventListener("click", function () {
      window.location.href = `index.html?page=${page + 1}`;
    });

    await load();
  }

  async function initLogin() {
    const form = $("#loginForm");
    const error = $("#loginError");
    const success = $("#loginSuccess");
    if (param("registered") === "1") show(success, true);

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setError(error, "");
      const button = form.querySelector("button[type='submit']");
      const data = Object.fromEntries(new FormData(form));
      setBusy(button, true, "Signing in...");
      try {
        const result = await Api.login({
          username: data.username.trim(),
          password: data.password
        });
        Auth.setToken(result.token);
        window.location.href = "index.html";
      } catch (requestError) {
        setError(error, requestError.status === 401 ? "Incorrect username or password" : requestError.message);
      } finally {
        setBusy(button, false);
      }
    });
  }

  async function initRegister() {
    const form = $("#registerForm");
    const error = $("#registerError");

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setError(error, "");
      const button = form.querySelector("button[type='submit']");
      const data = Object.fromEntries(new FormData(form));
      if (data.password !== data.confirmPassword) {
        setError(error, "Passwords do not match.");
        return;
      }
      setBusy(button, true, "Creating...");
      try {
        await Api.register({
          username: data.username.trim(),
          email: data.email.trim(),
          password: data.password
        });
        window.location.href = "login.html?registered=1";
      } catch (requestError) {
        setError(error, requestError.status === 409 ? requestError.message || "Username or email already taken" : requestError.message);
      } finally {
        setBusy(button, false);
      }
    });
  }

  function donorTotals(donors) {
    const totals = new Map();
    (donors || []).forEach(function (donor) {
      const username = donor.username || "Anonymous";
      const current = totals.get(username) || { username, amount: 0, lastTime: "" };
      current.amount += Number(donor.amount || 0);
      if (!current.lastTime || new Date(donor.time) > new Date(current.lastTime)) {
        current.lastTime = donor.time;
      }
      totals.set(username, current);
    });
    return Array.from(totals.values()).sort(function (a, b) {
      return b.amount - a.amount;
    });
  }

  function renderDonors(donors) {
    const list = donorTotals(donors);
    if (!list.length) return `<div class="empty-state">No donations yet.</div>`;
    return list.map(function (donor, index) {
      return `
        <div class="donor-row">
          <span class="donor-rank">${index + 1}</span>
          <span class="donor-name">${escapeHtml(donor.username)}</span>
          <strong>${formatCurrency(donor.amount)}</strong>
        </div>
      `;
    }).join("");
  }

  function renderComments(campaign) {
    const comments = campaign.comments || [];
    const loggedIn = isLoggedIn();
    const commentForm = loggedIn ? `
      <form class="inline-form" id="commentForm">
        <div class="field">
          <label for="commentText">Comment</label>
          <textarea id="commentText" name="text" required></textarea>
        </div>
        <button class="button button-primary" type="submit">
          <span class="material-symbols-outlined" aria-hidden="true">send</span>
          Post Comment
        </button>
      </form>
    ` : `<a class="button button-secondary" href="login.html">Log in to comment</a>`;

    const rendered = comments.length ? comments.map(function (comment) {
      const commentId = comment._id || comment.commentId;
      const replies = comment.replies || [];
      return `
        <article class="comment">
          <div class="comment-head">
            <span class="comment-author">${escapeHtml(comment.user && comment.user.username ? comment.user.username : "User")}</span>
            ${loggedIn ? `<button class="button button-ghost reply-toggle" type="button" data-comment-id="${escapeHtml(commentId)}">Reply</button>` : ""}
          </div>
          <p class="comment-body">${escapeHtml(comment.text)}</p>
          ${loggedIn ? `
            <form class="inline-form hidden reply-form" data-comment-id="${escapeHtml(commentId)}">
              <div class="field">
                <label>Reply</label>
                <textarea name="text" required></textarea>
              </div>
              <button class="button button-primary" type="submit">Post Reply</button>
            </form>
          ` : ""}
          ${replies.map(function (reply) {
            return `
              <div class="reply">
                <div class="comment-author">${escapeHtml(reply.user && reply.user.username ? reply.user.username : "User")}</div>
                <p class="comment-body">${escapeHtml(reply.text)}</p>
              </div>
            `;
          }).join("")}
        </article>
      `;
    }).join("") : `<div class="empty-state">No comments yet.</div>`;

    return `${rendered}${commentForm}`;
  }

  function renderReports(campaign) {
    const reports = campaign.reports || [];
    if (!reports.length) return `<div class="empty-state">No updates have been posted yet.</div>`;
    return reports.map(function (report) {
      const images = report.attachedImages || [];
      return `
        <article class="report-item">
          <div class="report-head">
            <span class="report-title">${escapeHtml(report.reportTitle || "Campaign update")}</span>
            <strong>${formatCurrency(report.amount)}</strong>
          </div>
          <p class="muted small">${escapeHtml(formatDate(report.time))}</p>
          ${images.length ? `
            <div class="report-images">
              ${images.map(function (name) {
                return `<img src="${Api.imageUrl(name)}" alt="${escapeHtml(report.reportTitle || "Report image")}" loading="lazy">`;
              }).join("")}
            </div>
          ` : ""}
        </article>
      `;
    }).join("");
  }

  function renderCampaignDetail(campaign, live) {
    const id = Api.getCampaignId(campaign);
    const info = getInfo(campaign);
    const owner = campaignOwner(campaign);
    const open = campaign.isOpen !== false;
    const payload = Auth.getPayload();
    const loggedIn = isLoggedIn();
    const canManage = userCanManage(campaign);
    const likedBy = (info.likedBy || []).map(Number);
    const alreadyLiked = payload ? likedBy.includes(Number(payload.sub)) : false;

    return `
      <div class="detail-layout">
        <div class="detail-main">
          <section class="detail-media">
            ${videoMarkup(info.videolink)}
            <div class="detail-copy">
              <div class="section-title-row">
                <span class="badge ${open ? "badge-open" : "badge-closed"}">${open ? "Open" : "Closed"}</span>
                <span class="badge badge-action">${Number(info.likes || 0)} likes</span>
              </div>
              <h1>${escapeHtml(campaignTitle(campaign))}</h1>
              <p>${escapeHtml(info.description || "")}</p>
              <div class="owner-row">
                <span>By <a href="profile.html?ownerId=${encodeURIComponent(owner.userId || "")}">${escapeHtml(owner.username || "Unknown owner")}</a></span>
                <span>${escapeHtml(formatDate(info.created))}</span>
              </div>
              ${canManage ? `
                <div class="owner-actions" style="margin-top: 20px;">
                  <a class="button button-secondary" href="edit-campaign.html?id=${encodeURIComponent(id)}">
                    <span class="material-symbols-outlined" aria-hidden="true">edit</span>
                    Edit
                  </a>
                  <a class="button button-secondary" href="report.html?campaignId=${encodeURIComponent(id)}">
                    <span class="material-symbols-outlined" aria-hidden="true">receipt_long</span>
                    Post Update
                  </a>
                  ${open ? `<button class="button button-danger" id="closeCampaignButton" type="button">Close Campaign</button>` : ""}
                </div>
              ` : ""}
            </div>
          </section>
          <section class="surface-panel" style="padding: 24px;">
            <div class="tabs" role="tablist">
              <button class="tab-button active" type="button" data-tab="comments">Comments</button>
              <button class="tab-button" type="button" data-tab="updates">Updates</button>
            </div>
            <div id="tab-comments" class="tab-panel">
              <div id="campaignComments" class="comment-list">${renderComments(campaign)}</div>
            </div>
            <div id="tab-updates" class="tab-panel hidden">
              <div class="report-list">${renderReports(campaign)}</div>
            </div>
          </section>
        </div>
        <aside class="sidebar">
          <section class="card donation-panel">
            <div class="stat-value" id="currentRaised">${formatCurrency(campaign.current)}</div>
            <p class="muted">raised of ${formatCurrency(campaign.goal)}</p>
            ${progressMarkup(campaign.current, campaign.goal, live)}
            <div class="panel-actions">
              ${open && loggedIn ? `
                <a class="button button-action button-wide" href="donate.html?id=${encodeURIComponent(id)}">
                  <span class="material-symbols-outlined" aria-hidden="true">payments</span>
                  Donate Now
                </a>
              ` : ""}
              ${open && !loggedIn ? `<a class="button button-action button-wide" href="login.html">Log in to Donate</a>` : ""}
              ${!open ? `<span class="badge badge-closed">Closed</span>` : ""}
              ${loggedIn && !alreadyLiked ? `
                <button class="button button-secondary button-wide" id="likeButton" type="button">
                  <span class="material-symbols-outlined" aria-hidden="true">favorite</span>
                  Like Campaign
                </button>
              ` : ""}
              ${loggedIn && alreadyLiked ? `<span class="success">You liked this campaign.</span>` : ""}
            </div>
          </section>
          <section class="card donation-panel">
            <h2 class="section-title">Top Donors</h2>
            <div id="donorList" class="donor-list" style="margin-top: 16px;">
              <span class="loader">Loading donors</span>
            </div>
          </section>
        </aside>
      </div>
    `;
  }

  async function initCampaign() {
    const id = param("id");
    const content = $("#campaignContent");
    const error = $("#campaignError");
    let campaign = null;
    let ws = null;

    async function loadDonors() {
      const donorList = $("#donorList");
      if (!donorList) return;
      try {
        const data = await Api.getDonations(id);
        donorList.innerHTML = renderDonors(data.donors || []);
      } catch (requestError) {
        donorList.innerHTML = `<div class="empty-state">${escapeHtml(requestError.message)}</div>`;
      }
    }

    function attachCampaignEvents() {
      $all(".tab-button").forEach(function (button) {
        button.addEventListener("click", function () {
          const tab = button.dataset.tab;
          $all(".tab-button").forEach(function (item) {
            item.classList.toggle("active", item === button);
          });
          show($("#tab-comments"), tab === "comments");
          show($("#tab-updates"), tab === "updates");
        });
      });

      const likeButton = $("#likeButton");
      if (likeButton) {
        likeButton.addEventListener("click", async function () {
          setBusy(likeButton, true, "Liking...");
          try {
            await Api.likeCampaign(id, Auth.currentUserId());
            await loadCampaign(false);
          } catch (requestError) {
            setError(error, requestError.message);
          } finally {
            setBusy(likeButton, false);
          }
        });
      }

      const closeButton = $("#closeCampaignButton");
      if (closeButton) {
        closeButton.addEventListener("click", async function () {
          setBusy(closeButton, true, "Closing...");
          try {
            await Api.updateCampaign(id, { close: true });
            await loadCampaign(false);
          } catch (requestError) {
            setError(error, requestError.message);
          } finally {
            setBusy(closeButton, false);
          }
        });
      }

      const commentForm = $("#commentForm");
      if (commentForm) {
        commentForm.addEventListener("submit", async function (event) {
          event.preventDefault();
          const button = commentForm.querySelector("button[type='submit']");
          const text = new FormData(commentForm).get("text").toString().trim();
          if (!text) return;
          setBusy(button, true, "Posting...");
          try {
            await Api.postComment({ campaignId: id, text });
            await loadCampaign(false);
          } catch (requestError) {
            setError(error, requestError.message);
          } finally {
            setBusy(button, false);
          }
        });
      }

      $all(".reply-toggle").forEach(function (button) {
        button.addEventListener("click", function () {
          const form = $all(".reply-form").find(function (item) {
            return item.dataset.commentId === button.dataset.commentId;
          });
          if (form) show(form, form.classList.contains("hidden"));
        });
      });

      $all(".reply-form").forEach(function (form) {
        form.addEventListener("submit", async function (event) {
          event.preventDefault();
          const button = form.querySelector("button[type='submit']");
          const text = new FormData(form).get("text").toString().trim();
          if (!text) return;
          setBusy(button, true, "Posting...");
          try {
            await Api.postReply(form.dataset.commentId, { campaignId: id, text });
            await loadCampaign(false);
          } catch (requestError) {
            setError(error, requestError.message);
          } finally {
            setBusy(button, false);
          }
        });
      });
    }

    async function loadCampaign(live) {
      if (!id) {
        setError(error, "Campaign not found.");
        return;
      }
      setError(error, "");
      if (!campaign) content.innerHTML = `<span class="loader">Loading campaign</span>`;
      try {
        const data = await Api.getCampaign(id);
        campaign = data.campaign;
        content.innerHTML = renderCampaignDetail(campaign, live);
        attachCampaignEvents();
        await loadDonors();
      } catch (requestError) {
        content.innerHTML = "";
        setError(error, requestError.message);
      }
    }

    function connectWebSocket() {
      if (!id || !window.WebSocket) return;
      ws = new WebSocket(Api.wsUrl(id));
      ws.addEventListener("message", function (event) {
        try {
          const data = JSON.parse(event.data);
          if (data.event === "counter_refresh" && String(data.campaignId) === String(id)) {
            loadCampaign(true);
          }
        } catch (error) {
          return;
        }
      });
    }

    await loadCampaign(false);
    connectWebSocket();
    window.addEventListener("beforeunload", function () {
      if (ws) ws.close();
    });
  }

  async function initDonate() {
    const payload = Auth.requireAuth();
    if (!payload) return;
    const id = param("id");
    const form = $("#donateForm");
    const error = $("#donateError");
    const receiptNotice = $("#receiptNotice");
    const amountInput = $("#donationAmount");
    const total = $("#donationTotal");
    const campaignTitleEl = $("#donationCampaignTitle");
    const summary = $("#donationSummary");
    let campaign = null;

    function updateTotal() {
      const amount = Number(amountInput.value || 0);
      total.textContent = formatCurrency(amount);
      show(receiptNotice, amount > 50);
    }

    try {
      const data = await Api.getCampaign(id);
      campaign = data.campaign;
      campaignTitleEl.textContent = campaignTitle(campaign);
      summary.innerHTML = progressMarkup(campaign.current, campaign.goal, false);
      if (campaign.isOpen === false) {
        setError(error, "This campaign is closed.");
        form.querySelector("button[type='submit']").disabled = true;
      }
    } catch (requestError) {
      setError(error, requestError.message);
      form.querySelector("button[type='submit']").disabled = true;
    }

    amountInput.addEventListener("input", updateTotal);
    updateTotal();

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setError(error, "");
      const amount = Number(amountInput.value);
      if (!amount || amount <= 0) {
        setError(error, "Enter a donation amount greater than $0.00.");
        return;
      }
      const button = form.querySelector("button[type='submit']");
      setBusy(button, true, "Confirming...");
      try {
        await Api.donate({
          campaignID: id,
          amount,
          time: new Date().toISOString()
        });
        window.location.href = `campaign.html?id=${encodeURIComponent(id)}`;
      } catch (requestError) {
        setError(error, requestError.message);
      } finally {
        setBusy(button, false);
      }
    });
  }

  async function initCreateCampaign() {
    const payload = Auth.requireAuth();
    if (!payload) return;
    const form = $("#campaignForm");
    const error = $("#campaignFormError");

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setError(error, "");
      const button = form.querySelector("button[type='submit']");
      const data = Object.fromEntries(new FormData(form));
      setBusy(button, true, "Creating...");
      try {
        const result = await Api.createCampaign({
          title: data.title.trim(),
          description: data.description.trim(),
          goal: Number(data.goal),
          videolink: data.videolink.trim()
        });
        window.location.href = `campaign.html?id=${encodeURIComponent(result.campaignId)}`;
      } catch (requestError) {
        setError(error, requestError.message);
      } finally {
        setBusy(button, false);
      }
    });
  }

  async function initEditCampaign() {
    const payload = Auth.requireAuth();
    if (!payload) return;
    const id = param("id");
    const form = $("#campaignForm");
    const error = $("#campaignFormError");
    let campaign = null;

    try {
      const data = await Api.getCampaign(id);
      campaign = data.campaign;
      if (!userCanManage(campaign)) {
        setError(error, "Permission denied.");
        form.classList.add("hidden");
        return;
      }
      form.elements.title.value = campaignTitle(campaign);
      form.elements.description.value = getInfo(campaign).description || "";
      form.elements.videolink.value = getInfo(campaign).videolink || "";
    } catch (requestError) {
      setError(error, requestError.message);
      form.classList.add("hidden");
      return;
    }

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setError(error, "");
      const data = Object.fromEntries(new FormData(form));
      const payload = {};
      if (data.title.trim() !== campaignTitle(campaign)) payload.title = data.title.trim();
      if (data.description.trim() !== (getInfo(campaign).description || "")) payload.description = data.description.trim();
      if (data.videolink.trim() !== (getInfo(campaign).videolink || "")) payload.videolink = data.videolink.trim();
      if (!Object.keys(payload).length) {
        window.location.href = `campaign.html?id=${encodeURIComponent(id)}`;
        return;
      }
      const button = form.querySelector("button[type='submit']");
      setBusy(button, true, "Saving...");
      try {
        await Api.updateCampaign(id, payload);
        window.location.href = `campaign.html?id=${encodeURIComponent(id)}`;
      } catch (requestError) {
        setError(error, requestError.message);
      } finally {
        setBusy(button, false);
      }
    });
  }

  async function initProfile() {
    const ownerId = param("ownerId");
    const error = $("#profileError");
    const header = $("#profileHeader");
    const grid = $("#profileCampaigns");

    if (!ownerId) {
      setError(error, "Profile not found.");
      return;
    }

    try {
      const user = await Api.getUser(ownerId);
      header.innerHTML = `
        <div class="profile-user">
          <div class="avatar">${escapeHtml((user.username || "U").charAt(0).toUpperCase())}</div>
          <div>
            <h1 style="margin: 0;">${escapeHtml(user.username)}</h1>
            <p class="muted" style="margin: 4px 0 0;">${escapeHtml(user.email || "")}</p>
          </div>
        </div>
        <span class="badge badge-open">${escapeHtml(user.role || "user")}</span>
      `;
      const campaigns = await Api.searchByOwner(ownerId);
      renderCampaignGrid(campaigns.campaigns || [], grid, "This owner has not created any campaigns yet.");
    } catch (requestError) {
      setError(error, requestError.message);
    }
  }

  async function initReport() {
    const payload = Auth.requireAuth();
    if (!payload) return;
    const id = param("campaignId");
    const form = $("#reportForm");
    const error = $("#reportError");
    const title = $("#reportCampaignTitle");
    const summary = $("#reportCampaignSummary");
    let campaign = null;

    try {
      const data = await Api.getCampaign(id);
      campaign = data.campaign;
      if (!userCanManage(campaign)) {
        setError(error, "Permission denied.");
        form.classList.add("hidden");
        return;
      }
      title.textContent = campaignTitle(campaign);
      summary.innerHTML = `
        <p class="muted">Available balance</p>
        <div class="stat-value">${formatCurrency(campaign.available || 0)}</div>
      `;
    } catch (requestError) {
      setError(error, requestError.message);
      form.classList.add("hidden");
      return;
    }

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setError(error, "");
      const button = form.querySelector("button[type='submit']");
      const data = new FormData(form);
      const files = Array.from(form.elements.images.files || []);
      const invalidFile = files.find(function (file) {
        return !["image/jpeg", "image/png"].includes(file.type);
      });
      if (invalidFile) {
        setError(error, "Only JPEG and PNG images are allowed.");
        return;
      }

      setBusy(button, true, "Posting...");
      try {
        const report = await Api.postReport({
          campaignId: id,
          reportTitle: data.get("reportTitle").toString().trim(),
          amount: Number(data.get("amount"))
        });
        if (files.length) {
          const imageData = new FormData();
          files.forEach(function (file) {
            imageData.append("images", file);
          });
          await Api.uploadImages(report.reportId, id, imageData);
        }
        window.location.href = `campaign.html?id=${encodeURIComponent(id)}`;
      } catch (requestError) {
        setError(error, requestError.message);
      } finally {
        setBusy(button, false);
      }
    });
  }

  async function initApp() {
    renderNav();
    const initializers = {
      home: initHome,
      login: initLogin,
      register: initRegister,
      campaign: initCampaign,
      donate: initDonate,
      createCampaign: initCreateCampaign,
      editCampaign: initEditCampaign,
      profile: initProfile,
      report: initReport
    };
    if (initializers[PAGE]) {
      await initializers[PAGE]();
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initApp().catch(function (error) {
      const globalError = document.getElementById("globalError");
      if (globalError) {
        setError(globalError, error.message || "Something went wrong. Please try again.");
      }
    });
  });
})();
