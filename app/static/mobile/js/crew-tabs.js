/* Crew screen tabs: section + doc sub-pills, keyboard, swipe, persistence */
(function () {
    'use strict';

    var PANELS = ['employees', 'items', 'docs'];
    var DOC_SUBS = ['maps', 'pictures', 'material'];

    var tabRow = document.getElementById('wcTabRow');
    var announce = document.getElementById('wcTabAnnounce');
    var storageKey = tabRow ? (tabRow.getAttribute('data-storage') || '') : '';

    function tabFor(name) {
        return tabRow ? tabRow.querySelector('.wc-tab[data-panel="' + name + '"]') : null;
    }
    function panelFor(name) {
        return document.getElementById('panel-' + name);
    }
    function currentSection() {
        var p = new URLSearchParams(window.location.search);
        var sec = p.get('section');
        return sec && PANELS.indexOf(sec) !== -1 ? sec : null;
    }
    function currentDocSub() {
        var p = new URLSearchParams(window.location.search);
        var s = p.get('sub');
        return s && DOC_SUBS.indexOf(s) !== -1 ? s : null;
    }
    function updateLocation(params) {
        try {
            var p = new URLSearchParams(window.location.search);
            Object.keys(params).forEach(function (k) {
                if (params[k] === null) {
                    p.delete(k);
                } else {
                    p.set(k, params[k]);
                }
            });
            history.replaceState(null, '', window.location.pathname + (p.toString() ? '?' + p.toString() : ''));
        } catch (e) { /* history API unavailable */ }
    }

    function activateTab(name, persist) {
        if (!tabRow || PANELS.indexOf(name) === -1) return;
        PANELS.forEach(function (sec) {
            var btn = tabFor(sec);
            var panel = panelFor(sec);
            if (!btn || !panel) return;
            var active = sec === name;
            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-selected', active ? 'true' : 'false');
            btn.setAttribute('tabindex', active ? '0' : '-1');
            panel.classList.toggle('is-visible', active);
            if (active) {
                panel.removeAttribute('hidden');
            } else {
                panel.setAttribute('hidden', '');
            }
        });
        if (announce) announce.textContent = 'Showing ' + name;
        if (persist) {
            try { localStorage.setItem('wc-crew-tab:' + storageKey, name); } catch (e) {}
            updateLocation({ section: name });
        }
    }

    function activateDocSub(sub, persist) {
        if (!sub || DOC_SUBS.indexOf(sub) === -1) return;
        document.querySelectorAll('.wc-doc-subpill').forEach(function (btn) {
            btn.classList.toggle('is-active', btn.getAttribute('data-docsub') === sub);
        });
        document.querySelectorAll('.wc-doc-group').forEach(function (g) {
            var active = g.getAttribute('data-docgroup') === sub;
            g.classList.toggle('is-visible', active);
            if (active) {
                g.removeAttribute('hidden');
            } else {
                g.setAttribute('hidden', '');
            }
        });
        if (persist) {
            try { localStorage.setItem('wc-crew-doc:' + storageKey, sub); } catch (e) {}
            updateLocation({ section: 'docs', sub: sub });
        }
    }

    function initTabs() {
        if (!tabRow) return;

        var urlSection = currentSection();
        var stored = null;
        try { stored = localStorage.getItem('wc-crew-tab:' + storageKey); } catch (e) {}
        var initial = urlSection || stored || 'employees';
        if (initial !== currentSection()) {
            updateLocation({ section: initial });
        }
        activateTab(initial, false);

        tabRow.addEventListener('click', function (ev) {
            var btn = ev.target.closest('.wc-tab');
            if (!btn) return;
            activateTab(btn.getAttribute('data-panel'), true);
        });

        tabRow.addEventListener('keydown', function (ev) {
            var btn = ev.target.closest('.wc-tab');
            if (!btn) return;
            var idx = PANELS.indexOf(btn.getAttribute('data-panel'));
            var next = null;
            if (ev.key === 'ArrowRight') next = PANELS[(idx + 1) % PANELS.length];
            if (ev.key === 'ArrowLeft') next = PANELS[(idx - 1 + PANELS.length) % PANELS.length];
            if (next) {
                ev.preventDefault();
                var target = tabFor(next);
                if (target) { target.focus(); }
                activateTab(next, true);
            }
        });
    }

    function initDocSubs() {
        var subpills = document.querySelector('.wc-doc-subpills');
        if (!subpills) return;
        var urlSub = currentDocSub();
        var stored = null;
        try { stored = localStorage.getItem('wc-crew-doc:' + storageKey); } catch (e) {}
        var initial = urlSub || stored || 'maps';
        activateDocSub(initial, false);

        subpills.addEventListener('click', function (ev) {
            var btn = ev.target.closest('.wc-doc-subpill');
            if (!btn) return;
            activateDocSub(btn.getAttribute('data-docsub'), true);
        });
    }

    function initSwipe() {
        var startX = null;
        var startY = null;
        document.querySelectorAll('.wc-tab-panel').forEach(function (panel) {
            panel.addEventListener('touchstart', function (ev) {
                var t = ev.target.closest ? ev.target.closest('textarea,input,select,.wc-crew-scroll,.documents-container') : null;
                if (t) { startX = null; return; }
                startX = ev.changedTouches[0].clientX;
                startY = ev.changedTouches[0].clientY;
            }, { passive: true });
            panel.addEventListener('touchend', function (ev) {
                if (startX === null) return;
                var dx = ev.changedTouches[0].clientX - startX;
                var dy = ev.changedTouches[0].clientY - startY;
                startX = null;
                if (Math.abs(dx) < 60 || Math.abs(dy) > Math.max(40, Math.abs(dx))) return;
                var cur = null;
                PANELS.forEach(function (n) {
                    var p = panelFor(n);
                    if (p && !p.hasAttribute('hidden')) cur = n;
                });
                if (!cur) return;
                var idx = PANELS.indexOf(cur);
                var next = dx < 0 ? PANELS[(idx + 1) % PANELS.length] : PANELS[(idx - 1 + PANELS.length) % PANELS.length];
                activateTab(next, true);
            }, { passive: true });
        });
    }

    function initScrollElevation() {
        var bar = document.getElementById('wcContextBar');
        if (!bar) return;
        var onScroll = function () {
            bar.classList.toggle('is-scrolled', window.scrollY > 12);
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    /* ---- Actions sheet + readiness ---- */

    var sheet = null;
    var sheetBackdrop = null;
    var sheetBtn = null;

    function openSheet() {
        if (!sheet) return;
        sheet.removeAttribute('hidden');
        sheetBackdrop.removeAttribute('hidden');
        sheetBtn.setAttribute('aria-expanded', 'true');
        document.body.classList.add('wc-sheet-open');
        setTimeout(function () { sheet.classList.add('is-open'); }, 10);
    }
    function closeSheet() {
        if (!sheet) return;
        sheet.classList.remove('is-open');
        document.body.classList.remove('wc-sheet-open');
        setTimeout(function () {
            sheet.setAttribute('hidden', '');
            sheetBackdrop.setAttribute('hidden', '');
        }, 180);
        if (sheetBtn) sheetBtn.setAttribute('aria-expanded', 'false');
    }

    function showSendValid(blockers) {
        var list = document.getElementById('wcValidList');
        var modal = document.getElementById('wcValidModal');
        if (!list || !modal) return;
        list.innerHTML = '';
        blockers.forEach(function (msg) {
            var li = document.createElement('li');
            li.textContent = msg;
            list.appendChild(li);
        });
        var inst = window._wcValidModal || new bootstrap.Modal(modal);
        window._wcValidModal = inst;
        inst.show();
    }

    function runSendPrecheck() {
        var d = window.wcPrecheck;
        if (!d) return [];
        var blockers = [];
        if (!d.hasWO) blockers.push('Select a Work Order.');
        if (!d.hasSup) blockers.push('Select a Supervisor.');
        if (!d.hasEmp) blockers.push('Add at least one employee.');
        if (!d.hasItem) blockers.push('Add at least one item.');
        if (d.hasEmp && d.hasItem && d.totalPay !== 100) blockers.push('Total % to Pay must equal 100.');
        if (d.hasWO && d.woCount > 0) blockers.push('This WO is already used in another Daily today.');
        return blockers;
    }

    function handleSend() {
        closeSheet();
        var blockers = runSendPrecheck();
        if (blockers.length) {
            showSendValid(blockers);
            return;
        }
        if (window.wcConfirm && window.send_payroll) {
            window.wcConfirm('Are you sure you want to send this daily for approval?', function () {
                window.send_payroll(window.wcPrecheck.dailyId, window.wcPrecheck.locId, 1);
            });
        }
    }

    function initActionsSheet() {
        sheet = document.getElementById('wcActionsSheet');
        sheetBackdrop = document.getElementById('wcActionsBackdrop');
        sheetBtn = document.getElementById('wcActionsBtn');
        if (!sheet || !sheetBackdrop) return;

        if (sheetBtn) {
            sheetBtn.addEventListener('click', function () {
                if (sheet.classList.contains('is-open')) {
                    closeSheet();
                } else {
                    openSheet();
                }
            });
        }

        sheet.addEventListener('click', function (ev) {
            var item = ev.target.closest('.wc-actions-item');
            if (!item) return;
            var action = item.getAttribute('data-action');
            if (action === 'cancel') {
                closeSheet();
            } else if (action === 'download') {
                closeSheet();
            } else if (action === 'send') {
                handleSend();
            } else if (action === 'delete' && window.wcConfirm && window.delete_daily) {
                closeSheet();
                window.delete_daily(window.wcPrecheck.dailyId, window.wcPrecheck.locId);
            }
        });

        sheetBackdrop.addEventListener('click', closeSheet);
        document.addEventListener('keydown', function (ev) {
            if (ev.key === 'Escape' && sheet.classList.contains('is-open')) closeSheet();
        });
    }

    function updateReadyChip() {
        var chip = document.getElementById('wcReadyChip');
        var text = document.getElementById('wcReadyChipText');
        if (!chip || !text) return;
        if (chip.getAttribute('data-rejected') === 'true') {
            chip.className = 'wc-status-chip wc-status-chip--danger';
            text.textContent = 'Rejected';
            return;
        }
        var blockers = runSendPrecheck();
        if (blockers.length) {
            chip.className = 'wc-status-chip wc-status-chip--warn';
            text.textContent = 'Not ready';
        } else {
            chip.className = 'wc-status-chip wc-status-chip--ok';
            text.textContent = 'Ready to send';
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        initTabs();
        initDocSubs();
        initSwipe();
        initScrollElevation();
        initActionsSheet();
        updateReadyChip();
    });
})();