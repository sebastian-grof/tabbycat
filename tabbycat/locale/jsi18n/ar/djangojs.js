
'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5);
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
      "\u0644\u0627 \u0634\u064a \u0645\u062d\u062f\u062f",
      "%(sel)s \u0645\u0646 %(cnt)s \u0645\u062d\u062f\u062f",
      "%(sel)s \u0645\u0646 %(cnt)s \u0645\u062d\u062f\u062f",
      "%(sel)s \u0645\u0646 %(cnt)s \u0645\u062d\u062f\u062f\u0629",
      "%(sel)s \u0645\u0646 %(cnt)s \u0645\u062d\u062f\u062f",
      "%(sel)s \u0645\u0646 %(cnt)s \u0645\u062d\u062f\u062f"
    ],
    "%s event": [
      "%s udalos\u0165",
      "%s udalosti",
      "%s udalosti",
      "%s udalost\u00ed",
      "",
      ""
    ],
    "%s selected option not visible": [
      "%s ozna\u010den\u00e1 mo\u017enos\u0165 sa nezobrazuje",
      "%s ozna\u010den\u00e9 mo\u017enosti sa nezobrazuj\u00fa",
      "%s ozna\u010den\u00fdch mo\u017enost\u00ed sa nezobrazuje",
      "%s ozna\u010den\u00fdch mo\u017enost\u00ed sa nezobrazuje",
      "",
      ""
    ],
    "6 a.m.": "6 \u0635.",
    "6 p.m.": "6 \u0645\u0633\u0627\u0621\u064b",
    "; ": "; ",
    "Active": "Akt\u00edvna",
    "Add": "\u0623\u0636\u0641",
    "Add Ballot": "Prida\u0165 Ballot",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicator Demographics": "\u062a\u0648\u0632\u064a\u0639 \u0627\u0644\u062d\u0643\u0627\u0645 ",
    "Adjudicator Results": "\u0646\u062a\u0627\u0626\u062c \u0627\u0644\u062d\u0643\u0645 ",
    "All": "\u0627\u0644\u0643\u0644",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "Anon",
    "Anonymous (due to team codes)": "Anonymn\u00e9 (kv\u00f4li t\u00edmov\u00fdm k\u00f3dom)",
    "April": "\u0623\u0628\u0631\u064a\u0644",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "\u0623\u063a\u0633\u0637\u0633",
    "Auto-Allocate": "Automatick\u00e9 pride\u013eovanie",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "%s \u0627\u0644\u0645\u062a\u0648\u0641\u0631\u0629",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "Registr\u00e1cia ballotov",
    "Ballot Statuses": "Status Ballotov",
    "Ballots Status": "Status ballotov",
    "Break": "\u062a\u0623\u0647\u0644 ",
    "By ": "Od ",
    "By how many points did they win:": "O ko\u013eko bodov vyhrali:",
    "Cancel": "\u0625\u0644\u063a\u0627\u0621",
    "Category": "\u0627\u0644\u0641\u0626\u0629",
    "Chair": "Chair",
    "Check time": "Skontrolujte \u010das",
    "Choose": "\u0627\u062e\u062a\u064a\u0627\u0631",
    "Choose a Date": "\u0625\u062e\u062a\u0631 \u062a\u0627\u0631\u064a\u062e ",
    "Choose a Time": "\u0625\u062e\u062a\u0631 \u0648\u0642\u062a",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "\u0627\u062e\u062a\u0631 \u0648\u0642\u062a\u0627\u064b",
    "Choose all": "\u0627\u062e\u062a\u0631 \u0627\u0644\u0643\u0644",
    "Chosen %s": "%s \u0627\u0644\u0645\u064f\u062e\u062a\u0627\u0631\u0629",
    "Circle Rank:": "Zakr\u00fa\u017ekuj poradie:",
    "Circle the last digit of the team's total:": "Zakr\u00fa\u017ekuj posledn\u00fa \u010d\u00edslicu t\u00edmov\u00e9ho s\u00fa\u010dtu:",
    "Click to choose all %s at once.": "\u0627\u0636\u063a\u0637 \u0644\u0627\u062e\u062a\u064a\u0627\u0631 \u062c\u0645\u064a\u0639 %s \u062c\u0645\u0644\u0629 \u0648\u0627\u062d\u062f\u0629.",
    "Click to remove all chosen %s at once.": "\u0627\u0636\u063a\u0637 \u0644\u0625\u0632\u0627\u0644\u0629 \u062c\u0645\u064a\u0639 %s \u0627\u0644\u0645\u062d\u062f\u062f\u0629 \u062c\u0645\u0644\u0629 \u0648\u0627\u062d\u062f\u0629.",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Confirmed": "\u0645\u0639\u062a\u0645\u062f",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Copy From Check-Ins": "\u0646\u0633\u062e\u0629 \u0645\u0646 \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644 ",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "December": "\u062f\u064a\u0633\u0645\u0628\u0631",
    "Delete": "\u062d\u0630\u0641",
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
    "February": "\u0641\u0628\u0631\u0627\u064a\u0631",
    "Filter": "\u062a\u0635\u0641\u064a\u0629",
    "Find in Table": "\u0627\u0644\u0628\u062d\u062b \u0641\u064a \u0627\u0644\u062c\u062f\u0648\u0644",
    "Folders": "Prie\u010dinky",
    "Friday": "piatok",
    "General": "\u0639\u0627\u0645",
    "Hidden": "Skryt\u00e9",
    "Hide": "\u0627\u062e\u0641",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "D\u00d4LE\u017dIT\u00c9: Skontrolujte a explicitne zazna\u010dte, \u010di re\u010dn\u00edk prednesie viacero re\u010d\u00ed",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "Nez\u00e1visl\u00fd",
    "Institution": "Debatn\u00fd klub",
    "January": "\u064a\u0646\u0627\u064a\u0631",
    "July": "\u064a\u0648\u0644\u064a\u0648",
    "June": "\u064a\u0648\u0646\u064a\u0648",
    "Latest Actions": "Najnov\u0161ie akcie",
    "Latest Results": "Najnov\u0161ie v\u00fdsledky",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "\u0645\u0627\u0631\u0633",
    "Match": "\u062a\u0648\u0627\u0641\u0642",
    "Match Check-Ins": "\u062a\u0634\u0627\u0628\u0647 \u0627\u0644\u0625\u062f\u062e\u0627\u0644 ",
    "May": "\u0645\u0627\u064a\u0648",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "\u0645\u0646\u062a\u0635\u0641 \u0627\u0644\u0644\u064a\u0644",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "pondelok",
    "Motion is:": "T\u00e9za je:",
    "N/A": "N/A",
    "Needs a date": "Ch\u00fdba d\u00e1tum",
    "New folder": "Nov\u00fd prie\u010dinok",
    "New schedule day": "Nov\u00fd de\u0148 rozvrhu",
    "No": "\u0644\u0627",
    "No ": "Nie ",
    "No Actions Yet": "Zatia\u013e \u017eiadne akcie",
    "No Adjudicator Ratings Information": "\u0644\u0627 \u062a\u0648\u062c\u062f \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u062d\u0648\u0644 \u062a\u0635\u0646\u064a\u0641 \u0627\u0644\u062d\u0643\u0627\u0645",
    "No Adjudicator-Adjudicator Feedback Information": "\u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0639\u0646 \u0627\u0644\u062a\u063a\u0630\u064a\u0629 \u0627\u0644\u0631\u0627\u062c\u0639\u0629 \u062d\u0648\u0644 \u062a\u062d\u0643\u064a\u0645 \u0627\u0644\u0645\u062d\u0643\u0645\u064a\u0646 ",
    "No Category": "Bez kateg\u00f3rie",
    "No Confirmed Results Yet": "Zatia\u013e \u017eiadne potvrden\u00e9 v\u00fdsledky",
    "No Gender Information": "\u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u062c\u0646\u0633",
    "No Position Information": "\u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0639\u0646 \u0627\u0644\u0648\u0638\u064a\u0641\u0629 ",
    "No Region Information": "\u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0639\u0646 \u0627\u0644\u0645\u0646\u0637\u0642\u0629 ",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "\u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0639\u0646 \u0641\u0626\u0629 \u0627\u0644\u0645\u062a\u062d\u062f\u062b ",
    "No code name set": "Nie je nastaven\u00e9 k\u00f3dov\u00e9 meno",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face osoby.",
    "No matching rooms found.": "Nena\u0161li sa \u017eiadne zodpovedaj\u00face mietnosti.",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "Nie, odosielam sp\u00e4tn\u00fa v\u00e4zbu na:",
    "Noon": "\u0627\u0644\u0638\u0647\u0631",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0642\u062f\u0645 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0642\u062f\u0645 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0642\u062f\u0645 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0642\u062f\u0645 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0642\u062f\u0645 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0642\u062f\u0645 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645."
    ],
    "Note: You are %s hour behind server time.": [
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0623\u062e\u0631 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0623\u062e\u0631 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0623\u062e\u0631 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0623\u062e\u0631 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0623\u062e\u0631 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645.",
      "\u0645\u0644\u0627\u062d\u0638\u0629: \u0623\u0646\u062a \u0645\u062a\u0623\u062e\u0631 \u0628\u0640 %s \u0633\u0627\u0639\u0629 \u0645\u0646 \u0648\u0642\u062a \u0627\u0644\u062e\u0627\u062f\u0645."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "\u0646\u0648\u0641\u0645\u0628\u0631",
    "Now": "\u0627\u0644\u0622\u0646",
    "October": "\u0623\u0643\u062a\u0648\u0628\u0631",
    "Open": "Open",
    "Order": "Poradie",
    "Panellist": "Panelista",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank": "\u0627\u0644\u0645\u0633\u062a\u0648\u0649",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "Op\u00e4tovn\u00e1 \u00faprava",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Remove": "\u0627\u062d\u0630\u0641",
    "Remove all": "\u0625\u0632\u0627\u0644\u0629 \u0627\u0644\u0643\u0644",
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
    "September": "\u0633\u0628\u062a\u0645\u0628\u0631",
    "Set All Breaking as Available": "\u0648\u0636\u0639 \u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u062a\u0623\u0647\u0644\u064a\u0646 \"\u0645\u062a\u0648\u0627\u062c\u062f\u0648\u0646\"",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Set all the availabilities to exactly match what they were in the previous round.": "\u062a\u0639\u064a\u064a\u0646 \u062c\u0645\u064a\u0639 \u0627\u0644\u0623\u0634\u064a\u0627\u0621 \u0644\u0644\u062a\u062a\u0648\u0627\u0641\u0642 \u0645\u0639 \u062a\u0644\u0643 \u0627\u0644\u0645\u062a\u0627\u062d\u0629 \u0641\u064a \u0627\u0644\u062c\u0648\u0644\u0629 \u0627\u0644\u0633\u0627\u0628\u0642\u0629.",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "\u062a\u0639\u064a\u064a\u0646 \u0627\u0644\u0623\u0634\u062e\u0627\u0635 \u0639\u0644\u0649 \u0623\u0646\u0647\u0627 \u0645\u062a\u0648\u0641\u0631\u0629 \u0641\u0642\u0637 \u0625\u0630\u0627 \u0643\u0627\u0646 \u0644\u062f\u064a\u0647\u0645 \u062a\u0633\u062c\u064a\u0644 \u062f\u062e\u0648\u0644 \u0648 \u063a\u064a\u0631 \u0645\u062a\u0627\u062d\u0648\u0646 \u062d\u0627\u0644\u064a\u064b\u0627 \u2014 \u0628\u0645\u0639\u0646\u0649 \u0623\u0646\u0647 \u0644\u0646 \u064a\u0624\u062f\u064a \u0625\u0644\u0649 \u0627\u0633\u062a\u0628\u062f\u0627\u0644 \u0623\u064a \u0645\u0646 \u0627\u0644\u0645\u062a\u0648\u0641\u0631\u064a\u0646 \u062d\u0627\u0644\u064a\u0627.",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "\u0623\u0638\u0647\u0631",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "Samostatn\u00fd Chair",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "\u062a\u0648\u0632\u064a\u0639 \u0627\u0644\u0645\u062a\u062d\u062f\u062b\u064a\u0646 ",
    "Speaker Results": "\u0646\u062a\u0627\u0626\u062c \u0627\u0644\u0645\u062a\u062d\u062f\u062b ",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "Zastavi\u0165 skenovanie fotoapar\u00e1tom",
    "Sunday": "nede\u013ea",
    "Team": "\u0641\u0631\u064a\u0642",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u0647\u0630\u0647 \u0642\u0627\u0626\u0645\u0629 %s \u0627\u0644\u0645\u062a\u0648\u0641\u0631\u0629. \u064a\u0645\u0643\u0646\u0643 \u0627\u062e\u062a\u064a\u0627\u0631 \u0628\u0639\u0636\u0647\u0627 \u0628\u0627\u0646\u062a\u0642\u0627\u0626\u0647\u0627 \u0641\u064a \u0627\u0644\u0635\u0646\u062f\u0648\u0642 \u0623\u062f\u0646\u0627\u0647 \u062b\u0645 \u0627\u0644\u0636\u063a\u0637 \u0639\u0644\u0649 \u0633\u0647\u0645 \u0627\u0644\u0640\"\u0627\u062e\u062a\u064a\u0627\u0631\" \u0628\u064a\u0646 \u0627\u0644\u0635\u0646\u062f\u0648\u0642\u064a\u0646.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u0647\u0630\u0647 \u0642\u0627\u0626\u0645\u0629 %s \u0627\u0644\u0645\u062d\u062f\u062f\u0629. \u064a\u0645\u0643\u0646\u0643 \u0625\u0632\u0627\u0644\u0629 \u0628\u0639\u0636\u0647\u0627 \u0628\u0627\u062e\u062a\u064a\u0627\u0631\u0647\u0627 \u0641\u064a \u0627\u0644\u0635\u0646\u062f\u0648\u0642 \u0623\u062f\u0646\u0627\u0647 \u062b\u0645 \u0627\u0636\u063a\u0637 \u0639\u0644\u0649 \u0633\u0647\u0645 \u0627\u0644\u0640\"\u0625\u0632\u0627\u0644\u0629\" \u0628\u064a\u0646 \u0627\u0644\u0635\u0646\u062f\u0648\u0642\u064a\u0646.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "T\u00e1to str\u00e1nka sa bude aktualizova\u0165 v re\u00e1lnom \u010dase s nov\u00fdmi registr\u00e1ciami, ako sa bud\u00fa vyskytova\u0165, hoci po\u010diato\u010dn\u00fd zoznam m\u00f4\u017ee by\u0165 star\u00fd a\u017e jednu min\u00fatu.",
    "Thursday": "\u0161tvrtok",
    "Today": "\u0627\u0644\u064a\u0648\u0645",
    "Tomorrow": "\u063a\u062f\u0627\u064b",
    "Total:": "Celkovo:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "Shadow",
    "Tuesday": "utorok",
    "Turn On Sounds": "Zapn\u00fa\u0165 zvuky",
    "Type into this box to filter down the list of available %s.": "\u0627\u0643\u062a\u0628 \u0641\u064a \u0647\u0630\u0627 \u0627\u0644\u0635\u0646\u062f\u0648\u0642 \u0644\u062a\u0635\u0641\u064a\u0629 \u0642\u0627\u0626\u0645\u0629 %s \u0627\u0644\u0645\u062a\u0648\u0641\u0631\u0629.",
    "Type into this box to filter down the list of selected %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie ozna\u010den\u00fdch %s.",
    "Unaffiliated": "\u063a\u064a\u0631 \u0645\u0646\u062a\u0633\u0628\u064a\u0646",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unknown": "\u0645\u062c\u0647\u0648\u0644 ",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "Nie som si ist\u00fd/\u00e1",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Warning: you have unsaved changes": "\u062a\u062d\u0630\u064a\u0631: \u0644\u062f\u064a\u0643 \u062a\u063a\u064a\u0631\u0627\u062a \u063a\u064a\u0631 \u0645\u062d\u0641\u0648\u0638\u0629",
    "Wednesday": "streda",
    "Which team won the debate:": "Ktor\u00fd t\u00edm vyhral debatu:",
    "Yes": "\u0646\u0639\u0645 ",
    "Yesterday": "\u0623\u0645\u0633",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "\u0644\u0642\u062f \u062d\u062f\u062f\u062a \u0625\u062c\u0631\u0627\u0621 \u060c \u0648\u0644\u0645 \u062a\u0642\u0645 \u0628\u0625\u062c\u0631\u0627\u0621 \u0623\u064a \u062a\u063a\u064a\u064a\u0631\u0627\u062a \u0639\u0644\u0649 \u0627\u0644\u062d\u0642\u0648\u0644 \u0627\u0644\u0641\u0631\u062f\u064a\u0629. \u0645\u0646 \u0627\u0644\u0645\u062d\u062a\u0645\u0644 \u0623\u0646\u0643 \u062a\u0628\u062d\u062b \u0639\u0646 \u0627\u0644\u0632\u0631 \u0623\u0630\u0647\u0628 \u0628\u062f\u0644\u0627\u064b \u0645\u0646 \u0627\u0644\u0632\u0631 \u062d\u0641\u0638.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "\u0644\u0642\u062f \u062d\u062f\u062f\u062a \u0625\u062c\u0631\u0627\u0621\u064b \u060c \u0644\u0643\u0646\u0643 \u0644\u0645 \u062a\u062d\u0641\u0638 \u062a\u063a\u064a\u064a\u0631\u0627\u062a\u0643 \u0641\u064a \u0627\u0644\u062d\u0642\u0648\u0644 \u0627\u0644\u0641\u0631\u062f\u064a\u0629 \u062d\u062a\u0649 \u0627\u0644\u0622\u0646. \u064a\u0631\u062c\u0649 \u0627\u0644\u0646\u0642\u0631 \u0641\u0648\u0642 \u0645\u0648\u0627\u0641\u0642 \u0644\u0644\u062d\u0641\u0638. \u0633\u062a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u0625\u0639\u0627\u062f\u0629 \u062a\u0634\u063a\u064a\u0644 \u0627\u0644\u0625\u062c\u0631\u0627\u0621.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0644\u062f\u064a\u0643 \u062a\u0639\u062f\u064a\u0644\u0627\u062a \u063a\u064a\u0631 \u0645\u062d\u0641\u0648\u0638\u0629 \u0639\u0644\u0649 \u0628\u0639\u0636 \u0627\u0644\u062d\u0642\u0648\u0644 \u0627\u0644\u0642\u0627\u0628\u0644\u0629 \u0644\u0644\u062a\u0639\u062f\u064a\u0644. \u0625\u0646 \u0646\u0641\u0630\u062a \u0623\u064a \u0625\u062c\u0631\u0627\u0621 \u0641\u0633\u0648\u0641 \u062a\u062e\u0633\u0631 \u062a\u0639\u062f\u064a\u0644\u0627\u062a\u0643.",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "pi",
    "abbrev. day Monday\u0004Mon": "po",
    "abbrev. day Saturday\u0004Sat": "so",
    "abbrev. day Sunday\u0004Sun": "ne",
    "abbrev. day Thursday\u0004Thur": "\u0161t",
    "abbrev. day Tuesday\u0004Tue": "ut",
    "abbrev. day Wednesday\u0004Wed": "st",
    "abbrev. month April\u0004Apr": "\u0625\u0628\u0631\u064a\u0644",
    "abbrev. month August\u0004Aug": "\u0623\u063a\u0633\u0637\u0633",
    "abbrev. month December\u0004Dec": "\u062f\u064a\u0633\u0645\u0628\u0631",
    "abbrev. month February\u0004Feb": "\u0641\u0628\u0631\u0627\u064a\u0631",
    "abbrev. month January\u0004Jan": "\u064a\u0646\u0627\u064a\u0631",
    "abbrev. month July\u0004Jul": "\u064a\u0648\u0644\u064a\u0648",
    "abbrev. month June\u0004Jun": "\u064a\u0648\u0646\u064a\u0648",
    "abbrev. month March\u0004Mar": "\u0645\u0627\u0631\u0633",
    "abbrev. month May\u0004May": "\u0645\u0627\u064a\u0648",
    "abbrev. month November\u0004Nov": "\u0646\u0648\u0641\u0645\u0628\u0631",
    "abbrev. month October\u0004Oct": "\u0623\u0643\u062a\u0648\u0628\u0631",
    "abbrev. month September\u0004Sep": "\u0633\u0628\u062a\u0645\u0628\u0631",
    "adjudicators with gender data": "\u0627\u0644\u062d\u0643\u0627\u0645 \u0645\u0639 \u0628\u064a\u0627\u0646\u0627\u062a \u062c\u0646\u0633\u0647\u0645",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "desatinn\u00e9 body s\u00fa povolen\u00e9",
    "deselect all": "\u0625\u0644\u063a\u0627\u0621 \u062a\u062d\u062f\u064a\u062f \u0627\u0644\u0643\u0644",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "feedback scores total": "\u0645\u062c\u0645\u0648\u0639 \u062f\u0631\u062c\u0627\u062a \u0627\u0644\u062a\u063a\u0630\u064a\u0629 \u0627\u0644\u0631\u0627\u062c\u0639\u0629 ",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "bez polbodov",
    "one letter Friday\u0004F": "\u062c\u0645\u0639\u0629",
    "one letter Monday\u0004M": "\u0625\u062b\u0646\u064a\u0646",
    "one letter Saturday\u0004S": "\u0633\u0628\u062a",
    "one letter Sunday\u0004S": "\u0623\u062d\u062f",
    "one letter Thursday\u0004T": "\u062e\u0645\u064a\u0633",
    "one letter Tuesday\u0004T": "\u062b\u0644\u0627\u062b\u0627\u0621",
    "one letter Wednesday\u0004W": "\u0623\u0631\u0628\u0639\u0627\u0621",
    "optional": "nepovinn\u00e9",
    "select all": "\u062a\u062d\u062f\u064a\u062f \u0627\u0644\u0643\u0644",
    "speaker scores analysed": "analyzovan\u00fdch sk\u00f3re re\u010dn\u00edkov",
    "speaker scores total": "\u0645\u062c\u0645\u0648\u0639 \u062f\u0631\u062c\u0627\u062a \u0627\u0644\u0645\u062a\u062d\u062f\u062b ",
    "speakers with gender data": "\u0627\u0644\u0645\u062a\u062d\u062f\u062b\u0648\u0646 \u0645\u0639 \u0628\u064a\u0627\u0646\u0627\u062a \u062c\u0646\u0633\u0647\u0645",
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
    "DATETIME_FORMAT": "N j, Y, P",
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
    "DATE_FORMAT": "j F\u060c Y",
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
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "SHORT_DATE_FORMAT": "d\u200f/m\u200f/Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "g:i A",
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

