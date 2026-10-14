(function () {
  "use strict";
  if (window.__collegeDecodedAdvisorLoaded) return;
  window.__collegeDecodedAdvisorLoaded = true;

  var root = document.createElement("div");
  root.id = "cd-advisor-root";
  root.innerHTML = [
    '<button id="cd-advisor-launcher" type="button" aria-haspopup="dialog" aria-expanded="false"><span class="cd-advisor-orb" aria-hidden="true">✦</span><span>Talk to a College Advisor</span></button>',
    '<section id="cd-advisor-panel" role="dialog" aria-label="CollegeDecoded AI admission advisor" aria-modal="false">',
      '<header id="cd-advisor-header"><div id="cd-advisor-avatar" aria-hidden="true">✦</div><div id="cd-advisor-heading"><strong>Your College Advisor</strong><span>CollegeDecoded · MBA admission guidance</span></div><button class="cd-advisor-header-btn" id="cd-advisor-minimize" type="button" aria-label="Minimize advisor">—</button><button class="cd-advisor-header-btn" id="cd-advisor-close" type="button" aria-label="Close advisor">×</button></header>',
      '<div id="cd-advisor-messages" aria-live="polite" aria-relevant="additions"></div>',
      '<div id="cd-advisor-quick"><button class="cd-advisor-chip" type="button" data-prompt="Find MBA colleges.">Find colleges</button><button class="cd-advisor-chip" type="button" data-prompt="Compare MBA colleges.">Compare colleges</button><button class="cd-advisor-chip" type="button" data-prompt="Help me choose.">Choose college</button></div>',
      '<div id="cd-advisor-composer"><form id="cd-advisor-form"><textarea id="cd-advisor-input" rows="1" maxlength="3000" aria-label="Ask your college advisor" placeholder="Ask about MBA colleges…"></textarea><button id="cd-advisor-send" type="submit" aria-label="Send message">↑</button></form><div id="cd-advisor-footnote">AI advisor · Check important admission details against official sources.</div></div>',
      '<div id="cd-advisor-actions"><button class="cd-advisor-action" id="cd-advisor-followup" type="button">Request email / WhatsApp follow-up</button><button class="cd-advisor-action" id="cd-advisor-reset" type="button">New conversation</button></div>',
      '<div id="cd-advisor-lead" aria-label="Request follow-up"><h3>Keep your MBA plan handy</h3><p>Choose how you would like CollegeDecoded to contact you about your request. Contact details are optional for using the advisor.</p><form id="cd-advisor-lead-form"><label for="cd-advisor-channel">Preferred contact method</label><select id="cd-advisor-channel"><option value="email">Email</option><option value="whatsapp">WhatsApp</option></select><label id="cd-advisor-contact-label" for="cd-advisor-contact">Email address</label><input id="cd-advisor-contact" type="email" autocomplete="email" maxlength="254" placeholder="you@example.com" required><label for="cd-advisor-service">What would help?</label><select id="cd-advisor-service"><option value="advisor_follow_up">Follow-up about my MBA options</option><option value="shortlist_follow_up">Follow-up about my college shortlist</option><option value="admission_updates">Admission-related updates</option></select><label class="cd-consent"><input id="cd-advisor-marketing" type="checkbox"><span>I would also like to receive relevant CollegeDecoded updates. Optional; I can withdraw this permission later.</span></label><div class="cd-lead-buttons"><button id="cd-advisor-lead-cancel" type="button">Back to chat</button><button class="cd-lead-submit" id="cd-advisor-lead-submit" type="submit">Submit request</button></div><div id="cd-advisor-lead-status" role="status"></div></form></div>',
    '</section>'
  ].join("");
  document.body.appendChild(root);

  var launcher = document.getElementById("cd-advisor-launcher");
  var panel = document.getElementById("cd-advisor-panel");
  var messagesEl = document.getElementById("cd-advisor-messages");
  var input = document.getElementById("cd-advisor-input");
  var sendBtn = document.getElementById("cd-advisor-send");
  var quick = document.getElementById("cd-advisor-quick");
  var leadPanel = document.getElementById("cd-advisor-lead");
  var leadForm = document.getElementById("cd-advisor-lead-form");
  var leadChannel = document.getElementById("cd-advisor-channel");
  var leadContact = document.getElementById("cd-advisor-contact");
  var leadContactLabel = document.getElementById("cd-advisor-contact-label");
  var leadStatus = document.getElementById("cd-advisor-lead-status");
  var history = [];
  var busy = false;
  var welcomed = false;

  function pageContext() {
    var main = document.querySelector("main") || document.querySelector("article") || document.querySelector("[role=main]");
    var text = main ? (main.innerText || main.textContent || "") : (document.body.innerText || "");
    return {
      pageTitle: document.title || "",
      pagePath: window.location.pathname || "/",
      pageContext: text.replace(/\s+/g, " ").trim().slice(0, 5000)
    };
  }

  function showPanel() {
    panel.classList.add("cd-open");
    launcher.style.display = "none";
    launcher.setAttribute("aria-expanded", "true");
    input.focus();
    if (!welcomed) {
      welcomed = true;
      var path = window.location.pathname || "/";
      var title = document.title || "";
      var pageSpecific = /iim-|mba|placement|fees|cutoff|admission|college/i.test(path + " " + title);
      addMessage("assistant", pageSpecific
        ? "Hi! I'm your CollegeDecoded AI advisor. I can help you make sense of MBA admissions, fees, cutoffs and placements—not just list colleges. What are you trying to decide right now?"
        : "Hi! Let's figure out your MBA options together. Tell me where you are in your admission journey, or ask me anything about colleges, fees, cutoffs and placements.");
      quick.style.display = "flex";
    }
  }
  function hidePanel() {
    panel.classList.remove("cd-open");
    launcher.style.display = "flex";
    launcher.setAttribute("aria-expanded", "false");
    leadPanel.classList.remove("cd-show");
  }
  function addMessage(role, text, sources) {
    var bubble = document.createElement("div");
    bubble.className = "cd-advisor-message " + role;
    bubble.textContent = text;
    if (Array.isArray(sources) && sources.length) {
      var sourceWrap = document.createElement("div");
      sourceWrap.className = "cd-advisor-sources";
      var label = document.createElement("strong");
      label.textContent = "Sources to check";
      sourceWrap.appendChild(label);
      sources.forEach(function (source) {
        try {
          var url = new URL(source.url);
          if (url.protocol !== "https:") return;
          var a = document.createElement("a");
          a.href = url.href;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.textContent = (source.title || url.hostname).slice(0, 180);
          sourceWrap.appendChild(a);
        } catch (_) {}
      });
      bubble.appendChild(sourceWrap);
    }
    messagesEl.appendChild(bubble);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
  }
  function setBusy(value) {
    busy = value;
    sendBtn.disabled = value;
    input.disabled = value;
    sendBtn.textContent = value ? "…" : "↑";
  }
  async function sendMessage(text) {
    text = (text || "").trim();
    if (!text || busy) return;
    quick.style.display = "none";
    addMessage("user", text);
    history.push({ role: "user", content: text });
    input.value = "";
    setBusy(true);
    var waiting = addMessage("assistant", "Let me think this through…");
    try {
      var context = pageContext();
      var response = await fetch("/api/advisor/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          messages: history.slice(-12, -1),
          pageTitle: context.pageTitle,
          pagePath: context.pagePath,
          pageContext: context.pageContext
        })
      });
      var data = await response.json().catch(function () { return {}; });
      waiting.remove();
      if (!response.ok || !data.reply) {
        addMessage("assistant", data.error || "I couldn't complete that answer just now. Please try again.");
        history.pop();
      } else {
        addMessage("assistant", data.reply, data.sources || []);
        history.push({ role: "assistant", content: data.reply });
      }
    } catch (_) {
      waiting.remove();
      addMessage("assistant", "I'm having trouble connecting right now. Please try again in a moment.");
      history.pop();
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  launcher.addEventListener("click", showPanel);
  document.getElementById("cd-advisor-close").addEventListener("click", hidePanel);
  document.getElementById("cd-advisor-minimize").addEventListener("click", hidePanel);
  document.getElementById("cd-advisor-form").addEventListener("submit", function (event) {
    event.preventDefault();
    sendMessage(input.value);
  });
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(input.value);
    }
  });
  quick.querySelectorAll("[data-prompt]").forEach(function (button) {
    button.addEventListener("click", function () { sendMessage(button.getAttribute("data-prompt")); });
  });
  document.getElementById("cd-advisor-reset").addEventListener("click", function () {
    history = [];
    messagesEl.innerHTML = "";
    welcomed = false;
    quick.style.display = "flex";
    leadPanel.classList.remove("cd-show");
    showPanel();
  });
  document.getElementById("cd-advisor-followup").addEventListener("click", function () {
    leadPanel.classList.add("cd-show");
    leadStatus.textContent = "";
    leadForm.reset();
    updateContactField();
  });
  document.getElementById("cd-advisor-lead-cancel").addEventListener("click", function () {
    leadPanel.classList.remove("cd-show");
  });
  function updateContactField() {
    var channel = leadChannel.value;
    leadContactLabel.textContent = channel === "email" ? "Email address" : "WhatsApp number";
    leadContact.type = channel === "email" ? "email" : "tel";
    leadContact.autocomplete = channel === "email" ? "email" : "tel";
    leadContact.placeholder = channel === "email" ? "you@example.com" : "+91 98765 43210";
    leadContact.required = true;
    leadContact.value = "";
  }
  leadChannel.addEventListener("change", updateContactField);
  leadForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    var channel = leadChannel.value;
    var contact = leadContact.value.trim();
    var button = document.getElementById("cd-advisor-lead-submit");
    button.disabled = true;
    leadStatus.textContent = "Submitting your request…";
    var recentSummary = history.slice(-8).map(function (item) {
      return (item.role === "user" ? "Student: " : "Advisor: ") + item.content;
    }).join("\n").slice(0, 1500);
    try {
      var payload = {
        channel: channel,
        email: channel === "email" ? contact : "",
        whatsapp: channel === "whatsapp" ? contact : "",
        service: document.getElementById("cd-advisor-service").value,
        marketingConsent: document.getElementById("cd-advisor-marketing").checked,
        pagePath: window.location.pathname || "/",
        summary: recentSummary
      };
      var response = await fetch("/api/advisor/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      var data = await response.json().catch(function () { return {}; });
      if (!response.ok) throw new Error(data.error || "Your request couldn't be saved.");
      leadStatus.textContent = data.message || "Your request has been recorded.";
      leadForm.reset();
    } catch (error) {
      leadStatus.textContent = error.message || "Your request couldn't be saved. Please try again later.";
    } finally {
      button.disabled = false;
    }
  });
})();