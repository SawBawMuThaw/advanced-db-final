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

  function formatLongDate(value) {
    if (!value) return "Unknown date";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Unknown date";
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric"
    });
  }

  function backLinkRow(href, label) {
    const safeHref = String(href == null ? "" : href).replace(/"/g, "&quot;");
    return `
      <div class="page-back-row">
        <a class="back-link" href="${safeHref}">
          <span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>
          ${escapeHtml(label)}
        </a>
      </div>
    `;
  }

  function insertBackRow(mainSelector, href, label) {
    const main = document.querySelector(mainSelector);
    if (!main || main.querySelector(".page-back-row")) return;
    main.insertAdjacentHTML("afterbegin", backLinkRow(href, label));
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

  // Image modal: open updates images in a larger overlay when clicked
  function initImageModal() {
    if (document.getElementById("imageModalOverlay")) return;
    const overlay = document.createElement("div");
    overlay.id = "imageModalOverlay";
    overlay.className = "image-modal-overlay hidden";
    overlay.innerHTML = `
      <div class="image-modal-content">
        <button class="image-modal-close" aria-label="Close image">×</button>
        <img class="image-modal-img" src="" alt="" />
      </div>
    `;
    document.body.appendChild(overlay);

    overlay.addEventListener("click", function (event) {
      if (event.target === overlay || event.target.classList.contains("image-modal-close")) {
        overlay.classList.add("hidden");
        overlay.querySelector(".image-modal-img").src = "";
      }
    });

    // delegate clicks on report images
    document.body.addEventListener("click", function (event) {
      const img = event.target.closest && event.target.closest(".report-images img");
      if (!img) return;
      const large = overlay.querySelector(".image-modal-img");
      large.src = img.src.replace(/(=s\d+(-c)?$)/, "") || img.src; // try stripping size param if present
      large.alt = img.alt || "Update image";
      overlay.classList.remove("hidden");
    });
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

  function campaignText(campaign) {
    const info = getInfo(campaign);
    return `${info.title || ""} ${info.description || ""}`.toLowerCase();
  }

  function campaignCategory(campaign) {
    const text = campaignText(campaign);
    if (/(medical|surgery|clinic|health|hospital|patient|doctor)/.test(text)) return "Medical";
    if (/(school|education|library|student|class|teacher)/.test(text)) return "Education";
    if (/(tree|forest|amazon|environment|climate|water|river)/.test(text)) return "Environment";
    if (/(animal|dog|cat|shelter|wildlife)/.test(text)) return "Animals";
    if (/(crisis|relief|emergency|disaster|flood|fire)/.test(text)) return "Crisis Relief";
    return "Community";
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
    const images = {
      Medical: "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=900&q=80",
      Education: "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=900&q=80",
      Environment: "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=900&q=80",
      Animals: "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=900&q=80",
      "Crisis Relief": "https://images.unsplash.com/photo-1469571486292-0ba58a3f068b?auto=format&fit=crop&w=900&q=80",
      Community: "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=900&q=80"
    };
    const category = campaignCategory(campaign);
    return `<img alt="" src="${images[category] || images.Community}" loading="lazy">`;
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
    const open = campaign.isOpen !== false;
    const category = campaignCategory(campaign);
    const pct = progressPercent(campaign.current, campaign.goal);
    const urgent = open && pct >= 75;
    return `
      <article class="campaign-card">
        <a class="campaign-thumb" href="campaign.html?id=${encodeURIComponent(id)}" aria-label="Open ${escapeHtml(campaignTitle(campaign))}">
          ${campaignThumb(campaign)}
          ${urgent ? `<span class="urgency-badge"><span class="material-symbols-outlined" aria-hidden="true">local_fire_department</span>Urgent</span>` : ""}
        </a>
        <div class="campaign-body">
          <div>
            <span class="campaign-category">${escapeHtml(category)}</span>
            <h3>${escapeHtml(campaignTitle(campaign))}</h3>
          </div>
          ${progressMarkup(campaign.current, campaign.goal, false)}
          <p class="campaign-goal">of ${formatCurrency(campaign.goal)} goal</p>
          ${!open ? `<span class="badge badge-closed">Closed</span>` : ""}
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

  async function loadNavUsername(payload) {
    const link = document.getElementById("navProfileLink");
    if (!link || !payload || !payload.sub) return;
    try {
      const user = await Api.getUser(payload.sub);
      link.textContent = user.username || `User ${payload.sub}`;
      link.href = `profile.html?ownerId=${encodeURIComponent(payload.sub)}`;
    } catch (error) {
      link.textContent = `Profile`;
    }
  }

  function renderNav() {
    const mount = document.getElementById("site-nav");
    if (!mount) return;
    const payload = Auth.getPayload();
    const loggedIn = isLoggedIn();
    const username = loggedIn ? "Profile" : "";
    const currentSearch = param("q") || param("title") || "";

    mount.innerHTML = `
      <nav class="top-nav" aria-label="Main navigation">
        <div class="container top-nav-inner">
          <a class="brand" href="index.html" aria-label="No Refunds home">
            <span>No Refunds</span>
          </a>
          <div class="nav-links" aria-label="Sections">
            <a href="index.html#campaigns">Explore</a>
            <a href="index.html#how-it-works">How it Works</a>
            <a href="index.html#about">About Us</a>
          </div>
          <form class="nav-search" id="navSearch">
            <span class="material-symbols-outlined" aria-hidden="true">search</span>
            <input name="q" value="${escapeHtml(currentSearch)}" placeholder="Search campaigns" autocomplete="off">
          </form>
          <div class="nav-actions">
            ${loggedIn ? `<a class="nav-user" id="navProfileLink" href="profile.html?ownerId=${encodeURIComponent(payload.sub)}">${username}</a>` : `<a class="nav-signin" href="login.html">Sign In</a>`}
            <a class="button button-primary nav-start" href="${loggedIn ? "create-campaign.html" : "login.html"}">Start a Campaign</a>
            ${loggedIn ? `<button class="button button-ghost" id="logoutButton" type="button">Logout</button>` : ""}
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
    if (loggedIn) loadNavUsername(payload);
  }

  async function initHome() {
    const grid = $("#campaignGrid");
    const error = $("#homeError");
    const pageLabel = $("#pageLabel");
    const prevButton = $("#prevPage");
    const nextButton = $("#nextPage");
    const homeSearch = $("#homeSearch");
    const categoryPills = $("#categoryPills");
    let page = Math.max(1, Number(param("page") || 1));
    const searchTerm = (param("q") || param("title") || "").trim();
    const categoryTerm = (param("category") || "").trim();

    if (homeSearch && searchTerm) {
      homeSearch.elements.q.value = searchTerm;
    }
    if (categoryPills) {
      $all(".category-pill", categoryPills).forEach(function (button) {
        button.classList.toggle("active", button.dataset.category === categoryTerm);
      });
    }

    async function loadCategoryPool() {
      const pages = [1, 2, 3, 4, 5];
      const results = [];
      for (const pageNumber of pages) {
        const data = await Api.listCampaigns(pageNumber);
        const campaigns = data.campaigns || [];
        results.push(...campaigns);
        if (campaigns.length < 6) break;
      }
      return { campaigns: results };
    }

    async function load() {
      setError(error, "");
      grid.innerHTML = `<span class="loader">Loading campaigns</span>`;
      try {
        const data = searchTerm ? await Api.searchCampaigns(searchTerm) : categoryTerm ? await loadCategoryPool() : await Api.listCampaigns(page);
        let campaigns = data.campaigns || [];
        if (categoryTerm) {
          campaigns = campaigns.filter(function (campaign) {
            return campaignCategory(campaign) === categoryTerm;
          });
        }
        const filtered = searchTerm || categoryTerm;
        renderCampaignGrid(campaigns, grid, filtered ? "No campaigns match that search." : "No campaigns are available yet.");
        pageLabel.textContent = filtered ? "Search results" : `Page ${page}`;
        prevButton.disabled = Boolean(filtered) || page <= 1;
        nextButton.disabled = Boolean(filtered) || campaigns.length < 6;
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

    if (categoryPills) {
      $all(".category-pill", categoryPills).forEach(function (button) {
        button.addEventListener("click", function () {
          const category = button.dataset.category;
          window.location.href = category ? `index.html?category=${encodeURIComponent(category)}#campaigns` : "index.html#campaigns";
        });
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

  function donorSignature(donor) {
    const username = donor.username || "Anonymous";
    const amount = Number(donor.amount || 0);
    const parsedTime = new Date(donor.time);
    const time = Number.isNaN(parsedTime.getTime()) ? String(donor.time || "") : String(parsedTime.getTime());
    return `${username}|${amount.toFixed(2)}|${time}`;
  }

  function uniqueDonors(donors) {
    const seen = new Set();
    return (donors || []).filter(function (donor) {
      const signature = donorSignature(donor);
      if (seen.has(signature)) return false;
      seen.add(signature);
      return true;
    });
  }

  function donorTotals(donors) {
    const totals = new Map();
    uniqueDonors(donors).forEach(function (donor) {
      const username = donor.username || "Anonymous";
      const current = totals.get(username) || { username, amount: 0, lastTime: "", gifts: 0 };
      current.amount += Number(donor.amount || 0);
      current.gifts += 1;
      if (!current.lastTime || new Date(donor.time) > new Date(current.lastTime)) {
        current.lastTime = donor.time;
      }
      totals.set(username, current);
    });
    return Array.from(totals.values()).sort(function (a, b) {
      return b.amount - a.amount;
    });
  }

  function renderDonationActivity(entries) {
    const list = (entries || []).slice(-4).reverse();
    if (!list.length) return "";
    return `
      <div class="donation-activity">
        <div class="mini-title">Recent Donations</div>
        ${list.map(function (entry) {
          return `
            <div class="activity-row">
              <span>${escapeHtml(entry.username || "Anonymous")}</span>
              <strong>${formatCurrency(entry.amount)}</strong>
              <small>${formatCurrency(entry.runningTotal)} total</small>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  function renderDonors(donors, entries) {
    const unique = uniqueDonors(donors);
    const list = donorTotals(unique);
    if (!list.length) return `<div class="empty-state">No donations yet.</div>`;
    const totalAmount = unique.reduce(function (sum, donor) {
      return sum + Number(donor.amount || 0);
    }, 0);
    const topDonors = list.map(function (donor, index) {
      return `
        <div class="donor-row">
          <span class="donor-rank">${index + 1}</span>
          <span class="donor-name">
            ${escapeHtml(donor.username)}
            <small>${donor.gifts} ${donor.gifts === 1 ? "gift" : "gifts"}</small>
          </span>
          <strong>${formatCurrency(donor.amount)}</strong>
        </div>
      `;
    }).join("");
    return `
      <div class="donor-summary">
        <div>
          <strong>${unique.length}</strong>
          <span>donations</span>
        </div>
        <div>
          <strong>${formatCurrency(totalAmount)}</strong>
          <span>tracked here</span>
        </div>
      </div>
      ${topDonors}
      ${renderDonationActivity(entries)}
    `;
  }

  function renderReplies(replies, parentId, loggedIn) {
    if (!replies || !replies.length) return "";
    return replies.map(function (reply) {
      const replyId = reply._id || reply.replyId;
      const nestedReplies = reply.replies || [];
      return `
        <div class="reply">
          <div class="comment-head">
            <span class="comment-author">${escapeHtml(reply.user && reply.user.username ? reply.user.username : "User")}</span>
            ${loggedIn ? `<button class="button button-ghost reply-toggle" type="button" data-comment-id="${escapeHtml(replyId)}">Reply</button>` : ""}
          </div>
          <p class="comment-body">${escapeHtml(reply.text)}</p>
          ${loggedIn ? `
            <form class="inline-form hidden reply-form" data-comment-id="${escapeHtml(replyId)}">
              <div class="field">
                <label>Reply</label>
                <textarea name="text" required></textarea>
              </div>
              <button class="button button-primary" type="submit">Post Reply</button>
            </form>
          ` : ""}
          ${renderReplies(nestedReplies, replyId, loggedIn)}
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
          ${renderReplies(comment.replies, commentId, loggedIn)}
        </article>
      `;
    }).join("") : `<div class="empty-state">No comments yet.</div>`;

    return `${rendered}${commentForm}`;
  }

  function renderReports(campaign) {
    const reports = campaign.reports || [];
    if (!reports.length) return `<div class="empty-state">No updates have been posted yet.</div>`;
    return reports.map(function (report) {
      const images = report.attachedImages || report.attached_images || [];
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

  function renderClosedPending(campaign, compact) {
    const reports = campaign.reports || [];
    const id = Api.getCampaignId(campaign);
    const title = campaignTitle(campaign);
    const raised = Number(campaign.current || 0);
    return `
      <section class="pending-update ${compact ? "pending-update-compact" : ""}">
        <div class="pending-visual">
          <img alt="" src="https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=900&q=80" loading="lazy">
        </div>
        <div class="pending-copy">
          <span class="badge badge-open">Goal Reached</span>
          <h2>Thanks for your donation.</h2>
          <p>We are currently in progress with the project implementation. The campaign is closed to new donations while the team prepares transparent spending updates.</p>
          <div class="pending-note">
            <span class="material-symbols-outlined" aria-hidden="true">info</span>
            <div>
              <strong>What happens next?</strong>
              <p>Campaign managers will post photo evidence, withdrawal reports, and financial receipts. Expect the first field update once spending details are ready.</p>
            </div>
          </div>
          <div class="pending-actions">
            <a class="button button-primary" href="campaign.html?id=${encodeURIComponent(id)}#updates">View Updates</a>
            ${reports.length ? `<span class="success">${reports.length} update${reports.length === 1 ? "" : "s"} posted</span>` : `<span class="notice">Updates pending</span>`}
          </div>
        </div>
        <aside class="project-snapshot">
          <h3>Project Snapshot</h3>
          <div><span>Total Raised</span><strong>${formatCurrency(raised)}</strong></div>
          <div><span>Status</span><strong>Implementation</strong></div>
          <div><span>Owner</span><strong>${escapeHtml(campaignOwner(campaign).username || "Campaign owner")}</strong></div>
          <div><span>Project</span><strong>${escapeHtml(title)}</strong></div>
        </aside>
      </section>
    `;
  }

  function renderDonationResult(status, campaignId, donationId) {
    const success = status === "success";
    return `
      <section class="payment-result ${success ? "payment-result-success" : "payment-result-failed"}">
        <div class="result-icon">
          <span class="material-symbols-outlined" aria-hidden="true">${success ? "check" : "priority_high"}</span>
        </div>
        <h2>${success ? "Donation Successful" : "Payment Failed"}</h2>
        <p>${success ? "Your contribution is final and making an immediate impact. Thank you for your radical transparency." : "We couldn't process your transaction securely. Please check your details or try a different payment method."}</p>
        ${success ? `
          <a class="button button-primary button-wide" href="${donationId ? `receipt.html?donationId=${encodeURIComponent(donationId)}&campaignId=${encodeURIComponent(campaignId)}` : `campaign.html?id=${encodeURIComponent(campaignId)}`}">
            <span class="material-symbols-outlined" aria-hidden="true">${donationId ? "download" : "arrow_back"}</span>
            ${donationId ? "Download Receipt" : "Return to Campaign"}
          </a>
          ${donationId ? `<a class="result-link" href="campaign.html?id=${encodeURIComponent(campaignId)}">Return to Campaign</a>` : ""}
        ` : `
          <a class="button button-danger button-wide" href="donate.html?id=${encodeURIComponent(campaignId)}">
            <span class="material-symbols-outlined" aria-hidden="true">refresh</span>
            Try Again
          </a>
          <a class="result-link danger-text" href="mailto:support@norefunds.local">Contact Support</a>
        `}
      </section>
    `;
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
      ${backLinkRow("index.html", "Back to campaigns")}
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
          ${!open ? renderClosedPending(campaign, false) : ""}
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
              ${!open ? `<span class="badge badge-closed">Donations Closed</span><a class="button button-secondary button-wide" href="#tab-updates">Campaign Updates</a>` : ""}
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
        const [donationResult, runningResult] = await Promise.allSettled([
          Api.getDonations(id),
          Api.getDonationRunningTotal(id)
        ]);
        if (donationResult.status === "rejected") throw donationResult.reason;
        const donors = donationResult.value.donors || [];
        const entries = runningResult.status === "fulfilled" ? runningResult.value.entries || [] : [];
        donorList.innerHTML = renderDonors(donors, entries);
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
    const status = param("status");
    const donationId = param("donationId");
    const form = $("#donateForm");
    const error = $("#donateError");
    const receiptNotice = $("#receiptNotice");
    const amountInput = $("#donationAmount");
    const total = $("#donationTotal");
    const campaignTitleEl = $("#donationCampaignTitle");
    const summary = $("#donationSummary");
    const resultPanel = $("#donationResult");
    const checkoutLayout = $("#checkoutLayout");
    let campaign = null;

    function updateTotal() {
      const amount = Number(amountInput.value || 0);
      total.textContent = formatCurrency(amount);
      show(receiptNotice, amount > 50);
    }

    try {
      const data = await Api.getCampaign(id);
      campaign = data.campaign;
      insertBackRow("main.container.section", `campaign.html?id=${encodeURIComponent(id)}`, "Back to campaign");
      campaignTitleEl.textContent = campaignTitle(campaign);
      summary.innerHTML = progressMarkup(campaign.current, campaign.goal, false);
      if (status === "success") {
        checkoutLayout.classList.add("hidden");
        resultPanel.innerHTML = renderDonationResult("success", id, donationId);
        show(resultPanel, true);
        return;
      }
      if (campaign.isOpen === false) {
        checkoutLayout.innerHTML = renderClosedPending(campaign, true);
        return;
      }
    } catch (requestError) {
      setError(error, requestError.message);
      form.querySelector("button[type='submit']").disabled = true;
    }

    amountInput.addEventListener("input", updateTotal);
    $all(".amount-chip").forEach(function (button) {
      button.addEventListener("click", function () {
        amountInput.value = button.dataset.amount;
        updateTotal();
        amountInput.focus();
      });
    });
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
        const result = await Api.donate({
          campaignID: id,
          amount,
          time: new Date().toISOString()
        });
        if (result.receiptGenerated) {
          window.location.href = `receipt.html?donationId=${encodeURIComponent(result.donationId)}&campaignId=${encodeURIComponent(id)}`;
        } else {
          window.location.href = `donate.html?id=${encodeURIComponent(id)}&status=success`;
        }
      } catch (requestError) {
        setError(error, requestError.message);
        checkoutLayout.classList.add("hidden");
        resultPanel.innerHTML = renderDonationResult("failed", id);
        show(resultPanel, true);
      } finally {
        setBusy(button, false);
      }
    });
  }

  function receiptMarkup(receipt, campaign) {
    const donor = receipt.donor || {};
    const campaignName = campaign ? campaignTitle(campaign) : "Campaign contribution";
    const receiptNumber = `NR-${String(receipt.receiptId || receipt.donationId).padStart(6, "0")}`;
    const backHref = campaign && Api.getCampaignId(campaign)
      ? `campaign.html?id=${encodeURIComponent(Api.getCampaignId(campaign))}`
      : "index.html";
    const backLabel = campaign ? "Back to campaign" : "Back to home";
    return `
      ${backLinkRow(backHref, backLabel)}
      <article class="tax-receipt" id="printableReceipt">
        <header class="receipt-header">
          <div>
            <strong class="receipt-brand">No Refunds</strong>
            <h1>Official Tax Receipt</h1>
          </div>
          <dl>
            <div><dt>Receipt ID:</dt><dd>${escapeHtml(receiptNumber)}</dd></div>
            <div><dt>Date Issued:</dt><dd>${escapeHtml(formatLongDate(receipt.time || new Date().toISOString()))}</dd></div>
          </dl>
        </header>
        <p class="receipt-intro">Thank you for your contribution. Your commitment to radical transparency ensures this donation creates immediate, verifiable impact.</p>
        <section class="receipt-party-grid">
          <div>
            <span>Received From</span>
            <strong>${escapeHtml(donor.username || "Donor")}</strong>
            <p>${escapeHtml(donor.email || "")}</p>
          </div>
          <div>
            <span>Organization</span>
            <strong>No Refunds Inc.</strong>
            <p>500 Transparency Blvd, Suite 100<br>New York, NY 10001</p>
            <p class="receipt-ein">Tax-Exempt EIN: 12-3456789</p>
          </div>
        </section>
        <section class="receipt-table">
          <div class="receipt-table-head">
            <span>Contribution Details</span>
            <span>Amount</span>
          </div>
          <div class="receipt-line">
            <div>
              <strong>${escapeHtml(campaignName)}</strong>
              <p>Direct Allocation Fund</p>
            </div>
            <strong>${formatCurrency(receipt.amount)}</strong>
          </div>
          <div class="receipt-total">
            <strong>Total Eligible Donation</strong>
            <strong>${formatCurrency(receipt.amount)}</strong>
          </div>
        </section>
        <p class="receipt-fineprint">No goods or services were provided by No Refunds Inc. in return for this contribution. Please retain this receipt for your tax records.</p>
      </article>
      <div class="receipt-actions">
        <button class="button button-secondary" id="printReceiptButton" type="button">
          <span class="material-symbols-outlined" aria-hidden="true">print</span>
          Print Receipt
        </button>
        <button class="button button-primary" id="downloadReceiptButton" type="button">
          <span class="material-symbols-outlined" aria-hidden="true">download</span>
          Download PDF
        </button>
      </div>
    `;
  }

  async function initReceipt() {
    const donationId = param("donationId");
    const campaignId = param("campaignId");
    const content = $("#receiptContent");
    const error = $("#receiptError");
    if (!donationId) {
      setError(error, "Receipt not found.");
      content.innerHTML = "";
      return;
    }
    try {
      const [receipt, campaignResult] = await Promise.all([
        Api.getDonationReceipt(donationId),
        campaignId ? Api.getCampaign(campaignId).catch(function () { return null; }) : Promise.resolve(null)
      ]);
      content.innerHTML = receiptMarkup(receipt, campaignResult && campaignResult.campaign);
      ["printReceiptButton", "downloadReceiptButton"].forEach(function (id) {
        const button = document.getElementById(id);
        if (button) button.addEventListener("click", function () { window.print(); });
      });
    } catch (requestError) {
      content.innerHTML = `
        <section class="payment-result payment-result-success">
          <div class="result-icon"><span class="material-symbols-outlined" aria-hidden="true">check</span></div>
          <h2>Donation Recorded</h2>
          <p>${escapeHtml(requestError.status === 404 ? "This donation does not have a tax receipt. Receipts are generated automatically for eligible large donations." : requestError.message)}</p>
          <a class="button button-primary button-wide" href="${campaignId ? `campaign.html?id=${encodeURIComponent(campaignId)}` : "index.html"}">Return</a>
        </section>
      `;
      setError(error, requestError.status === 404 ? "This donation does not have a tax receipt. Receipts are generated automatically for eligible large donations." : requestError.message);
    }
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
      insertBackRow("main.container.section", `campaign.html?id=${encodeURIComponent(id)}`, "Back to campaign");
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
    const ownerId = param("ownerId") || Auth.currentUserId();
    const error = $("#profileError");
    const header = $("#profileHeader");
    const grid = $("#profileCampaigns");

    if (!ownerId) {
      setError(error, "Log in to view your profile.");
      return;
    }

    try {
      const user = await Api.getUser(ownerId);
      const campaigns = await Api.searchByOwner(ownerId);
      const ownedCampaigns = campaigns.campaigns || [];
      const totalRaised = ownedCampaigns.reduce(function (sum, campaign) {
        return sum + Number(campaign.current || 0);
      }, 0);
      const completed = ownedCampaigns.filter(function (campaign) {
        return campaign.isOpen === false || Number(campaign.current || 0) >= Number(campaign.goal || 1);
      }).length;
      const successRate = ownedCampaigns.length ? Math.round((completed / ownedCampaigns.length) * 100) : 0;
      header.innerHTML = `
        <div class="creator-hero">
          <div class="profile-user">
            <div class="avatar avatar-large">${escapeHtml((user.username || "U").charAt(0).toUpperCase())}</div>
            <div>
              <h1>${escapeHtml(user.username)}</h1>
              <p>${escapeHtml(user.email || "Creator profile")}</p>
              <div class="creator-meta">
                <span><span class="material-symbols-outlined" aria-hidden="true">verified</span>${escapeHtml(user.role || "user")}</span>
                <span><span class="material-symbols-outlined" aria-hidden="true">calendar_month</span>${ownedCampaigns.length} campaigns</span>
              </div>
            </div>
          </div>
          <span class="badge badge-open">Creator Hub</span>
        </div>
        <aside class="impact-panel">
          <h2>Impact</h2>
          <p>Total Raised</p>
          <strong>${formatCurrency(totalRaised)}</strong>
          <div>
            <span>Campaigns <b>${ownedCampaigns.length}</b></span>
            <span>Success Rate <b>${successRate}%</b></span>
          </div>
        </aside>
      `;
      if (ownedCampaigns.length) {
        grid.innerHTML = ownedCampaigns.map(campaignCard).join("") + `
          <article class="create-tile">
            <span class="material-symbols-outlined" aria-hidden="true">add</span>
            <h3>Start Something New</h3>
            <p>Launch your next campaign with radical transparency.</p>
            <a class="button button-primary" href="create-campaign.html">Create Campaign</a>
          </article>
        `;
      } else {
        grid.innerHTML = `
          <article class="create-tile create-tile-wide">
            <span class="material-symbols-outlined" aria-hidden="true">add</span>
            <h3>Start Something New</h3>
            <p>This creator has not launched a campaign yet.</p>
            <a class="button button-primary" href="create-campaign.html">Create Campaign</a>
          </article>
        `;
      }
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
      insertBackRow("main.container.section", `campaign.html?id=${encodeURIComponent(id)}`, "Back to campaign");
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
    initImageModal();
    renderNav();
    const initializers = {
      home: initHome,
      login: initLogin,
      register: initRegister,
      campaign: initCampaign,
      donate: initDonate,
      receipt: initReceipt,
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
