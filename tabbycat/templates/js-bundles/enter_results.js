// When using anonymous speaker names prepopulate the form to save time
aff_speakers = $("#id_aff_speaker_s1 option").text();
neg_speakers = $("#id_neg_speaker_s1 option").text();
if (aff_speakers.indexOf("Speaker 1") != -1 && neg_speakers.indexOf("Speaker 1") != -1) {
  $("div.aff.s1").find("select :nth-child(2)").prop('selected', true);
  $("div.aff.s2").find("select :nth-child(3)").prop('selected', true);
  $("div.aff.s3").find("select :nth-child(4)").prop('selected', true);
  $("div.aff.s4").find("select :nth-child(5)").prop('selected', true);
  $("div.neg.s1").find("select :nth-child(2)").prop('selected', true);
  $("div.neg.s2").find("select :nth-child(3)").prop('selected', true);
  $("div.neg.s3").find("select :nth-child(4)").prop('selected', true);
  $("div.neg.s4").find("select :nth-child(5)").prop('selected', true);
}

function ballot_i18n(message) {
  return typeof gettext === 'function' ? gettext(message) : message;
}

const ballotWonLabel = ballot_i18n('Won');
const ballotLostLabel = ballot_i18n('Lost');
const ballotTieLabel = ballot_i18n('Tie');
const ballotTieUpperLabel = ballot_i18n('TIE');

function refresh_weighted_speaker_totals($scoresheet, side) {
  if (!$('.criterion', $scoresheet).length) {
    return;
  }

  for (const speaker of [...$(`.side-${side}.score`, $scoresheet)]) {
    const criteria = $('.criterion input', speaker);
    var weighted = 0;
    var missingRequired = false;
    criteria.each((i, c) => {
      const rawValue = c.value;
      const required = c.dataset.required !== 'false';
      if (rawValue === '') {
        if (required) {
          missingRequired = true;
        }
        return;
      }

      const score = parseFloat(rawValue);
      const weight = parseFloat(c.getAttribute('weight') || 1);
      if (!Number.isNaN(score) && !Number.isNaN(weight)) {
        weighted += score * weight;
      }
    });

    const totalField = speaker.querySelector('input.total');
    if (totalField) {
      totalField.value = missingRequired ? '' : weighted;
      set_whole_number_total_validity(totalField);
    }
  }
}

function side_has_missing_speaker_totals($scoresheet, side) {
  return [...$(`.side-${side}.score input.total`, $scoresheet)].some((input) => input.value === '');
}

