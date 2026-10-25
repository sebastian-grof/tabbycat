
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
      "%(sel)s z %(cnt)s vybran\u00e9",
      "%(sel)s z %(cnt)s vybran\u00e9"
    ],
    "%1 %2 from %3": "crwdns34816:0%1crwdnd34816:0%2crwdnd34816:0%3crwdne34816:0",
    "%1 %2 from %3 %4": "crwdns34818:0%1crwdnd34818:0%2crwdnd34818:0%3crwdnd34818:0%4crwdne34818:0",
    "%1 %2 from %3 on %4 (Chair)": "crwdns34820:0%1crwdnd34820:0%2crwdnd34820:0%3crwdnd34820:0%4crwdne34820:0",
    "%1 %2 from %3 on %4 (Panellist)": "crwdns34822:0%1crwdnd34822:0%2crwdnd34822:0%3crwdnd34822:0%4crwdne34822:0",
    "%1 %2 from %3 on %4 (Trainee)": "crwdns34824:0%1crwdnd34824:0%2crwdnd34824:0%3crwdnd34824:0%4crwdne34824:0",
    "%1 (%2) with identifier of %3": "crwdns34804:0%1crwdnd34804:0%2crwdnd34804:0%3crwdne34804:0",
    "%1 (%2) with no assigned identifier": "crwdns34808:0%1crwdnd34808:0%2crwdne34808:0",
    "%1 (%2, %3)": "crwdns34886:0%1crwdnd34886:0%2crwdnd34886:0%3crwdne34886:0",
    "%1 (Absent; id=%2)": "crwdns34790:0%1crwdnd34790:0%2crwdne34790:0",
    "%1 (Present; id=%2)": "crwdns34788:0%1crwdnd34788:0%2crwdne34788:0",
    "%1 (no category) with identifier of %2": "crwdns34806:0%1crwdnd34806:0%2crwdne34806:0",
    "%1 (no category) with no assigned identifier": "crwdns34810:0%1crwdne34810:0",
    "%1 checked in %2: %3": "crwdns34752:0%1crwdnd34752:0%2crwdnd34752:0%3crwdne34752:0",
    "%1, %2": "crwdns34908:0%1crwdnd34908:0%2crwdne34908:0",
    "%1, a %2": "crwdns34794:0%1crwdnd34794:0%2crwdne34794:0",
    "%1, a %2 from %3 with identifier of %4": "crwdns34784:0%1crwdnd34784:0%2crwdnd34784:0%3crwdnd34784:0%4crwdne34784:0",
    "%1, a %2 from %3 with no assigned identifier": "crwdns34786:0%1crwdnd34786:0%2crwdnd34786:0%3crwdne34786:0",
    "%1, a %2 of no institutional affiliation with identifier of %3": "crwdns34780:0%1crwdnd34780:0%2crwdnd34780:0%3crwdne34780:0",
    "%1, a %2 of no institutional affiliation with no assigned identifier": "crwdns34782:0%1crwdnd34782:0%2crwdne34782:0",
    "%1, a team with speakers %2": "crwdns34792:0%1crwdnd34792:0%2crwdne34792:0",
    "%1:": "crwdns34864:0%1crwdne34864:0",
    "%s event": [
      "%s udalos\u0165",
      "%s udalosti"
    ],
    "%s selected option not visible": [
      "%s ozna\u010den\u00e1 mo\u017enos\u0165 sa nezobrazuje",
      "%s ozna\u010den\u00e9 mo\u017enosti sa nezobrazuj\u00fa"
    ],
    "6 a.m.": "6:00",
    "6 p.m.": "18:00",
    "; ": "crwdns34890:0crwdne34890:0",
    "<strong>%1</strong>: %2": "crwdns34852:0%1crwdnd34852:0%2crwdne34852:0",
    "<strong>\u2613</strong> All": "crwdns34766:0crwdne34766:0",
    "<strong>\u2713</strong> All": "crwdns34764:0crwdne34764:0",
    "Active": "Akt\u00edvna",
    "Add Ballot": "crwdns35022:0crwdne35022:0",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicating with %1.": "crwdns34888:0%1crwdne34888:0",
    "Adjudicator Demographics": "crwdns34992:0crwdne34992:0",
    "Adjudicator Results": "crwdns34996:0crwdne34996:0",
    "Aff Veto": "crwdns34854:0crwdne34854:0",
    "All": "crwdns34754:0crwdne34754:0",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "crwdns34798:0crwdne34798:0",
    "Anonymous (due to team codes)": "crwdns34796:0crwdne34796:0",
    "April": "apr\u00edl",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "august",
    "Auto-Allocate": "crwdns35034:0crwdne35034:0",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-Prioritise": "crwdns35032:0crwdne35032:0",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "Dostupn\u00e9 %s",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "crwdns35010:0crwdne35010:0",
    "Ballot Statuses": "crwdns35018:0crwdne35018:0",
    "Ballots Status": "crwdns34968:0crwdne34968:0",
    "Break": "crwdns35639:0crwdne35639:0",
    "By ": "Od ",
    "By %1": "crwdns34756:0%1crwdne34756:0",
    "By how many points did they win:": "crwdns34906:0crwdne34906:0",
    "Cancel": "Zru\u0161i\u0165",
    "Category": "crwdns35647:0crwdne35647:0",
    "Chair": "Chair",
    "Chair for Panel of %1": "crwdns34830:0%1crwdne34830:0",
    "Check time": "Skontrolujte \u010das",
    "Checked-In": "crwdns35006:0crwdne35006:0",
    "Choose": "Vybra\u0165",
    "Choose a Date": "Vybra\u0165 D\u00e1tum",
    "Choose a Time": "Vybra\u0165 \u010cas",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "Vybra\u0165 \u010das",
    "Choose all": "Vybra\u0165 v\u0161etko",
    "Chosen %s": "Vybran\u00e9 %s",
    "Circle %1": "crwdns34850:0%1crwdne34850:0",
    "Circle Rank:": "crwdns34938:0crwdne34938:0",
    "Circle the last digit of the %1's score:": "crwdns34916:0%1crwdne34916:0",
    "Circle the last digit of the team's total:": "crwdns34950:0crwdne34950:0",
    "Click to check-in manually": "crwdns34768:0crwdne34768:0",
    "Click to choose all %s at once.": "Kliknite sem pre vybratie v\u0161etk\u00fdch %s naraz.",
    "Click to remove all chosen %s at once.": "Kliknite sem pre vymazanie vybrat\u00fdch %s naraz.",
    "Click to undo a check-in": "crwdns34778:0crwdne34778:0",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Confirmed": "crwdns35016:0crwdne35016:0",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Copy From Check-Ins": "crwdns34966:0crwdne34966:0",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "Debated": "crwdns34848:0crwdne34848:0",
    "December": "december",
    "Delete this folder?": "Vymaza\u0165 tento prie\u010dinok?",
    "Delete this folder? Its contents will move up to the level above.": "Vymaza\u0165 tento prie\u010dinok? Jeho obsah sa presunie o \u00farove\u0148 vy\u0161\u0161ie.",
    "Description": "Popis",
    "Did %1 deliver the adjudication?": "crwdns34892:0%1crwdne34892:0",
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
    "February": "febru\u00e1r",
    "Filter": "Filtrova\u0165",
    "Find in Table": "crwdns34952:0crwdne34952:0",
    "Folders": "Prie\u010dinky",
    "Friday": "piatok",
    "Gender": "crwdns35641:0crwdne35641:0",
    "Hidden": "Skryt\u00e9",
    "Hide": "Skry\u0165",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "ID %1,": "crwdns34826:0%1crwdne34826:0",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "crwdns34910:0crwdne34910:0",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "crwdns34774:0crwdne34774:0",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "crwdns34800:0crwdne34800:0",
    "Institution": "Debatn\u00fd klub",
    "January": "janu\u00e1r",
    "July": "j\u00fal",
    "June": "j\u00fan",
    "Latest Actions": "crwdns34970:0crwdne34970:0",
    "Latest Results": "crwdns34974:0crwdne34974:0",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "marec",
    "Mark replies %1 to %2; <strong>%3</strong>.": "crwdns34842:0%1crwdnd34842:0%2crwdnd34842:0%3crwdne34842:0",
    "Mark speeches %1 to %2; <strong>%3</strong>.": "crwdns34840:0%1crwdnd34840:0%2crwdnd34840:0%3crwdne34840:0",
    "Match": "crwdns34958:0crwdne34958:0",
    "Match Check-Ins": "crwdns34962:0crwdne34962:0",
    "May": "m\u00e1j",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "Polnoc",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "pondelok",
    "Motion is:": "T\u00e9za je:",
    "N/A": "N/A",
    "Needs a date": "Ch\u00fdba d\u00e1tum",
    "Neg Veto": "crwdns34856:0crwdne34856:0",
    "New folder": "Nov\u00fd prie\u010dinok",
    "New schedule day": "Nov\u00fd de\u0148 rozvrhu",
    "No": "crwdns34902:0crwdne34902:0",
    "No ": "Nie ",
    "No Actions Yet": "crwdns34972:0crwdne34972:0",
    "No Adjudicator Ratings Information": "crwdns35002:0crwdne35002:0",
    "No Adjudicator-Adjudicator Feedback Information": "crwdns35004:0crwdne35004:0",
    "No Category": "crwdns35637:0crwdne35637:0",
    "No Confirmed Results Yet": "crwdns34976:0crwdne34976:0",
    "No Gender Information": "crwdns34980:0crwdne34980:0",
    "No Position Information": "crwdns34994:0crwdne34994:0",
    "No Region Information": "crwdns34990:0crwdne34990:0",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "crwdns34982:0crwdne34982:0",
    "No changes": "crwdns35028:0crwdne35028:0",
    "No code name set": "crwdns35064:0crwdne35064:0",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "crwdns34760:0crwdne34760:0",
    "No matching rooms found.": "crwdns51658:0crwdne51658:0",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "crwdns34896:0crwdne34896:0",
    "Noon": "Poludnie",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Not Checked-In": "crwdns35008:0crwdne35008:0",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "Pozn\u00e1mka: Ste %s hodinu pred \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hodiny pred \u010dasom servera."
    ],
    "Note: You are %s hour behind server time.": [
      "Pozn\u00e1mka: Ste %s hodinu za \u010dasom servera.",
      "Pozn\u00e1mka: Ste %s hodiny za \u010dasom servera."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "november",
    "Now": "Teraz",
    "October": "okt\u00f3ber",
    "Open": "Open",
    "Open the assistant version.": "crwdns34776:0crwdne34776:0",
    "Order": "Poradie",
    "Panellist": "crwdns34834:0crwdne34834:0",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Priority %1": "crwdns34814:0%1crwdne34814:0",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank": "crwdns35643:0crwdne35643:0",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "crwdns35024:0crwdne35024:0",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Region": "crwdns35645:0crwdne35645:0",
    "Remove": "Odstr\u00e1ni\u0165",
    "Remove all": "Odstr\u00e1ni\u0165 v\u0161etky",
    "Return ballots to %1.": "crwdns34844:0%1crwdne34844:0",
    "Return to Draw": "crwdns35030:0crwdne35030:0",
    "Review": "crwdns35026:0crwdne35026:0",
    "Room:": "crwdns51660:0crwdne51660:0",
    "Round": "Kolo",
    "Saturday": "sobota",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "crwdns34746:0crwdne34746:0",
    "Score:": "crwdns34914:0crwdne34914:0",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "september",
    "Set All Breaking as Available": "crwdns34954:0crwdne34954:0",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Set all availabilities to exactly match check-ins.": "crwdns34960:0crwdne34960:0",
    "Set all the availabilities to exactly match what they were in the previous round.": "crwdns34956:0crwdne34956:0",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "crwdns34964:0crwdne34964:0",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "Zobrazi\u0165",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "crwdns34832:0crwdne34832:0",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "crwdns34978:0crwdne34978:0",
    "Speaker Results": "crwdns34984:0crwdne34984:0",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "crwdns34748:0crwdne34748:0",
    "Sunday": "nede\u013ea",
    "Team": "crwdns34838:0crwdne34838:0",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "The bracket range of the hypothetical debate": "crwdns35056:0crwdne35056:0",
    "The debate's bracket": "crwdns35054:0crwdne35054:0",
    "The estimated total number of live break categories across all teams of the hypothetical debate": "crwdns35060:0crwdne35060:0",
    "The motion is <em>%1</em>": "crwdns34846:0%1crwdne34846:0",
    "The total number of live break categories across all teams": "crwdns35058:0crwdne35058:0",
    "This debate's priority": "crwdns35062:0crwdne35062:0",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre v\u00fdber je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVybra\u0165\u201c presun\u00fa\u0165.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre vymazanie je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVymaza\u0165\u201c vymaza\u0165.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "crwdns34762:0crwdne34762:0",
    "This person does not have a check-in identifier so they can't be checked in": "crwdns34772:0crwdne34772:0",
    "Thursday": "\u0161tvrtok",
    "Today": "Dnes",
    "Tomorrow": "Zajtra",
    "Total:": "crwdns34948:0crwdne34948:0",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "crwdns34836:0crwdne34836:0",
    "Tuesday": "utorok",
    "Turn On Sounds": "crwdns34750:0crwdne34750:0",
    "Type into this box to filter down the list of available %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie dostupn\u00fdch %s.",
    "Type into this box to filter down the list of selected %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie ozna\u010den\u00fdch %s.",
    "Unaffiliated": "crwdns34802:0crwdne34802:0",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised": "crwdns34812:0crwdne34812:0",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unconfirmed": "crwdns35014:0crwdne35014:0",
    "Unknown": "crwdns35012:0crwdne35012:0",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "crwdns34900:0crwdne34900:0",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Wednesday": "streda",
    "Which team won the debate:": "crwdns34904:0crwdne34904:0",
    "Yes": "crwdns34894:0crwdne34894:0",
    "Yesterday": "V\u010dera",
    "You cannot confirm this ballot because you entered it": "crwdns35020:0crwdne35020:0",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Vybrali ste akciu, ale neurobili ste \u017eiadne zmeny v jednotliv\u00fdch poliach. Pravdepodobne ste chceli pou\u017ei\u0165 tla\u010didlo Vykona\u0165 namiesto Ulo\u017ei\u0165.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Vybrali ste akciu, ale neulo\u017eili ste jednotliv\u00e9 polia. Pros\u00edm, ulo\u017ete zmeny kliknut\u00edm na OK. Akciu budete musie\u0165 vykona\u0165 znova.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Vr\u00e1mci jednotliv\u00fdch editovate\u013en\u00fdch pol\u00ed m\u00e1te neulo\u017een\u00e9 zmeny. Ak vykon\u00e1te akciu, va\u0161e zmeny bud\u00fa straten\u00e9.",
    "Z\u2013A": "Z\u2013A",
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
    "adjudicators with gender data": "crwdns34998:0crwdne34998:0",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "crwdns34876:0crwdne34876:0",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "feedback scores total": "crwdns35000:0crwdne35000:0",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "crwdns34872:0crwdne34872:0",
    "one letter Friday\u0004F": "P",
    "one letter Monday\u0004M": "P",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "N",
    "one letter Thursday\u0004T": "\u0160",
    "one letter Tuesday\u0004T": "U",
    "one letter Wednesday\u0004W": "S",
    "optional": "nepovinn\u00e9",
    "saving...": "crwdns34770:0crwdne34770:0",
    "speaker scores analysed": "analyzovan\u00fdch sk\u00f3re re\u010dn\u00edkov",
    "speaker scores total": "crwdns34988:0crwdne34988:0",
    "speakers with gender data": "crwdns34986:0crwdne34986:0",
    "tab check": "crwdns34868:0crwdne34868:0",
    "tab entry": "crwdns34866:0crwdne34866:0",
    "tournament": "turnaj",
    "tournaments": "turnaje",
    "unconfirmed": "nepotvrden\u00e9",
    "\u00bd marks are allowed": "crwdns34874:0crwdne34874:0",
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
    "DATETIME_FORMAT": "j M Y, P",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%d/%m/%y %H:%M:%S",
      "%d/%m/%y %H:%M:%S.%f",
      "%d/%m/%y %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j M Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ".",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "j M Y P",
    "SHORT_DATE_FORMAT": "j M Y",
    "THOUSAND_SEPARATOR": ",",
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

