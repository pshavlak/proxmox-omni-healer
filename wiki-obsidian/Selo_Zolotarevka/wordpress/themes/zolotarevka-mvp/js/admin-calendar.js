(function() {
  'use strict';

  let matchCounters = {};

  function getEl(id) { return document.getElementById(id); }

  /* === Calendar Editor === */

  function initCalendar() {
    // Tab switching
    document.querySelectorAll('.zolo-circle-tab').forEach(function(tab) {
      tab.addEventListener('click', function() {
        var circle = this.dataset.circle;
        document.querySelectorAll('.zolo-circle-tab').forEach(function(t) { t.classList.remove('active'); });
        this.classList.add('active');
        document.querySelectorAll('.zolo-circle-panel').forEach(function(p) { p.classList.remove('active'); });
        var panel = getEl('zolo-circle-panel-' + circle);
        if (panel) panel.classList.add('active');
      });
    });

    // Init match counters per round
    document.querySelectorAll('.zolo-round-block').forEach(function(block) {
      var key = block.dataset.circle + '_' + block.dataset.roundIdx;
      var matches = block.querySelectorAll('.zolo-matches-table tbody tr').length;
      matchCounters[key] = matches;
    });

    // Bind remove buttons
    bindCalendarButtons();
  }

  function bindCalendarButtons() {
    // Add match buttons
    document.querySelectorAll('.zolo-add-match-btn').forEach(function(btn) {
      btn.removeEventListener('click', addMatch);
      btn.addEventListener('click', addMatch);
    });

    // Remove match buttons
    document.querySelectorAll('.zolo-remove-match').forEach(function(btn) {
      btn.removeEventListener('click', removeMatch);
      btn.addEventListener('click', removeMatch);
    });

    // Remove round buttons
    document.querySelectorAll('.zolo-remove-round-btn').forEach(function(btn) {
      btn.removeEventListener('click', removeRound);
      btn.addEventListener('click', removeRound);
    });

    // Add round buttons
    document.querySelectorAll('.zolo-add-round-btn').forEach(function(btn) {
      btn.removeEventListener('click', addRound);
      btn.addEventListener('click', addRound);
    });
  }

  function addMatch(e) {
    var btn = e.target;
    var block = btn.closest('.zolo-round-block');
    var circle = block.dataset.circle;
    var roundIdx = block.dataset.roundIdx;
    var key = circle + '_' + roundIdx;
    if (!matchCounters[key]) matchCounters[key] = 0;
    var idx = matchCounters[key];

    var tbody = block.querySelector('.zolo-matches-table tbody');
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td class="zolo-col-num">' + (tbody.querySelectorAll('tr').length + 1) + '</td>' +
      '<td class="zolo-col-team"><input type="text" name="zolo_calendar[' + circle + '][' + roundIdx + '][m][' + idx + '][home]" value="" placeholder="Хозяева"></td>' +
      '<td class="zolo-col-vs">—</td>' +
      '<td class="zolo-col-team"><input type="text" name="zolo_calendar[' + circle + '][' + roundIdx + '][m][' + idx + '][away]" value="" placeholder="Гости"></td>' +
      '<td class="zolo-col-score"><input type="text" name="zolo_calendar[' + circle + '][' + roundIdx + '][m][' + idx + '][score_h]" value="" placeholder="–" size="3"></td>' +
      '<td class="zolo-col-score"><input type="text" name="zolo_calendar[' + circle + '][' + roundIdx + '][m][' + idx + '][score_a]" value="" placeholder="–" size="3"></td>' +
      '<td class="zolo-col-status">' +
        '<select name="zolo_calendar[' + circle + '][' + roundIdx + '][m][' + idx + '][status]">' +
          '<option value="scheduled">Запланирован</option>' +
          '<option value="played">Сыгран</option>' +
          '<option value="postponed">Перенесён</option>' +
        '</select>' +
      '</td>' +
      '<td class="zolo-col-action"><button type="button" class="zolo-remove-match" title="Удалить матч">✕</button></td>';
    tbody.appendChild(tr);
    matchCounters[key] = idx + 1;

    // Bind remove on new row
    tr.querySelector('.zolo-remove-match').addEventListener('click', removeMatch);
    renumberMatches(block);
  }

  function removeMatch(e) {
    var btn = e.target;
    var block = btn.closest('.zolo-round-block');
    var tr = btn.closest('tr');
    var tbody = tr.closest('tbody');
    if (tbody.querySelectorAll('tr').length <= 1) return;
    tr.parentNode.removeChild(tr);
    renumberMatches(block);
  }

  function renumberMatches(block) {
    var rows = block.querySelectorAll('.zolo-matches-table tbody tr');
    rows.forEach(function(row, i) {
      row.querySelector('.zolo-col-num').textContent = i + 1;
    });
  }

  function addRound(e) {
    var btn = e.target;
    var panel = btn.closest('.zolo-circle-panel');
    var circle = panel.dataset.circle;
    var rounds = panel.querySelectorAll('.zolo-round-block');
    var idx = rounds.length;

    var div = document.createElement('div');
    div.className = 'zolo-round-block';
    div.dataset.circle = circle;
    div.dataset.roundIdx = idx;

    var key = circle + '_' + idx;
    matchCounters[key] = 0;

    div.innerHTML =
      '<div class="zolo-round-header">' +
        '<span class="zolo-round-title">Тур <span class="zolo-round-display">' + (idx + 1) + '</span></span>' +
        '<input type="hidden" name="zolo_calendar[' + circle + '][' + idx + '][round]" value="' + (idx + 1) + '">' +
        '<span class="zolo-date-label">Дата:</span>' +
        '<input type="text" name="zolo_calendar[' + circle + '][' + idx + '][date]" value="" placeholder="напр. 18 апреля">' +
        '<button type="button" class="button zolo-remove-round-btn" style="margin-left:auto;">✕ Удалить тур</button>' +
      '</div>' +
      '<table class="zolo-matches-table">' +
        '<thead><tr>' +
          '<th class="zolo-col-num">#</th>' +
          '<th class="zolo-col-team">Хозяева</th>' +
          '<th class="zolo-col-vs"></th>' +
          '<th class="zolo-col-team">Гости</th>' +
          '<th class="zolo-col-score" colspan="2">Счёт</th>' +
          '<th class="zolo-col-status">Статус</th>' +
          '<th class="zolo-col-action"></th>' +
        '</tr></thead>' +
        '<tbody></tbody>' +
      '</table>' +
      '<div class="zolo-round-actions">' +
        '<button type="button" class="button zolo-add-match-btn">+ Добавить матч</button>' +
      '</div>';

    panel.insertBefore(div, btn.parentNode);

    // Bind events on new round
    div.querySelector('.zolo-add-match-btn').addEventListener('click', addMatch);
    div.querySelector('.zolo-remove-round-btn').addEventListener('click', removeRound);

    // Add first empty match row
    var tbody = div.querySelector('tbody');
    addMatch({target: div.querySelector('.zolo-add-match-btn')});
  }

  function removeRound(e) {
    var btn = e.target;
    var block = btn.closest('.zolo-round-block');
    var panel = block.closest('.zolo-circle-panel');
    if (panel.querySelectorAll('.zolo-round-block').length <= 1) return;
    block.parentNode.removeChild(block);
  }

  /* === Auto-Calculate Standings === */

  function initCalcButton() {
    var btn = getEl('zolo-calc-standings');
    if (!btn) return;
    btn.addEventListener('click', function() {
      var teamStats = {};
      var calendarInputs = document.querySelectorAll('[name^="zolo_calendar"]');

      // Collect all matches with scores
      calendarInputs.forEach(function(input) {
        var name = input.name;
        // Match names: zolo_calendar[1][0][m][0][score_h], etc.
        var match = name.match(/zolo_calendar\[(\d+)\]\[(\d+)\]\[m\]\[(\d+)\]\[(\w+)\]/);
        if (!match) return;

        var circle = match[1], round = match[2], matchIdx = match[3], field = match[4];
        if (field !== 'score_h' && field !== 'score_a' && field !== 'status' &&
            field !== 'home' && field !== 'away') return;

        // Store value
        var key = circle + '_' + round + '_' + matchIdx;
        if (!window._zoloMatchData) window._zoloMatchData = {};
        if (!window._zoloMatchData[key]) window._zoloMatchData[key] = {};
        window._zoloMatchData[key][field] = input.value;
      });

      // We need to process after all data is collected
      processStandingsCalc(btn);
    });
  }

  function processStandingsCalc(btn) {
    var data = window._zoloMatchData || {};
    var teams = {};
    var resultDiv = getEl('zolo-calc-result');

    for (var key in data) {
      var m = data[key];
      if (!m.home || !m.away) continue;
      if (m.status !== 'played' && m.status !== '') continue;
      if (m.score_h === '' || m.score_a === '') continue;

      var sh = parseInt(m.score_h, 10);
      var sa = parseInt(m.score_a, 10);
      if (isNaN(sh) || isNaN(sa)) continue;

      if (!teams[m.home]) teams[m.home] = {team: m.home, gp: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, gd: 0, pts: 0};
      if (!teams[m.away]) teams[m.away] = {team: m.away, gp: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, gd: 0, pts: 0};

      teams[m.home].gp++;
      teams[m.home].gf += sh;
      teams[m.home].ga += sa;

      teams[m.away].gp++;
      teams[m.away].gf += sa;
      teams[m.away].ga += sh;

      if (sh > sa) {
        teams[m.home].w++; teams[m.home].pts += 3;
        teams[m.away].l++;
      } else if (sa > sh) {
        teams[m.away].w++; teams[m.away].pts += 3;
        teams[m.home].l++;
      } else {
        teams[m.home].d++; teams[m.home].pts += 1;
        teams[m.away].d++; teams[m.away].pts += 1;
      }
    }

    // Calculate GD
    for (var t in teams) {
      teams[t].gd = teams[t].gf - teams[t].ga;
    }

    // Sort
    var sorted = Object.values(teams).sort(function(a, b) {
      if (b.pts !== a.pts) return b.pts - a.pts;
      if (b.gd !== a.gd) return b.gd - a.gd;
      if (b.gf !== a.gf) return b.gf - a.gf;
      return a.team.localeCompare(b.team);
    });

    // Fill standings table
    var standingsTable = getEl('zolo-standings-table');
    if (!standingsTable) {
      showCalcResult(resultDiv, 'Таблица не найдена на странице', true);
      return;
    }

    var tbody = standingsTable.querySelector('tbody');

    // Clear existing rows
    tbody.innerHTML = '';

    // Add calculated rows
    sorted.forEach(function(team, i) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + (i + 1) + '</td>' +
        '<td><input type="text" name="standings[' + i + '][team]" value="' + escHtml(team.team) + '" style="width:100%;"></td>' +
        '<td><input type="number" name="standings[' + i + '][gp]" value="' + team.gp + '" min="0" style="width:100%;"></td>' +
        '<td><input type="number" name="standings[' + i + '][w]" value="' + team.w + '" min="0" style="width:100%;"></td>' +
        '<td><input type="number" name="standings[' + i + '][d]" value="' + team.d + '" min="0" style="width:100%;"></td>' +
        '<td><input type="number" name="standings[' + i + '][l]" value="' + team.l + '" min="0" style="width:100%;"></td>' +
        '<td><input type="number" name="standings[' + i + '][gf]" value="' + team.gf + '" min="0" style="width:100%;"></td>' +
        '<td><input type="number" name="standings[' + i + '][ga]" value="' + team.ga + '" min="0" style="width:100%;"></td>' +
        '<td class="zolo-standings-gd ' + (team.gd > 0 ? 'positive' : team.gd < 0 ? 'negative' : '') + '">' +
          (team.gd > 0 ? '+' : '') + team.gd +
        '</td>' +
        '<td><input type="number" name="standings[' + i + '][pts]" value="' + team.pts + '" min="0" style="width:100%;"></td>' +
        '<td><button type="button" class="button zolo-remove-row" style="background:#dc3545;color:#fff;border:none;cursor:pointer;">✕</button></td>';
      tbody.appendChild(tr);
    });

    // Update standings index for add-row
    window._zoloStandingsIdx = sorted.length;

    // Re-bind remove buttons
    tbody.querySelectorAll('.zolo-remove-row').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        var row = e.target.closest('tr');
        if (tbody.querySelectorAll('tr').length > 1) {
          row.parentNode.removeChild(row);
          renumberStandings(tbody);
        }
      });
    });

    showCalcResult(resultDiv, 'Турнирная таблица рассчитана: ' + sorted.length + ' команд');
    window._zoloMatchData = null;
  }

  function renumberStandings(tbody) {
    tbody.querySelectorAll('tr').forEach(function(tr, i) {
      tr.cells[0].textContent = i + 1;
    });
  }

  function showCalcResult(el, msg, isError) {
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
    el.className = 'zolo-calc-result' + (isError ? ' error' : '');
  }

  function escHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  /* === Init === */
  document.addEventListener('DOMContentLoaded', function() {
    initCalendar();
    initCalcButton();
  });

})();
