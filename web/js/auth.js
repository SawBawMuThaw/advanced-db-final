(function () {
  const TOKEN_KEY = "token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function decodeBase64Url(value) {
    const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - normalized.length % 4) % 4), "=");
    return atob(padded);
  }

  function getPayload() {
    const token = getToken();
    if (!token) return null;
    try {
      return JSON.parse(decodeBase64Url(token.split(".")[1]));
    } catch (error) {
      clearToken();
      return null;
    }
  }

  function isExpired(payload) {
    if (!payload || !payload.exp) return false;
    return payload.exp * 1000 <= Date.now();
  }

  function hasValidToken() {
    const payload = getPayload();
    if (!payload) return false;
    if (isExpired(payload)) {
      clearToken();
      return false;
    }
    return true;
  }

  function requireAuth() {
    const payload = getPayload();
    if (!payload || isExpired(payload)) {
      clearToken();
      window.location.href = "login.html";
      return null;
    }
    return payload;
  }

  function authedHeaders(includeContentType) {
    const headers = {
      Authorization: `Bearer ${getToken()}`
    };
    if (includeContentType !== false) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  function logout() {
    clearToken();
    window.location.href = "login.html";
  }

  function currentUserId() {
    const payload = getPayload();
    return payload && payload.sub ? Number(payload.sub) : null;
  }

  window.Auth = {
    getToken,
    setToken,
    clearToken,
    getPayload,
    hasValidToken,
    requireAuth,
    authedHeaders,
    logout,
    currentUserId
  };
})();