function refresh_totals(scoresheet) {

  $scoresheet = $(scoresheet);

  // Fix the branching logic here into something cleaner
  var allClasses = 'btn-dark btn-secondary btn-success btn-primary btn-warning btn-danger btn-info';

  if ("{{ pref.teams_in_debate }}" == 1) {
    // Solo speech formats still need live criterion totals before submit.
    for (const totalButton of [...$('button[name$="_total"]', $scoresheet)]) {
      const match = totalButton.name.match(/^(\d+)_total$/);
      if (!match) { continue; }

      const side = parseInt(match[1]);
      refresh_weighted_speaker_totals($scoresheet, side);
      var team_total = sum($(`.side-${side}.score input.total`, $scoresheet)) + cross_total($scoresheet, side);
      if (side_has_missing_speaker_totals($scoresheet, side)) {
        $(totalButton).text("00");
      } else {
        $(totalButton).text(team_total);
      }
    }
  } else if ("{{ pref.teams_in_debate }}" == 2) {
    // 2-team
    $aff_total = $('[name="0_total"]', $scoresheet);
    $neg_total = $('[name="1_total"]', $scoresheet);
    $aff_rank = $('[name="0_rank"]', $scoresheet);
    $neg_rank = $('[name="1_rank"]', $scoresheet);
    $aff_margin = $('[name="0_margin"]', $scoresheet);
    $neg_margin = $('[name="1_margin"]', $scoresheet);
    if ($('.criterion', $scoresheet).length) {
      for (const side of [0, 1]) {
        for (const speaker of [...$(`.side-${side}.score`, $scoresheet)]) {
          const criteria = $('.criterion input', speaker);
          var weighted = 0;
          var missingRequired = false;
          criteria.each((i, c) => {
            const rawValue = c.value;
            const required = c.dataset.required !== 'false';
            if (rawValue === '') {
              if (required) {
                missingRequired = true;
              }
              return;
            }

            const score = parseFloat(rawValue);
            const weight = parseFloat(c.getAttribute('weight') || 1);
            if (!Number.isNaN(score) && !Number.isNaN(weight)) {
              weighted += score * weight;
            }
          });
          const totalField = speaker.querySelector('input.total');
          if (totalField) {
            totalField.value = missingRequired ? '' : weighted;
            set_whole_number_total_validity(totalField);
          }
        }
      }
    }
    var affCross = cross_total($scoresheet, 0);
    var negCross = cross_total($scoresheet, 1);
    var aff = sum($('.side-0.score input.total', $scoresheet)) + affCross;
    var neg = sum($('.side-1.score input.total', $scoresheet)) + negCross;
    $aff_total.text(aff);
    $neg_total.text(neg);

    $aff_rank.removeClass(allClasses);
    $neg_rank.removeClass(allClasses);
    if (aff > neg) {
      $aff_rank.addClass('btn-success');
      $neg_rank.addClass('btn-danger');
      $aff_rank.text(ballotWonLabel);
      $neg_rank.text(ballotLostLabel);
      $aff_margin.text("+" + Number(aff - neg));
      $neg_margin.text(Number(neg - aff));
    } else if (neg > aff) {
      $aff_rank.addClass('btn-danger');
      $neg_rank.addClass('btn-success');
      $aff_rank.text(ballotLostLabel);
      $neg_rank.text(ballotWonLabel);
      $aff_margin.text(Number(aff - neg));
      $neg_margin.text("+" + Number(neg - aff));
    } else {
      $aff_rank.addClass('btn-dark');
      $neg_rank.addClass('btn-dark');
      $aff_rank.text(ballotTieLabel);
      $neg_rank.text(ballotTieLabel);
      $aff_margin.text(Number(aff - neg));
      $neg_margin.text(Number(neg - aff));
    }
  } else {
    // BP
    var totals_elements = []
    var margins_elements = []
    var total_scores = []
    var rank_elements = []

    for (var i = 0; i < $('.scoresheet > div').length; i++) {
      totals_elements[i] = $(`[name="${i}_total"]`, $scoresheet);
      margins_elements[i] = $(`[name="${i}_margin"]`, $scoresheet);
      rank_elements[i] = $(`[name="${i}_rank"]`, $scoresheet);
      if ($('.criterion', $scoresheet).length) {
        for (const speaker of [...$(`.side-${i}.score`, $scoresheet)]) {
          const criteria = $('.criterion input', speaker);
          var weighted = 0;
          var missingRequired = false;
          criteria.each((i, c) => {
            const rawValue = c.value;
            const required = c.dataset.required !== 'false';
            if (rawValue === '') {
              if (required) {
                missingRequired = true;
              }
              return;
            }

            const score = parseFloat(rawValue);
            const weight = parseFloat(c.getAttribute('weight') || 1);
            if (!Number.isNaN(score) && !Number.isNaN(weight)) {
              weighted += score * weight;
            }
          });
          const totalField = speaker.querySelector('input.total');
          if (totalField) {
            totalField.value = missingRequired ? '' : weighted;
            set_whole_number_total_validity(totalField);
          }
        }
      }
      var team_total = sum($(`.side-${i}.score input.total`, $scoresheet)) + cross_total($scoresheet, i);
      // Always record a numeric total so `total_scores` stays a dense array;
      // a sparse array here makes `.map()` skip holes and the downstream
      // `sortedScores[i][0]` / `sortedScores[j][0]` reads crash on undefined.
      total_scores[i] = team_total > 99 ? team_total : 0;
      // Only display the total once both speaker scores have been entered.
      if (team_total > 99) {
        totals_elements[i].text(total_scores[i]);
      }
    }

    // Create new dict with total scores sorted high-low
    var sortedScores = total_scores.map(function(val, i) {
      return [i, val];
    });
    sortedScores.sort(function(first, second) {
      return second[1] - first[1];
    });

    // Use sorted dictionary to assign relative margins and win indicators
    for (var i = 0; i < sortedScores.length; i++) {

      if (!sortedScores[i]) { continue }
      var team = sortedScores[i][0];
      if (total_scores[team] === 0) { continue }

      // Add winning class indicators; but not if there was a tie
      var tie = false;
      for (var j = 0; j < sortedScores.length; j++) {
        if (j === i) { continue }
        tie ||= total_scores[team] === total_scores[sortedScores[j][0]];
      }

      rank_elements[team].removeClass(allClasses);
      rank_elements[team].text("?");
      if (!tie && sortedScores.length > 3) {
        const btn_classes = ['btn-success', 'btn-info', 'btn-warning', 'btn-danger'];
        const ordinals = ['1st', '2nd', '3rd', '4th'];
        rank_elements[team].addClass(btn_classes[i]);
        rank_elements[team].text(ordinals[i]);
      } else if (tie) {
        rank_elements[team].addClass('btn-dark');
        rank_elements[team].text(ballotTieUpperLabel);
      } else {
        rank_elements[team].addClass('btn-secondary');
      }

      // Display margin
      var top_score = total_scores[sortedScores[0][0]];
      var margin = String(top_score - total_scores[team]);
      if (margin !== "0") {
        margin = "-" + margin
      }
      margins_elements[team].text(margin);
    }
  }


}

