
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
      " %(sel)s  c\u1ee7a %(cnt)s \u0111\u01b0\u1ee3c ch\u1ecdn"
    ],
    "%1 checked in %2: %3": "%1 \u0111\u00e3 \u0111i\u1ec3m danh %2: %3",
    "%s event": [
      "%s udalos\u0165"
    ],
    "%s selected option not visible": [
      "%s ozna\u010den\u00e1 mo\u017enos\u0165 sa nezobrazuje"
    ],
    "6 a.m.": "6 gi\u1edd s\u00e1ng",
    "6 p.m.": "6 gi\u1edd chi\u1ec1u",
    "; ": "; ",
    "<strong>\u2613</strong> All": "<strong>\u2613</strong> T\u1ea5t c\u1ea3",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> T\u1ea5t c\u1ea3",
    "Active": "Akt\u00edvna",
    "Add Ballot": "Prida\u0165 Ballot",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicator Demographics": "Demografia rozhodcov",
    "Adjudicator Results": "V\u00fdsledky rozhodcu",
    "All": "T\u1ea5t c\u1ea3",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "\u1ea8n danh",
    "Anonymous (due to team codes)": "\u1ea8n danh (theo m\u00e3 \u0111\u1ed9i)",
    "April": "Th\u00e1ng T\u01b0",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "Th\u00e1ng T\u00e1m",
    "Auto-Allocate": "Automatick\u00e9 pride\u013eovanie",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "C\u00f3 s\u1eb5n %s",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "Ballot Check-Ins",
    "Ballot Statuses": "T\u00ecnh tr\u1ea1ng Ballot",
    "Ballots Status": "Status ballotov",
    "By ": "Od ",
    "By %1": "%1",
    "By how many points did they win:": "O ko\u013eko bodov vyhrali:",
    "Cancel": "H\u1ee7y b\u1ecf",
    "Category": "Th\u1ec3 lo\u1ea1i",
    "Chair": "Chair",
    "Check time": "Skontrolujte \u010das",
    "Checked-In": "\u0110\u00e3 \u0111i\u1ec3m danh",
    "Choose": "Ch\u1ecdn",
    "Choose a Date": "Ch\u1ecdn Ng\u00e0y",
    "Choose a Time": "Ch\u1ecdn Th\u1eddi gian",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "Ch\u1ecdn gi\u1edd",
    "Choose all": "Ch\u1ecdn t\u1ea5t c\u1ea3",
    "Chosen %s": "Ch\u1ecdn %s",
    "Circle %1": "Khoanh %1",
    "Circle Rank:": "Zakr\u00fa\u017ekuj poradie:",
    "Circle the last digit of the team's total:": "Zakr\u00fa\u017ekuj posledn\u00fa \u010d\u00edslicu t\u00edmov\u00e9ho s\u00fa\u010dtu:",
    "Click to check-in manually": "Click \u0111\u1ec3 \u0111i\u1ec3m danh th\u1ee7 c\u00f4ng",
    "Click to choose all %s at once.": "Click \u0111\u1ec3 ch\u1ecdn t\u1ea5t c\u1ea3 %s .",
    "Click to remove all chosen %s at once.": "Click \u0111\u1ec3 b\u1ecf ch\u1ecdn t\u1ea5t c\u1ea3 %s",
    "Click to undo a check-in": "Nh\u1ea5n \u0111\u1ec3 ho\u00e0n t\u00e1c \u0111i\u1ec3m danh",
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
    "Debated": "\u0110\u00e3 tranh bi\u1ec7n",
    "December": "Th\u00e1ng M\u01b0\u1eddi Hai",
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
    "February": "Th\u00e1ng Hai",
    "Filter": "L\u1ecdc",
    "Find in Table": "T\u00ecm trong B\u1ea3ng",
    "Folders": "Prie\u010dinky",
    "Friday": "piatok",
    "Hidden": "Skryt\u00e9",
    "Hide": "D\u1ea5u \u0111i",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "D\u00d4LE\u017dIT\u00c9: Skontrolujte a explicitne zazna\u010dte, \u010di re\u010dn\u00edk prednesie viacero re\u010d\u00ed",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "N\u1ebfu b\u1ea1n mu\u1ed1n hi\u1ec3n th\u1ecb trang n\u00e0y m\u00e0 kh\u00f4ng c\u00f3 thanh cu\u1ed9n (v\u00ed d\u1ee5: \u0111\u1ec3 hi\u1ec3n th\u1ecb \u1edf kh\u00e1n ph\u00f2ng), b\u1ea1n c\u00f3 th\u1ec3 d\u00f9ng phi\u00ean b\u1ea3n c\u1ee7a tr\u1ee3 l\u00fd.",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "\u0110\u1ed9c l\u1eadp",
    "Institution": "Debatn\u00fd klub",
    "January": "Th\u00e1ng M\u1ed9t",
    "July": "Th\u00e1ng B\u1ea3y",
    "June": "Th\u00e1ng S\u00e1u",
    "Latest Actions": "H\u00e0nh \u0111\u1ed9ng g\u1ea7n \u0111\u00e2y nh\u1ea5t",
    "Latest Results": "K\u1ebft qu\u1ea3 g\u1ea7n \u0111\u00e2y nh\u1ea5t",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "Th\u00e1ng Ba",
    "May": "Th\u00e1ng N\u0103m",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "N\u1eeda \u0111\u00eam",
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
    "No Category": "Kh\u00f4ng c\u00f3 ph\u00e2n lo\u1ea1i",
    "No Confirmed Results Yet": "Ch\u01b0a c\u00f3 k\u1ebft qu\u1ea3 x\u00e1c nh\u1eadn",
    "No Gender Information": "\u017diadne inform\u00e1cie o rode",
    "No Position Information": "\u017diadne inform\u00e1cie o poz\u00edcii",
    "No Region Information": "\u017diadne inform\u00e1cie o regi\u00f3ne",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "\u017diadne inform\u00e1cie o kateg\u00f3ri\u00e1ch re\u010dn\u00edkov",
    "No code name set": "Nie je nastaven\u00e9 k\u00f3dov\u00e9 meno",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "Kh\u00f4ng t\u00ecm th\u1ea5y ng\u01b0\u1eddi ph\u00f9 h\u1ee3p.",
    "No matching rooms found.": "Kh\u00f4ng c\u00f3 ph\u00f2ng n\u00e0o t\u01b0\u01a1ng \u1ee9ng.",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "Nie, odosielam sp\u00e4tn\u00fa v\u00e4zbu na:",
    "Noon": "Bu\u1ed5i tr\u01b0a",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "L\u01b0u \u00fd: Hi\u1ec7n t\u1ea1i b\u1ea1n \u0111ang th\u1ea5y th\u1eddi gian tr\u01b0\u1edbc %s gi\u1edd so v\u1edbi th\u1eddi gian m\u00e1y ch\u1ee7."
    ],
    "Note: You are %s hour behind server time.": [
      "L\u01b0u \u00fd: Hi\u1ec7n t\u1ea1i b\u1ea1n \u0111ang th\u1ea5y th\u1eddi gian sau %s gi\u1edd so v\u1edbi th\u1eddi gian m\u00e1y ch\u1ee7."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "Th\u00e1ng M\u01b0\u1eddi M\u1ed9t",
    "Now": "B\u00e2y gi\u1edd",
    "October": "Th\u00e1ng M\u01b0\u1eddi",
    "Open": "Open",
    "Open the assistant version.": "M\u1edf phi\u00ean b\u1ea3n c\u1ee7a tr\u1ee3 l\u00fd.",
    "Order": "Poradie",
    "Panellist": "Panelista",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Priority %1": "\u01afu ti\u00ean %1",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "Op\u00e4tovn\u00e1 \u00faprava",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Remove": "X\u00f3a",
    "Remove all": "Xo\u00e1 t\u1ea5t c\u1ea3",
    "Review": "Kontrola",
    "Room:": "Ph\u00f2ng:",
    "Round": "Kolo",
    "Saturday": "sobota",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "Qu\u00e9t B\u1eb1ng M\u00e1y \u1ea2nh",
    "Score:": "Sk\u00f3re:",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "Th\u00e1ng Ch\u00edn",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "Hi\u1ec7n ra",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "Samostatn\u00fd Chair",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "Demografia re\u010dn\u00edkov",
    "Speaker Results": "V\u00fdsledky re\u010dn\u00edkov",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "D\u1eebng Qu\u00e9t M\u00e1y \u1ea2nh",
    "Sunday": "nede\u013ea",
    "Team": "\u0110\u1ed9i",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Danh s\u00e1ch c\u00e1c l\u1ef1a ch\u1ecdn \u0111ang c\u00f3 %s. B\u1ea1n c\u00f3 th\u1ec3 ch\u1ecdn b\u1eb1ng b\u00e1ch click v\u00e0o m\u0169i t\u00ean \"Ch\u1ecdn\" n\u1eb1m gi\u1eefa hai h\u1ed9p.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Danh s\u00e1ch b\u1ea1n \u0111\u00e3 ch\u1ecdn %s. B\u1ea1n c\u00f3 th\u1ec3 b\u1ecf ch\u1ecdn b\u1eb1ng c\u00e1ch click v\u00e0o m\u0169i t\u00ean \"Xo\u00e1\" n\u1eb1m gi\u1eefa hai \u00f4.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "Trang n\u00e0y s\u1ebd t\u1ef1 \u0111\u1ed9ng c\u1eadp nh\u1eadt check-in m\u1edbi t\u1ee9c th\u00ec.",
    "This person does not have a check-in identifier so they can't be checked in": "Ng\u01b0\u1eddi n\u00e0y kh\u00f4ng c\u00f3 m\u00e3 \u0111i\u1ec3m danh n\u00ean h\u1ecd kh\u00f4ng th\u1ec3 \u0111\u01b0\u1ee3c \u0111i\u1ec3m danh",
    "Thursday": "\u0161tvrtok",
    "Today": "H\u00f4m nay",
    "Tomorrow": "Ng\u00e0y mai",
    "Total:": "Celkovo:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "Shadow",
    "Tuesday": "utorok",
    "Turn On Sounds": "B\u1eadt \u00c2m Thanh",
    "Type into this box to filter down the list of available %s.": "B\u1ea1n h\u00e3y nh\u1eadp v\u00e0o \u00f4 n\u00e0y \u0111\u1ec3 l\u1ecdc c\u00e1c danh s\u00e1ch sau %s.",
    "Type into this box to filter down the list of selected %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie ozna\u010den\u00fdch %s.",
    "Unaffiliated": "Nez\u00e1visl\u00fd",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised": "Ch\u01b0a ph\u00e2n lo\u1ea1i",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unknown": "Kh\u00f4ng x\u00e1c \u0111\u1ecbnh",
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
    "Yesterday": "H\u00f4m qua",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "B\u1ea1n \u0111\u00e3 ch\u1ecdn m\u1ed9t h\u00e0nh \u0111\u1ed9ng v\u00e0 b\u1ea1n \u0111\u00e3 kh\u00f4ng th\u1ef1c hi\u1ec7n b\u1ea5t k\u1ef3 thay \u0111\u1ed5i n\u00e0o tr\u00ean c\u00e1c tr\u01b0\u1eddng. C\u00f3 l\u1ebd b\u1ea1n n\u00ean b\u1ea5m n\u00fat \u0110i \u0111\u1ebfn h\u01a1n l\u00e0 n\u00fat L\u01b0u l\u1ea1i.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "B\u1ea1n \u0111\u00e3 ch\u1ecdn m\u1ed9t h\u00e0nh \u0111\u1ed9ng, nh\u01b0ng b\u1ea1n ch\u01b0a l\u01b0u c\u00e1c thay \u0111\u1ed5i tr\u00ean c\u00e1c tr\u01b0\u1eddng. Vui l\u00f2ng b\u1ea5m OK \u0111\u1ec3 l\u01b0u l\u1ea1i. B\u1ea1n s\u1ebd c\u1ea7n ch\u1ea1y l\u1ea1i h\u00e0nh d\u1ed9ng.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "B\u1ea1n ch\u01b0a l\u01b0u nh\u1eefng tr\u01b0\u1eddng \u0111\u00e3 ch\u1ec9nh s\u1eeda. N\u1ebfu b\u1ea1n ch\u1ecdn h\u00e0nh \u0111\u1ed9ng n\u00e0y, nh\u1eefng ch\u1ec9nh s\u1eeda ch\u01b0a \u0111\u01b0\u1ee3c l\u01b0u s\u1ebd b\u1ecb m\u1ea5t.",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "pi",
    "abbrev. day Monday\u0004Mon": "po",
    "abbrev. day Saturday\u0004Sat": "so",
    "abbrev. day Sunday\u0004Sun": "ne",
    "abbrev. day Thursday\u0004Thur": "\u0161t",
    "abbrev. day Tuesday\u0004Tue": "ut",
    "abbrev. day Wednesday\u0004Wed": "st",
    "abbrev. month April\u0004Apr": "Th\u00e1ng T\u01b0",
    "abbrev. month August\u0004Aug": "Th\u00e1ng T\u00e1m",
    "abbrev. month December\u0004Dec": "Th\u00e1ng M\u01b0\u1eddi Hai",
    "abbrev. month February\u0004Feb": "Th\u00e1ng Hai",
    "abbrev. month January\u0004Jan": "Th\u00e1ng M\u1ed9t",
    "abbrev. month July\u0004Jul": "Th\u00e1ng B\u1ea3y",
    "abbrev. month June\u0004Jun": "Th\u00e1ng S\u00e1u",
    "abbrev. month March\u0004Mar": "Th\u00e1ng Ba",
    "abbrev. month May\u0004May": "Th\u00e1ng N\u0103m",
    "abbrev. month November\u0004Nov": "Th\u00e1ng M\u01b0\u1eddi M\u1ed9t",
    "abbrev. month October\u0004Oct": "Th\u00e1ng M\u01b0\u1eddi",
    "abbrev. month September\u0004Sep": "Th\u00e1ng Ch\u00edn",
    "adjudicators with gender data": "rozhodcovia s \u00fadajmi o rode",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "desatinn\u00e9 body s\u00fa povolen\u00e9",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "bez polbodov",
    "one letter Friday\u0004F": "6",
    "one letter Monday\u0004M": "2",
    "one letter Saturday\u0004S": "7",
    "one letter Sunday\u0004S": "CN",
    "one letter Thursday\u0004T": "5",
    "one letter Tuesday\u0004T": "3",
    "one letter Wednesday\u0004W": "4",
    "optional": "nepovinn\u00e9",
    "saving...": "\u0111ang l\u01b0u...",
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
    "DATETIME_FORMAT": "H:i \\N\\g\u00e0\\y d \\t\\h\u00e1\\n\\g n \\n\u0103\\m Y",
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
    "DATE_FORMAT": "\\N\\g\u00e0\\y d \\t\\h\u00e1\\n\\g n \\n\u0103\\m Y",
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
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "H:i d-m-Y",
    "SHORT_DATE_FORMAT": "d-m-Y",
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

