
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
      "%(sel)s \u03b1\u03c0\u03cc %(cnt)s \u03b5\u03c0\u03b9\u03bb\u03b5\u03b3\u03bc\u03ad\u03bd\u03b1",
      "%(sel)s \u03b1\u03c0\u03cc %(cnt)s \u03b5\u03c0\u03b9\u03bb\u03b5\u03b3\u03bc\u03ad\u03bd\u03b1"
    ],
    "%s event": [
      "%s udalos\u0165",
      "%s udalosti"
    ],
    "%s selected option not visible": [
      "%s ozna\u010den\u00e1 mo\u017enos\u0165 sa nezobrazuje",
      "%s ozna\u010den\u00e9 mo\u017enosti sa nezobrazuj\u00fa"
    ],
    "6 a.m.": "6 \u03c0.\u03bc.",
    "6 p.m.": "6 \u03bc.\u03bc.",
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
    "April": "\u0391\u03c0\u03c1\u03af\u03bb\u03b9\u03bf\u03c2",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "\u0391\u03cd\u03b3\u03bf\u03c5\u03c3\u03c4\u03bf\u03c2",
    "Auto-Allocate": "Automatick\u00e9 pride\u013eovanie",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "\u0394\u03b9\u03b1\u03b8\u03ad\u03c3\u03b9\u03bc\u03bf %s",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "Registr\u00e1cia ballotov",
    "Ballot Statuses": "Status Ballotov",
    "Ballots Status": "Status ballotov",
    "By ": "Od ",
    "By how many points did they win:": "O ko\u013eko bodov vyhrali:",
    "Cancel": "\u0391\u03ba\u03cd\u03c1\u03c9\u03c3\u03b7",
    "Chair": "Chair",
    "Check time": "Skontrolujte \u010das",
    "Choose": "\u0395\u03c0\u03b9\u03bb\u03bf\u03b3\u03ae",
    "Choose a Date": "\u0395\u03c0\u03b9\u03bb\u03ad\u03be\u03c4\u03b5 \u03bc\u03b9\u03b1 \u0397\u03bc\u03b5\u03c1\u03bf\u03bc\u03b7\u03bd\u03af\u03b1",
    "Choose a Time": "\u0395\u03c0\u03b9\u03bb\u03ad\u03be\u03c4\u03b5 \u03a7\u03c1\u03cc\u03bd\u03bf",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "\u0395\u03c0\u03b9\u03bb\u03ad\u03be\u03c4\u03b5 \u03c7\u03c1\u03cc\u03bd\u03bf",
    "Choose all": "\u0395\u03c0\u03b9\u03bb\u03bf\u03b3\u03ae \u03cc\u03bb\u03c9\u03bd",
    "Chosen %s": "\u0395\u03c0\u03b9\u03bb\u03ad\u03c7\u03b8\u03b7\u03ba\u03b5 %s",
    "Circle Rank:": "Zakr\u00fa\u017ekuj poradie:",
    "Circle the last digit of the team's total:": "Zakr\u00fa\u017ekuj posledn\u00fa \u010d\u00edslicu t\u00edmov\u00e9ho s\u00fa\u010dtu:",
    "Click to choose all %s at once.": "\u03a0\u03b1\u03c4\u03ae\u03c3\u03c4\u03b5 \u03b3\u03b9\u03b1 \u03b5\u03c0\u03b9\u03bb\u03bf\u03b3\u03ae \u03cc\u03bb\u03c9\u03bd \u03c4\u03c9\u03bd %s \u03bc\u03b5 \u03c4\u03b7 \u03bc\u03af\u03b1.",
    "Click to remove all chosen %s at once.": "\u039a\u03bb\u03af\u03ba \u03b3\u03b9\u03b1 \u03bd\u03b1 \u03b1\u03c6\u03b1\u03b9\u03c1\u03b5\u03b8\u03bf\u03cd\u03bd \u03cc\u03bb\u03b1 \u03c4\u03b1 \u03b5\u03c0\u03b9\u03bb\u03b5\u03b3\u03bc\u03ad\u03bd\u03b1 %s \u03bc\u03b5 \u03c4\u03b7 \u03bc\u03af\u03b1.",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "December": "\u0394\u03b5\u03ba\u03ad\u03bc\u03b2\u03c1\u03b9\u03bf\u03c2",
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
    "February": "\u03a6\u03b5\u03b2\u03c1\u03bf\u03c5\u03ac\u03c1\u03b9\u03bf\u03c2",
    "Filter": "\u03a6\u03af\u03bb\u03c4\u03c1\u03bf",
    "Folders": "Prie\u010dinky",
    "Friday": "piatok",
    "Hidden": "Skryt\u00e9",
    "Hide": "\u0391\u03c0\u03cc\u03ba\u03c1\u03c5\u03c8\u03b7",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "D\u00d4LE\u017dIT\u00c9: Skontrolujte a explicitne zazna\u010dte, \u010di re\u010dn\u00edk prednesie viacero re\u010d\u00ed",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "Nez\u00e1visl\u00fd",
    "Institution": "Debatn\u00fd klub",
    "January": "\u0399\u03b1\u03bd\u03bf\u03c5\u03ac\u03c1\u03b9\u03bf\u03c2",
    "July": "\u0399\u03bf\u03cd\u03bb\u03b9\u03bf\u03c2",
    "June": "\u0399\u03bf\u03cd\u03bd\u03b9\u03bf\u03c2",
    "Latest Actions": "Najnov\u0161ie akcie",
    "Latest Results": "Najnov\u0161ie v\u00fdsledky",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "\u039c\u03ac\u03c1\u03c4\u03b9\u03bf\u03c2",
    "May": "\u039c\u03ac\u03b9\u03bf\u03c2",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "\u039c\u03b5\u03c3\u03ac\u03bd\u03c5\u03c7\u03c4\u03b1",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "pondelok",
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
    "Noon": "\u039c\u03b5\u03c3\u03b7\u03bc\u03ad\u03c1\u03b9",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "\u03a3\u03b7\u03bc\u03b5\u03af\u03c9\u03c3\u03b7: \u0395\u03af\u03c3\u03c4\u03b5 %s \u03ce\u03c1\u03b1 \u03bc\u03c0\u03c1\u03bf\u03c3\u03c4\u03ac \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd \u03ce\u03c1\u03b1 \u03c4\u03bf\u03c5 \u03b5\u03be\u03c5\u03c0\u03b7\u03c1\u03b5\u03c4\u03b7\u03c4\u03ae.",
      "\u03a3\u03b7\u03bc\u03b5\u03af\u03c9\u03c3\u03b7: \u0395\u03af\u03c3\u03c4\u03b5 %s \u03ce\u03c1\u03b5\u03c2 \u03bc\u03c0\u03c1\u03bf\u03c3\u03c4\u03ac \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd \u03ce\u03c1\u03b1 \u03c4\u03bf\u03c5 \u03b5\u03be\u03c5\u03c0\u03b7\u03c1\u03b5\u03c4\u03b7\u03c4\u03ae."
    ],
    "Note: You are %s hour behind server time.": [
      "\u03a3\u03b7\u03bc\u03b5\u03af\u03c9\u03c3\u03b7: \u0395\u03af\u03c3\u03c4\u03b5 %s \u03ce\u03c1\u03b1 \u03c0\u03af\u03c3\u03c9 \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd \u03ce\u03c1\u03b1 \u03c4\u03bf\u03c5 \u03b5\u03be\u03c5\u03c0\u03b7\u03c1\u03b5\u03c4\u03b7\u03c4\u03ae",
      "\u03a3\u03b7\u03bc\u03b5\u03af\u03c9\u03c3\u03b7: \u0395\u03af\u03c3\u03c4\u03b5 %s \u03ce\u03c1\u03b5\u03c2 \u03c0\u03af\u03c3\u03c9 \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd \u03ce\u03c1\u03b1 \u03c4\u03bf\u03c5 \u03b5\u03be\u03c5\u03c0\u03b7\u03c1\u03b5\u03c4\u03b7\u03c4\u03ae."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "\u039d\u03bf\u03ad\u03bc\u03b2\u03c1\u03b9\u03bf\u03c2",
    "Now": "\u03a4\u03ce\u03c1\u03b1",
    "October": "\u039f\u03ba\u03c4\u03ce\u03b2\u03c1\u03b9\u03bf\u03c2",
    "Open": "Open",
    "Order": "Poradie",
    "Panellist": "Panelista",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "Op\u00e4tovn\u00e1 \u00faprava",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Remove": "\u0391\u03c6\u03b1\u03af\u03c1\u03b5\u03c3\u03b7",
    "Remove all": "\u0391\u03c6\u03b1\u03af\u03c1\u03b5\u03c3\u03b7 \u03cc\u03bb\u03c9\u03bd",
    "Review": "Kontrola",
    "Room:": "Miestnos\u0165:",
    "Round": "Kolo",
    "Saturday": "sobota",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "Skenovanie pomocou fotoapar\u00e1tu",
    "Score:": "Sk\u00f3re:",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "\u03a3\u03b5\u03c0\u03c4\u03ad\u03bc\u03b2\u03c1\u03b9\u03bf\u03c2",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "\u03a0\u03c1\u03bf\u03b2\u03bf\u03bb\u03ae",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "Samostatn\u00fd Chair",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "Demografia re\u010dn\u00edkov",
    "Speaker Results": "V\u00fdsledky re\u010dn\u00edkov",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "Zastavi\u0165 skenovanie fotoapar\u00e1tom",
    "Sunday": "nede\u013ea",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u0391\u03c5\u03c4\u03ae \u03b5\u03af\u03bd\u03b1\u03b9 \u03b7 \u03bb\u03af\u03c3\u03c4\u03b1 \u03c4\u03c9\u03bd \u03b4\u03b9\u03b1\u03b8\u03ad\u03c3\u03b9\u03bc\u03c9\u03bd %s. \u039c\u03c0\u03bf\u03c1\u03b5\u03af\u03c4\u03b5 \u03bd\u03b1 \u03b5\u03c0\u03b9\u03bb\u03ad\u03be\u03b5\u03c4\u03b5 \u03ba\u03ac\u03c0\u03bf\u03b9\u03b1, \u03b1\u03c0\u03cc \u03c4\u03bf \u03c0\u03b1\u03c1\u03b1\u03ba\u03ac\u03c4\u03c9 \u03c0\u03b5\u03b4\u03af\u03bf \u03ba\u03b1\u03b9 \u03c0\u03b1\u03c4\u03ce\u03bd\u03c4\u03b1\u03c2 \u03c4\u03bf \u03b2\u03ad\u03bb\u03bf\u03c2 \"\u0395\u03c0\u03b9\u03bb\u03bf\u03b3\u03ae\" \u03bc\u03b5\u03c4\u03b1\u03be\u03cd \u03c4\u03c9\u03bd \u03b4\u03cd\u03bf \u03c0\u03b5\u03b4\u03af\u03c9\u03bd.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u0391\u03c5\u03c4\u03ae \u03b5\u03af\u03bd\u03b1\u03b9 \u03b7 \u03bb\u03af\u03c3\u03c4\u03b1 \u03c4\u03c9\u03bd \u03b5\u03c0\u03b9\u03bb\u03b5\u03b3\u03bc\u03ad\u03bd\u03c9\u03bd %s. \u039c\u03c0\u03bf\u03c1\u03b5\u03af\u03c4\u03b5 \u03bd\u03b1 \u03b1\u03c6\u03b1\u03b9\u03c1\u03ad\u03c3\u03b5\u03c4\u03b5 \u03bc\u03b5\u03c1\u03b9\u03ba\u03ac \u03b5\u03c0\u03b9\u03bb\u03ad\u03b3\u03bf\u03bd\u03c4\u03b1\u03c2 \u03c4\u03b1 \u03b1\u03c0\u03bf \u03c4\u03bf \u03ba\u03bf\u03c5\u03c4\u03af \u03c0\u03b1\u03c1\u03b1\u03ba\u03ac\u03c4\u03c9 \u03ba\u03b1\u03b9 \u03bc\u03b5\u03c4\u03ac \u03ba\u03ac\u03bd\u03bf\u03bd\u03c4\u03b1\u03c2 \u03ba\u03bb\u03af\u03ba \u03c3\u03c4\u03bf \u03b2\u03b5\u03bb\u03ac\u03ba\u03b9 \"\u0391\u03c6\u03b1\u03af\u03c1\u03b5\u03c3\u03b7\" \u03b1\u03bd\u03ac\u03bc\u03b5\u03c3\u03b1 \u03c3\u03c4\u03b1 \u03b4\u03cd\u03bf \u03ba\u03bf\u03c5\u03c4\u03b9\u03ac.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "T\u00e1to str\u00e1nka sa bude aktualizova\u0165 v re\u00e1lnom \u010dase s nov\u00fdmi registr\u00e1ciami, ako sa bud\u00fa vyskytova\u0165, hoci po\u010diato\u010dn\u00fd zoznam m\u00f4\u017ee by\u0165 star\u00fd a\u017e jednu min\u00fatu.",
    "Thursday": "\u0161tvrtok",
    "Today": "\u03a3\u03ae\u03bc\u03b5\u03c1\u03b1",
    "Tomorrow": "\u0391\u03cd\u03c1\u03b9\u03bf",
    "Total:": "Celkovo:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "Shadow",
    "Tuesday": "utorok",
    "Turn On Sounds": "Zapn\u00fa\u0165 zvuky",
    "Type into this box to filter down the list of available %s.": "\u03a0\u03bb\u03b7\u03ba\u03c4\u03c1\u03bf\u03bb\u03bf\u03b3\u03ae\u03c3\u03c4\u03b5 \u03c3\u03b5 \u03b1\u03c5\u03c4\u03cc \u03c4\u03bf \u03c0\u03b5\u03b4\u03af\u03bf \u03b3\u03b9\u03b1 \u03bd\u03b1 \u03c6\u03b9\u03bb\u03c4\u03c1\u03ac\u03c1\u03b5\u03c4\u03b5 \u03c4\u03b7 \u03bb\u03af\u03c3\u03c4\u03b1 \u03c4\u03c9\u03bd \u03b4\u03b9\u03b1\u03b8\u03ad\u03c3\u03b9\u03bc\u03c9\u03bd %s.",
    "Type into this box to filter down the list of selected %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie ozna\u010den\u00fdch %s.",
    "Unaffiliated": "Nez\u00e1visl\u00fd",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "Nie som si ist\u00fd/\u00e1",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Wednesday": "streda",
    "Which team won the debate:": "Ktor\u00fd t\u00edm vyhral debatu:",
    "Yes": "Ano",
    "Yesterday": "\u03a7\u03b8\u03ad\u03c2",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "\u0388\u03c7\u03b5\u03c4\u03b5 \u03b5\u03c0\u03b9\u03bb\u03ad\u03be\u03b5\u03b9 \u03bc\u03b9\u03b1 \u03b5\u03bd\u03ad\u03c1\u03b3\u03b5\u03b9\u03b1, \u03ba\u03b1\u03b9 \u03b4\u03b5\u03bd \u03ad\u03c7\u03b5\u03c4\u03b5 \u03ba\u03ac\u03bd\u03b5\u03b9 \u03ba\u03b1\u03bc\u03af\u03b1 \u03b1\u03bb\u03bb\u03b1\u03b3\u03ae \u03c3\u03c4\u03b1 \u03b5\u03ba\u03ac\u03c3\u03c4\u03bf\u03c4\u03b5 \u03c0\u03b5\u03b4\u03af\u03b1. \u03a0\u03b9\u03b8\u03b1\u03bd\u03ce\u03bd \u03b8\u03ad\u03bb\u03b5\u03c4\u03b5 \u03c4\u03bf \u03ba\u03bf\u03c5\u03bc\u03c0\u03af Go \u03b1\u03bd\u03c4\u03af \u03c4\u03bf\u03c5 \u03ba\u03bf\u03c5\u03bc\u03c0\u03b9\u03bf\u03cd \u0391\u03c0\u03bf\u03b8\u03ae\u03ba\u03b5\u03c5\u03c3\u03b7\u03c2.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "\u0388\u03c7\u03b5\u03c4\u03b5 \u03b5\u03c0\u03b9\u03bb\u03ad\u03be\u03b5\u03b9 \u03bc\u03b9\u03b1 \u03b5\u03bd\u03ad\u03c1\u03b3\u03b5\u03b9\u03b1, \u03b1\u03bb\u03bb\u03ac \u03b4\u03b5\u03bd \u03ad\u03c7\u03b5\u03c4\u03b5 \u03b1\u03c0\u03bf\u03b8\u03b7\u03ba\u03b5\u03cd\u03c3\u03b5\u03b9 \u03c4\u03b9\u03c2 \u03b1\u03bb\u03bb\u03b1\u03b3\u03ad\u03c2 \u03c3\u03c4\u03b1 \u03b5\u03ba\u03ac\u03c3\u03c4\u03c9\u03c4\u03b5 \u03c0\u03b5\u03b4\u03af\u03b1 \u03b1\u03ba\u03cc\u03bc\u03b1. \u03a0\u03b1\u03c1\u03b1\u03ba\u03b1\u03bb\u03ce \u03c0\u03b1\u03c4\u03ae\u03c3\u03c4\u03b5 \u039f\u039a \u03b3\u03b9\u03b1 \u03bd\u03b1 \u03c4\u03b9\u03c2 \u03b1\u03c0\u03bf\u03b8\u03b7\u03ba\u03b5\u03cd\u03c3\u03b5\u03c4\u03b5. \u0398\u03b1 \u03c7\u03c1\u03b5\u03b9\u03b1\u03c3\u03c4\u03b5\u03af \u03bd\u03b1 \u03b5\u03ba\u03c4\u03b5\u03bb\u03ad\u03c3\u03b5\u03c4\u03b5 \u03be\u03b1\u03bd\u03ac \u03c4\u03b7\u03bd \u03b5\u03bd\u03ad\u03c1\u03b3\u03b5\u03b9\u03b1.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0388\u03c7\u03b5\u03c4\u03b5 \u03bc\u03b7 \u03b1\u03c0\u03bf\u03b8\u03b7\u03ba\u03b5\u03c5\u03bc\u03ad\u03bd\u03b5\u03c2 \u03b1\u03bb\u03bb\u03b1\u03b3\u03ad\u03c2 \u03c3\u03b5 \u03bc\u03b5\u03bc\u03bf\u03bd\u03c9\u03bc\u03ad\u03bd\u03b1 \u03b5\u03c0\u03b5\u03be\u03b5\u03c1\u03b3\u03ac\u03c3\u03b9\u03bc\u03b1 \u03c0\u03b5\u03b4\u03af\u03b1. \u0386\u03bd \u03b5\u03ba\u03c4\u03b5\u03bb\u03ad\u03c3\u03b5\u03c4\u03b5 \u03bc\u03b9\u03b1 \u03b5\u03bd\u03ad\u03c1\u03b3\u03b5\u03b9\u03b1, \u03bf\u03b9 \u03bc\u03b7 \u03b1\u03c0\u03bf\u03b8\u03b7\u03ba\u03b5\u03c5\u03bc\u03ad\u03bd\u03b5\u03c2 \u03b1\u03bb\u03bb\u03ac\u03b3\u03b5\u03c2 \u03b8\u03b1 \u03c7\u03b1\u03b8\u03bf\u03cd\u03bd",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "pi",
    "abbrev. day Monday\u0004Mon": "po",
    "abbrev. day Saturday\u0004Sat": "so",
    "abbrev. day Sunday\u0004Sun": "ne",
    "abbrev. day Thursday\u0004Thur": "\u0161t",
    "abbrev. day Tuesday\u0004Tue": "ut",
    "abbrev. day Wednesday\u0004Wed": "st",
    "abbrev. month April\u0004Apr": "\u0391\u03c0\u03c1",
    "abbrev. month August\u0004Aug": "\u0391\u03cd\u03b3",
    "abbrev. month December\u0004Dec": "\u0394\u03b5\u03ba",
    "abbrev. month February\u0004Feb": "\u03a6\u03b5\u03b2",
    "abbrev. month January\u0004Jan": "\u0399\u03b1\u03bd",
    "abbrev. month July\u0004Jul": "\u0399\u03bf\u03cd\u03bb",
    "abbrev. month June\u0004Jun": "\u0399\u03bf\u03cd\u03bd",
    "abbrev. month March\u0004Mar": "\u039c\u03ac\u03c1",
    "abbrev. month May\u0004May": "\u039c\u03ac\u03b9",
    "abbrev. month November\u0004Nov": "\u039d\u03bf\u03ad",
    "abbrev. month October\u0004Oct": "\u039f\u03ba\u03c4",
    "abbrev. month September\u0004Sep": "\u03a3\u03b5\u03c0",
    "adjudicators with gender data": "rozhodcovia s \u00fadajmi o rode",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "desatinn\u00e9 body s\u00fa povolen\u00e9",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "bez polbodov",
    "one letter Friday\u0004F": "\u03a0",
    "one letter Monday\u0004M": "\u0394",
    "one letter Saturday\u0004S": "\u03a3",
    "one letter Sunday\u0004S": "\u039a",
    "one letter Thursday\u0004T": "\u03a0",
    "one letter Tuesday\u0004T": "\u03a4",
    "one letter Wednesday\u0004W": "\u03a4",
    "optional": "nepovinn\u00e9",
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
    "DATETIME_FORMAT": "d/m/Y P",
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%d/%m/%y %H:%M:%S",
      "%d/%m/%y %H:%M:%S.%f",
      "%d/%m/%y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "d/m/Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d/m/Y P",
    "SHORT_DATE_FORMAT": "d/m/Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "P",
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