function sum(elems) {
  var r = 0;
  elems.each(function(){
    var p = parseFloat($(this).val());
    if (!Number.isNaN(p)) r += p;
  });
  return r;
}

function weighted_sum(elems) {
  var r = 0;
  elems.each(function(){
    var p = parseFloat($(this).val());
    var w = parseFloat($(this).attr('weight') || 1);
    if (!Number.isNaN(p) && !Number.isNaN(w)) r += p * w;
  });
  return r;
}

function cross_total(scoresheet, side) {
  var $criteriaInputs = $(`.side-${side}.cross input.cross-criterion`, scoresheet);
  var $totalInput = $(`.side-${side}.cross input.cross-total`, scoresheet);

  if ($criteriaInputs.length > 0) {
    var total = 0;
    var missingRequired = false;
    $criteriaInputs.each(function() {
      const rawValue = this.value;
      const required = this.dataset.required !== 'false';
      if (rawValue === '') {
        if (required) {
          missingRequired = true;
        }
        return;
      }

      const score = parseFloat(rawValue);
      const weight = parseFloat(this.getAttribute('weight') || 1);
      if (!Number.isNaN(score) && !Number.isNaN(weight)) {
        total += score * weight;
      }
    });
    if ($totalInput.length) {
      const totalInput = $totalInput.get(0);
      totalInput.value = missingRequired ? '' : total;
      set_whole_number_total_validity(totalInput);
    }
    return missingRequired ? 0 : total;
  }

  if ($totalInput.length === 0) {
    return 0;
  }

  const fallbackInput = $totalInput.get(0);
  set_whole_number_total_validity(fallbackInput);
  var fallback = parseFloat($totalInput.val());
  return Number.isNaN(fallback) ? 0 : fallback;
}

const sliderUiEnabled = $('#ballot_set').data('sliderUiEnabled') === true || $('#ballot_set').data('sliderUiEnabled') === "true";
const sliderModeStorageKey = 'tabbycat-ballot-input-mode';

