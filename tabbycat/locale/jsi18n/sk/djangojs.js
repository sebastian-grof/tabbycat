

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
      "%1 (%2) with identifier of %3": "%1 (%2) s identifikátorom %3",
      "%1 (%2) with no assigned identifier": "%1 (%2) bez priradeného identifikátora",
      "%1 (%2, %3)": "%1 (%2, %3)",
      "%1 (Absent; id=%2)": "%1 (neprítomný/á; id=%2)",
      "%1 (Present; id=%2)": "%1 (prítomný/á; id=%2)",
      "%1 (no category) with identifier of %2": "%1 (bez kategórie) s identifikátorom %2",
      "%1 (no category) with no assigned identifier": "%1 (bez kategórie) bez priradeného identifikátora",
      "%1 checked in %2: %3": "%1 prihlásený v %2: %3",
      "%1, %2": "%1, %2",
      "%1, a %2": "%1, %2",
      "%1, a %2 from %3 with identifier of %4": "%1, %2 z %3 s identifikátorom %4",
      "%1, a %2 from %3 with no assigned identifier": "%1, %2 z %3 bez priradeného identifikátora",
      "%1, a %2 of no institutional affiliation with identifier of %3": "%1, %2 bez klubovej príslušnosti s identifikátorom %3",
      "%1, a %2 of no institutional affiliation with no assigned identifier": "%1, %2 bez klubovej príslušnosti bez priradeného identifikátora",
      "%1, a team with speakers %2": "%1, tím s rečníkmi %2",
      "%1:": "%1:",
      "; ": "; ",
      "<strong>%1</strong>: %2": "<strong>%1</strong>: %2",
      "<strong>☓</strong> All": "<strong>☓</strong> Všetkých",
      "<strong>✓</strong> All": "<strong>✓</strong> Všetkých",
      "Add Ballot": "Pridať ballot",
      "Adjudicating with %1.": "Rozhoduješ s %1.",
      "Adjudicator Demographics": "Demografia rozhodcov",
      "Adjudicator Results": "Výsledky rozhodcu",
      "Aff Veto": "Veto súhlasu",
      "All": "Všetky",
      "Anon": "Anon.",
      "Anonymous (due to team codes)": "Anonymné (kvôli tímovým kódom)",
      "Auto-Allocate": "Automatické prideľovanie",
      "Auto-Prioritise": "Automaticky prioritizovať",
      "Ballot Check-Ins": "Registrácia ballotov",
      "Ballot Statuses": "Status Ballotov",
      "Ballots Status": "Status ballotov",
      "Break": "Break",
      "By %1": "Od %1",
      "By how many points did they win:": "O koľko bodov vyhrali:",
      "Category": "Kategória",
      "Chair for Panel of %1": "Chair pre Panel - %1",
      "Checked-In": "Zaregistrovaný",
      "Circle %1": "Zakrúžkuj %1",
      "Circle Rank:": "Zakrúžkuj poradie:",
      "Circle the last digit of the %1's score:": "Zakrúžkuj poslednú číslicu skóre pre %1:",
      "Circle the last digit of the team's total:": "Zakrúžkuj poslednú číslicu tímového súčtu:",
      "Click to check-in manually": "Kliknite pre manuálnu registráciu",
      "Click to undo a check-in": "Kliknite pre zvrátenie registrácie",
      "Confirmed": "Potvrdené",
      "Copy From Check-Ins": "Kopírovať z check-inov",
      "Debated": "Debatované",
      "Did %1 deliver the adjudication?": "Dával/a %1 oral adjudication?",
      "Find in Table": "Hľadať v tabuľke",
      "Gender": "Pohlavie",
      "ID %1,": "ID %1,",
      "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "DÔLEŽITÉ: Skontrolujte a explicitne zaznačte, či rečník prednesie viacero rečí",
      "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "Ak chcete zobraziť túto stránku bez bočného panela (napr. pre zobrazenie v prednáškovej sále), môžete použiť \"assitenciu\".",
      "Independent": "Nezávislý",
      "Latest Actions": "Najnovšie akcie",
      "Latest Results": "Najnovšie výsledky",
      "Lost": "Prehra",
      "Mark replies %1 to %2; <strong>%3</strong>.": "Oboduj záverečné reči od %1 až %2; <strong>%3</strong>.",
      "Mark speeches %1 to %2; <strong>%3</strong>.": "Boduj reči od %1 až %2; <strong>%3</strong>.",
      "Match": "Zhodovať",
      "Match Check-Ins": "Zhodovať s check-inmi",
      "Neg Veto": "Veto nesúhlasu",
      "No": "Nie",
      "No Actions Yet": "Zatiaľ žiadne akcie",
      "No Adjudicator Ratings Information": "Žiadne informácie o hodnoteniach rozhodcov",
      "No Adjudicator-Adjudicator Feedback Information": "Žiadne informácie o spätnej väzbe rozhodca-rozhodca",
      "No Category": "Bez kategórie",
      "No Confirmed Results Yet": "Zatiaľ žiadne potvrdené výsledky",
      "No Gender Information": "Žiadne informácie o rode",
      "No Position Information": "Žiadne informácie o pozícii",
      "No Region Information": "Žiadne informácie o regióne",
      "No Speaker Categories Information": "Žiadne informácie o kategóriách rečníkov",
      "No changes": "Bez zmeny",
      "No code name set": "Nie je nastavené kódové meno",
      "No matching people found.": "Nenašli sa žiadne zodpovedajúce osoby.",
      "No matching rooms found.": "Nenašli sa žiadne zodpovedajúce mietnosti.",
      "No, I am submitting feedback on:": "Nie, odosielam spätnú väzbu na:",
      "Not Checked-In": "Nezaregistrovaný",
      "Not set": "Nenastavené",
      "Open the assistant version.": "Otvoriť asistenciu.",
      "Panellist": "Panelista",
      "Please set all scores in this block.": "Prosím zadajte všetky skóre pre túto sekciu.",
      "Priority %1": "Priorita %1",
      "Rank": "Poradie",
      "Re-Edit": "Opätovná úprava",
      "Region": "Región",
      "Return ballots to %1.": "Vrátiť ballot %1.",
      "Return to Draw": "Späť na draw",
      "Review": "Kontrola",
      "Room:": "Miestnosť:",
      "Scan Using Camera": "Skenovanie pomocou fotoaparátu",
      "Score:": "Skóre:",
      "Set All Breaking as Available": "Nastaviť všetkých breakujúcich ako dostupných",
      "Set all availabilities to exactly match check-ins.": "Nastavte všetky dostupné termíny tak, aby presne zodpovedali registrácií.",
      "Set all the availabilities to exactly match what they were in the previous round.": "Nastaví všetku dostupnosť presne podľa predchádzajúceho kola.",
      "Set people as available only if they have a check-in and are currently unavailable — i.e. it will not overwrite any existing availabilities.": "Nastaví ľudí ako dostupných iba vtedy, ak majú check-in a momentálne sú nedostupní, teda neprepíše existujúcu dostupnosť.",
      "Solo Chair": "Samostatný Chair",
      "Speaker Demographics": "Demografia rečníkov",
      "Speaker Results": "Výsledky rečníkov",
      "Stop Camera Scan": "Zastaviť skenovanie fotoaparátom",
      "TIE": "REMÍZA",
      "Team": "Tím",
      "The bracket range of the hypothetical debate": "Rozsah bracketu hypotetickej debaty",
      "The debate's bracket": "Bracket debaty",
      "The estimated total number of live break categories across all teams of the hypothetical debate": "Odhadovaný celkový počet živých break kategórií naprieč všetkými tímami hypotetickej debaty",
      "The motion is <em>%1</em>": "Téza je <em>%1</em>",
      "The total number of live break categories across all teams": "Celkový počet živých break kategórií naprieč všetkými tímami",
      "The total score for this block must be a whole number.": "Celkové body musia byť celé číslo.",
      "This debate's priority": "Priorita tejto debaty",
      "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "Táto stránka sa bude aktualizovať v reálnom čase s novými registráciami, ako sa budú vyskytovať, hoci počiatočný zoznam môže byť starý až jednu minútu.",
      "This person does not have a check-in identifier so they can't be checked in": "Táto osoba nemá identifikačný kód na registráciu, preto nemôže byť zaregistrovaný",
      "Tie": "Remíza",
      "Total for": "Spolu pre",
      "Total:": "Celkovo:",
      "Trainee": "Shadow",
      "Turn On Sounds": "Zapnúť zvuky",
      "Unaffiliated": "Nezávislý",
      "Uncategorised": "Nekategorizovaný",
      "Unconfirmed": "Nepotrvrdené",
      "Unknown": "Neznáme",
      "Unsure": "Nie som si istý/á",
      "Use classic ballot UI": "Použiť klasické UI ballotu",
      "Use slider ballot UI": "Použiť slider UI ballotu",
      "Which team won the debate:": "Ktorý tím vyhral debatu:",
      "Won": "Výhra",
      "Yes": "Ano",
      "You cannot confirm this ballot because you entered it": "Tento ballot nemôžete potvrdiť, pretože ste ho vyplnili",
      "adjudicators with gender data": "rozhodcovia s údajmi o rode",
      "decimal marks are allowed": "desatinné body sú povolené",
      "feedback scores total": "celkové skóre spätnej väzby",
      "no ½ marks": "bez polbodov",
      "saving...": "ukladám..",
      "speaker scores total": "celkové skóre rečníka",
      "speakers with gender data": "výsledky rečníkov s údajmi o pohlaví",
      "tab check": "kontrola tabu",
      "tab entry": "zadanie tabu",
      "½ marks are allowed": "polbody sú povolené"
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
