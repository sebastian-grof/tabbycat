
'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = 0;
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
      "%(cnt)s\u500b\u4e2d%(sel)s\u500b\u9078\u629e"
    ],
    "%1 (%2) with identifier of %3": "%1\uff08%2\u3001\u8b58\u5225\u30b3\u30fc\u30c9%3\uff09",
    "%1 (%2) with no assigned identifier": "%1\uff08%2\u3001\u8b58\u5225\u30b3\u30fc\u30c9\u7121\u3057\uff09",
    "%1 (Absent; id=%2)": "%1\uff08\u6b20\u5e2d\u3001id=%2\uff09",
    "%1 (Present; id=%2)": "%1\uff08\u51fa\u5e2d\u3001id=%2\uff09",
    "%1 (no category) with identifier of %2": "%1\uff08\u30ab\u30c6\u30b4\u30ea\u30fc\u306a\u3057\u3001\u8b58\u5225\u30b3\u30fc\u30c9%2\uff09",
    "%1 (no category) with no assigned identifier": "%1\uff08\u30ab\u30c6\u30b4\u30ea\u30fc\u306a\u3057\u3001\u8b58\u5225\u30b3\u30fc\u30c9\u7121\u3057\uff09",
    "%1 checked in %2: %3": "%1\u306b%3\uff08\u30b3\u30fc\u30c9%2\uff09\u304c\u30c1\u30a7\u30c3\u30af\u30a4\u30f3",
    "%1, a %2 from %3 with identifier of %4": "%1\uff08%2\u3001\u30a4\u30f3\u30b9\u30c6%3\u3001\u8b58\u5225\u30b3\u30fc\u30c9%4\uff09",
    "%1, a %2 from %3 with no assigned identifier": "%1\uff08%2\u3001\u30a4\u30f3\u30b9\u30c6%3\u3001\u8b58\u5225\u30b3\u30fc\u30c9\u306a\u3057\uff09",
    "%1, a %2 of no institutional affiliation with identifier of %3": "%1\uff08%2\u3001\u30a4\u30f3\u30b9\u30c6\u306a\u3057\u3001\u8b58\u5225\u30b3\u30fc\u30c9%3\uff09",
    "%1, a %2 of no institutional affiliation with no assigned identifier": "%1\uff08%2\u3001\u30a4\u30f3\u30b9\u30c6\u306a\u3057\u3001\u8b58\u5225\u30b3\u30fc\u30c9\u306a\u3057\uff09",
    "%1, a team with speakers %2": "%1\uff08\u30c1\u30fc\u30e0\uff09\u3001\u30b9\u30d4\u30fc\u30ab\u30fc%2",
    "%s event": [
      "%s udalos\u0165"
    ],
    "%s selected option not visible": [
      "\u9078\u629e\u3055\u308c\u305f%s\u4ef6\u306e\u30aa\u30d7\u30b7\u30e7\u30f3\u306f\u975e\u8868\u793a\u3067\u3059\u3002"
    ],
    "(click to clear)": "(\u30af\u30ea\u30c3\u30af\u3067\u30af\u30ea\u30a2)",
    "6 a.m.": "\u5348\u524d 6 \u6642",
    "6 p.m.": "\u5348\u5f8c 6 \u6642",
    "; ": "; ",
    "<strong>\u2613</strong> All": "<strong>\u2613</strong> \u5168\u54e1",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> \u3059\u3079\u3066",
    "Active": "Akt\u00edvna",
    "Add Ballot": "\u30d0\u30ed\u30c3\u30c8\u3092\u8ffd\u52a0",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicator Demographics": "\u30b8\u30e3\u30c3\u30b8\u306e\u5c5e\u6027\u5206\u5e03",
    "Adjudicator Results": "\u30b8\u30e3\u30c3\u30b8\u306e\u7d50\u679c",
    "All": "\u3059\u3079\u3066",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "\u533f\u540d",
    "Anonymous (due to team codes)": "\u533f\u540d\uff08\u30c1\u30fc\u30e0\u30b3\u30fc\u30c9\u5236\u306e\u305f\u3081\uff09",
    "April": "4\u6708",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "8\u6708",
    "Auto-Allocate": "\u81ea\u52d5\u914d\u7f6e",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-Prioritise": "\u81ea\u52d5\u3067\u512a\u5148\u5ea6\u4ed8\u3051",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "\u5229\u7528\u53ef\u80fd %s",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "Registr\u00e1cia ballotov",
    "Ballot Statuses": "\u30d0\u30ed\u30c3\u30c8\u306e\u72b6\u6cc1",
    "Ballots Status": "\u30d0\u30ed\u30c3\u30c8\u306e\u72b6\u6cc1",
    "Break": "\u30d6\u30ec\u30a4\u30af",
    "By ": "Od ",
    "By how many points did they win:": "O ko\u013eko bodov vyhrali:",
    "Cancel": "\u30ad\u30e3\u30f3\u30bb\u30eb",
    "Category": "\u30ab\u30c6\u30b4\u30ea\u30fc",
    "Chair": "Chair",
    "Check time": "Skontrolujte \u010das",
    "Checked-In": "\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u6e08\u307f",
    "Choose": "Vybra\u0165",
    "Choose %s by selecting them and then select the \"Choose\" arrow button.": "%s\u3092\u9078\u629e\u3059\u308b\u306b\u306f\u3001\u9805\u76ee\u3092\u9078\u629e\u3057\u3066\u304b\u3089\"\u9078\u629e\"\u77e2\u5370\u30dc\u30bf\u30f3\u3092\u9078\u629e\u3057\u307e\u3059\u3002",
    "Choose a Date": "\u65e5\u4ed8\u3092\u9078\u629e",
    "Choose a Time": "\u6642\u9593\u3092\u9078\u629e",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "\u6642\u9593\u3092\u9078\u629e",
    "Choose all": "Vybra\u0165 v\u0161etko",
    "Choose all %s": "%s\u3092\u3059\u3079\u3066\u9078\u629e",
    "Choose selected %s": "\u9078\u629e\u3055\u308c\u305f%s\u3092\u9078\u629e",
    "Chosen %s": "\u9078\u629e\u3055\u308c\u305f %s",
    "Circle Rank:": "Zakr\u00fa\u017ekuj poradie:",
    "Circle the last digit of the team's total:": "Zakr\u00fa\u017ekuj posledn\u00fa \u010d\u00edslicu t\u00edmov\u00e9ho s\u00fa\u010dtu:",
    "Click to check-in manually": "\u3053\u3053\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u624b\u52d5\u3067\u30c1\u30a7\u30c3\u30af\u30a4\u30f3",
    "Click to choose all %s at once.": "Kliknite sem pre vybratie v\u0161etk\u00fdch %s naraz.",
    "Click to remove all chosen %s at once.": "Kliknite sem pre vymazanie vybrat\u00fdch %s naraz.",
    "Click to undo a check-in": "\u3053\u3053\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u3092\u30ad\u30e3\u30f3\u30bb\u30eb",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Confirmed": "\u627f\u8a8d\u6e08\u307f",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Copy From Check-Ins": "\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u304b\u3089\u30b3\u30d4\u30fc",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "December": "12\u6708",
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
    "February": "2\u6708",
    "Filter": "\u30d5\u30a3\u30eb\u30bf\u30fc",
    "Folders": "Prie\u010dinky",
    "Friday": "\u91d1\u66dc\u65e5",
    "Gender": "\u30b8\u30a7\u30f3\u30c0\u30fc",
    "Hidden": "Skryt\u00e9",
    "Hide": "Skry\u0165",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "D\u00d4LE\u017dIT\u00c9: Skontrolujte a explicitne zazna\u010dte, \u010di re\u010dn\u00edk prednesie viacero re\u010d\u00ed",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "\u30b5\u30a4\u30c9\u30d0\u30fc\u306a\u3057\u3067\u3053\u306e\u30da\u30fc\u30b8\u3092\u8868\u793a\u3057\u305f\u3044\u5834\u5408\uff08e.g. OR\u3067\u8868\u793a\u3059\u308b\u305f\u3081\uff09\u3001\u30a2\u30b7\u30b9\u30bf\u30f3\u30c8\u306e\u3082\u306e\u3092\u4f7f\u7528\u3067\u304d\u307e\u3059\u3002",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "\u500b\u4eba",
    "Institution": "Debatn\u00fd klub",
    "January": "1\u6708",
    "July": "7\u6708",
    "June": "6\u6708",
    "Latest Actions": "\u76f4\u8fd1\u306e\u30a2\u30af\u30b7\u30e7\u30f3",
    "Latest Results": "\u76f4\u8fd1\u306e\u7d50\u679c",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "3\u6708",
    "Match Check-Ins": "\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u306b\u5408\u308f\u305b\u308b",
    "May": "5\u6708",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "0\u6642",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "\u6708\u66dc\u65e5",
    "Motion is:": "T\u00e9za je:",
    "N/A": "N/A",
    "Needs a date": "Ch\u00fdba d\u00e1tum",
    "New folder": "Nov\u00fd prie\u010dinok",
    "New schedule day": "Nov\u00fd de\u0148 rozvrhu",
    "No": "\u3044\u3044\u3048",
    "No ": "Nie ",
    "No Actions Yet": "\u30a2\u30af\u30b7\u30e7\u30f3\u306a\u3057",
    "No Adjudicator Ratings Information": "\u30b8\u30e3\u30c3\u30b8\u306e\u8a55\u4fa1\u306e\u60c5\u5831\u306a\u3057",
    "No Adjudicator-Adjudicator Feedback Information": "\u30b8\u30e3\u30c3\u30b8\u9593\u30d5\u30a3\u30fc\u30c9\u30d0\u30c3\u30af\u306e\u60c5\u5831\u306a\u3057",
    "No Category": "\u30ab\u30c6\u30b4\u30ea\u30fc\u306a\u3057",
    "No Confirmed Results Yet": "\u627f\u8a8d\u6e08\u307f\u7d50\u679c\u306a\u3057",
    "No Gender Information": "\u30b8\u30a7\u30f3\u30c0\u30fc\u306e\u60c5\u5831\u306a\u3057",
    "No Position Information": "\u4f4d\u7f6e\u60c5\u5831\u306a\u3057",
    "No Region Information": "\u5730\u57df\u60c5\u5831\u306a\u3057",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "\u30b9\u30d4\u30fc\u30ab\u30fc\u30ab\u30c6\u30b4\u30ea\u30fc\u306e\u60c5\u5831\u306a\u3057",
    "No changes": "\u5909\u66f4\u306a\u3057",
    "No code name set": "\u30b3\u30fc\u30c9\u540d\u306a\u3057",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "\u8a72\u5f53\u306e\u53c2\u52a0\u8005\u304c\u3044\u307e\u305b\u3093\u3002",
    "No matching rooms found.": "\u8a72\u5f53\u306e\u90e8\u5c4b\u304c\u3042\u308a\u307e\u305b\u3093\u3002",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "Nie, odosielam sp\u00e4tn\u00fa v\u00e4zbu na:",
    "Noon": "12\u6642",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Not Checked-In": "\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u6e08\u307f\u3067\u306a\u3044",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "\u30ce\u30fc\u30c8: \u3042\u306a\u305f\u306e\u74b0\u5883\u306f\u30b5\u30fc\u30d0\u30fc\u6642\u9593\u3088\u308a\u3001%s\u6642\u9593\u9032\u3093\u3067\u3044\u307e\u3059\u3002"
    ],
    "Note: You are %s hour behind server time.": [
      "\u30ce\u30fc\u30c8: \u3042\u306a\u305f\u306e\u74b0\u5883\u306f\u30b5\u30fc\u30d0\u30fc\u6642\u9593\u3088\u308a\u3001%s\u6642\u9593\u9045\u308c\u3066\u3044\u307e\u3059\u3002"
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "11\u6708",
    "Now": "\u73fe\u5728",
    "October": "10\u6708",
    "Open": "Open",
    "Open the assistant version.": "\u30a2\u30b7\u30b9\u30bf\u30f3\u30c8\u7248\u3092\u958b\u304f",
    "Order": "Poradie",
    "Panellist": "\u30d1\u30cd\u30eb",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Priority %1": "\u512a\u5148\u5ea6%1",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank": "\u30e9\u30f3\u30af",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "\u518d\u7de8\u96c6",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Region": "\u5730\u57df",
    "Remove": "Odstr\u00e1ni\u0165",
    "Remove %s by selecting them and then select the \"Remove\" arrow button.": "%s\u3092\u524a\u9664\u3059\u308b\u306b\u306f\u3001\u9805\u76ee\u3092\u9078\u629e\u3057\u3066\u304b\u3089\"\u524a\u9664\"\u77e2\u5370\u30dc\u30bf\u30f3\u3092\u9078\u629e\u3057\u307e\u3059\u3002",
    "Remove all": "Odstr\u00e1ni\u0165 v\u0161etky",
    "Remove all %s": "%s\u3092\u3059\u3079\u3066\u524a\u9664",
    "Remove selected %s": "\u9078\u629e\u3055\u308c\u305f%s\u3092\u524a\u9664",
    "Return to Draw": "\u5bfe\u6226\u8868\u306b\u623b\u308b",
    "Review": "\u518d\u95b2\u89a7",
    "Room:": "Miestnos\u0165:",
    "Round": "Kolo",
    "Saturday": "\u571f\u66dc\u65e5",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "\u30ab\u30e1\u30e9\u3067\u30b9\u30ad\u30e3\u30f3",
    "Score:": "Sk\u00f3re:",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "9\u6708",
    "Set All Breaking as Available": "\u30d6\u30ec\u30a4\u30af\u3057\u305f\u5168\u54e1\u3092\u53c2\u52a0\u53ef\u80fd\u306b\u3059\u308b",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Set all availabilities to exactly match check-ins.": "\u30e9\u30a6\u30f3\u30c9\u306e\u53c2\u52a0\u72b6\u6cc1\u3092\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u72b6\u6cc1\u3068\u4e00\u81f4\u3055\u305b\u308b",
    "Set all the availabilities to exactly match what they were in the previous round.": "\u500b\u306e\u30e9\u30a6\u30f3\u30c9\u306e\u53c2\u52a0\u72b6\u6cc1\u3092\u76f4\u524d\u306e\u30e9\u30a6\u30f3\u30c9\u3068\u4e00\u81f4\u3055\u305b\u308b",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u3092\u3057\u3066\u3044\u3066\u30e9\u30a6\u30f3\u30c9\u306e\u53c2\u52a0\u72b6\u6cc1\u304c\u4e0d\u53ef\u306e\u4eba\u306e\u307f\u3092\u53ef\u306b\u3059\u308b\u3002",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "Zobrazi\u0165",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "\u5358\u30c1\u30a7\u30a2",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "\u30b9\u30d4\u30fc\u30ab\u30fc\u306e\u5c5e\u6027\u5206\u5e03",
    "Speaker Results": "\u30b9\u30d4\u30fc\u30ab\u30fc\u306e\u7d50\u679c",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "\u30ab\u30e1\u30e9\u30b9\u30ad\u30e3\u30f3\u3092\u4e2d\u6b62",
    "Sunday": "\u65e5\u66dc\u65e5",
    "Team": "\u30c1\u30fc\u30e0",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "The bracket range of the hypothetical debate": "\u4eee\u88c5\u306e\u30c7\u30a3\u30d9\u30fc\u30c8\u306e\u30d6\u30e9\u30b1\u30c3\u30c8\u7bc4\u56f2",
    "The debate's bracket": "\u8a66\u5408\u306e\u30d6\u30e9\u30b1\u30c3\u30c8",
    "The estimated total number of live break categories across all teams of the hypothetical debate": "\u4eee\u306e\u8a66\u5408\u306e\u5168\u30c1\u30fc\u30e0\u306e\u30d6\u30ec\u30a4\u30af\u306e\u53ef\u80fd\u6027\u304c\u6b8b\u3063\u3066\u3044\u308b\u30ab\u30c6\u30b4\u30ea\u30fc\u306e\u7dcf\u6570",
    "The total number of live break categories across all teams": "\u5168\u30c1\u30fc\u30e0\u306e\u30d6\u30ec\u30a4\u30af\u306e\u53ef\u80fd\u6027\u304c\u6b8b\u3063\u3066\u3044\u308b\u30ab\u30c6\u30b4\u30ea\u30fc\u306e\u7dcf\u6570",
    "This debate's priority": "\u30c7\u30a3\u30d9\u30fc\u30c8\u306e\u512a\u5148\u5ea6",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre v\u00fdber je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVybra\u0165\u201c presun\u00fa\u0165.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre vymazanie je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVymaza\u0165\u201c vymaza\u0165.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "\u65b0\u305f\u306a\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u306f\u81ea\u52d5\u7684\u306b\u53cd\u6620\u3055\u308c\u307e\u3059\uff08\u305f\u3060\u30571\u5206\u7a0b\u5ea6\u306e\u9045\u5ef6\u304c\u3042\u308b\u5834\u5408\u304c\u3042\u308a\u307e\u3059\uff09\u3002",
    "This person does not have a check-in identifier so they can't be checked in": "\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u306e\u8b58\u5225\u30b3\u30fc\u30c9\u304c\u306a\u3044\u305f\u3081\u30c1\u30a7\u30c3\u30af\u30a4\u30f3\u3067\u304d\u307e\u305b\u3093",
    "Thursday": "\u6728\u66dc\u65e5",
    "Today": "\u4eca\u65e5",
    "Tomorrow": "\u660e\u65e5",
    "Total:": "Celkovo:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "\u30c8\u30ec\u30a4\u30cb\u30fc",
    "Tuesday": "\u706b\u66dc\u65e5",
    "Turn On Sounds": "\u97f3\u58f0\u3092\u30aa\u30f3\u306b\u3059\u308b",
    "Type into this box to filter down the list of available %s.": "\u4f7f\u7528\u53ef\u80fd\u306a %s \u306e\u30ea\u30b9\u30c8\u3092\u7d5e\u308a\u8fbc\u3080\u306b\u306f\u3001\u3053\u306e\u30dc\u30c3\u30af\u30b9\u306b\u5165\u529b\u3057\u307e\u3059\u3002",
    "Type into this box to filter down the list of selected %s.": "\u9078\u629e\u3055\u308c\u305f%s\u306e\u30ea\u30b9\u30c8\u3092\u7d5e\u308a\u8fbc\u3080\u306b\u306f\u3001\u3053\u306e\u30dc\u30c3\u30af\u30b9\u306b\u5165\u529b\u3057\u307e\u3059\u3002",
    "Unaffiliated": "\u7121\u6240\u5c5e",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised": "\u30ab\u30c6\u30b4\u30ea\u30fc\u306a\u3057",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unconfirmed": "\u672a\u627f\u8a8d",
    "Unknown": "\u4e0d\u660e",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "Nie som si ist\u00fd/\u00e1",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Wednesday": "\u6c34\u66dc\u65e5",
    "Which team won the debate:": "Ktor\u00fd t\u00edm vyhral debatu:",
    "Yes": "\u306f\u3044",
    "Yesterday": "\u6628\u65e5",
    "You cannot confirm this ballot because you entered it": "\u81ea\u5206\u3067\u5165\u529b\u3057\u305f\u30d0\u30ed\u30c3\u30c8\u306f\u627f\u8a8d\u3067\u304d\u307e\u305b\u3093",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "\u64cd\u4f5c\u3092\u9078\u629e\u3057\u307e\u3057\u305f\u304c\u3001\u30d5\u30a3\u30fc\u30eb\u30c9\u306b\u5909\u66f4\u306f\u3042\u308a\u307e\u305b\u3093\u3067\u3057\u305f\u3002\u3082\u3057\u304b\u3057\u3066\u4fdd\u5b58\u30dc\u30bf\u30f3\u3067\u306f\u306a\u304f\u3066\u5b9f\u884c\u30dc\u30bf\u30f3\u3092\u304a\u63a2\u3057\u3067\u3059\u304b\u3002",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "\u64cd\u4f5c\u3092\u9078\u629e\u3057\u307e\u3057\u305f\u304c\u3001\u30d5\u30a3\u30fc\u30eb\u30c9\u306b\u672a\u4fdd\u5b58\u306e\u5909\u66f4\u304c\u3042\u308a\u307e\u3059\u3002OK\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u4fdd\u5b58\u3057\u3066\u304f\u3060\u3055\u3044\u3002\u305d\u306e\u5f8c\u3001\u64cd\u4f5c\u3092\u518d\u5ea6\u5b9f\u884c\u3059\u308b\u5fc5\u8981\u304c\u3042\u308a\u307e\u3059\u3002",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u30d5\u30a3\u30fc\u30eb\u30c9\u306b\u672a\u4fdd\u5b58\u306e\u5909\u66f4\u304c\u3042\u308a\u307e\u3059\u3002\u64cd\u4f5c\u3092\u5b9f\u884c\u3059\u308b\u3068\u672a\u4fdd\u5b58\u306e\u5909\u66f4\u306f\u5931\u308f\u308c\u307e\u3059\u3002",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "\u91d1",
    "abbrev. day Monday\u0004Mon": "\u6708",
    "abbrev. day Saturday\u0004Sat": "\u571f",
    "abbrev. day Sunday\u0004Sun": "\u65e5",
    "abbrev. day Thursday\u0004Thur": "\u6728",
    "abbrev. day Tuesday\u0004Tue": "\u706b",
    "abbrev. day Wednesday\u0004Wed": "\u6c34",
    "abbrev. month April\u0004Apr": "4\u6708",
    "abbrev. month August\u0004Aug": "8\u6708",
    "abbrev. month December\u0004Dec": "12\u6708",
    "abbrev. month February\u0004Feb": "2\u6708",
    "abbrev. month January\u0004Jan": "1\u6708",
    "abbrev. month July\u0004Jul": "7\u6708",
    "abbrev. month June\u0004Jun": "6\u6708",
    "abbrev. month March\u0004Mar": "3\u6708",
    "abbrev. month May\u0004May": "5\u6708",
    "abbrev. month November\u0004Nov": "11\u6708",
    "abbrev. month October\u0004Oct": "10\u6708",
    "abbrev. month September\u0004Sep": "9\u6708",
    "adjudicators with gender data": "\u4eba\u306e\u30b8\u30a7\u30f3\u30c0\u30fc\u60c5\u5831\u3042\u308a\u306e\u30b8\u30e3\u30c3\u30b8",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "desatinn\u00e9 body s\u00fa povolen\u00e9",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "feedback scores total": "\u3064\u306e\u30d5\u30a3\u30fc\u30c9\u30d0\u30c3\u30af\u30b9\u30b3\u30a2",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "bez polbodov",
    "one letter Friday\u0004F": "\u91d1",
    "one letter Monday\u0004M": "\u6708",
    "one letter Saturday\u0004S": "\u571f",
    "one letter Sunday\u0004S": "\u65e5",
    "one letter Thursday\u0004T": "\u6728",
    "one letter Tuesday\u0004T": "\u706b",
    "one letter Wednesday\u0004W": "\u6c34",
    "optional": "nepovinn\u00e9",
    "saving...": "\u4fdd\u5b58\u4e2d...",
    "speaker scores analysed": "analyzovan\u00fdch sk\u00f3re re\u010dn\u00edkov",
    "speaker scores total": "\u3064\u306e\u30b9\u30d4\u30fc\u30ab\u30fc\u30b9\u30b3\u30a2",
    "speakers with gender data": "\u4eba\u306e\u30b8\u30a7\u30f3\u30c0\u30fc\u60c5\u5831\u3042\u308a\u306e\u30b9\u30d4\u30fc\u30ab\u30fc",
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
    "DATETIME_FORMAT": "Y\u5e74n\u6708j\u65e5G:i",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%m/%d/%Y %H:%M:%S",
      "%m/%d/%Y %H:%M:%S.%f",
      "%m/%d/%Y %H:%M",
      "%m/%d/%y %H:%M:%S",
      "%m/%d/%y %H:%M:%S.%f",
      "%m/%d/%y %H:%M"
    ],
    "DATE_FORMAT": "Y\u5e74n\u6708j\u65e5",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%m/%d/%Y",
      "%m/%d/%y",
      "%b %d %Y",
      "%b %d, %Y",
      "%d %b %Y",
      "%d %b, %Y",
      "%B %d %Y",
      "%B %d, %Y",
      "%d %B %Y",
      "%d %B, %Y"
    ],
    "DECIMAL_SEPARATOR": ".",
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "n\u6708j\u65e5",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "Y/m/d G:i",
    "SHORT_DATE_FORMAT": "Y/m/d",
    "THOUSAND_SEPARATOR": ",",
    "TIME_FORMAT": "G:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "Y\u5e74n\u6708"
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