function slider_i18n(message) {
  return ballot_i18n(message);
}

const wholeNumberTotalMessage = slider_i18n('The total score for this block must be a whole number.');
const missingBlockScoresMessage = slider_i18n('Please set all scores in this block.');
let sliderValidationRequested = false;

function is_effectively_integer(value) {
  return Math.abs(value - Math.round(value)) < 1e-9;
}

function set_whole_number_total_validity(input) {
  if (!input) {
    return true;
  }

  const rawValue = input.value;
  const parsedValue = parseFloat(rawValue);
  const hasValue = rawValue !== '' && !Number.isNaN(parsedValue);
  const isValid = !hasValue || is_effectively_integer(parsedValue);

  input.setAttribute('step', '1');
  input.setCustomValidity(isValid ? '' : wholeNumberTotalMessage);
  input.classList.toggle('is-invalid', !isValid);

  const block = input.closest('.ballot-sliderized-target');
  if (block) {
    block.classList.toggle('ballot-total-invalid', !isValid);
  }

  return isValid;
}

function block_has_missing_scores(block) {
  const criteriaInputs = [...block.querySelectorAll('.criterion input.js-slider-source-number')];
  if (criteriaInputs.length > 0) {
    return criteriaInputs.some((input) => input.dataset.required !== 'false' && input.value === '');
  }

  const totalInput = block.querySelector('.ballot-total-field input.js-slider-source-number');
  return !!(totalInput && totalInput.value === '');
}

function find_first_invalid_slider_block(form) {
  return [...form.querySelectorAll('.ballot-sliderized-target')].find((block) => {
    const totalInput = block.querySelector('.ballot-total-field input.js-slider-source-number');
    const hasInvalidTotal = !!(totalInput && !set_whole_number_total_validity(totalInput));
    const hasMissingScores = sliderValidationRequested && block_has_missing_scores(block);
    const hasValidationError = !!block.querySelector('.errorlist, .error');
    return hasInvalidTotal || hasMissingScores || hasValidationError;
  });
}

function validate_whole_number_totals(form) {
  const totalInputs = [...form.querySelectorAll('.ballot-total-field input')];
  const firstInvalid = totalInputs.find((input) => !set_whole_number_total_validity(input));
  return !firstInvalid;
}

function reset_submit_buttons(form) {
  const $form = $(form);
  const $buttons = $form.find('button[type="submit"], input[type="submit"]');

  if ($.fn.resetButton) {
    $buttons.each(function() {
      $.fn.resetButton($(this));
    });
  }

  $buttons.prop('disabled', false).removeClass('disabled');
}

function format_slider_value(value, step) {
  if (value === undefined || value === null || value === '') {
    return slider_i18n('Not set');
  }

  var number = parseFloat(value);
  if (Number.isNaN(number)) {
    return slider_i18n('Not set');
  }

  var stepString = String(step || '1');
  if (stepString.indexOf('.') === -1) {
    return String(number);
  }

  var decimals = stepString.split('.')[1].length;
  return number.toFixed(decimals).replace(/\.0+$/, '').replace(/(\.\d*?[1-9])0+$/, '$1');
}

function ensure_slider_source_id(sourceInput) {
  if (!sourceInput.id) {
    sourceInput.id = `slider-source-${Math.random().toString(36).slice(2, 10)}`;
  }
  return sourceInput.id;
}

function sync_slider_control(sourceInput, rangeInput, valueNode) {
  if (!sourceInput || !rangeInput || !valueNode) {
    return;
  }

  if (sourceInput.value !== '' && !Number.isNaN(parseFloat(sourceInput.value))) {
    rangeInput.value = sourceInput.value;
  }

  if (sourceInput.closest('.ballot-total-field')) {
    sourceInput.setAttribute('step', '1');
  }

  rangeInput.step = sourceInput.getAttribute('step') || '1';
  rangeInput.disabled = sourceInput.disabled;
  valueNode.textContent = `- ${format_slider_value(sourceInput.value, sourceInput.getAttribute('step'))}`;

  const control = rangeInput.closest('.ballot-slider-control');
  if (control) {
    control.classList.toggle('is-unset', sourceInput.value === '');
  }
}

