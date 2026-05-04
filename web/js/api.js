(function () {
  const BASE_URL = "http://localhost:3000";

  function errorMessage(data, fallbackStatus) {
    if (data && typeof data === "object" && data.detail) return String(data.detail);
    if (typeof data === "string" && data.trim()) return data;
    if (fallbackStatus === 401) return "Please log in to continue.";
    if (fallbackStatus === 403) return "Permission denied.";
    if (fallbackStatus === 404) return "Not found.";
    if (fallbackStatus >= 500) return "Something went wrong. Please try again.";
    return "The request could not be completed.";
  }

  async function parseResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json().catch(function () {
        return null;
      });
    }
    return response.text().catch(function () {
      return "";
    });
  }

  async function request(path, options) {
    const config = Object.assign({ method: "GET", auth: false }, options || {});
    const init = {
      method: config.method,
      headers: Object.assign({}, config.headers || {})
    };

    if (config.auth) {
      const token = Auth.getToken();
      if (!token || !Auth.hasValidToken()) {
        Auth.clearToken();
        window.location.href = "login.html";
        throw new Error("Please log in to continue.");
      }
      init.headers.Authorization = `Bearer ${token}`;
    }

    if (config.body !== undefined) {
      if (config.formData) {
        init.body = config.body;
      } else {
        init.headers["Content-Type"] = "application/json";
        init.body = JSON.stringify(config.body);
      }
    }

    const response = await fetch(`${BASE_URL}${path}`, init);
    const data = await parseResponse(response);

    if (!response.ok) {
      if (response.status === 401 && config.auth) {
        Auth.clearToken();
      }
      const error = new Error(errorMessage(data, response.status));
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  }

  function getCampaignId(campaign) {
    return campaign ? campaign._id || campaign.campaignID || campaign.id : "";
  }

  function imageUrl(name) {
    return `${BASE_URL}/image/${encodeURIComponent(name)}`;
  }

  function wsUrl(campaignId) {
    return `${BASE_URL.replace(/^http/, "ws")}/ws/campaign/${encodeURIComponent(campaignId)}`;
  }

  window.Api = {
    BASE_URL,
    request,
    getCampaignId,
    imageUrl,
    wsUrl,
    login: function (payload) {
      return request("/login", { method: "POST", body: payload });
    },
    register: function (payload) {
      return request("/register", { method: "POST", body: payload });
    },
    getUser: function (id) {
      return request(`/user/${encodeURIComponent(id)}`);
    },
    listCampaigns: function (page) {
      return request(`/campaign?page=${encodeURIComponent(page || 1)}`);
    },
    getCampaign: function (id) {
      return request(`/campaign/${encodeURIComponent(id)}`);
    },
    searchCampaigns: function (title) {
      return request(`/search?title=${encodeURIComponent(title)}`);
    },
    searchByOwner: function (ownerId) {
      return request(`/search/owner?ownerId=${encodeURIComponent(ownerId)}`);
    },
    createCampaign: function (payload) {
      return request("/campaign", { method: "POST", auth: true, body: payload });
    },
    updateCampaign: function (id, payload) {
      return request(`/campaign/${encodeURIComponent(id)}`, { method: "PUT", auth: true, body: payload });
    },
    donate: function (payload) {
      return request("/donate", { method: "POST", auth: true, body: payload });
    },
    getDonations: function (campaignId) {
      return request(`/donate/${encodeURIComponent(campaignId)}`);
    },
    postComment: function (payload) {
      return request("/comment", { method: "POST", auth: true, body: payload });
    },
    postReply: function (commentId, payload) {
      return request(`/reply/${encodeURIComponent(commentId)}`, { method: "PUT", auth: true, body: payload });
    },
    postReport: function (payload) {
      return request("/report", { method: "POST", auth: true, body: payload });
    },
    uploadImages: function (reportId, campaignId, formData) {
      return request(`/image/${encodeURIComponent(reportId)}/${encodeURIComponent(campaignId)}`, {
        method: "POST",
        auth: true,
        formData: true,
        body: formData
      });
    },
    likeCampaign: function (campaignId, userId) {
      return request(`/like/${encodeURIComponent(campaignId)}/${encodeURIComponent(userId)}`, {
        method: "PUT",
        auth: true
      });
    }
  };
})();
