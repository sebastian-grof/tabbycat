
'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n==1) ? 0 : (n>=2 && n<=4) ? 1 : 3;
    if (typeof v === 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  const newcatalog = {
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s z %(cnt)s vybran\u00e9",
      "%(sel)s z %(cnt)s vybran\u00e9",
      "%(sel)s z %(cnt)s vybran\u00fdch",
      "%(sel)s z %(cnt)s vybran\u00fdch"
    ],
    "%1 %2 from %3": "%1 %2 od %3",
    "%1 %2 from %3 %4": "%1 %2 od %3 %4",
    "%1 %2 from %3 on %4 (Chair)": "%1 %2 od %3 on %4 (Chair)",
    "%1 %2 from %3 on %4 (Panellist)": "%1 %2 od %3 on %4 (Panellista)",
    "%1 %2 from %3 on %4 (Trainee)": "%1 %2 od %3 na %4 (Shadow)",
    "%1 (%2) with identifier of %3": "%1 (%2) s identifik\u00e1torom %3",
    "%1 (%2) with no assigned identifier": "%1 (%2) bez priraden\u00e9ho identifik\u00e1tora",
    "%1 (%2, %3)": "%1 (%2, %3)",
    "%1 (Absent; id=%2)": "%1 (nepr\u00edtomn\u00fd/\u00e1; id=%2)",
    "%1 (Present; id=%2)": "%1 (pr\u00edtomn\u00fd/\u00e1; id=%2)",
    "%1 (no category) with identifier of %2": "%1 (bez kateg\u00f3rie) s identifik\u00e1torom %2",
    "%1 (no category) with no assigned identifier": "%1 (bez kateg\u00f3rie) bez priraden\u00e9ho identifik\u00e1tora",
    "%1 checked in %2: %3": "%1 prihl\u00e1sen\u00fd v %2: %3",
    "%1, %2": "%1, %2",
    "%1, a %2": "%1, %2",
    "%1, a %2 from %3 with identifier of %4": "%1, %2 z %3 s identifik\u00e1torom %4",
    "%1, a %2 from %3 with no assigned identifier": "%1, %2 z %3 bez priraden\u00e9ho identifik\u00e1tora",
    "%1, a %2 of no institutional affiliation with identifier of %3": "%1, %2 bez klubovej pr\u00edslu\u0161nosti s identifik\u00e1torom %3",
    "%1, a %2 of no institutional affiliation with no assigned identifier": "%1, %2 bez klubovej pr\u00edslu\u0161nosti bez priraden\u00e9ho identifik\u00e1tora",
    "%1, a team with speakers %2": "%1, t\u00edm s re\u010dn\u00edkmi %2",
    "%1:": "%1:",
    "%s selected option not visible": [
      "%s ozna\u010den\u00e1 mo\u017enos\u0165 sa nezobrazuje",
      "%s ozna\u010den\u00e9 mo\u017enosti sa nezobrazuj\u00fa",
      "%s ozna\u010den\u00fdch mo\u017enost\u00ed sa nezobrazuje",
      "%s ozna\u010den\u00fdch mo\u017enost\u00ed sa nezobrazuje"
    ],
    "6 a.m.": "6:00",
    "6 p.m.": "18:00",
    "; ": "; ",
    "<strong>%1</strong>: %2": "<strong>%1</strong>: %2",
    "<strong>\u2613</strong> All": "<strong>\u2613</strong> V\u0161etk\u00fdch",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> V\u0161etk\u00fdch",
    "Add Ballot": "Prida\u0165 Ballot",
    "Adjudicating with %1.": "Rozhoduje\u0161 s %1.",
    "Adjudicator Demographics": "Demografia rozhodcov",
    "Adjudicator Results": "V\u00fdsledky rozhodcu",
    "Aff Veto": "Veto s\u00fahlasu",
    "All": "V\u0161etky",
    "Anon": "Anon",
    "Anonymous (due to team codes)": "Anonymn\u00e9 (kv\u00f4li t\u00edmov\u00fdm k\u00f3dom)",
    "April": "apr\u00edl",
    "August": "august",
    "Auto-Allocate": "Automatick\u00e9 pride\u013eovanie",
    "Auto-Prioritise": "Automaticky prioritizova\u0165",
    "Available %s": "Dostupn\u00e9 %s",
    "Ballot Check-Ins": "Registr\u00e1cia ballotov",
    "Ballot Statuses": "Status Ballotov",
    "Ballots Status": "Status ballotov",
    "Break": "Postup",
    "By %1": "Od %1",
    "By how many points did they win:": "O ko\u013eko bodov vyhrali:",
    "Cancel": "Zru\u0161i\u0165",
    "Category": "Kateg\u00f3ria",
    "Chair for Panel of %1": "Chair pre Panel - %1",
    "Checked-In": "Zaregistrovan\u00fd",
    "Choose": "Vybra\u0165",
    "Choose a Date": "Vybra\u0165 D\u00e1tum",
    "Choose a Time": "Vybra\u0165 \u010cas",
    "Choose a time": "Vybra\u0165 \u010das",
    "Choose all": "Vybra\u0165 v\u0161etko",
    "Chosen %s": "Vybran\u00e9 %s",
    "Circle %1": "Zakr\u00fa\u017ekuj %1",
    "Circle Rank:": "Zakr\u00fa\u017ekuj poradie:",
    "Circle the last digit of the %1's score:": "Zakr\u00fa\u017ekuj posledn\u00fa \u010d\u00edslicu sk\u00f3re pre %1:",
    "Circle the last digit of the team's total:": "Zakr\u00fa\u017ekuj posledn\u00fa \u010d\u00edslicu t\u00edmov\u00e9ho s\u00fa\u010dtu:",
    "Click to check-in manually": "Kliknite pre manu\u00e1lnu registr\u00e1ciu",
    "Click to choose all %s at once.": "Kliknite sem pre vybratie v\u0161etk\u00fdch %s naraz.",
    "Click to remove all chosen %s at once.": "Kliknite sem pre vymazanie vybrat\u00fdch %s naraz.",
    "Click to undo a check-in": "Kliknite pre zvr\u00e1tenie registr\u00e1cie",
    "Confirmed": "Potvrden\u00e9",
    "Copy From Check-Ins": "Kop\u00edrova\u0165 z check-inov",
    "Debated": "Debatovan\u00e9",
    "December": "december",
    "Did %1 deliver the adjudication?": "D\u00e1val/a %1 oral adjudication?",
    "February": "febru\u00e1r",
    "Filter": "Filtrova\u0165",
    "Find in Table": "H\u013eada\u0165 v tabu\u013eke",
    "Friday": "piatok",
    "Gender": "Pohlavie",
    "Hide": "Skry\u0165",
    "ID %1,": "ID %1,",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "D\u00d4LE\u017dIT\u00c9: Skontrolujte a explicitne zazna\u010dte, \u010di re\u010dn\u00edk prednesie viacero re\u010d\u00ed",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "Ak chcete zobrazi\u0165 t\u00fato str\u00e1nku bez bo\u010dn\u00e9ho panela (napr. pre zobrazenie v predn\u00e1\u0161kovej s\u00e1le), m\u00f4\u017eete pou\u017ei\u0165 \"assitenciu\".",
    "Independent": "Nez\u00e1visl\u00fd",
    "January": "janu\u00e1r",
    "July": "j\u00fal",
    "June": "j\u00fan",
    "Latest Actions": "Najnov\u0161ie akcie",
    "Latest Results": "Najnov\u0161ie v\u00fdsledky",
    "Lost": "Prehra",
    "March": "marec",
    "Mark replies %1 to %2; <strong>%3</strong>.": "Oboduj z\u00e1vere\u010dn\u00e9 re\u010di od %1 a\u017e %2; <strong>%3</strong>.",
    "Mark speeches %1 to %2; <strong>%3</strong>.": "Boduj re\u010di od %1 a\u017e %2; <strong>%3</strong>.",
    "Match": "Zhodova\u0165",
    "Match Check-Ins": "Zhodova\u0165 s check-inmi",
    "May": "m\u00e1j",
    "Midnight": "Polnoc",
    "Monday": "pondelok",
    "Neg Veto": "Veto nes\u00fahlasu",
    "No": "Nie",
    "No Actions Yet": "Zatia\u013e \u017eiadne akcie",
    "No Adjudicator Ratings Information": "\u017diadne inform\u00e1cie o hodnoteniach rozhodcov",
    "No Adjudicator-Adjudicator Feedback Information": "\u017diadne inform\u00e1cie o sp\u00e4tnej v\u00e4zbe rozhodca-rozhodca",
    "No Category": "Bez kateg\u00f3rie",
    "No Confirmed Results Yet": "Zatia\u013e \u017eiadne potvrden\u00e9 v\u00fdsledky",
    "No Gender Information": "\u017diadne inform\u00e1cie o rode",
    "No Position Information": "\u017diadne inform\u00e1cie o poz\u00edcii",
    "No Region Information": "\u017diadne inform\u00e1cie o regi\u00f3ne",
    "No Speaker Categories Information": "\u017diadne inform\u00e1cie o kateg\u00f3ri\u00e1ch re\u010dn\u00edkov",
    "No changes": "Bez zmeny",
    "No code name set": "Nie je nastaven\u00e9 k\u00f3dov\u00e9 meno",
    "No matching people found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face osoby.",
    "No matching rooms found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face mietnosti.",
    "No, I am submitting feedback on:": "Nie, odosielam sp\u00e4tn\u00fa v\u00e4zbu na:",
    "Noon": "Poludnie",
    "Not Checked-In": "Nezaregistrovan\u00fd",
    "Not set": "Nenastaven\u00e9",
    "Note: You are %s hour ahead of server time.": [
      "Pozn\u00e1mka: Ste %s hodinu pred \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hodiny pred \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hod\u00edn pred \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hod\u00edn pred \u010dasom servera."
    ],
    "Note: You are %s hour behind server time.": [
      "Pozn\u00e1mka: Ste %s hodinu za \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hodiny za \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hod\u00edn za \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hod\u00edn za \u010dasom servera."
    ],
    "November": "november",
    "Now": "Teraz",
    "October": "okt\u00f3ber",
    "Open the assistant version.": "Otvori\u0165 asistenciu.",
    "Panellist": "Panelista",
    "Please set all scores in this block.": "Pros\u00edm zadajte v\u0161etky sk\u00f3re pre t\u00fato sekciu.",
    "Priority %1": "Priorita %1",
    "Rank": "Poradie",
    "Re-Edit": "Op\u00e4tovn\u00e1 \u00faprava",
    "Region": "Regi\u00f3n",
    "Remove": "Odstr\u00e1ni\u0165",
    "Remove all": "Odstr\u00e1ni\u0165 v\u0161etky",
    "Return ballots to %1.": "Return hlasovania na %1.",
    "Return to Draw": "Return na?reb",
    "Review": "Kontrola",
    "Room:": "Miestnos\u0165:",
    "Saturday": "sobota",
    "Scan Using Camera": "Skenovanie pomocou fotoapar\u00e1tu",
    "Score:": "Sk\u00f3re:",
    "September": "september",
    "Set All Breaking as Available": "Nastavi\u0165 v\u0161etk\u00fdch breakuj\u00facich ako dostupn\u00fdch",
    "Set all availabilities to exactly match check-ins.": "Nastavte v\u0161etky dostupn\u00e9 term\u00edny tak, aby presne zodpovedali registr\u00e1ci\u00ed.",
    "Set all the availabilities to exactly match what they were in the previous round.": "Nastav\u00ed v\u0161etku dostupnos\u0165 presne pod\u013ea predch\u00e1dzaj\u00faceho kola.",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "Nastav\u00ed \u013eud\u00ed ako dostupn\u00fdch iba vtedy, ak maj\u00fa check-in a moment\u00e1lne s\u00fa nedostupn\u00ed, teda neprep\u00ed\u0161e existuj\u00facu dostupnos\u0165.",
    "Show": "Zobrazi\u0165",
    "Solo Chair": "Samostatn\u00fd Chair",
    "Speaker Demographics": "Demografia re\u010dn\u00edkov",
    "Speaker Results": "V\u00fdsledky re\u010dn\u00edkov",
    "Stop Camera Scan": "Zastavi\u0165 skenovanie fotoapar\u00e1tom",
    "Sunday": "nede\u013ea",
    "TIE": "REM\u00cdZA",
    "Team": "T\u00edm",
    "The bracket range of the hypothetical debate": "Rozsah bracketu hypotetickej debaty",
    "The debate's bracket": "Bracket debaty",
    "The estimated total number of live break categories across all teams of the hypothetical debate": "Predpokladan\u00e9 cel\u00e9 \u010d\u00edslo live break kateg\u00f3ri\u00ed naprie\u010d v\u0161etk\u00fdmi t\u00edmami v hypotetickej debate",
    "The motion is <em>%1</em>": "T\u00e9za je <em>%1</em>",
    "The total number of live break categories across all teams": "S\u00fa\u010det v\u0161etk\u00fdch break kateg\u00f3ri\u00ed napire\u010d v\u0161etk\u00fdmi t\u00edmami",
    "The total score for this block must be a whole number.": "Celkov\u00e9 body musia by\u0165 cel\u00e9 \u010d\u00edslo.",
    "This debate's priority": "Priorita tejto debaty",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre v\u00fdber je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVybra\u0165\u201c presun\u00fa\u0165.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre vymazanie je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVymaza\u0165\u201c vymaza\u0165.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "T\u00e1to str\u00e1nka sa bude aktualizova\u0165 v re\u00e1lnom \u010dase s nov\u00fdmi registr\u00e1ciami, ako sa bud\u00fa vyskytova\u0165, hoci po\u010diato\u010dn\u00fd zoznam m\u00f4\u017ee by\u0165 star\u00fd a\u017e jednu min\u00fatu.",
    "This person does not have a check-in identifier so they can't be checked in": "T\u00e1to osoba nem\u00e1 identifika\u010dn\u00fd k\u00f3d na registr\u00e1ciu, preto nem\u00f4\u017ee by\u0165 zaregistrovan\u00fd",
    "Thursday": "\u0161tvrtok",
    "Tie": "Rem\u00edza",
    "Today": "Dnes",
    "Tomorrow": "Zajtra",
    "Total for": "Spolu pre",
    "Total:": "Celkovo:",
    "Trainee": "Shadow",
    "Tuesday": "utorok",
    "Turn On Sounds": "Zapn\u00fa\u0165 zvuky",
    "Type into this box to filter down the list of available %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie dostupn\u00fdch %s.",
    "Type into this box to filter down the list of selected %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie ozna\u010den\u00fdch %s.",
    "Unaffiliated": "Nez\u00e1visl\u00fd",
    "Uncategorised": "Nekategorizovan\u00fd",
    "Unconfirmed": "Nepotrvrden\u00e9",
    "Unknown": "Nezn\u00e1me",
    "Unsure": "Nie som si ist\u00fd/\u00e1",
    "Use classic ballot UI": "Pou\u017ei\u0165 klasick\u00e9 UI ballotu",
    "Use slider ballot UI": "Pou\u017ei\u0165 slider UI ballotu",
    "Wednesday": "streda",
    "Which team won the debate:": "Ktor\u00fd t\u00edm vyhral debatu:",
    "Won": "V\u00fdhra",
    "Yes": "Ano",
    "Yesterday": "V\u010dera",
    "You cannot confirm this ballot because you entered it": "Nem\u00f4\u017ee\u0161 potvrdi\u0165 ballot, ktor\u00fd ste zadali vy",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Vybrali ste akciu, ale neurobili ste \u017eiadne zmeny v jednotliv\u00fdch poliach. Pravdepodobne ste chceli pou\u017ei\u0165 tla\u010didlo Vykona\u0165 namiesto Ulo\u017ei\u0165.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Vybrali ste akciu, ale neulo\u017eili ste jednotliv\u00e9 polia. Pros\u00edm, ulo\u017ete zmeny kliknut\u00edm na OK. Akciu budete musie\u0165 vykona\u0165 znova.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Vr\u00e1mci jednotliv\u00fdch editovate\u013en\u00fdch pol\u00ed m\u00e1te neulo\u017een\u00e9 zmeny. Ak vykon\u00e1te akciu, va\u0161e zmeny bud\u00fa straten\u00e9.",
    "abbrev. day Friday\u0004Fri": "pi",
    "abbrev. day Monday\u0004Mon": "po",
    "abbrev. day Saturday\u0004Sat": "so",
    "abbrev. day Sunday\u0004Sun": "ne",
    "abbrev. day Thursday\u0004Thur": "\u0161t",
    "abbrev. day Tuesday\u0004Tue": "ut",
    "abbrev. day Wednesday\u0004Wed": "st",
    "abbrev. month April\u0004Apr": "apr.",
    "abbrev. month August\u0004Aug": "aug.",
    "abbrev. month December\u0004Dec": "dec.",
    "abbrev. month February\u0004Feb": "feb.",
    "abbrev. month January\u0004Jan": "jan.",
    "abbrev. month July\u0004Jul": "j\u00fal",
    "abbrev. month June\u0004Jun": "j\u00fan",
    "abbrev. month March\u0004Mar": "mar.",
    "abbrev. month May\u0004May": "m\u00e1j",
    "abbrev. month November\u0004Nov": "nov.",
    "abbrev. month October\u0004Oct": "okt.",
    "abbrev. month September\u0004Sep": "sep.",
    "adjudicators with gender data": "rozhodcovia s \u00fadajmi o rode",
    "decimal marks are allowed": "desatinn\u00e9 body s\u00fa povolen\u00e9",
    "feedback scores total": "celkov\u00e9 sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "no \u00bd marks": "bez polbodov",
    "one letter Friday\u0004F": "P",
    "one letter Monday\u0004M": "P",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "N",
    "one letter Thursday\u0004T": "\u0160",
    "one letter Tuesday\u0004T": "U",
    "one letter Wednesday\u0004W": "S",
    "saving...": "uklad\u00e1m..",
    "speaker scores total": "celkov\u00e9 sk\u00f3re re\u010dn\u00edka",
    "speakers with gender data": "v\u00fdsledky re\u010dn\u00edkov s \u00fadajmi o pohlav\u00ed",
    "tab check": "kontrola tabu",
    "tab entry": "zadanie tabu",
    "\u00bd marks are allowed": "polbody s\u00fa povolen\u00e9"
  };
  for (const key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      const value = django.catalog[msgid];
      if (typeof value === 'undefined') {
        return msgid;
      } else {
        return (typeof value === 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      const value = django.catalog[singular];
      if (typeof value === 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value.constructor === Array ? value[django.pluralidx(count)] : value;
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      let value = django.gettext(context + '\x04' + msgid);
      if (value.includes('\x04')) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      let value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.includes('\x04')) {
        value = django.ngettext(singular, plural, count);
      }
      return value;
    };

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    };


    /* formatting library */

    django.formats = {
    "DATETIME_FORMAT": "j. F Y G:i",
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S",
      "%d.%m.%Y %H:%M:%S.%f",
      "%d.%m.%Y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j. F Y",
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y",
      "%d.%m.%y",
      "%y-%m-%d",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j. F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y G:i",
    "SHORT_DATE_FORMAT": "d.m.Y",
    "THOUSAND_SEPARATOR": "\u00a0",
    "TIME_FORMAT": "G:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F Y"
  };

    django.get_format = function(format_type) {
      const value = django.formats[format_type];
      if (typeof value === 'undefined') {
        return format_type;
      } else {
        return value;
      }
    };

    /* add to global namespace */
    globals.pluralidx = django.pluralidx;
    globals.gettext = django.gettext;
    globals.ngettext = django.ngettext;
    globals.gettext_noop = django.gettext_noop;
    globals.pgettext = django.pgettext;
    globals.npgettext = django.npgettext;
    globals.interpolate = django.interpolate;
    globals.get_format = django.get_format;

    django.jsi18n_initialized = true;
  }
};