function build_slider_control(sourceRow, sourceInput, labelText) {
  if (!sourceInput) {
    return null;
  }

  const control = document.createElement('div');
  control.className = 'ballot-slider-control';

  const meta = document.createElement('div');
  meta.className = 'ballot-slider-meta';

  const label = document.createElement('span');
  label.className = 'ballot-slider-label';
  label.textContent = labelText;

  const value = document.createElement('span');
  value.className = 'ballot-slider-value';

  meta.appendChild(label);
  meta.appendChild(value);

  const range = document.createElement('input');
  range.type = 'range';
  range.className = 'ballot-slider-range';
  range.min = sourceInput.getAttribute('min') || '0';
  range.max = sourceInput.getAttribute('max') || '100';
  range.step = sourceInput.getAttribute('step') || '1';
  range.dataset.sourceInputId = ensure_slider_source_id(sourceInput);
  range.value = sourceInput.value !== '' && !Number.isNaN(parseFloat(sourceInput.value)) ? sourceInput.value : range.min;

  range.addEventListener('input', function() {
    sourceInput.value = range.value;
    $(sourceInput).trigger('input').trigger('change');
    sync_slider_control(sourceInput, range, value);
  });

  sourceInput.addEventListener('input', function() {
    sync_slider_control(sourceInput, range, value);
  });
  sourceInput.addEventListener('change', function() {
    sync_slider_control(sourceInput, range, value);
  });

  control.appendChild(meta);
  control.appendChild(range);

  sourceRow.querySelectorAll('.errorlist').forEach(function(errorList) {
    const clone = errorList.cloneNode(true);
    clone.classList.add('ballot-slider-errorlist');
    control.appendChild(clone);
  });

  sync_slider_control(sourceInput, range, value);
  return control;
}

function update_slider_block(block) {
  const toggle = block.querySelector('.ballot-slider-toggle');
  const totalInput = block.querySelector('.ballot-total-field input.js-slider-source-number');
  if (!toggle || !totalInput) {
    return;
  }

  const title = block.dataset.sliderTitle || slider_i18n('Total');
  const labelNode = toggle.querySelector('.ballot-slider-summary-label');
  const valueNode = toggle.querySelector('.ballot-slider-summary-value');
  const inlineError = block.querySelector('.ballot-slider-inline-error');
  const hasValidationError = !!block.querySelector('.errorlist, .error');
  const blockMissingScores = block_has_missing_scores(block);
  const hasInvalidTotal = !!(totalInput && !set_whole_number_total_validity(totalInput));
  const hasMissingScores = sliderValidationRequested && blockMissingScores;
  labelNode.textContent = `${slider_i18n('Total for')} ${title}`;
  valueNode.textContent = blockMissingScores ? slider_i18n('Not set') : format_slider_value(totalInput.value, totalInput.getAttribute('step'));
  toggle.classList.toggle('ballot-slider-error', hasValidationError || hasInvalidTotal || hasMissingScores);
  block.classList.toggle('ballot-total-invalid', hasInvalidTotal || hasMissingScores);
  block.classList.toggle('is-open', hasValidationError || hasInvalidTotal || hasMissingScores || block.classList.contains('is-open'));

  if (inlineError) {
    if (hasMissingScores) {
      inlineError.textContent = missingBlockScoresMessage;
      inlineError.hidden = false;
    } else if (hasInvalidTotal) {
      inlineError.textContent = wholeNumberTotalMessage;
      inlineError.hidden = false;
    } else {
      inlineError.textContent = '';
      inlineError.hidden = true;
    }
  }

  block.querySelectorAll('.ballot-slider-range').forEach(function(rangeInput) {
    const sourceInput = document.getElementById(rangeInput.dataset.sourceInputId);
    const control = rangeInput.closest('.ballot-slider-control');
    const controlValue = control ? control.querySelector('.ballot-slider-value') : null;
    sync_slider_control(sourceInput, rangeInput, controlValue);
  });
}

