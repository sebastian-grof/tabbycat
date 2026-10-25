
'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = ((n%10==1 && n%100!=11) ? 0 : ((n%10 >= 2 && n%10 <=4 && (n%100 < 12 || n%100 > 14)) ? 1 : ((n%10 == 0 || (n%10 >= 5 && n%10 <=9)) || (n%100 >= 11 && n%100 <= 14)) ? 2 : 3));
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
      "\u0412\u044b\u0431\u0440\u0430\u043d %(sel)s \u0438\u0437 %(cnt)s",
      "\u0412\u044b\u0431\u0440\u0430\u043d\u043e %(sel)s \u0438\u0437 %(cnt)s",
      "\u0412\u044b\u0431\u0440\u0430\u043d\u043e %(sel)s \u0438\u0437 %(cnt)s",
      "\u0412\u044b\u0431\u0440\u0430\u043d\u043e %(sel)s \u0438\u0437 %(cnt)s"
    ],
    "%1 %2 from %3": "%1-%2 \u0438\u0437 %3",
    "%1 %2 from %3 %4": "%1 %2 \u0438\u0437 %3 %4",
    "%1 %2 from %3 on %4 (Chair)": "%1 %2 \u0438\u0437 %3 \u043d\u0430 %4 (\u0447\u044d\u0439\u0440)",
    "%1 %2 from %3 on %4 (Panellist)": "%1 %2 \u0438\u0437 %3 \u043d\u0430 %4 (\u0432\u0438\u043d\u0433)",
    "%1 %2 from %3 on %4 (Trainee)": "%1 %2 \u0438\u0437 %3 \u043d\u0430 %4 (\u0432\u0438\u043d\u0433 \u0431\u0435\u0437 \u043f\u0440\u0430\u0432\u0430 \u0433\u043e\u043b\u043e\u0441\u0430)",
    "%1 (%2) with identifier of %3": "%1 (%2) \u0441 \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u043e\u043c %3",
    "%1 (%2) with no assigned identifier": "%1 (%2) \u0431\u0435\u0437 \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u043d\u043e\u0433\u043e \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u0430",
    "%1 (%2, %3)": "%1 (%2, %3)",
    "%1 (Absent; id=%2)": "%1 (\u043e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0439; id=%2)",
    "%1 (Present; id=%2)": "%1 (\u043f\u0440\u0438\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0439; id=%2)",
    "%1 (no category) with identifier of %2": "%1 (\u0431\u0435\u0437 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438) \u0441 \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u043e\u043c %2",
    "%1 (no category) with no assigned identifier": "%1 (\u043d\u0435\u0442 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438) \u0431\u0435\u0437 \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u043d\u043e\u0433\u043e \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u0430",
    "%1 checked in %2: %3": "%1\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d \u0432 %2: %3",
    "%1, %2": "%1, %2",
    "%1, a %2": "%1, %2",
    "%1, a %2 from %3 with identifier of %4": "%1, %2 \u0438\u0437 %3 \u0441 \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u043e\u043c %4",
    "%1, a %2 from %3 with no assigned identifier": "%1, %2 \u0438\u0437 %3 \u0431\u0435\u0437 \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u043d\u043e\u0433\u043e \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u0430",
    "%1, a %2 of no institutional affiliation with identifier of %3": "%1, %2 \u043d\u0435 \u0441\u0443\u0449\u0435\u0441\u0442\u0432\u0443\u0435\u0442 \u0438\u043d\u0441\u0442\u0438\u0442\u0443\u0446\u0438\u043e\u043d\u0430\u043b\u044c\u043d\u043e\u0439 \u0430\u0444\u0444\u0438\u043b\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u043e\u0441\u0442\u0438 \u0441 \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u043e\u043c %3",
    "%1, a %2 of no institutional affiliation with no assigned identifier": "%1, %2 \u043d\u0435 \u0441\u0443\u0449\u0435\u0441\u0442\u0432\u0443\u0435\u0442 \u0438\u043d\u0441\u0442\u0438\u0442\u0443\u0446\u0438\u043e\u043d\u0430\u043b\u044c\u043d\u043e\u0439 \u0430\u0444\u0444\u0438\u043b\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u043e\u0441\u0442\u0438 \u043d\u0438 \u0441 \u043e\u0434\u043d\u0438\u043c \u0438\u0437 \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u043e\u0432",
    "%1, a team with speakers %2": "%1, \u043a\u043e\u043c\u0430\u043d\u0434\u0430 \u0441\u043e \u0441\u043f\u0438\u043a\u0435\u0440\u0430\u043c\u0438 %2",
    "%1:": "%1:",
    "%s event": [
      "%s udalos\u0165",
      "%s udalosti",
      "%s udalosti",
      "%s udalost\u00ed"
    ],
    "%s selected option not visible": [
      "%s \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0439 \u043e\u0431\u044a\u0435\u043a\u0442 \u043d\u0435 \u0432\u0438\u0434\u0435\u043d",
      "%s \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0445 \u043e\u0431\u044a\u0435\u043a\u0442\u0430 \u043d\u0435 \u0432\u0438\u0434\u043d\u044b",
      "%s \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0445 \u043e\u0431\u044a\u0435\u043a\u0442\u043e\u0432 \u043d\u0435 \u0432\u0438\u0434\u043d\u044b",
      "%s \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0445 \u043e\u0431\u044a\u0435\u043a\u0442\u043e\u0432 \u043d\u0435 \u0432\u0438\u0434\u043d\u044b"
    ],
    "(click to clear)": "(\u043d\u0430\u0436\u043c\u0438\u0442\u0435, \u0447\u0442\u043e\u0431\u044b \u043e\u0447\u0438\u0441\u0442\u0438\u0442\u044c)",
    "6 a.m.": "6 \u0443\u0442\u0440\u0430",
    "6 p.m.": "6 \u0432\u0435\u0447\u0435\u0440\u0430",
    "; ": "; ",
    "<strong>%1</strong>: %2": "<strong>%1</strong>: %2",
    "<strong>\u2613</strong> All": "<strong>X</strong> \u0412\u0441\u0435",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> \u0412\u0441\u0435",
    "Active": "Akt\u00edvna",
    "Add": "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c",
    "Add Ballot": "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0431\u044d\u043b\u043b\u043e\u0442",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicating with %1.": "\u0421\u0443\u0434\u0438\u0442 \u0441 %1.",
    "Adjudicator Demographics": "\u0414\u0435\u043c\u043e\u0433\u0440\u0430\u0444\u0438\u044f \u0441\u0443\u0434\u0435\u0439",
    "Adjudicator Results": "\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b \u0441\u0443\u0434\u0435\u0439",
    "Aff Veto": "\u0412\u0435\u0442\u043e \u0443\u0442\u0432",
    "All": "\u0412\u0441\u0435",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "\u0410\u043d\u043e\u043d\u0438\u043c",
    "Anonymous (due to team codes)": "\u0410\u043d\u043e\u043d\u0438\u043c\u043d\u044b\u0435 (\u0438\u0437-\u0437\u0430 \u043a\u043e\u0434\u043e\u0432 \u043a\u043e\u043c\u0430\u043d\u0434\u044b)",
    "April": "\u0410\u043f\u0440\u0435\u043b\u044c",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "\u0410\u0432\u0433\u0443\u0441\u0442",
    "Auto-Allocate": "\u0420\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442\u044c \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-Prioritise": "\u0410\u0432\u0442\u043e\u043f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 %s",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0431\u044d\u043b\u043b\u043e\u0442\u043e\u0432",
    "Ballot Statuses": "\u0421\u0442\u0430\u0442\u0443\u0441 \u0431\u044d\u043b\u043b\u043e\u0442\u043e\u0432",
    "Ballots Status": "\u0421\u0442\u0430\u0442\u0443\u0441 \u0431\u044d\u043b\u043b\u043e\u0442\u043e\u0432",
    "Break": "\u0411\u0440\u0435\u0439\u043a",
    "By ": "Od ",
    "By %1": "\u041d\u0430 %1",
    "By how many points did they win:": "\u041d\u0430 \u0441\u043a\u043e\u043b\u044c\u043a\u043e \u043e\u0447\u043a\u043e\u0432 \u043e\u043d\u0438 \u0432\u044b\u0438\u0433\u0440\u0430\u043b\u0438:",
    "Cancel": "\u041e\u0442\u043c\u0435\u043d\u0430",
    "Category": "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f",
    "Chair": "Chair",
    "Chair for Panel of %1": "\u0427\u044d\u0439\u0440 \u043a\u043e\u043b\u043b\u0435\u0433\u0438\u0438 %1",
    "Check time": "Skontrolujte \u010das",
    "Checked-In": "\u0417\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b",
    "Choose": "Vybra\u0165",
    "Choose %s by selecting them and then select the \"Choose\" arrow button.": "\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u0435 \u044d\u043b\u0435\u043c\u0435\u043d\u0442\u044b \u0432 \u0441\u043f\u0438\u0441\u043a\u0435 \"%s\" \u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u0441\u043e \u0441\u0442\u0440\u0435\u043b\u043a\u043e\u0439 \u0432\u043f\u0440\u0430\u0432\u043e, \u0447\u0442\u043e\u0431\u044b \u0434\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0438\u0445 \u043a \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u043c.",
    "Choose a Date": "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0430\u0442\u0443",
    "Choose a Time": "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0432\u0440\u0435\u043c\u044f",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0432\u0440\u0435\u043c\u044f",
    "Choose all": "Vybra\u0165 v\u0161etko",
    "Choose all %s": "\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0432\u0441\u0435 %s",
    "Choose selected %s": "\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u043e\u0442\u043c\u0435\u0447\u0435\u043d\u043d\u044b\u0435 %s",
    "Chosen %s": "\u0412\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0435 %s",
    "Circle %1": "\u041a\u0440\u0443\u0433 %1",
    "Circle Rank:": "\u041e\u043a\u0440\u0443\u0433\u043b\u0435\u043d\u043d\u043e\u0435 \u043c\u0435\u0441\u0442\u043e:",
    "Circle the last digit of the %1's score:": "\u041e\u043a\u0440\u0443\u0433\u043b\u0438\u0442\u044c \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u044e\u044e \u0446\u0438\u0444\u0440\u0443 %1 \u0431\u0430\u043b\u043b\u0430:",
    "Circle the last digit of the team's total:": "\u041e\u043a\u0440\u0443\u0433\u043b\u0438\u0442\u044c \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u044e\u044e \u0446\u0438\u0444\u0440\u0443 \u043e\u0431\u0449\u0435\u0433\u043e \u0431\u0430\u043b\u043b\u0430 \u043a\u043e\u043c\u0430\u043d\u0434\u044b:",
    "Click to check-in manually": "\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u0434\u043b\u044f \u0442\u043e\u0433\u043e, \u0447\u0442\u043e\u0431\u044b \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0432\u0440\u0443\u0447\u043d\u0443\u044e",
    "Click to choose all %s at once.": "Kliknite sem pre vybratie v\u0161etk\u00fdch %s naraz.",
    "Click to remove all chosen %s at once.": "Kliknite sem pre vymazanie vybrat\u00fdch %s naraz.",
    "Click to undo a check-in": "\u041d\u0430\u0436\u043c\u0438\u0442\u0435, \u0447\u0442\u043e\u0431\u044b \u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044e",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Confirmed": "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043d\u044b\u0435",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Copy From Check-Ins": "\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0438\u0437 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0439",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "Debated": "\u0414\u0435\u0431\u0430\u0442\u0438\u0440\u043e\u0432\u0430\u043b\u0430",
    "December": "\u0414\u0435\u043a\u0430\u0431\u0440\u044c",
    "Delete": "\u0423\u0434\u0430\u043b\u0438\u0442\u044c",
    "Delete this folder?": "Vymaza\u0165 tento prie\u010dinok?",
    "Delete this folder? Its contents will move up to the level above.": "Vymaza\u0165 tento prie\u010dinok? Jeho obsah sa presunie o \u00farove\u0148 vy\u0161\u0161ie.",
    "Description": "Popis",
    "Did %1 deliver the adjudication?": "%1 \u043f\u043e\u0441\u0443\u0434\u0438\u043b?",
    "Direct Allocate": "Priame pridelenie",
    "Discard all unsaved changes?": "Zahodi\u0165 v\u0161etky neulo\u017een\u00e9 zmeny?",
    "Discard changes": "Zahodi\u0165 zmeny",
    "Do not allocate panellists": "Nepride\u013eova\u0165 panelistov",
    "Do not allocate trainees": "Nepride\u013eova\u0165 shadows",
    "Duration": "Trvanie",
    "Empty \u2014 drag folders or tournaments here.": "Pr\u00e1zdne \u2014 presu\u0148te sem prie\u010dinky alebo turnaje.",
    "End": "Koniec",
    "Event type": "Typ udalosti",
    "Every tournament is filed into a folder.": "Ka\u017ed\u00fd turnaj je zaraden\u00fd do prie\u010dinka.",
    "February": "\u0424\u0435\u0432\u0440\u0430\u043b\u044c",
    "Filter": "\u0424\u0438\u043b\u044c\u0442\u0440",
    "Find in Table": "\u041d\u0430\u0439\u0442\u0438 \u0432 \u0442\u0430\u0431\u043b\u0438\u0446\u0435",
    "Folders": "Prie\u010dinky",
    "Friday": "\u041f\u044f\u0442\u043d\u0438\u0446\u0430",
    "Gender": "\u0413\u0435\u043d\u0434\u0435\u0440",
    "General": "\u041e\u0431\u0449\u0435\u0435",
    "Hidden": "Skryt\u00e9",
    "Hide": "Skry\u0165",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "ID %1,": "ID %1,",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "\u0412\u0410\u0416\u041d\u041e: \u0443\u0431\u0435\u0434\u0438\u0442\u0435\u0441\u044c \u0438 \u0441\u0434\u0435\u043b\u0430\u0439\u0442\u0435 \u043e\u0442\u043c\u0435\u0442\u043a\u0443 \u0435\u0441\u0442\u044c \u0441\u043f\u0438\u043a\u0435\u0440 \u043f\u0440\u043e\u0438\u0437\u043d\u043e\u0441\u0438\u0442 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0440\u0435\u0447\u0435\u0439",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "\u0415\u0441\u043b\u0438 \u0432\u044b \u0445\u043e\u0442\u0438\u0442\u0435 \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u044d\u0442\u0443 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0443 \u0431\u0435\u0437 \u0431\u043e\u043a\u043e\u0432\u043e\u0439 \u043f\u0430\u043d\u0435\u043b\u0438 (\u0442.\u0435. \u0434\u043b\u044f \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f \u0434\u043b\u044f \u0430\u0443\u0434\u0438\u0442\u043e\u0440\u0438\u0438), \u0432\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442-\u0432\u0435\u0440\u0441\u0438\u044e.",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "\u041d\u0435\u0437\u0430\u0432\u0438\u0441\u0438\u043c\u044b\u0439",
    "Institution": "Debatn\u00fd klub",
    "January": "\u042f\u043d\u0432\u0430\u0440\u044c",
    "July": "\u0418\u044e\u043b\u044c",
    "June": "\u0418\u044e\u043d\u044c",
    "Latest Actions": "\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f",
    "Latest Results": "\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0435 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "\u041c\u0430\u0440\u0442",
    "Mark replies %1 to %2; <strong>%3</strong>.": "\u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u043e\u0442\u0432\u0435\u0442\u044b %1 \u043d\u0430 %2; <strong>%3</strong>.",
    "Mark speeches %1 to %2; <strong>%3</strong>.": "\u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u0440\u0435\u0447\u0438 \u043e\u0442 %1 \u0434\u043e %2; <strong>%3</strong>.",
    "Match": "\u0421\u043e\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0435",
    "Match Check-Ins": "\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0441\u043e\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0439",
    "May": "\u041c\u0430\u0439",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "\u041f\u043e\u043b\u043d\u043e\u0447\u044c",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "\u041f\u043e\u043d\u0435\u0434\u0435\u043b\u044c\u043d\u0438\u043a",
    "Motion is:": "T\u00e9za je:",
    "N/A": "N/A",
    "Needs a date": "Ch\u00fdba d\u00e1tum",
    "Neg Veto": "\u0412\u0435\u0442\u043e \u043e\u0442\u0440",
    "New folder": "Nov\u00fd prie\u010dinok",
    "New schedule day": "Nov\u00fd de\u0148 rozvrhu",
    "No": "\u041d\u0435\u0442",
    "No ": "Nie ",
    "No Actions Yet": "\u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0439",
    "No Adjudicator Ratings Information": "\u041d\u0435\u0442 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438 \u043e \u0440\u0435\u0439\u0442\u0438\u043d\u0433\u0430\u0445 \u0441\u0443\u0434\u0435\u0439",
    "No Adjudicator-Adjudicator Feedback Information": "\u041d\u0435\u0442 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438 \u043e\u0431 \u043e\u0431\u0440\u0430\u0442\u043d\u043e\u0439 \u0441\u0432\u044f\u0437\u0438 \u0441\u0443\u0434\u0435\u0439 \u0434\u0440\u0443\u0433 \u0434\u043b\u044f \u0434\u0440\u0443\u0433\u0430",
    "No Category": "\u041d\u0435\u0442 \u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438",
    "No Confirmed Results Yet": "\u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043d\u044b\u0445 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u043e\u0432",
    "No Gender Information": "\u041d\u0435\u0442 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438 \u043e \u0433\u0435\u043d\u0434\u0435\u0440\u0430\u0445",
    "No Position Information": "\u041d\u0435\u0442 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438 \u043e \u043f\u043e\u0437\u0438\u0446\u0438\u044f\u0445",
    "No Region Information": "\u041d\u0435\u0442 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438 \u043e \u0440\u0435\u0433\u0438\u043e\u043d\u0430\u0445",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "\u041d\u0435\u0442 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438 \u043e \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\u0445 \u0441\u043f\u0438\u043a\u0435\u0440\u043e\u0432",
    "No changes": "\u0411\u0435\u0437 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0439",
    "No code name set": "\u041d\u0435 \u0437\u0430\u0434\u0430\u043d\u043e \u043a\u043e\u0434\u043e\u0432\u043e\u0435 \u0438\u043c\u044f",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0445 \u043b\u044e\u0434\u0435\u0439.",
    "No matching rooms found.": "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0445 \u0430\u0443\u0434\u0438\u0442\u043e\u0440\u0438\u0439.",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "\u041d\u0435\u0442, \u044f \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u044f\u044e \u043e\u0431\u0440\u0430\u0442\u043d\u0443\u044e \u0441\u0432\u044f\u0437\u044c \u043d\u0430:",
    "Noon": "\u041f\u043e\u043b\u0434\u0435\u043d\u044c",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Not Checked-In": "\u041d\u0435 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u043f\u0435\u0440\u0435\u0436\u0430\u0435\u0442 \u0432\u0440\u0435\u043c\u044f \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441.",
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u043f\u0435\u0440\u0435\u0436\u0430\u0435\u0442 \u0432\u0440\u0435\u043c\u044f \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441\u0430.",
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u043f\u0435\u0440\u0435\u0436\u0430\u0435\u0442 \u0432\u0440\u0435\u043c\u044f \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441\u043e\u0432.",
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u043f\u0435\u0440\u0435\u0436\u0430\u0435\u0442 \u0432\u0440\u0435\u043c\u044f \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441\u043e\u0432."
    ],
    "Note: You are %s hour behind server time.": [
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u0442\u0441\u0442\u0430\u0451\u0442 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u043d\u0438 \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441.",
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u0442\u0441\u0442\u0430\u0451\u0442 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u043d\u0438 \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441\u0430.",
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u0442\u0441\u0442\u0430\u0451\u0442 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u043d\u0438 \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441\u043e\u0432.",
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0430\u0448\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u043e\u0442\u0441\u0442\u0430\u0451\u0442 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u043d\u0438 \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043d\u0430 %s \u0447\u0430\u0441\u043e\u0432."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "\u041d\u043e\u044f\u0431\u0440\u044c",
    "Now": "\u0421\u0435\u0439\u0447\u0430\u0441",
    "October": "\u041e\u043a\u0442\u044f\u0431\u0440\u044c",
    "Open": "Open",
    "Open the assistant version.": "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442-\u0432\u0435\u0440\u0441\u0438\u044e.",
    "Order": "Poradie",
    "Panellist": "\u0412\u0438\u043d\u0433",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Priority %1": "\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442 %1",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank": "\u041c\u0435\u0441\u0442\u043e",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Region": "\u0420\u0435\u0433\u0438\u043e\u043d",
    "Remove": "Odstr\u00e1ni\u0165",
    "Remove %s by selecting them and then select the \"Remove\" arrow button.": "\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u0435 \u044d\u043b\u0435\u043c\u0435\u043d\u0442\u044b \u0432 \u0441\u043f\u0438\u0441\u043a\u0435 \"%s\" \u0438 \u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u0441\u0442\u0440\u0435\u043b\u043a\u0443 \u0432\u043b\u0435\u0432\u043e, \u0447\u0442\u043e\u0431\u044b \u0443\u0431\u0440\u0430\u0442\u044c \u0438\u0445 \u0438\u0437 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0445.",
    "Remove all": "Odstr\u00e1ni\u0165 v\u0161etky",
    "Remove all %s": "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0432\u0441\u0435 %s",
    "Remove selected %s": "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043e\u0442\u043c\u0435\u0447\u0435\u043d\u043d\u044b\u0435 %s",
    "Return ballots to %1.": "\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0431\u044d\u043b\u043b\u043e\u0442\u044b \u0432 %1.",
    "Return to Draw": "\u0412\u0435\u0440\u043d\u0443\u0442\u044c\u0441\u044f \u043a \u0441\u0435\u0442\u043a\u0435",
    "Review": "\u041e\u0431\u0437\u043e\u0440",
    "Room:": "\u0410\u0443\u0434\u0438\u0442\u043e\u0440\u0438\u044f:",
    "Round": "Kolo",
    "Saturday": "\u0421\u0443\u0431\u0431\u043e\u0442\u0430",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "\u0421\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u043c\u0435\u0440\u043e\u0439",
    "Score:": "\u041e\u0446\u0435\u043d\u043a\u0430:",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "\u0421\u0435\u043d\u0442\u044f\u0431\u0440\u044c",
    "Set All Breaking as Available": "\u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u0432\u0441\u0435\u0445 \u0431\u0440\u0435\u0439\u043a\u0430\u044e\u0449\u0438\u0445\u0441\u044f \u043a\u0430\u043a \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Set all availabilities to exactly match check-ins.": "\u0423\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0441\u0442\u044c, \u0447\u0442\u043e\u0431\u044b \u043e\u043d\u0430 \u0441\u043e\u0432\u043f\u0430\u0434\u0430\u043b\u0430 \u0441 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f\u043c\u0438.",
    "Set all the availabilities to exactly match what they were in the previous round.": "\u0423\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0441\u0442\u044c \u0442\u043e\u0447\u043d\u043e \u0442\u0430\u043a \u0436\u0435, \u043a\u0430\u043a \u0432 \u043f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0435\u043c \u0440\u0430\u0443\u043d\u0434\u0435.",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "\u0423\u0441\u0442\u0430\u043d\u0430\u0432\u043b\u0438\u0432\u0430\u0439\u0442\u0435 \u043b\u044e\u0434\u0435\u0439 \u043a\u0430\u043a \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u0442\u043e\u043b\u044c\u043a\u043e \u0435\u0441\u043b\u0438 \u043e\u043d\u0438 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043b\u0438\u0441\u044c \u0438 \u0432 \u0434\u0430\u043d\u043d\u044b\u0439 \u043c\u043e\u043c\u0435\u043d\u0442 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b - \u0442.\u043a. \u044d\u0442\u043e \u043d\u0435 \u043d\u0430\u043b\u043e\u0436\u0438\u0442\u0441\u044f \u043d\u0430 \u0443\u0436\u0435 \u0441\u0443\u0449\u0435\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0435 \u043f\u043e\u043a\u0430\u0437\u0430\u0442\u0435\u043b\u0438 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0441\u0442\u0438.",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "Zobrazi\u0165",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "\u0427\u044d\u0439\u0440 \u043e\u0434\u0438\u043d",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "\u0414\u0435\u043c\u043e\u0433\u0440\u0430\u0444\u0438\u044f \u0441\u043f\u0438\u043a\u0435\u0440\u043e\u0432",
    "Speaker Results": "\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b \u0441\u043f\u0438\u043a\u0435\u0440\u043e\u0432",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "\u041e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u043a\u0430\u043c\u0435\u0440\u043e\u0439",
    "Sunday": "\u0412\u043e\u0441\u043a\u0440\u0435\u0441\u0435\u043d\u044c\u0435",
    "Team": "\u041a\u043e\u043c\u0430\u043d\u0434\u0430",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "The bracket range of the hypothetical debate": "\u0414\u0438\u0430\u043f\u0430\u0437\u043e\u043d \u0431\u0430\u043b\u043b\u043e\u0432 \u0433\u0438\u043f\u043e\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u0434\u0435\u0431\u0430\u0442\u043e\u0432",
    "The debate's bracket": "\u0411\u0430\u043b\u043b\u044b \u043a\u043e\u043c\u0430\u043d\u0434 \u0432 \u044d\u0442\u0438\u0445 \u0434\u0435\u0431\u0430\u0442\u0430\u0445",
    "The estimated total number of live break categories across all teams of the hypothetical debate": "\u041f\u0440\u0435\u0434\u043f\u043e\u043b\u0430\u0433\u0430\u0435\u043c\u043e\u0435 \u043e\u0431\u0449\u0435\u0435 \u0447\u0438\u0441\u043b\u043e \u0432\u0441\u0435\u0445 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u0431\u0440\u0435\u0439\u043a\u043e\u0432\u044b\u0445 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0439 \u0434\u043b\u044f \u0432\u0441\u0435\u0445 \u043a\u043e\u043c\u0430\u043d\u0434 \u0433\u0438\u043f\u043e\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u0434\u0435\u0431\u0430\u0442\u043e\u0432",
    "The motion is <em>%1</em>": "\u0422\u0435\u043c\u0430 <em>%1</em>",
    "The total number of live break categories across all teams": "\u041e\u0431\u0449\u0435\u0435 \u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u0431\u0440\u0435\u0439\u043a\u043e\u0432\u044b\u0445 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0439 \u0434\u043b\u044f \u0432\u0441\u0435\u0445 \u043a\u043e\u043c\u0430\u043d\u0434",
    "This debate's priority": "\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442 \u044d\u0442\u0438\u0445 \u0434\u0435\u0431\u0430\u0442\u043e\u0432",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre v\u00fdber je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVybra\u0165\u201c presun\u00fa\u0165.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre vymazanie je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVymaza\u0165\u201c vymaza\u0165.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "\u042d\u0442\u0430 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0430 \u0431\u0443\u0434\u0435\u0442 \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043e\u0431\u043d\u043e\u0432\u043b\u044f\u0442\u044c\u0441\u044f \u0441 \u043d\u043e\u0432\u044b\u043c\u0438 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f\u043c\u0438 \u043f\u043e \u043c\u0435\u0440\u0435 \u0442\u043e\u0433\u043e, \u043a\u0430\u043a \u043e\u043d\u0438 \u0431\u0443\u0434\u0443\u0442 \u043f\u043e\u0441\u0442\u0443\u043f\u0430\u0442\u044c, \u0445\u043e\u0442\u044f \u0438\u0437\u043d\u0430\u0447\u0430\u043b\u044c\u043d\u044b\u0439 \u0441\u043f\u0438\u0441\u043e\u043a \u043c\u043e\u0436\u0435\u0442 \u0431\u044b\u0442\u044c \u043c\u0438\u043d\u0443\u0442\u043d\u043e\u0439 \u0434\u0430\u0432\u043d\u043e\u0441\u0442\u0438.",
    "This person does not have a check-in identifier so they can't be checked in": "\u0423 \u044d\u0442\u043e\u0433\u043e \u0447\u0435\u043b\u043e\u0432\u0435\u043a\u0430 \u043d\u0435\u0442 \u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u0430 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438, \u0442\u0430\u043a \u0447\u0442\u043e \u043e\u043d \u043d\u0435 \u0431\u044b\u043b \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d",
    "Thursday": "\u0427\u0435\u0442\u0432\u0435\u0440\u0433",
    "Today": "\u0421\u0435\u0433\u043e\u0434\u043d\u044f",
    "Tomorrow": "\u0417\u0430\u0432\u0442\u0440\u0430",
    "Total:": "\u0412\u0441\u0435\u0433\u043e:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "\u0412\u0438\u043d\u0433 \u0431\u0435\u0437 \u043f\u0440\u0430\u0432\u0430 \u0433\u043e\u043b\u043e\u0441\u0430",
    "Tuesday": "\u0412\u0442\u043e\u0440\u043d\u0438\u043a",
    "Turn On Sounds": "\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0437\u0432\u0443\u043a",
    "Type into this box to filter down the list of available %s.": "\u041d\u0430\u0447\u043d\u0438\u0442\u0435 \u0432\u0432\u043e\u0434\u0438\u0442\u044c \u0442\u0435\u043a\u0441\u0442 \u0432 \u044d\u0442\u043e\u043c \u043f\u043e\u043b\u0435, \u0447\u0442\u043e\u0431\u044b \u043e\u0442\u0444\u0438\u0442\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 %s.",
    "Type into this box to filter down the list of selected %s.": "\u041d\u0430\u0431\u0438\u0440\u0430\u0439\u0442\u0435 \u0441\u0438\u043c\u0432\u043e\u043b\u044b \u0432 \u044d\u0442\u043e\u043c \u043f\u043e\u043b\u0435, \u0447\u0442\u043e\u0431\u044b \u043e\u0442\u0444\u0438\u043b\u044c\u0442\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0445 %s.",
    "Unaffiliated": "\u041d\u0435\u0430\u0444\u0444\u0438\u043b\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised": "\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0430 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unconfirmed": "\u041d\u0435 \u043f\u043e\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043e",
    "Unknown": "\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "\u041d\u0435 \u0442\u043e\u0447\u043d\u043e",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Warning: you have unsaved changes": "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0443 \u0432\u0430\u0441 \u0435\u0441\u0442\u044c \u043d\u0435\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043d\u044b\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f",
    "Wednesday": "\u0421\u0440\u0435\u0434\u0430",
    "Which team won the debate:": "\u041a\u0430\u043a\u0430\u044f \u043a\u043e\u043c\u0430\u043d\u0434\u0430 \u0432\u044b\u0438\u0433\u0440\u0430\u043b\u0430 \u0434\u0435\u0431\u0430\u0442\u044b:",
    "Yes": "\u0414\u0430",
    "Yesterday": "\u0412\u0447\u0435\u0440\u0430",
    "You cannot confirm this ballot because you entered it": "\u0412\u044b \u043d\u0435 \u043c\u043e\u0436\u0435\u0442\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c \u044d\u0442\u043e\u0442 \u0431\u044d\u043b\u043b\u043e\u0442, \u043f\u043e\u0442\u043e\u043c\u0443 \u0447\u0442\u043e \u0441\u0430\u043c\u0438 \u0432\u0432\u0435\u043b\u0438 \u0435\u0433\u043e",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "\u0412\u044b \u0432\u044b\u0431\u0440\u0430\u043b\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435 \u0438 \u043d\u0435 \u0432\u043d\u0435\u0441\u043b\u0438 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0439 \u0432 \u0434\u0430\u043d\u043d\u044b\u0435. \u0412\u043e\u0437\u043c\u043e\u0436\u043d\u043e, \u0432\u044b \u0445\u043e\u0442\u0435\u043b\u0438 \u0432\u043e\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c\u0441\u044f \u043a\u043d\u043e\u043f\u043a\u043e\u0439 \"\u0412\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c\", \u0430 \u043d\u0435 \u043a\u043d\u043e\u043f\u043a\u043e\u0439 \"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c\". \u0415\u0441\u043b\u0438 \u044d\u0442\u043e \u0442\u0430\u043a, \u0442\u043e \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \"\u041e\u0442\u043c\u0435\u043d\u0430\", \u0447\u0442\u043e\u0431\u044b \u0432\u0435\u0440\u043d\u0443\u0442\u044c\u0441\u044f \u0432 \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441 \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "\u0412\u044b \u0432\u044b\u0431\u0440\u0430\u043b\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435, \u043d\u043e \u0435\u0449\u0435 \u043d\u0435 \u0441\u043e\u0445\u0440\u0430\u043d\u0438\u043b\u0438 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f, \u0432\u043d\u0435\u0441\u0435\u043d\u043d\u044b\u0435 \u0432 \u043d\u0435\u043a\u043e\u0442\u043e\u0440\u044b\u0445 \u043f\u043e\u043b\u044f\u0445 \u0434\u043b\u044f \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f. \u041d\u0430\u0436\u043c\u0438\u0442\u0435 OK, \u0447\u0442\u043e\u0431\u044b \u0441\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f. \u041f\u043e\u0441\u043b\u0435 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f \u0432\u0430\u043c \u043f\u0440\u0438\u0434\u0435\u0442\u0441\u044f \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435 \u0435\u0449\u0435 \u0440\u0430\u0437.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0418\u043c\u0435\u044e\u0442\u0441\u044f \u043d\u0435\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043d\u044b\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0432 \u043e\u0442\u0434\u0435\u043b\u044c\u043d\u044b\u0445 \u043f\u043e\u043b\u044f\u0445 \u0434\u043b\u044f \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f. \u0415\u0441\u043b\u0438 \u0432\u044b \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435, \u043d\u0435\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043d\u044b\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0431\u0443\u0434\u0443\u0442 \u043f\u043e\u0442\u0435\u0440\u044f\u043d\u044b.",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "\u041f\u0442",
    "abbrev. day Monday\u0004Mon": "\u041f\u043d",
    "abbrev. day Saturday\u0004Sat": "\u0421\u0431",
    "abbrev. day Sunday\u0004Sun": "\u0412\u0441",
    "abbrev. day Thursday\u0004Thur": "\u0427\u0442",
    "abbrev. day Tuesday\u0004Tue": "\u0412\u0442",
    "abbrev. day Wednesday\u0004Wed": "\u0421\u0440",
    "abbrev. month April\u0004Apr": "\u0410\u043f\u0440",
    "abbrev. month August\u0004Aug": "\u0410\u0432\u0433",
    "abbrev. month December\u0004Dec": "\u0414\u0435\u043a",
    "abbrev. month February\u0004Feb": "\u0424\u0435\u0432",
    "abbrev. month January\u0004Jan": "\u042f\u043d\u0432",
    "abbrev. month July\u0004Jul": "\u0418\u044e\u043b",
    "abbrev. month June\u0004Jun": "\u0418\u044e\u043d",
    "abbrev. month March\u0004Mar": "\u041c\u0430\u0440",
    "abbrev. month May\u0004May": "\u041c\u0430\u0439",
    "abbrev. month November\u0004Nov": "\u041d\u043e\u044f",
    "abbrev. month October\u0004Oct": "\u041e\u043a\u0442",
    "abbrev. month September\u0004Sep": "\u0421\u0435\u043d",
    "adjudicators with gender data": "\u0441\u0443\u0434\u044c\u0438 \u0441 \u0434\u0430\u043d\u043d\u044b\u043c\u0438 \u043e \u0433\u0435\u043d\u0434\u0435\u0440\u0435",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "\u0434\u0435\u0441\u044f\u0442\u0438\u0447\u043d\u044b\u0435 \u043e\u0446\u0435\u043d\u043a\u0438 \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u044b",
    "deselect all": "\u0443\u0431\u0440\u0430\u0442\u044c \u0432\u0441\u0435",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "feedback scores total": "\u043e\u0431\u0449\u0438\u0439 \u0431\u0430\u043b\u043b \u043f\u043e \u043e\u0431\u0440\u0430\u0442\u043d\u043e\u0439 \u0441\u0432\u044f\u0437\u0438",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "\u043d\u0435 \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u044b \u043e\u0446\u0435\u043d\u043a\u0438 1/2",
    "one letter Friday\u0004F": "\u041f",
    "one letter Monday\u0004M": "\u041f",
    "one letter Saturday\u0004S": "\u0421",
    "one letter Sunday\u0004S": "\u0412",
    "one letter Thursday\u0004T": "\u0427",
    "one letter Tuesday\u0004T": "\u0412",
    "one letter Wednesday\u0004W": "\u0421",
    "optional": "nepovinn\u00e9",
    "saving...": "\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435...",
    "select all": "\u0432\u044b\u0431\u0440\u0430\u0442\u044c \u0432\u0441\u0435",
    "speaker scores analysed": "analyzovan\u00fdch sk\u00f3re re\u010dn\u00edkov",
    "speaker scores total": "\u043e\u0431\u0449\u0438\u0439 \u0441\u043f\u0438\u043a\u0435\u0440\u0441\u043a\u0438\u0439 \u0431\u0430\u043b\u043b",
    "speakers with gender data": "\u0441\u043f\u0438\u043a\u0435\u0440\u044b \u0441 \u0434\u0430\u043d\u043d\u044b\u043c\u0438 \u043f\u043e \u0433\u0435\u043d\u0434\u0435\u0440\u0443",
    "tab check": "\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0442\u044d\u0431\u0430",
    "tab entry": "\u0432\u0432\u0435\u0434\u0435\u043d\u0438\u0435 \u0442\u044d\u0431\u0430",
    "tournament": "turnaj",
    "tournaments": "turnaje",
    "unconfirmed": "nepotvrden\u00e9",
    "\u00bd marks are allowed": "\u043e\u0446\u0435\u043d\u043a\u0438 1/2 \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u044b",
    "\u2613 All": "\u2613 V\u0161etky",
    "\u2713 All": "\u2713 V\u0161etky"
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
    "DATETIME_FORMAT": "j E Y \u0433. G:i",
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S",
      "%d.%m.%Y %H:%M:%S.%f",
      "%d.%m.%Y %H:%M",
      "%d.%m.%y %H:%M:%S",
      "%d.%m.%y %H:%M:%S.%f",
      "%d.%m.%y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j E Y \u0433.",
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y",
      "%d.%m.%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y H:i",
    "SHORT_DATE_FORMAT": "d.m.Y",
    "THOUSAND_SEPARATOR": "\u00a0",
    "TIME_FORMAT": "G:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F Y \u0433."
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

