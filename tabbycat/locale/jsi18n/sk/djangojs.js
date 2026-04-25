

'use strict'
{
  const globals = this
  const django = globals.django || (globals.django = {})


  django.pluralidx = function(count) {
    const v = (count==1) ? 0 : (count>=2 && count<=4) ? 1 : 3
    if (typeof v === 'boolean') {
      return v ? 1 : 0
    } else {
      return v
    }
  }


  /* gettext library */

  django.catalog = django.catalog || {}

  const newcatalog = {
    "%1 %2 from %3": "%1 %2 od %3",
    "%1 %2 from %3 %4": "%1 %2 od %3 %4",
    "%1 %2 from %3 on %4 (Chair)": "%1 %2 od %3 on %4 (Chair)",
    "%1 %2 from %3 on %4 (Panellist)": "%1 %2 od %3 on %4 (Panellista)",
    "%1 %2 from %3 on %4 (Trainee)": "%1 %2 from %3 on %4 (Shadow)",
    "%1 checked in %2: %3": "%1 prihl\u00e1sen\u00fd v %2: %3",
    "%1:": "%1:",
    "<strong>\u2613</strong> All": "<strong>\u2613</strong> V\u0161etk\u00fdch",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> V\u0161etk\u00fdch",
    "Add Ballot": "Prida\u0165 ballot",
    "Adjudicating with %1.": "Rozhoduje\u0161 s %1.",
    "Adjudicator Results": "V\u00fdsledky rozhodcu",
    "All": "V\u0161etky",
    "Auto-Allocate": "Automatick\u00e9 pride\u013eovanie",
    "Ballot Check-Ins": "Registr\u00e1cia ballotov",
    "Ballot Statuses": "Status Ballotov",
    "Ballots Status": "Status ballotov",
    "By how many points did they win:": "O ko\u013eko bodov vyhrali:",
    "Category": "Kateg\u00f3ria",
    "Chair for Panel of %1": "Chair pre Panel - %1",
    "Checked-In": "Zaregistrovan\u00fd",
    "Click to check-in manually": "Kliknite pre manu\u00e1lnu registr\u00e1ciu",
    "Click to undo a check-in": "Kliknite pre zvr\u00e1tenie registr\u00e1cie",
    "Confirmed": "Potvrden\u00e9",
    "Debated": "Debatovan\u00e9",
    "Find in Table": "H\u013eada\u0165 v tabu\u013eke",
    "Gender": "Pohlavie",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "D\u00d4LE\u017dIT\u00c9: Skontrolujte a explicitne zazna\u010dte, \u010di re\u010dn\u00edk prednesie viacero re\u010d\u00ed.",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "Ak chcete zobrazi\u0165 t\u00fato str\u00e1nku bez bo\u010dn\u00e9ho panela (napr. pre zobrazenie v predn\u00e1\u0161kovej s\u00e1le), m\u00f4\u017eete pou\u017ei\u0165 \"assitenciu\".",
    "Independent": "Nez\u00e1visl\u00fd",
    "Lost": "Prehra",
    "Mark replies %1 to %2; <strong>%3</strong>.": "Oboduj z\u00e1vere\u010dn\u00e9 re\u010di od %1 a\u017e %2; <strong>%3</strong>.",
    "Mark speeches %1 to %2; <strong>%3</strong>.": "Boduj re\u010di od %1 a\u017e %2; <strong>%3</strong>.",
    "No": "Nie",
    "No Category": "Bez kateg\u00f3rie",
    "No changes": "Bez zmeny",
    "No matching people found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face osoby.",
    "No matching rooms found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face mietnosti.",
    "Not Checked-In": "Nezaregistrovan\u00fd",
    "Open the assistant version.": "Otvori\u0165 asistenciu.",
    "Panellist": "Panelista",
    "Please set all scores in this block.": "Pros\u00edm zadajte v\u0161etky sk\u00f3re pre t\u00fato sekciu.",
    "Priority %1": "Priorita %1",
    "Rank": "Poradie",
    "Re-Edit": "Op\u00e4tovn\u00e1 \u00faprava",
    "Region": "Regi\u00f3n",
    "Return ballots to %1.": "Vr\u00e1ti\u0165 ballot %1.",
    "Review": "Kontrola",
    "Room:": "Miestnos\u0165:",
    "Scan Using Camera": "Skenovanie pomocou fotoapar\u00e1tu",
    "Score:": "Sk\u00f3re",
    "Set all availabilities to exactly match check-ins.": "Nastavte v\u0161etky dostupn\u00e9 term\u00edny tak, aby presne zodpovedali registr\u00e1ci\u00ed.",
    "Solo Chair": "Samostatn\u00fd Chair",
    "Speaker Results": "V\u00fdsledky re\u010dn\u00edkov",
    "Stop Camera Scan": "Zastavi\u0165 skenovanie fotoapar\u00e1tom",
    "TIE": "REM\u00cdZA",
    "Team": "T\u00edm",
    "The motion is <em>%1</em>": "T\u00e9za je <em>%1</em>",
    "The total score for this block must be a whole number.": "Celkov\u00e9 body musia by\u0165 cel\u00e9 \u010d\u00edslo.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "T\u00e1to str\u00e1nka sa bude aktualizova\u0165 v re\u00e1lnom \u010dase s nov\u00fdmi registr\u00e1ciami, ako sa bud\u00fa vyskytova\u0165, hoci po\u010diato\u010dn\u00fd zoznam m\u00f4\u017ee by\u0165 star\u00fd a\u017e jednu min\u00fatu.",
    "This person does not have a check-in identifier so they can't be checked in": "T\u00e1to osoba nem\u00e1 identifika\u010dn\u00fd k\u00f3d na registr\u00e1ciu, preto nem\u00f4\u017ee by\u0165 zaregistrovan\u00fd.",
    "Tie": "Rem\u00edza",
    "Total for": "Celkovo body pre",
    "Total:": "Celkovo:",
    "Trainee": "Shadow",
    "Turn On Sounds": "Zapn\u00fa\u0165 zvuky",
    "Unaffiliated": "Nez\u00e1visl\u00fd",
    "Uncategorised": "Nekategorizovan\u00fd",
    "Unconfirmed": "Nepotrvrden\u00e9",
    "Unknown": "Nezn\u00e1me",
    "Use classic ballot UI": "Pou\u017ei\u0165 klasick\u00e9 UI ballotu",
    "Use slider ballot UI": "Pou\u017ei\u0165 slider UI ballotu",
    "Which team won the debate:": "Ktor\u00fd t\u00edm vyhral debatu:",
    "Won": "V\u00fdhra",
    "Yes": "Ano",
    "You cannot confirm this ballot because you entered it": "Tento ballot nem\u00f4\u017eete potvrdi\u0165, preto\u017ee ste ho vyplnili.",
    "saving...": "uklad\u00e1m..",
    "speaker scores total": "celkov\u00e9 sk\u00f3re re\u010dn\u00edka",
    "speakers with gender data": "v\u00fdsledky re\u010dn\u00edkov s \u00fadajmi o pohlav\u00ed"
}
  for (const key in newcatalog) {
    django.catalog[key] = newcatalog[key]
  }


  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      const value = django.catalog[msgid]
      if (typeof value === 'undefined') {
        return msgid
      } else {
        return (typeof value === 'string') ? value : value[0]
      }
    }

    django.ngettext = function(singular, plural, count) {
      const value = django.catalog[singular]
      if (typeof value === 'undefined') {
        return (count == 1) ? singular : plural
      } else {
        return value.constructor === Array ? value[django.pluralidx(count)] : value
      }
    }

    django.gettext_noop = function(msgid) { return msgid }

    django.pgettext = function(context, msgid) {
      let value = django.gettext(context + '\x04' + msgid)
      if (value.includes('\x04')) {
        value = msgid
      }
      return value
    }

    django.npgettext = function(context, singular, plural, count) {
      let value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count)
      if (value.includes('\x04')) {
        value = django.ngettext(singular, plural, count)
      }
      return value
    }

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])})
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())})
      }
    }


    /* formatting library */

    django.formats = {
      'DATETIME_FORMAT': 'j. E Y G:i',
      'DATETIME_INPUT_FORMATS': [
        '%d.%m.%Y %H:%M:%S',
        '%d.%m.%Y %H:%M:%S.%f',
        '%d.%m.%Y %H.%M',
        '%d.%m.%Y %H:%M',
        '%d. %m. %Y %H:%M:%S',
        '%d. %m. %Y %H:%M:%S.%f',
        '%d. %m. %Y %H.%M',
        '%d. %m. %Y %H:%M',
        '%Y-%m-%d %H.%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
      ],
      'DATE_FORMAT': 'j. E Y',
      'DATE_INPUT_FORMATS': [
        '%d.%m.%Y',
        '%d.%m.%y',
        '%d. %m. %Y',
        '%d. %m. %y',
        '%Y-%m-%d',
      ],
      'DECIMAL_SEPARATOR': ',',
      'FIRST_DAY_OF_WEEK': 1,
      'MONTH_DAY_FORMAT': 'j. F',
      'NUMBER_GROUPING': 3,
      'SHORT_DATETIME_FORMAT': 'd.m.Y G:i',
      'SHORT_DATE_FORMAT': 'd.m.Y',
      'THOUSAND_SEPARATOR': '\u00a0',
      'TIME_FORMAT': 'G:i',
      'TIME_INPUT_FORMATS': [
        '%H:%M:%S',
        '%H.%M',
        '%H:%M',
        '%H:%M:%S.%f',
      ],
      'YEAR_MONTH_FORMAT': 'F Y',
    }

    django.get_format = function(format_type) {
      const value = django.formats[format_type]
      if (typeof value === 'undefined') {
        return format_type
      } else {
        return value
      }
    }

    /* add to global namespace */
    globals.pluralidx = django.pluralidx
    globals.gettext = django.gettext
    globals.ngettext = django.ngettext
    globals.gettext_noop = django.gettext_noop
    globals.pgettext = django.pgettext
    globals.npgettext = django.npgettext
    globals.interpolate = django.interpolate
    globals.get_format = django.get_format

    django.jsi18n_initialized = true
  }
};
