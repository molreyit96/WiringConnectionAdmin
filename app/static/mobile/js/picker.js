(function () {
  window.initSearchPicker = function (opts) {
    var input = opts.inputEl;
    var list = opts.listEl;
    var data = opts.data || [];
    var maxResults = opts.maxResults || 50;
    var onPick = opts.onPick || function () {};
    var renderRow = opts.renderRow || function (item) {
      return item.name;
    };

    function render(query) {
      list.innerHTML = "";
      var key = (query || "").trim().toLowerCase();
      var matches = [];
      for (var i = 0; i < data.length; i++) {
        var item = data[i];
        var hay = (item.text || item.name || "").toLowerCase();
        if (item.id) hay += " " + item.id;
        if (!key || hay.indexOf(key) !== -1) {
          matches.push(item);
          if (matches.length >= maxResults) break;
        }
      }

      if (!matches.length) {
        var empty = document.createElement("div");
        empty.className = "picker-empty";
        empty.textContent = key ? "No results found" : "Type to search";
        list.appendChild(empty);
        return;
      }

      for (var j = 0; j < matches.length; j++) {
        (function (item) {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "picker-row tap-target";
          var content = renderRow(item);
          if (content && content.nodeType) {
            btn.appendChild(content);
          } else {
            var span = document.createElement("span");
            span.className = "picker-name";
            span.textContent = content;
            btn.appendChild(span);
          }
          btn.addEventListener("click", function () {
            onPick(item);
          });
          list.appendChild(btn);
        })(matches[j]);
      }

      if (matches.length < data.length) {
        var count = document.createElement("div");
        count.className = "picker-count";
        count.textContent = "Showing " + matches.length + " of " + data.length;
        list.appendChild(count);
      }
    }

    if (input) {
      input.addEventListener("input", function () {
        render(input.value);
      });
    }

    render(input ? input.value : "");
    return { render: render };
  };
})();