function refresh_all_slider_blocks() {
  if (!sliderUiEnabled) {
    return;
  }
  document.querySelectorAll('.ballot-sliderized-target').forEach(update_slider_block);
}

function initialize_slider_block(block) {
  if (block.dataset.sliderEnhanced === 'true') {
    return;
  }

  const sourceRows = Array.from(block.children).filter(function(child) {
    return child.classList && (child.classList.contains('criterion') || child.classList.contains('ballot-total-field'));
  });
  if (!sourceRows.length) {
    return;
  }

  block.dataset.sliderEnhanced = 'true';
  const hasCriteria = sourceRows.some(function(row) { return row.classList.contains('criterion'); });

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'ballot-slider-toggle';
  toggle.innerHTML = '<span class="ballot-slider-summary"><span class="ballot-slider-summary-label"></span><span class="ballot-slider-summary-value"></span></span><span class="ballot-slider-caret">&#9662;</span>';

  const panel = document.createElement('div');
  panel.className = 'ballot-slider-panel';

  const inlineError = document.createElement('div');
  inlineError.className = 'ballot-slider-inline-error';
  inlineError.hidden = true;

  block.insertBefore(toggle, block.firstChild);
  block.insertBefore(panel, toggle.nextSibling);

  sourceRows.forEach(function(sourceRow) {
    const sourceInput = sourceRow.querySelector('input.js-slider-source-number');
    if (!sourceInput) {
      return;
    }

    if (hasCriteria && sourceRow.classList.contains('ballot-total-field')) {
      sourceRow.querySelectorAll('.errorlist').forEach(function(errorList) {
        const clone = errorList.cloneNode(true);
        clone.classList.add('ballot-slider-errorlist');
        panel.appendChild(clone);
      });
      return;
    }

    const labelNode = sourceRow.querySelector('.criterion-name, .ballot-total-label');
    const fallbackLabel = sourceRow.classList.contains('ballot-total-field') ? slider_i18n('Total') : block.dataset.sliderTitle || slider_i18n('Score');
    const labelText = labelNode ? labelNode.textContent.trim() : fallbackLabel;
    const control = build_slider_control(sourceRow, sourceInput, labelText);
    if (control) {
      panel.appendChild(control);
    }
  });

  panel.appendChild(inlineError);

  if (block.querySelector('.errorlist, .error')) {
    block.classList.add('is-open');
  }

  toggle.addEventListener('click', function() {
    block.classList.toggle('is-open');
  });

  update_slider_block(block);
}

function set_ballot_input_mode(mode) {
  if (!sliderUiEnabled) {
    return;
  }

  const root = document.getElementById('ballot_set');
  const toggle = document.getElementById('ballotUiModeToggle');
  if (!root) {
    return;
  }

  const sliderMode = mode !== 'classic';
  root.classList.toggle('ballot-slider-mode', sliderMode);

  if (toggle) {
    toggle.textContent = sliderMode ? (toggle.dataset.classicLabel || slider_i18n('Use classic ballot UI')) : (toggle.dataset.sliderLabel || slider_i18n('Use slider ballot UI'));
  }

  try {
    window.localStorage.setItem(sliderModeStorageKey, sliderMode ? 'slider' : 'classic');
  } catch (error) {
    // Ignore storage issues in private browsing or restricted environments.
  }

  if (sliderMode) {
    refresh_all_slider_blocks();
  }
}

