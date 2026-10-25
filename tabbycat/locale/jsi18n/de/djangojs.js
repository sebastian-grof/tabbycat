
'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n != 1);
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
      "%(sel)s von %(cnt)s ausgew\u00e4hlt",
      "%(sel)s von %(cnt)s ausgew\u00e4hlt"
    ],
    "%s event": [
      "%s udalos\u0165",
      "%s udalosti"
    ],
    "%s selected option not visible": [
      "%s ausgew\u00e4hlte Option nicht sichtbar",
      "%s ausgew\u00e4hlte Optionen nicht sichtbar"
    ],
    "6 a.m.": "6 Uhr",
    "6 p.m.": "18 Uhr",
    "; ": "; ",
    "Active": "Akt\u00edvna",
    "Add Ballot": "Prida\u0165 Ballot",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicator Demographics": "Demografia rozhodcov",
    "Adjudicator Results": "V\u00fdsledky rozhodcu",
    "All": "V\u0161etky",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "Anon",
    "Anonymous (due to team codes)": "Anonymn\u00e9 (kv\u00f4li t\u00edmov\u00fdm k\u00f3dom)",
    "April": "April",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "August",
    "Auto-Allocate": "Automatick\u00e9 pride\u013eovanie",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "Verf\u00fcgbare %s",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "Registr\u00e1cia ballotov",
    "Ballot Statuses": "Status Ballotov",
    "Ballots Status": "Status ballotov",
    "Break": "Break",
    "By ": "Od ",
    "By how many points did they win:": "O ko\u013eko bodov vyhrali:",
    "Cancel": "Abbrechen",
    "Category": "Kategorie",
    "Chair": "Chair",
    "Check time": "Skontrolujte \u010das",
    "Choose": "Ausw\u00e4hlen",
    "Choose a Date": "Datum w\u00e4hlen",
    "Choose a Time": "Uhrzeit w\u00e4hlen",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "Uhrzeit",
    "Choose all": "Alle ausw\u00e4hlen",
    "Chosen %s": "Ausgew\u00e4hlte %s",
    "Circle Rank:": "Zakr\u00fa\u017ekuj poradie:",
    "Circle the last digit of the team's total:": "Zakr\u00fa\u017ekuj posledn\u00fa \u010d\u00edslicu t\u00edmov\u00e9ho s\u00fa\u010dtu:",
    "Click to choose all %s at once.": "Klicken, um alle %s auf einmal auszuw\u00e4hlen.",
    "Click to remove all chosen %s at once.": "Klicken, um alle ausgew\u00e4hlten %s auf einmal zu entfernen.",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Confirmed": "Best\u00e4tigt",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "December": "Dezember",
    "Delete this folder?": "Vymaza\u0165 tento prie\u010dinok?",
    "Delete this folder? Its contents will move up to the level above.": "Vymaza\u0165 tento prie\u010dinok? Jeho obsah sa presunie o \u00farove\u0148 vy\u0161\u0161ie.",
    "Description": "Popis",
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
    "February": "Februar",
    "Filter": "Filter",
    "Folders": "Prie\u010dinky",
    "Friday": "Freitag",
    "Gender": "Geschlecht",
    "General": "Allgemein",
    "Hidden": "Skryt\u00e9",
    "Hide": "Ausblenden",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "D\u00d4LE\u017dIT\u00c9: Skontrolujte a explicitne zazna\u010dte, \u010di re\u010dn\u00edk prednesie viacero re\u010d\u00ed",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "Nez\u00e1visl\u00fd",
    "Institution": "Debatn\u00fd klub",
    "January": "Januar",
    "July": "Juli",
    "June": "Juni",
    "Latest Actions": "Najnov\u0161ie akcie",
    "Latest Results": "Najnov\u0161ie v\u00fdsledky",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "M\u00e4rz",
    "May": "Mai",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "Mitternacht",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "Montag",
    "Motion is:": "T\u00e9za je:",
    "N/A": "N/A",
    "Needs a date": "Ch\u00fdba d\u00e1tum",
    "New folder": "Nov\u00fd prie\u010dinok",
    "New schedule day": "Nov\u00fd de\u0148 rozvrhu",
    "No": "Nie",
    "No ": "Nie ",
    "No Actions Yet": "Zatia\u013e \u017eiadne akcie",
    "No Adjudicator Ratings Information": "\u017diadne inform\u00e1cie o hodnoteniach rozhodcov",
    "No Adjudicator-Adjudicator Feedback Information": "\u017diadne inform\u00e1cie o sp\u00e4tnej v\u00e4zbe rozhodca-rozhodca",
    "No Category": "Bez kateg\u00f3rie",
    "No Confirmed Results Yet": "Zatia\u013e \u017eiadne potvrden\u00e9 v\u00fdsledky",
    "No Gender Information": "\u017diadne inform\u00e1cie o rode",
    "No Position Information": "\u017diadne inform\u00e1cie o poz\u00edcii",
    "No Region Information": "\u017diadne inform\u00e1cie o regi\u00f3ne",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "\u017diadne inform\u00e1cie o kateg\u00f3ri\u00e1ch re\u010dn\u00edkov",
    "No code name set": "Nie je nastaven\u00e9 k\u00f3dov\u00e9 meno",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face osoby.",
    "No matching rooms found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face mietnosti.",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "Nie, odosielam sp\u00e4tn\u00fa v\u00e4zbu na:",
    "Noon": "Mittag",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "Achtung: Sie sind %s Stunde der Serverzeit vorraus.",
      "Achtung: Sie sind %s Stunden der Serverzeit vorraus."
    ],
    "Note: You are %s hour behind server time.": [
      "Achtung: Sie sind %s Stunde hinter der Serverzeit.",
      "Achtung: Sie sind %s Stunden hinter der Serverzeit."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "November",
    "Now": "Jetzt",
    "October": "Oktober",
    "Open": "Open",
    "Order": "Poradie",
    "Panellist": "Panelista",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank": "Rang",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "Op\u00e4tovn\u00e1 \u00faprava",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Region": "Region",
    "Remove": "Entfernen",
    "Remove all": "Alle entfernen",
    "Review": "Kontrola",
    "Room:": "Miestnos\u0165:",
    "Round": "Kolo",
    "Saturday": "Samstag",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "Skenovanie pomocou fotoapar\u00e1tu",
    "Score:": "Sk\u00f3re:",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "September",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "Einblenden",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "Samostatn\u00fd Chair",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "Demografia re\u010dn\u00edkov",
    "Speaker Results": "V\u00fdsledky re\u010dn\u00edkov",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "Zastavi\u0165 skenovanie fotoapar\u00e1tom",
    "Sunday": "Sonntag",
    "Team": "Team",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Dies ist die Liste der verf\u00fcgbaren %s. Einfach im unten stehenden Feld markieren und mithilfe des \u201eAusw\u00e4hlen\u201c-Pfeils ausw\u00e4hlen.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Dies ist die Liste der ausgew\u00e4hlten %s. Einfach im unten stehenden Feld markieren und mithilfe des \u201eEntfernen\u201c-Pfeils wieder entfernen.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "T\u00e1to str\u00e1nka sa bude aktualizova\u0165 v re\u00e1lnom \u010dase s nov\u00fdmi registr\u00e1ciami, ako sa bud\u00fa vyskytova\u0165, hoci po\u010diato\u010dn\u00fd zoznam m\u00f4\u017ee by\u0165 star\u00fd a\u017e jednu min\u00fatu.",
    "Thursday": "Donnerstag",
    "Today": "Heute",
    "Tomorrow": "Morgen",
    "Total:": "Gesamt:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "Trainee",
    "Tuesday": "Dienstag",
    "Turn On Sounds": "Zapn\u00fa\u0165 zvuky",
    "Type into this box to filter down the list of available %s.": "Durch Eingabe in diesem Feld l\u00e4sst sich die Liste der verf\u00fcgbaren %s eingrenzen.",
    "Type into this box to filter down the list of selected %s.": "In diesem Feld tippen, um die Liste der ausgew\u00e4hlten %s einzuschr\u00e4nken.",
    "Unaffiliated": "Unabh\u00e4ngig",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "Nie som si ist\u00fd/\u00e1",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Warning: you have unsaved changes": "Warnung: es gibt ungesicherte \u00c4nderungen",
    "Wednesday": "Mittwoch",
    "Which team won the debate:": "Ktor\u00fd t\u00edm vyhral debatu:",
    "Yes": "Ano",
    "Yesterday": "Gestern",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Sie haben eine Aktion ausgew\u00e4hlt, aber keine \u00c4nderungen an bearbeitbaren Feldern vorgenommen. Sie wollten wahrscheinlich auf \u201eAusf\u00fchren\u201c und nicht auf \u201eSpeichern\u201c klicken.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Sie haben eine Aktion ausgew\u00e4hlt, aber Ihre vorgenommenen \u00c4nderungen nicht gespeichert. Klicken Sie OK, um dennoch zu speichern. Danach m\u00fcssen Sie die Aktion erneut ausf\u00fchren.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Sie haben \u00c4nderungen an bearbeitbaren Feldern vorgenommen und nicht gespeichert. Wollen Sie die Aktion trotzdem ausf\u00fchren und Ihre \u00c4nderungen verwerfen?",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "Fr",
    "abbrev. day Monday\u0004Mon": "Mo",
    "abbrev. day Saturday\u0004Sat": "Sa",
    "abbrev. day Sunday\u0004Sun": "So",
    "abbrev. day Thursday\u0004Thur": "Do",
    "abbrev. day Tuesday\u0004Tue": "Di",
    "abbrev. day Wednesday\u0004Wed": "Mi",
    "abbrev. month April\u0004Apr": "Apr",
    "abbrev. month August\u0004Aug": "Aug",
    "abbrev. month December\u0004Dec": "Dez",
    "abbrev. month February\u0004Feb": "Feb",
    "abbrev. month January\u0004Jan": "Jan",
    "abbrev. month July\u0004Jul": "Jul",
    "abbrev. month June\u0004Jun": "Jun",
    "abbrev. month March\u0004Mar": "Mrz",
    "abbrev. month May\u0004May": "Mai",
    "abbrev. month November\u0004Nov": "Nov",
    "abbrev. month October\u0004Oct": "Okt",
    "abbrev. month September\u0004Sep": "Sep",
    "adjudicators with gender data": "rozhodcovia s \u00fadajmi o rode",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "desatinn\u00e9 body s\u00fa povolen\u00e9",
    "deselect all": "Alle abw\u00e4hlen",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "bez polbodov",
    "one letter Friday\u0004F": "Fr",
    "one letter Monday\u0004M": "Mo",
    "one letter Saturday\u0004S": "Sa",
    "one letter Sunday\u0004S": "So",
    "one letter Thursday\u0004T": "Do",
    "one letter Tuesday\u0004T": "Di",
    "one letter Wednesday\u0004W": "Mi",
    "optional": "nepovinn\u00e9",
    "select all": "Alle ausw\u00e4hlen",
    "speaker scores analysed": "analyzovan\u00fdch sk\u00f3re re\u010dn\u00edkov",
    "speakers with gender data": "v\u00fdsledky re\u010dn\u00edkov s \u00fadajmi o pohlav\u00ed",
    "tab check": "kontrola tabu",
    "tab entry": "zadanie tabu",
    "tournament": "turnaj",
    "tournaments": "turnaje",
    "unconfirmed": "nepotvrden\u00e9",
    "\u00bd marks are allowed": "polbody s\u00fa povolen\u00e9",
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
    "DATETIME_FORMAT": "j. F Y H:i",
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
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j. F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y H:i",
    "SHORT_DATE_FORMAT": "d.m.Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "H:i",
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

