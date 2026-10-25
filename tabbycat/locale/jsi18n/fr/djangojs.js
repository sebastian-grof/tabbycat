
'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n > 1);
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
      "%(sel)s sur %(cnt)s s\u00e9lectionn\u00e9",
      "%(sel)s sur %(cnt)s s\u00e9lectionn\u00e9s"
    ],
    "%1 %2 from %3": "%1 %2 par %3",
    "%1 %2 from %3 %4": "%1 %2 par %3 %4",
    "%1 %2 from %3 on %4 (Chair)": "%1 %2 par %3 sur %4 (Pr\u00e9sident)",
    "%1 %2 from %3 on %4 (Panellist)": "%1 %2 par %3 sur %4 (Panelliste)",
    "%1 %2 from %3 on %4 (Trainee)": "%1 %2 par %3 sur %4 (Stagiaire)",
    "%1 (%2) with identifier of %3": "%1 (%2) avec l'identifiant %3",
    "%1 (%2) with no assigned identifier": "%1 (%2) sans identifiant",
    "%1 (%2, %3)": "%1 (%2, %3)",
    "%1 (Absent; id=%2)": "%1 (Absent\u00a0; id=%2)",
    "%1 (Present; id=%2)": "%1 (Pr\u00e9sent\u00a0; id=%2)",
    "%1 (no category) with identifier of %2": "%1 (aucune cat\u00e9gorie) avec l'identifiant %2",
    "%1 (no category) with no assigned identifier": "%1 (aucune cat\u00e9gorie) sans identifiant",
    "%1 checked in %2: %3": "%1 enregistr\u00e9 %2\u00a0: %3",
    "%1, %2": "%1, %2",
    "%1, a %2": "%1, un %2",
    "%1, a %2 from %3 with identifier of %4": "%1, un %2 de %3 avec l'identifiant %4",
    "%1, a %2 from %3 with no assigned identifier": "%1, un %2 de %3 sans identifiant",
    "%1, a %2 of no institutional affiliation with identifier of %3": "%1, un %2 sans affiliation avec l'identifiant %3",
    "%1, a %2 of no institutional affiliation with no assigned identifier": "%1, un %2 sans affiliation ni identifiant",
    "%1, a team with speakers %2": "%1, un \u00e9quipe avec orateurs %2",
    "%1:": "%1\u00a0:",
    "%s event": [
      "%s udalos\u0165",
      "%s udalosti"
    ],
    "%s selected option not visible": [
      "%s option s\u00e9lectionn\u00e9e invisible",
      "%s options s\u00e9lectionn\u00e9es invisibles"
    ],
    "(click to clear)": "(cliquer pour effacer)",
    "6 a.m.": "6:00",
    "6 p.m.": "18:00",
    "; ": " ; ",
    "<strong>%1</strong>: %2": "<strong>%1</strong>\u00a0: %2",
    "<strong>\u2613</strong> All": "<strong>\u2613</strong> Tous",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> Tous",
    "Active": "Akt\u00edvna",
    "Add": "Ajouter",
    "Add Ballot": "Ajouter feuille",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicating with %1.": "Jugeant avec %1.",
    "Adjudicator Demographics": "D\u00e9mographiques des juges",
    "Adjudicator Results": "R\u00e9sultats de juge",
    "Aff Veto": "V\u00e9to Aff",
    "All": "Tout",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "Anon",
    "Anonymous (due to team codes)": "Anonyme (en raison des codes d'\u00e9quipe)",
    "April": "Avril",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "Ao\u00fbt",
    "Auto-Allocate": "Allouer automatiquement",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-Prioritise": "Prioriser automatiquement",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "%s disponible(s)",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "Enregistrements de feuilles",
    "Ballot Statuses": "Statuts de feuilles",
    "Ballots Status": "Statuts des feuilles de jugement",
    "Break": "Qualification",
    "By ": "Od ",
    "By %1": "Par %1",
    "By how many points did they win:": "Par combien de points ont-ils gagn\u00e9\u00a0:",
    "Cancel": "Annuler",
    "Category": "Cat\u00e9gorie",
    "Chair": "Chair",
    "Chair for Panel of %1": "Pr\u00e9sident pour le jury de %1",
    "Check time": "Skontrolujte \u010das",
    "Checked-In": "Enregistr\u00e9",
    "Choose": "Vybra\u0165",
    "Choose %s by selecting them and then select the \"Choose\" arrow button.": "Choisissez %s en les s\u00e9lectionnant puis cliquez sur le bouton fl\u00e8che \u00ab\u00a0Choisir\u00a0\u00bb.",
    "Choose a Date": "Choisir une date",
    "Choose a Time": "Choisir une heure",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "Choisir une heure",
    "Choose all": "Vybra\u0165 v\u0161etko",
    "Choose all %s": "Choisir toutes les valeurs \u00ab\u00a0%s\u00a0\u00bb",
    "Choose selected %s": "Choisir les valeurs \u00ab\u00a0%s\u00a0\u00bb s\u00e9lectionn\u00e9es",
    "Chosen %s": "Choix des \u00ab\u00a0%s\u00a0\u00bb",
    "Circle %1": "Encercler %1",
    "Circle Rank:": "Encerclez le rang\u00a0:",
    "Circle the last digit of the %1's score:": "Encerclez le dernier chiffre du score de %1\u00a0:",
    "Circle the last digit of the team's total:": "Encerclez le dernier chiffre du total de l'\u00e9quipe\u00a0:",
    "Click to check-in manually": "Cliquer pour enregistrer manuellement",
    "Click to choose all %s at once.": "Kliknite sem pre vybratie v\u0161etk\u00fdch %s naraz.",
    "Click to remove all chosen %s at once.": "Kliknite sem pre vymazanie vybrat\u00fdch %s naraz.",
    "Click to undo a check-in": "Cliquez pour annuler un enregistrement",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Confirmed": "Confirm\u00e9",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Copy From Check-Ins": "Copier \u00e0 partir des enregistrements",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "Debated": "D\u00e9battu",
    "December": "D\u00e9cembre",
    "Delete": "\u00c9ffacer",
    "Delete this folder?": "Vymaza\u0165 tento prie\u010dinok?",
    "Delete this folder? Its contents will move up to the level above.": "Vymaza\u0165 tento prie\u010dinok? Jeho obsah sa presunie o \u00farove\u0148 vy\u0161\u0161ie.",
    "Description": "Popis",
    "Did %1 deliver the adjudication?": "%1 a-t-il livr\u00e9 le jugement\u00a0?",
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
    "February": "F\u00e9vrier",
    "Filter": "Filtrer",
    "Find in Table": "Trouver dans la table",
    "Folders": "Prie\u010dinky",
    "Friday": "vendredi",
    "Gender": "Genre",
    "General": "G\u00e9n\u00e9ral",
    "Hidden": "Skryt\u00e9",
    "Hide": "Skry\u0165",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "ID %1,": "ID %1,",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "IMPORTANT\u00a0: Cochez et notez explicitement si un orateur a donn\u00e9 plusieurs discours",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "Si vous voulez afficher cette page sans la barre lat\u00e9rale (comme pour l'affichage dans un auditorium), vous pouvez utiliser la version d'assistant.",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "Ind\u00e9pendant",
    "Institution": "Debatn\u00fd klub",
    "January": "Janvier",
    "July": "Juillet",
    "June": "Juin",
    "Latest Actions": "Derni\u00e8res Actions",
    "Latest Results": "Derni\u00e8res R\u00e9sultats",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "Mars",
    "Mark replies %1 to %2; <strong>%3</strong>.": "Marquer r\u00e9pliques de %1 \u00e0 %2\u00a0; <strong>%3</strong>.",
    "Mark speeches %1 to %2; <strong>%3</strong>.": "Marquer les discours de %1 \u00e0 %2\u00a0; <strong>%3</strong>.",
    "Match": "Refl\u00e9ter",
    "Match Check-Ins": "Refl\u00e9ter les enregistrements",
    "May": "Mai",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "Minuit",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "lundi",
    "Motion is:": "T\u00e9za je:",
    "N/A": "N/A",
    "Needs a date": "Ch\u00fdba d\u00e1tum",
    "Neg Veto": "V\u00e9to N\u00e9g",
    "New folder": "Nov\u00fd prie\u010dinok",
    "New schedule day": "Nov\u00fd de\u0148 rozvrhu",
    "No": "Non",
    "No ": "Nie ",
    "No Actions Yet": "Aucune Action",
    "No Adjudicator Ratings Information": "Pas d\u2019information de rang de juge",
    "No Adjudicator-Adjudicator Feedback Information": "Pas d\u2019information d\u2019\u00e9valuations juge-juge",
    "No Category": "Aucune cat\u00e9gorie",
    "No Confirmed Results Yet": "Aucun R\u00e9sultat Confirm\u00e9",
    "No Gender Information": "Pas d\u2019information de genre",
    "No Position Information": "Pas d\u2019information de r\u00f4le",
    "No Region Information": "Pas d\u2019information de r\u00e9gion",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "Pas d\u2019information des cat\u00e9gories d\u2019orateur",
    "No changes": "Aucun changement",
    "No code name set": "Aucun nom code d\u00e9fini",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "Aucunes personnes correspondantes trouv\u00e9es.",
    "No matching rooms found.": "Aucunes salles correspondantes trouv\u00e9es.",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "Non, je donne un \u00e9valuation sur\u00a0:",
    "Noon": "Midi",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Not Checked-In": "Pas enregistr\u00e9",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "Note\u00a0: l'heure du serveur pr\u00e9c\u00e8de votre heure de %s heure.",
      "Note\u00a0: l'heure du serveur pr\u00e9c\u00e8de votre heure de %s heures."
    ],
    "Note: You are %s hour behind server time.": [
      "Note\u00a0: votre heure pr\u00e9c\u00e8de l'heure du serveur de %s heure.",
      "Note\u00a0: votre heure pr\u00e9c\u00e8de l'heure du serveur de %s heures."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "Novembre",
    "Now": "Maintenant",
    "October": "Octobre",
    "Open": "Open",
    "Open the assistant version.": "Ouvrir la version d'assistant.",
    "Order": "Poradie",
    "Panellist": "Membre",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Priority %1": "Priorit\u00e9 %1",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank": "Classement",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "Re-modifier",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Region": "R\u00e9gion",
    "Remove": "Odstr\u00e1ni\u0165",
    "Remove %s by selecting them and then select the \"Remove\" arrow button.": "Enlevez les valeurs \u00ab\u00a0%s\u00a0\u00bb en les s\u00e9lectionnant puis en cliquant sur le bouton fl\u00e8che \u00ab\u00a0Enlever\u00a0\u00bb.",
    "Remove all": "Odstr\u00e1ni\u0165 v\u0161etky",
    "Remove all %s": "Enlever toutes les valeurs \u00ab\u00a0%s\u00a0\u00bb",
    "Remove selected %s": "Enlever les valeurs \u00ab\u00a0%s\u00a0\u00bb s\u00e9lectionn\u00e9es",
    "Return ballots to %1.": "Soumettre feuilles de jugement \u00e0 %1.",
    "Return to Draw": "Retour au tirage",
    "Review": "R\u00e9viser",
    "Room:": "Salle\u00a0:",
    "Round": "Kolo",
    "Saturday": "samedi",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "Num\u00e9riser avec l'appareil photo",
    "Score:": "Score\u00a0:",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "Septembre",
    "Set All Breaking as Available": "Marquer tout qualifiant comme disponible",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Set all availabilities to exactly match check-ins.": "Fixer tous les disponibilit\u00e9s pour refl\u00e9ter les enregistrements.",
    "Set all the availabilities to exactly match what they were in the previous round.": "Fixer tous les disponibilit\u00e9s pour refl\u00e9ter leurs statuts dans la joute pr\u00e9c\u00e9dente.",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "Fixer participants comme disponible seulement s\u2019ils peuvent s\u2019enregistrer et qui sont pr\u00e9sentement indisponible \u2014 i.e. ne va pas \u00e9craser les disponibilit\u00e9s qui existent.",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "Zobrazi\u0165",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "Pr\u00e9sident Seul",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "D\u00e9mographiques des Orateurs",
    "Speaker Results": "R\u00e9sultats d\u2019orateur",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "Arr\u00eater Num\u00e9risation",
    "Sunday": "dimanche",
    "Team": "\u00c9quipe",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "The bracket range of the hypothetical debate": "La gamme des tranches du d\u00e9bat hypoth\u00e9tique",
    "The debate's bracket": "La tranche du d\u00e9bat",
    "The estimated total number of live break categories across all teams of the hypothetical debate": "Le nombre total estim\u00e9 de cat\u00e9gories de qualification vives sur toutes les \u00e9quipes du d\u00e9bat hypoth\u00e9tique",
    "The motion is <em>%1</em>": "La motion est <em>%1</em>",
    "The total number of live break categories across all teams": "Le nombre total de cat\u00e9gories de qualification vives sur toutes les \u00e9quipes",
    "This debate's priority": "La priorit\u00e9 de ce d\u00e9bat",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre v\u00fdber je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVybra\u0165\u201c presun\u00fa\u0165.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre vymazanie je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVymaza\u0165\u201c vymaza\u0165.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "Cette page se met \u00e0 jour automatiquement avec chaque enregistrement, m\u00eame si la liste initiale peut \u00eatre jusqu'\u00e0 une minute hors-jour.",
    "This person does not have a check-in identifier so they can't be checked in": "Cette personne n'a pas d'identifiant donc elle ne peut pas \u00eatre enregistr\u00e9e",
    "Thursday": "jeudi",
    "Today": "Aujourd'hui",
    "Tomorrow": "Demain",
    "Total:": "Total\u00a0:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "Stagiaire",
    "Tuesday": "mardi",
    "Turn On Sounds": "Activer les sons",
    "Type into this box to filter down the list of available %s.": "\u00c9crivez dans cette zone pour filtrer la liste des \u00ab\u00a0%s\u00a0\u00bb disponibles.",
    "Type into this box to filter down the list of selected %s.": "\u00c9crivez dans cette zone pour filtrer la liste des \u00ab\u00a0%s\u00a0\u00bb s\u00e9lectionn\u00e9\u00b7e\u00b7s.",
    "Unaffiliated": "Non-affili\u00e9",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised": "Non cat\u00e9goris\u00e9",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unconfirmed": "Non-confirm\u00e9",
    "Unknown": "Inconnu",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "Incertain",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Warning: you have unsaved changes": "Attention: vous avez des modifications non sauvegard\u00e9es",
    "Wednesday": "mercredi",
    "Which team won the debate:": "Quelle \u00e9quipe \u00e0 gagn\u00e9 le d\u00e9bat\u00a0:",
    "Yes": "Oui",
    "Yesterday": "Hier",
    "You cannot confirm this ballot because you entered it": "Vous pouvez pas confirmer ce feuille parce que vous l\u2019avez saisi",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Vous avez s\u00e9lectionn\u00e9 une action, et vous n'avez fait aucune modification sur des champs. Vous cherchez probablement le bouton Envoyer et non le bouton Enregistrer.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Vous avez s\u00e9lectionn\u00e9 une action, mais vous n'avez pas encore enregistr\u00e9 certains champs modifi\u00e9s. Cliquez sur OK pour enregistrer. Vous devrez r\u00e9appliquer l'action.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Vous avez des modifications non sauvegard\u00e9es sur certains champs \u00e9ditables. Si vous lancez une action, ces modifications vont \u00eatre perdues.",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "ven",
    "abbrev. day Monday\u0004Mon": "lun",
    "abbrev. day Saturday\u0004Sat": "sam",
    "abbrev. day Sunday\u0004Sun": "dim",
    "abbrev. day Thursday\u0004Thur": "jeu",
    "abbrev. day Tuesday\u0004Tue": "mar",
    "abbrev. day Wednesday\u0004Wed": "mer",
    "abbrev. month April\u0004Apr": "avr",
    "abbrev. month August\u0004Aug": "ao\u00fb",
    "abbrev. month December\u0004Dec": "d\u00e9c",
    "abbrev. month February\u0004Feb": "f\u00e9v",
    "abbrev. month January\u0004Jan": "jan",
    "abbrev. month July\u0004Jul": "jui",
    "abbrev. month June\u0004Jun": "jun",
    "abbrev. month March\u0004Mar": "mar",
    "abbrev. month May\u0004May": "mai",
    "abbrev. month November\u0004Nov": "nov",
    "abbrev. month October\u0004Oct": "oct",
    "abbrev. month September\u0004Sep": "sep",
    "adjudicators with gender data": "juges avec donn\u00e9es de genre",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "demi-scores sont permises",
    "deselect all": "d\u00e9s\u00e9lectionner tout",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "feedback scores total": "totale des scores d\u2019\u00e9valuation",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "pas de demi-points",
    "one letter Friday\u0004F": "V",
    "one letter Monday\u0004M": "L",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "J",
    "one letter Tuesday\u0004T": "M",
    "one letter Wednesday\u0004W": "M",
    "optional": "nepovinn\u00e9",
    "saving...": "enregistrement en cours...",
    "select all": "s\u00e9lectionner tout",
    "speaker scores analysed": "analyzovan\u00fdch sk\u00f3re re\u010dn\u00edkov",
    "speaker scores total": "total des scores d\u2019orateur",
    "speakers with gender data": "orateurs avec donn\u00e9es de genre",
    "tab check": "v\u00e9rification tab",
    "tab entry": "saisie tab",
    "tournament": "turnaj",
    "tournaments": "turnaje",
    "unconfirmed": "nepotvrden\u00e9",
    "\u00bd marks are allowed": "demi-points sont permises",
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
    "DATETIME_FORMAT": "j F Y H:i",
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j F Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d/m/Y H:i",
    "SHORT_DATE_FORMAT": "d/m/Y",
    "THOUSAND_SEPARATOR": "\u00a0",
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