function initialize_slider_ballot_ui() {
  if (!sliderUiEnabled) {
    return;
  }

  document.querySelectorAll('.ballot-sliderized-target').forEach(initialize_slider_block);

  const toggle = document.getElementById('ballotUiModeToggle');
  if (toggle) {
    toggle.addEventListener('click', function() {
      const root = document.getElementById('ballot_set');
      const nextMode = root && root.classList.contains('ballot-slider-mode') ? 'classic' : 'slider';
      set_ballot_input_mode(nextMode);
    });
  }

  let savedMode = 'slider';
  try {
    savedMode = window.localStorage.getItem(sliderModeStorageKey) || 'slider';
  } catch (error) {
    savedMode = 'slider';
  }
  set_ballot_input_mode(savedMode);
}

function update_speakers() {
  $('.js-speaker').each(update_speaker);
}

function update_speaker() {
  // e.g. id_aff_speaker_s1
  var parts = $(this).attr('id').split('_');
  var side = parts[1]; // e.g. 'aff'
  var pos = parts[3];  // e.g. 's1'
  var speaker = $(':selected', this).text();

  // Update speaker names for all judges other than the first
  // e.g. '.side-0.s1 .speaker-name' (side_code matches form field prefix, e.g. id_0_speaker_s1)
  $(`.side-${side}.${pos} .speaker-name`).html(speaker);

  var others = [];
  var posno = parseInt(pos.charAt(1));

  {% if form.using_replies %}
    if (posno != {{ form.reply_position }})
      for (var i = 1; i <= {{ form.last_substantive_position }}; i++)
        if (i != posno) others.push(i);
    if (posno == {{ form.last_substantive_position }})
      others.push({{ form.reply_position }});
    if (posno == {{ form.reply_position }})
      others.push({{ form.last_substantive_position }});
  {% elif form.last_substantive_position %}
    for (var i = 1; i <= {{ form.last_substantive_position }}; i++)
      if (i != posno) others.push(i);
  {% else %}
    // If there's no form (ie adj has no debate for this round) do nothing
  {% endif %}

  // Detect duplicates
  var dupe = false;
  $.each(others, function(idx, val) {
    $sel = $('#id_'+side+'_speaker_s'+val);
    if ($(':selected', $sel).text() == speaker) {
      dupe = true;
    };
  });
  if (dupe || speaker === '---------') {
    $(this).addClass('error');
  } else {
    $(this).removeClass('error');
  }

}

if ($.fn.validate) {
  $("#resultsForm").validate({
    invalidHandler: function(event, validator) {
      $.fn.resetButton($("#submit", event.target))
    }
  });
}

function refresh_all_scoresheets() {
  $('.scoresheet').each(function() {
    refresh_totals($(this));
  });
  document.querySelectorAll('.ballot-total-field input').forEach(function(input) {
    set_whole_number_total_validity(input);
  });
  refresh_all_slider_blocks();
}

