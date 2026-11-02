/*
 * GATEX forms — sends the site's forms (Contact, CTA, Request Email) by email
 * without Webflow hosting. Replaces Webflow's form handler on these forms and
 * keeps Webflow's own "Thank you" / "Oops" messages.
 *
 * Backend: Web3Forms (https://web3forms.com). Submissions are emailed to the
 * address the access key was created for (sales@gatex.info). The access key is
 * meant to be public; manage it or change the recipient at web3forms.com.
 */
(function () {
  var FORM_ENDPOINT = "https://api.web3forms.com/submit";
  var ACCESS_KEY = "1f539d1e-8e0d-41d9-9614-b69f5f85b07c";

  // Readable labels for Webflow's generated field names.
  var LABELS = {
    "name-3": "Full Name",
    "name-2": "Email Address",
    "Company-Name-2": "Company Name",
    "Service-2": "Service",
    "field-2": "Message"
  };

  function isSiteForm(form) {
    return (
      form.tagName === "FORM" &&
      form.id === "email-form" &&
      form.hasAttribute("data-gatex-form")
    );
  }

  function formKind(form) {
    // The Request Email form asks for a Client ID instead of a name.
    var nameInput = form.querySelector('[name="name-3"]');
    if (nameInput && /client id/i.test(nameInput.placeholder || "")) return "request-email";
    return "contact";
  }

  function collect(form, kind) {
    var data = {
      access_key: ACCESS_KEY,
      subject: kind === "request-email"
        ? "GATEX website: Request Email (Client ID)"
        : "GATEX website: New contact request",
      from_name: "GATEX Website"
    };
    var fields = form.querySelectorAll("input, select, textarea");
    for (var i = 0; i < fields.length; i++) {
      var el = fields[i];
      if (!el.name || el.type === "submit" || el.name === "botcheck" ||
          el.name.indexOf("cf-turnstile") === 0) continue;
      var label = LABELS[el.name] || el.getAttribute("data-name") || el.name;
      if (kind === "request-email" && el.name === "name-3") label = "Client ID";
      data[label] = el.tagName === "SELECT" && el.selectedIndex > 0
        ? el.options[el.selectedIndex].text
        : el.value;
    }
    var email = form.querySelector('input[type="email"]');
    if (email) data.replyto = email.value;
    data.Page = window.location.href;
    return data;
  }

  function show(form, ok) {
    var wrapper = form.parentNode;
    var done = wrapper.querySelector(".w-form-done");
    var fail = wrapper.querySelector(".w-form-fail");
    if (ok) {
      form.style.display = "none";
      if (done) done.style.display = "block";
      if (fail) fail.style.display = "none";
    } else if (fail) {
      fail.style.display = "block";
    }
  }

  function onSubmit(event) {
    var form = event.target;
    if (!isSiteForm(form)) return;
    // Stop Webflow's handler (it posts to Webflow's servers).
    event.preventDefault();
    event.stopImmediatePropagation();

    // Honeypot: bots fill hidden fields, humans don't.
    var trap = form.querySelector('input[name="botcheck"]');
    if (trap && trap.checked) { show(form, true); return; }

    var button = form.querySelector('input[type="submit"]');
    var label = button ? button.value : "";
    if (button) {
      button.value = button.getAttribute("data-wait") || "Please wait...";
      button.disabled = true;
    }

    fetch(FORM_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(collect(form, formKind(form)))
    })
      .then(function (res) {
        return res.json().then(function (body) {
          var ok = res.ok && body.success === true;
          show(form, ok);
          if (ok) form.reset();
        });
      })
      .catch(function () { show(form, false); })
      .then(function () {
        if (button) { button.value = label; button.disabled = false; }
      });
  }

  // Capture phase runs before Webflow's (jQuery, bubbling) submit handler.
  document.addEventListener("submit", onSubmit, true);

  document.addEventListener("DOMContentLoaded", function () {
    var forms = document.querySelectorAll("form[data-gatex-form]");
    for (var i = 0; i < forms.length; i++) {
      if (forms[i].querySelector('input[name="botcheck"]')) continue;
      var trap = document.createElement("input");
      trap.type = "checkbox";
      trap.name = "botcheck";
      trap.tabIndex = -1;
      trap.setAttribute("aria-hidden", "true");
      trap.style.cssText = "position:absolute;left:-9999px;width:1px;height:1px;opacity:0";
      forms[i].appendChild(trap);
    }
  });
})();
