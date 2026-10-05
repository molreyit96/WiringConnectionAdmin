(function () {
  "use strict";

  function createToggle() {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "password-field-toggle";
    button.setAttribute("aria-label", "Show password");
    button.setAttribute("aria-pressed", "false");
    button.title = "Show password";

    var icon = document.createElement("i");
    icon.className = "fa fa-eye password-field-icon";
    button.appendChild(icon);

    return button;
  }

  function isPositioned(element) {
    var position = window.getComputedStyle(element).position;
    return position !== "static";
  }

  function buildToggle(input) {
    if (input.classList.contains("password-field-control")) return;

    var parent = input.parentNode;

    // Outline/floating-label layouts position the label as a sibling of the
    // input, so the toggle is inserted next to the input to keep that intact.
    if (isPositioned(parent) && parent.querySelector(".form-label")) {
      parent.insertBefore(createToggle(), input.nextSibling);
      input.classList.add("password-field-inline");
    } else {
      var wrapper = document.createElement("div");
      wrapper.className = "password-field";
      parent.insertBefore(wrapper, input);
      wrapper.appendChild(input);
      wrapper.appendChild(createToggle());
    }

    input.classList.add("password-field-control");
  }

  function enhance(root) {
    var inputs = (root || document).querySelectorAll(
      'input[type="password"]:not([data-no-toggle])'
    );

    Array.prototype.forEach.call(inputs, buildToggle);
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".password-field-toggle");
    if (!button) return;

    var input = button.parentNode.querySelector(".password-field-control");
    if (!input) return;

    var hidden = input.type === "password";
    input.type = hidden ? "text" : "password";

    var icon = button.querySelector(".password-field-icon");
    if (icon) {
      icon.classList.toggle("fa-eye", !hidden);
      icon.classList.toggle("fa-eye-slash", hidden);
    }

    var label = hidden ? "Hide password" : "Show password";
    button.setAttribute("aria-label", label);
    button.setAttribute("aria-pressed", String(hidden));
    button.title = label;

    var caret = input.value.length;
    input.focus();
    if (hidden) input.setSelectionRange(caret, caret);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      enhance(document);
    });
  } else {
    enhance(document);
  }

  window.enhancePasswordFields = enhance;
})();