initialize_slider_ballot_ui();
refresh_all_scoresheets();
$('.score input:not(.ballot-slider-range), .cross input:not(.ballot-slider-range)').on('input change', function() {
  refresh_totals($(this).closest('.scoresheet'));
  refresh_all_slider_blocks();
});
$('#resultsForm').find('button[type="submit"], input[type="submit"]').on('click', function() {
  refresh_all_scoresheets();
});
$('#resultsForm').on('input change', 'input, select, textarea', function() {
  reset_submit_buttons($('#resultsForm'));
});
const resultsFormElement = document.getElementById('resultsForm');
if (resultsFormElement) {
  resultsFormElement.addEventListener('invalid', function() {
    reset_submit_buttons(resultsFormElement);
  }, true);
}
$('#resultsForm').on('submit', function(event) {
  sliderValidationRequested = true;
  refresh_all_scoresheets();

  const totalsAreValid = validate_whole_number_totals(this);
  const firstInvalidSliderBlock = find_first_invalid_slider_block(this);
  if (!totalsAreValid || firstInvalidSliderBlock) {
    event.preventDefault();
    reset_submit_buttons(this);

    if (firstInvalidSliderBlock) {
      firstInvalidSliderBlock.classList.add('is-open');
      firstInvalidSliderBlock.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
});

function checkForfeit() {
  const anyChecked = document.querySelectorAll('input.forfeit-check:checked').length;
  if (anyChecked) {
    [...document.querySelectorAll('.js-speaker,.total')].forEach(el => { el.disabled = true; });
  } else {
    [...document.querySelectorAll('.js-speaker,.total')].forEach(el => { el.disabled = false; });
  }
  refresh_all_slider_blocks();
}

checkForfeit();
[...document.querySelectorAll('input.forfeit-check')].forEach((checkbox) => {
  checkbox.addEventListener('change', checkForfeit);
});

$('.js-team-speakers select').change(update_speakers).each(update_speaker);

// Show/hide on initial input
$( ".iron-person input" ).each(function(index) {
  if ($(this).prop('checked') === true) {
    $("#hasIron").val('1');
    $(".iron-person").show()
  }
});

// Show/hide on toggle
$("#hasIron").change(function() {
  var enabled = $("#hasIron option:selected").val()
  if (enabled === "1") {
    $(".iron-person").show()
  } else if (enabled === "0") {
    $(".iron-person input").prop('checked', false);
    $(".iron-person").hide()
  }
});

{% if form.using_replies and form.last_substantive_position == 2 %}
// Fill in the reply speaker if there is only one option

  $('#id_aff_speaker_s1').change(function() {
    $('#id_aff_speaker_s{{ form.reply_position }}').val($(this).val());
    update_speakers();
  });
  $('#id_neg_speaker_s1').change(function() {
    $('#id_neg_speaker_s{{ form.reply_position }}').val($(this).val());
    update_speakers();
  });

{% endif %}

{% if form.choosing_sides %}

  var team_names = {};
  {% for team in form.debate.teams %}team_names['{{team.id}}'] = '{{team.short_name}}';
  {% endfor %}

  function swap_sides(selected_option) {

      team_ids = selected_option.split(',');
      aff_team_id = team_ids[0];
      neg_team_id = team_ids[1];

      // Copy team names
      $(".aff-team-name").text(team_names[aff_team_id]);
      $(".neg-team-name").text(team_names[neg_team_id]);

      // Take note of speaker positions
      current_speakers = {};
      $(".aff .js-speaker").each(function(index) {
        current_speakers["aff" + index] = $(this).val();
      })
      $(".neg .js-speaker").each(function(index) {
        current_speakers["neg" + index] = $(this).val();
      })

      // Copy speaker positions dropdowns
      $(".aff .js-speaker option").remove();
      $(".aff .js-speaker").each(function(index) {
        $("#id_team_" + aff_team_id + " option").clone().appendTo(this);
        // HACK TODO check for values before assigning
        $(this).val(current_speakers["aff" + index]);
        if (!$(this).val())
          $(this).val(current_speakers["neg" + index]);
      })
      $(".neg .js-speaker option").remove();
      $(".neg .js-speaker").each(function(index) {
        $("#id_team_" + neg_team_id + " option").clone().appendTo(this);
        // HACK TODO check for values before assigning
        $(this).val(current_speakers["neg" + index]);
        if (!$(this).val())
          $(this).val(current_speakers["aff" + index]);
      })

  }

  // On Load
  if ($("#id_choose_sides").val() == "") {
    $(".scoresheet").hide();
  } else {
    $(".sides-before-scores-warning").hide();
    var selected_option = $("#id_choose_sides").val()
    swap_sides(selected_option)
  }

  // On Change
  $('#id_choose_sides').change(function() {
    var selected_option = $("#id_choose_sides").val()
    if (selected_option != "") {
      $(".scoresheet").show();
      $(".sides-before-scores-warning").hide();
      swap_sides(selected_option)
    } else {
      $(".scoresheet").hide();
      $(".sides-before-scores-warning").show();
    }
    update_speakers();
  });

{% endif %}
