
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
      "%(sel)s / %(cnt)s se\u00e7ildi",
      "%(sel)s / %(cnt)s se\u00e7ildi"
    ],
    "%1 %2 from %3": "%1 %2'den %3",
    "%1 %2 from %3 %4": "%1 %2'den %3 %4",
    "%1 %2 from %3 on %4 (Chair)": "%1 %2'den %3'e %4 (Ba\u015fkan)",
    "%1 %2 from %3 on %4 (Panellist)": "%1 %2'den %3'e kadar% 4 (Panelist)",
    "%1 %2 from %3 on %4 (Trainee)": "%1 %2'den %3'e %4 (Acem,)",
    "%1 (%2) with identifier of %3": "%1 (%2), %3 tan\u0131mlay\u0131c\u0131s\u0131 ile",
    "%1 (%2) with no assigned identifier": "%1 (%2) atanm\u0131\u015f tan\u0131mlay\u0131c\u0131 yok",
    "%1 (%2, %3)": "%1 (%2, %3)",
    "%1 (Absent; id=%2)": "%1 (Yok; id=%2)",
    "%1 (Present; id=%2)": "%1 (Mevcut; id=%2)",
    "%1 (no category) with identifier of %2": "%1 (kategori yok) ve %2 tan\u0131mlay\u0131c\u0131s\u0131",
    "%1 (no category) with no assigned identifier": "%1 (kategori yok) atanm\u0131\u015f tan\u0131mlay\u0131c\u0131 yok",
    "%1 checked in %2: %3": "%1 %2'ye giri\u015f yapt\u0131: %3",
    "%1, %2": "%1, %2",
    "%1, a %2": "%1, bir %2",
    "%1, a %2 from %3 with identifier of %4": "%1, %3'ten %4 tan\u0131mlay\u0131c\u0131l\u0131 bir %2",
    "%1, a %2 from %3 with no assigned identifier": "%1, atanm\u0131\u015f tan\u0131mlay\u0131c\u0131 olmadan %3'ten bir %2",
    "%1, a %2 of no institutional affiliation with identifier of %3": "%1, %3 tan\u0131mlay\u0131c\u0131s\u0131 ile kurumsal ba\u011flant\u0131s\u0131 olmayan %2'si",
    "%1, a %2 of no institutional affiliation with no assigned identifier": "%1, atanm\u0131\u015f tan\u0131mlay\u0131c\u0131s\u0131 olmayan kurumsal bir ili\u015fkinin %2'si",
    "%1, a team with speakers %2": "%1, konu\u015fmac\u0131l\u0131 bir ekip %2",
    "%1:": "%1:",
    "%s event": [
      "%s udalos\u0165",
      "%s udalosti"
    ],
    "%s selected option not visible": [
      "%s se\u00e7ilen se\u00e7enek g\u00f6r\u00fcn\u00fcr de\u011fil",
      "%s se\u00e7ilen se\u00e7enek g\u00f6r\u00fcn\u00fcr de\u011fil"
    ],
    "(click to clear)": "(temizlemek i\u00e7in t\u0131klay\u0131n)",
    "6 a.m.": "Sabah 6",
    "6 p.m.": "6 \u00f6.s.",
    "; ": "; ",
    "<strong>%1</strong>: %2": "<strong>%1</strong>: %2",
    "<strong>\u2613</strong> All": "<strong>\u2613</strong> T\u00fcm\u00fc",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> T\u00fcm\u00fc",
    "Active": "Akt\u00edvna",
    "Add Ballot": "Ballot ekle",
    "Add day": "Prida\u0165 de\u0148",
    "Add event": "Prida\u0165 udalos\u0165",
    "Adjudicating with %1.": "%1 ile j\u00fcri g\u00f6revinde",
    "Adjudicator Demographics": "J\u00fcri Demografisi",
    "Adjudicator Results": "J\u00fcri Sonu\u00e7lar\u0131",
    "Aff Veto": "H\u00fckumet Veto",
    "All": "T\u00fcm",
    "Allocate": "Prideli\u0165",
    "Allocates panels in exact order going from top to bottom (ignoring debate priority and conflicts.)": "Pride\u013euje panely v presnom porad\u00ed zhora nadol (ignoruje prioritu debaty a konflikty).",
    "Allocates preformed panels to debates of similar priority level, while avoiding conflicts.": "Pride\u013euje predpripraven\u00e9 panely debat\u00e1m s podobnou \u00farov\u0148ou priority a z\u00e1rove\u0148 sa vyh\u00fdba konfliktom.",
    "Anon": "Anon",
    "Anonymous (due to team codes)": "Anonim (tak\u0131m kodlar\u0131 nedeniyle)",
    "April": "Nisan",
    "Assign Automatic Priorities by Bracket": "Priradi\u0165 automatick\u00e9 priority pod\u013ea ko\u0161a",
    "Assign Automatic Priorities by Liveness": "Priradi\u0165 automatick\u00e9 priority pod\u013ea liveness",
    "August": "A\u011fustos",
    "Auto-Allocate": "Otomatik Tahsis",
    "Auto-Allocate Adjudicators": "Automaticky prideli\u0165 rozhodcov",
    "Auto-Allocate Individual Adjudicators": "Automaticky prideli\u0165 jednotliv\u00fdch rozhodcov",
    "Auto-Allocate Preformed Panels": "Automaticky prideli\u0165 predpripraven\u00e9 panely",
    "Auto-Allocate Rooms to Debates": "Automaticky prideli\u0165 miestnosti debat\u00e1m",
    "Auto-Prioritise": "Otomatik \u00d6nceliklendirme",
    "Auto-allocate will remove adjudicators from all debates\n        and create new panels in their place.": "Automatick\u00e9 pridelenie odstr\u00e1ni rozhodcov zo v\u0161etk\u00fdch deb\u00e1t a vytvor\u00ed nov\u00e9 panely na ich mieste.",
    "Available %s": "Mevcut %s",
    "A\u2013Z": "A\u2013Z",
    "Ballot Check-Ins": "Ballot Giri\u015fi",
    "Ballot Statuses": "Ballot Durumlar\u0131",
    "Ballots Status": "Ballotlar\u0131n Durumu",
    "Break": "Break",
    "By ": "Od ",
    "By %1": "%1'e g\u00f6re",
    "By how many points did they win:": "Ka\u00e7 puanla kazand\u0131\u011f\u0131:",
    "Cancel": "\u0130ptal",
    "Category": "Kategori",
    "Chair": "Chair",
    "Chair for Panel of %1": "%1 Paneli Ba\u015fkan\u0131",
    "Check time": "Skontrolujte \u010das",
    "Checked-In": "Giri\u015fli",
    "Choose": "Vybra\u0165",
    "Choose %s by selecting them and then select the \"Choose\" arrow button.": "Bunlar\u0131 se\u00e7erek %s se\u00e7in ve ard\u0131ndan \"Se\u00e7\" ok d\u00fc\u011fmesine t\u0131klay\u0131n.",
    "Choose a Date": "Bir Tarih Se\u00e7in",
    "Choose a Time": "Bir Saat Se\u00e7in",
    "Choose a date above to start building the schedule.": "Vyberte d\u00e1tum vy\u0161\u0161ie a za\u010dnite zostavova\u0165 rozvrh.",
    "Choose a time": "Bir saat se\u00e7in",
    "Choose all": "Vybra\u0165 v\u0161etko",
    "Choose all %s": "T\u00fcm %s se\u00e7",
    "Choose selected %s": "Se\u00e7ilen %s se\u00e7",
    "Chosen %s": "Se\u00e7ilen %s",
    "Circle %1": "%1 yuvarlak i\u00e7ine al",
    "Circle Rank:": "Daire S\u0131ralamas\u0131:",
    "Circle the last digit of the %1's score:": "%1'in puan\u0131n\u0131n son basama\u011f\u0131n\u0131 daire i\u00e7ine al\u0131n:",
    "Circle the last digit of the team's total:": "Tak\u0131m\u0131n toplam\u0131n\u0131n son basama\u011f\u0131n\u0131 daire i\u00e7ine al\u0131n:",
    "Click to check-in manually": "Elle giri\u015f yapmak i\u00e7in t\u0131klay\u0131n",
    "Click to choose all %s at once.": "Kliknite sem pre vybratie v\u0161etk\u00fdch %s naraz.",
    "Click to remove all chosen %s at once.": "Kliknite sem pre vymazanie vybrat\u00fdch %s naraz.",
    "Click to undo a check-in": "Giri\u015fi geri almak i\u00e7in t\u0131klay\u0131n",
    "Close Shard": "Zatvori\u0165 shard",
    "Code Names": "K\u00f3dov\u00e9 men\u00e1",
    "Confirmed": "Onaylanm\u0131\u015f",
    "Conflict": "Konflikt",
    "Conflict penalty \u2014 higher numbers will more strongly avoid recorded conflicts": "Pokuta za konflikt \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 zaznamenan\u00fdm konfliktom",
    "Constraint": "Obmedzenie",
    "Copy From Check-Ins": "Giri\u015flerdem Kopyala",
    "Correct the start time below": "Opravte \u010das za\u010diatku ni\u017e\u0161ie",
    "Could not save the side. Try again.": "Stranu sa nepodarilo ulo\u017ei\u0165. Sk\u00faste to znova.",
    "Create Panels": "Vytvori\u0165 panely",
    "Create Preformed Panels": "Vytvori\u0165 predpripraven\u00e9 panely",
    "Create preformed panels by estimating the general brackets that will\n                              occur during this round.": "Vytvor predpripraven\u00e9 panely odhadnut\u00edm v\u0161eobecn\u00fdch ko\u0161ov, ktor\u00e9 sa vyskytn\u00fa po\u010das tohto kola.",
    "Custom title": "Vlastn\u00fd n\u00e1zov",
    "Debated": "Tart\u0131\u015f\u0131lan",
    "December": "Aral\u0131k",
    "Delete this folder?": "Vymaza\u0165 tento prie\u010dinok?",
    "Delete this folder? Its contents will move up to the level above.": "Vymaza\u0165 tento prie\u010dinok? Jeho obsah sa presunie o \u00farove\u0148 vy\u0161\u0161ie.",
    "Description": "Popis",
    "Did %1 deliver the adjudication?": "%1'i karar\u0131 verdi mi?",
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
    "February": "\u015eubat",
    "Filter": "S\u00fczge\u00e7",
    "Find in Table": "Tabloda Bul",
    "Folders": "Prie\u010dinky",
    "Friday": "Cuma",
    "Gender": "Cinsiyet",
    "Hidden": "Skryt\u00e9",
    "Hide": "Skry\u0165",
    "Highest bracket first": "Najvy\u0161\u0161ia skupina ako prv\u00e1",
    "History penalty \u2014 higher numbers will more strongly avoid\n                                         matching adjudicators to teams or panellists they have seen\n                                         before": "Pokuta za hist\u00f3riu \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie predch\u00e1dza\u0165 tomu, aby rozhodcovia posudzovali t\u00edmy alebo panelistov, ktor\u00fdch u\u017e videli predt\u00fdm",
    "ID %1,": "Kimlik %1,",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "\u00d6NEML\u0130: Bir konu\u015fmac\u0131n\u0131n birden fazla konu\u015fma yap\u0131p yapmad\u0131\u011f\u0131n\u0131 kontrol edin ve a\u00e7\u0131k\u00e7a not edin",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "Bu sayfay\u0131 kenar \u00e7ubu\u011fu olmadan g\u00f6r\u00fcnt\u00fclemek istiyorsan\u0131z (yani bir oditoryumda g\u00f6r\u00fcnt\u00fclemek i\u00e7in) yard\u0131mc\u0131 s\u00fcr\u00fcm\u00fc kullanabilirsiniz.",
    "Importance mismatch penalty \u2014 higher numbers will more\n                                         strongly match panel strengths to assigned importances": "Pokuta za nes\u00falad d\u00f4le\u017eitosti \u2014 vy\u0161\u0161ie \u010d\u00edsla bud\u00fa silnej\u0161ie prira\u010fova\u0165 silu panelov k pridelen\u00fdm d\u00f4le\u017eitostiam",
    "In ": "V ",
    "Incomplete": "Ne\u00fapln\u00e9",
    "Independent": "Ba\u011f\u0131ms\u0131z",
    "Institution": "Debatn\u00fd klub",
    "January": "Ocak",
    "July": "Temmuz",
    "June": "Haziran",
    "Latest Actions": "Son Eylemler",
    "Latest Results": "Son Sonu\u00e7lar",
    "Leave blank to show": "Ponechajte pr\u00e1zdne, ak chcete zobrazi\u0165",
    "Loading...": "Na\u010d\u00edtavam...",
    "Lowest bracket first": "Najni\u017e\u0161ia skupina ako prv\u00e1",
    "March": "Mart",
    "Mark replies %1 to %2; <strong>%3</strong>.": "Yan\u0131tlar\u0131 %1 ile %2 aras\u0131 puanlay\u0131n; <strong>%3</strong>.",
    "Mark speeches %1 to %2; <strong>%3</strong>.": "Konu\u015fmalar\u0131 %1 ila %2 aras\u0131nda puanlay\u0131n;<strong>%3</strong>.",
    "Match": "E\u015fle\u015ftir",
    "Match Check-Ins": "Giri\u015flerle E\u015fle\u015ftir",
    "May": "May\u0131s",
    "Merge Ballot(s)": "Zl\u00fa\u010di\u0165 ballot(y)",
    "Midnight": "Geceyar\u0131s\u0131",
    "Minimum feedback score required to be a chair or panellist": "Minim\u00e1lne sk\u00f3re sp\u00e4tnej v\u00e4zby potrebn\u00e9 na to, aby mohol by\u0165 chair alebo panelista",
    "Missing": "Ch\u00fdba",
    "Monday": "Pazartesi",
    "Motion is:": "T\u00e9za je:",
    "N/A": "N/A",
    "Needs a date": "Ch\u00fdba d\u00e1tum",
    "Neg Veto": "Muhalefet Veto",
    "New folder": "Nov\u00fd prie\u010dinok",
    "New schedule day": "Nov\u00fd de\u0148 rozvrhu",
    "No": "Hay\u0131r",
    "No ": "Nie ",
    "No Actions Yet": "Hen\u00fcz \u0130\u015flem Yok",
    "No Adjudicator Ratings Information": "J\u00fcri Derecelendirme Bilgileri Yok",
    "No Adjudicator-Adjudicator Feedback Information": "J\u00fcri-J\u00fcri Geri Bildirim Bilgisi Yok",
    "No Category": "Kategori Yok",
    "No Confirmed Results Yet": "Hen\u00fcz Do\u011frulanm\u0131\u015f Sonu\u00e7 Yok",
    "No Gender Information": "Cinsiyet Bilgisi Yok",
    "No Position Information": "Pozisyon bilgisi yok",
    "No Region Information": "B\u00f6lge Bilgisi Yok",
    "No Results Yet": "Zatia\u013e \u017eiadne v\u00fdsledky",
    "No Speaker Categories Information": "Konu\u015fmac\u0131 Kategorisi Bilgisi Yok",
    "No changes": "De\u011fi\u015fiklik yok",
    "No code name set": "Kod ad\u0131 ayarlanmad\u0131",
    "No folders or tournaments match your search.": "\u017diadne prie\u010dinky ani turnaje nezodpovedaj\u00fa vyh\u013ead\u00e1vaniu.",
    "No folders yet. Click \u201cNew folder\u201d to create one.": "Zatia\u013e tu nie s\u00fa \u017eiadne prie\u010dinky. Vytvorte ich kliknut\u00edm na \u201eNov\u00fd prie\u010dinok\u201c.",
    "No matching people found.": "E\u015fle\u015fen ki\u015fi bulunamad\u0131.",
    "No matching rooms found.": "E\u015fle\u015fen oda bulunamad\u0131.",
    "No preformed panels exist for this round. You can create some by going to Setup, and then Preformed Panels.": "Pre toto kolo neexistuj\u00fa \u017eiadne predpripraven\u00e9 panely. M\u00f4\u017ee\u0161 ich vytvori\u0165 v \u010dasti Nastavenie a potom Predpripraven\u00e9 panely.",
    "No schedule events yet": "Zatia\u013e tu nie s\u00fa \u017eiadne udalosti",
    "No, I am submitting feedback on:": "Hay\u0131r, a\u015fa\u011f\u0131dakilerle ilgili geri bildirim g\u00f6nderiyorum:",
    "Noon": "\u00d6\u011fle",
    "Not Checked In": "Neprihl\u00e1sen\u00fd",
    "Not Checked-In": "Giri\u015f Yap\u0131lmad\u0131",
    "Note that 'liveness' doesn't factor in special rules other than a\n                              strict mathematical break. Be sure to double-check the results": "Upozornenie: liveness nezoh\u013ead\u0148uje \u0161peci\u00e1lne pravidl\u00e1 okrem pr\u00edsneho matematick\u00e9ho postupu. Nezabudni si v\u00fdsledky dvojito skontrolova\u0165.",
    "Note: You are %s hour ahead of server time.": [
      "Not: Sunucu saatinin %s saat ilerisindesiniz.",
      "Not: Sunucu saatinin %s saat ilerisindesiniz."
    ],
    "Note: You are %s hour behind server time.": [
      "Not: Sunucu saatinin %s saat gerisindesiniz.",
      "Not: Sunucu saatinin %s saat gerisindesiniz."
    ],
    "Note: You should almost certainly not being using this page once results\n                               have been released. Be sure to fill all gaps before leaving.": "Pozn\u00e1mka: po zverejnen\u00ed v\u00fdsledkov by si t\u00fato str\u00e1nku takmer ur\u010dite nemal/a pou\u017e\u00edva\u0165. Pred odchodom sa uisti, \u017ee si vyplnil/a v\u0161etky medzery.",
    "November": "Kas\u0131m",
    "Now": "\u015eimdi",
    "October": "Ekim",
    "Open": "Open",
    "Open the assistant version.": "Yard\u0131mc\u0131 s\u00fcr\u00fcm\u00fcn\u00fc a\u00e7\u0131n.",
    "Order": "Poradie",
    "Panellist": "Panelist",
    "Prioritise": "Prioritizova\u0165",
    "Prioritise by bracket will split the draw into quartiles by bracket\n                              and give higher priorities to higher brackets.": "Prioritiz\u00e1cia pod\u013ea ko\u0161a rozdel\u00ed pairing do kvartilov pod\u013ea ko\u0161a a prirad\u00ed vy\u0161\u0161\u00edm ko\u0161om vy\u0161\u0161ie priority.",
    "Prioritise by liveness assign live rooms to be important,\n                              safe rooms (where all teams are guaranteed to break) to be neutral>,\n                              and dead rooms (where all teams cannot break) to be meh. This is\n                              typically only useful in the very last preliminary rounds, when many\n                              teams are ruled out of the break.": "Prioritiz\u00e1cia pod\u013ea liveness prirad\u00ed live miestnostiam d\u00f4le\u017eitos\u0165, bezpe\u010dn\u00fdm miestnostiam (kde je postup v\u0161etk\u00fdch t\u00edmov zaru\u010den\u00fd) neutr\u00e1lnu hodnotu a m\u0155tvym miestnostiam (kde \u017eiadny t\u00edm nem\u00f4\u017ee post\u00fapi\u0165) n\u00edzku hodnotu. Toto je spravidla u\u017eito\u010dn\u00e9 iba v posledn\u00fdch predkol\u00e1ch, ke\u010f s\u00fa mnoh\u00e9 t\u00edmy vyl\u00fa\u010den\u00e9 z postupu.",
    "Priority %1": "\u00d6ncelik %1",
    "Private": "S\u00fakromn\u00e1",
    "Public": "Verejn\u00e9",
    "Rank": "S\u0131ralama",
    "Rank %(rank)s": "Poradie %(rank)s",
    "Re-Edit": "Yeniden D\u00fczenle",
    "Real Names": "Skuto\u010dn\u00e9 men\u00e1",
    "Region": "B\u00f6lge",
    "Remove": "Odstr\u00e1ni\u0165",
    "Remove %s by selecting them and then select the \"Remove\" arrow button.": "Bunlar\u0131 se\u00e7erek %s kald\u0131r\u0131n ve ard\u0131ndan \"Kald\u0131r\" ok d\u00fc\u011fmesine t\u0131klay\u0131n.",
    "Remove all": "Odstr\u00e1ni\u0165 v\u0161etky",
    "Remove all %s": "T\u00fcm %s kald\u0131r",
    "Remove selected %s": "Se\u00e7ilen %s kald\u0131r",
    "Return ballots to %1.": "Ballotlar\u0131 %1'e d\u00f6nd\u00fcr\u00fcn.",
    "Return to Draw": "Kuraya D\u00f6n",
    "Review": "\u0130ncele",
    "Room:": "Oda:",
    "Round": "Kolo",
    "Saturday": "Cumartesi",
    "Save layout": "Ulo\u017ei\u0165 usporiadanie",
    "Saved.": "Ulo\u017een\u00e9.",
    "Saving\u2026": "Uklad\u00e1 sa\u2026",
    "Scan Using Camera": "Kamera Kullanarak Tara",
    "Score:": "Puan:",
    "Seen": "Viden\u00fd",
    "Select a count, sort, and mix to open a shard": "Vyber po\u010det, zoradenie a mie\u0161anie na otvorenie shardu",
    "September": "Eyl\u00fcl",
    "Set All Breaking as Available": "T\u00fcm Break'leri Kullan\u0131labilir Olarak Ayarla",
    "Set Breaking": "Nastavi\u0165 postupuj\u00facich",
    "Set all availabilities to exactly match check-ins.": "T\u00fcm kullan\u0131labilirlikleri giri\u015flerle tam olarak e\u015fle\u015fecek \u015fekilde ayarlay\u0131n.",
    "Set all the availabilities to exactly match what they were in the previous round.": "T\u00fcm kullan\u0131labilirlikleri bir \u00f6nceki turdakiyle tam olarak e\u015fle\u015fecek \u015fekilde ayarla.",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "Ki\u015fileri yaln\u0131zca bir giri\u015f i\u015flemi varsa ve \u015fu anda kullan\u0131lam\u0131yorsa kullan\u0131labilir olarak ayarlay\u0131n - yani mevcut kullan\u0131labilirlikleri silmez.",
    "Shard Mix": "Shard Mix",
    "Shard Sort": "Shard Sort",
    "Shard Split": "Shard Split",
    "Show": "Zobrazi\u0165",
    "Slug (public URL)": "Identifik\u00e1tor (verejn\u00e1 URL)",
    "Smart Allocate": "Smart pridelenie",
    "Solo Chair": "Tek Ba\u015fkan",
    "Solo speech mode: adjudicators can be assigned to multiple speeches in this round. Drag a judge from the bottom pool to every speech they judge; drag from a speech back to the pool to remove only that assignment. Auto-allocation is disabled for this format.": "Re\u017eim s\u00f3lovej re\u010di: rozhodcov mo\u017eno priradi\u0165 k viacer\u00fdm re\u010diam v tomto kole. Pretiahni rozhodcu zo spodn\u00e9ho zoznamu ku ka\u017edej re\u010di, ktor\u00fa posudzuje; pretiahnut\u00edm re\u010di sp\u00e4\u0165 do zoznamu odstr\u00e1ni\u0161 iba toto priradenie. Automatick\u00e9 pridelenie je pre tento form\u00e1t vypnut\u00e9.",
    "Speaker Demographics": "Konu\u015fmac\u0131 Demografisi",
    "Speaker Results": "Konu\u015fmac\u0131 Sonu\u00e7lar\u0131",
    "Start": "Za\u010diatok",
    "Stop Camera Scan": "Kamera Taramas\u0131n\u0131 Durdur",
    "Sunday": "Pazar",
    "Team": "Tak\u0131m",
    "The allocator assigns rooms to debates while trying to match\n                               all of the room constraints that have been specified.": "Pride\u013eova\u010d prirad\u00ed miestnosti debat\u00e1m a pritom sa sna\u017e\u00ed splni\u0165 v\u0161etky zadan\u00e9 obmedzenia miestnost\u00ed.",
    "The allocator creates stronger panels for debates that were given\n                                  higher importances. If importances have not been set it will allocate\n                                  stronger panels to debates in higher brackets.": "Pride\u013eova\u010d vytvor\u00ed silnej\u0161ie panely pre debaty s vy\u0161\u0161ou d\u00f4le\u017eitos\u0165ou. Ak d\u00f4le\u017eitosti neboli nastaven\u00e9, prirad\u00ed silnej\u0161ie panely debat\u00e1m vo vy\u0161\u0161\u00edch ko\u0161och.",
    "The bracket range of the hypothetical debate": "Varsay\u0131msal ma\u00e7\u0131n a\u015fama aral\u0131\u011f\u0131",
    "The debate's bracket": "Bu ma\u00e7\u0131n a\u015famas\u0131",
    "The estimated total number of live break categories across all teams of the hypothetical debate": "Varsay\u0131msal tart\u0131\u015fmada t\u00fcm tak\u0131mlardaki m\u00fcmk\u00fcn break kategorilerinin toplam say\u0131s\u0131",
    "The motion is <em>%1</em>": "\u00d6nerge <em>%1</em'dir>",
    "The total number of live break categories across all teams": "T\u00fcm tak\u0131mlardaki m\u00fcmk\u00fcn break kategorilerinin toplam say\u0131s\u0131",
    "This debate's priority": "Bu ma\u00e7\u0131n \u00f6nceli\u011fi",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre v\u00fdber je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVybra\u0165\u201c presun\u00fa\u0165.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre vymazanie je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \u201eVymaza\u0165\u201c vymaza\u0165.",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "Bu sayfa, ilk liste en fazla bir dakika gecikmeli olsa da, ger\u00e7ekle\u015ftikleri anda yeni giri\u015flerle canl\u0131 olarak g\u00fcncellenecektir.",
    "This person does not have a check-in identifier so they can't be checked in": "Bu ki\u015finin bir giri\u015f tan\u0131mlay\u0131c\u0131s\u0131 yok, bu nedenle giri\u015f yapam\u0131yor",
    "Thursday": "Per\u015fembe",
    "Today": "Bug\u00fcn",
    "Tomorrow": "Yar\u0131n",
    "Total:": "Toplam:",
    "Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.": "Tieto turnaje sa zobrazuj\u00fa priamo na domovskej str\u00e1nke. Presunut\u00edm do prie\u010dinka ich zarad\u00edte.",
    "Trainee": "Acemi",
    "Tuesday": "Sal\u0131",
    "Turn On Sounds": "Sesleri A\u00e7",
    "Type into this box to filter down the list of available %s.": "Mevcut %s listesini s\u00fczmek i\u00e7in bu kutu i\u00e7ine yaz\u0131n.",
    "Type into this box to filter down the list of selected %s.": "Se\u00e7ilen %s listesini s\u00fczmek i\u00e7in bu kutu i\u00e7ine yaz\u0131n.",
    "Unaffiliated": "Ba\u011f\u0131ms\u0131z",
    "Unavailable": "Nedostupn\u00fd",
    "Uncategorised": "Kategorize edilmemi\u015f",
    "Uncategorised tournaments": "Nezaraden\u00e9 turnaje",
    "Unconfirmed": "Onaylanmam\u0131\u015f",
    "Unknown": "Bilinmeyen",
    "Unknown Adj": "Nezn\u00e1my rozhodca",
    "Unranked": "Bez poradia",
    "Unsaved changes": "Neulo\u017een\u00e9 zmeny",
    "Unsaved changes.": "Neulo\u017een\u00e9 zmeny.",
    "Unsaved manual changes.": "Neulo\u017een\u00e9 ru\u010dn\u00e9 zmeny.",
    "Unsure": "Emin de\u011filim",
    "Untitled event": "Udalos\u0165 bez n\u00e1zvu",
    "Wednesday": "\u00c7ar\u015famba",
    "Which team won the debate:": "Tart\u0131\u015fmay\u0131 hangi tak\u0131m\u0131n kazand\u0131\u011f\u0131:",
    "Yes": "Evet",
    "Yesterday": "D\u00fcn",
    "You cannot confirm this ballot because you entered it": "Bu ballotu girdi\u011finiz i\u00e7in onaylayamazs\u0131n\u0131z",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Bir eylem se\u00e7tiniz, ancak tek tek alanlarda herhangi bir de\u011fi\u015fiklik yapmad\u0131n\u0131z. Muhtemelen Kaydet d\u00fc\u011fmesi yerine Git d\u00fc\u011fmesini ar\u0131yorsunuz.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Bir eylem se\u00e7tiniz, ancak de\u011fi\u015fikliklerinizi tek tek alanlara kaydetmediniz. Kaydetmek i\u00e7in l\u00fctfen TAMAM d\u00fc\u011fmesine t\u0131klay\u0131n. Eylemi yeniden \u00e7al\u0131\u015ft\u0131rman\u0131z gerekecek.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Bireysel d\u00fczenlenebilir alanlarda kaydedilmemi\u015f de\u011fi\u015fiklikleriniz var. E\u011fer bir eylem \u00e7al\u0131\u015ft\u0131r\u0131rsan\u0131z, kaydedilmemi\u015f de\u011fi\u015fiklikleriniz kaybolacakt\u0131r.",
    "Z\u2013A": "Z\u2013A",
    "abbrev. day Friday\u0004Fri": "Cum",
    "abbrev. day Monday\u0004Mon": "Pzt",
    "abbrev. day Saturday\u0004Sat": "Cmt",
    "abbrev. day Sunday\u0004Sun": "Paz",
    "abbrev. day Thursday\u0004Thur": "Per",
    "abbrev. day Tuesday\u0004Tue": "Sal",
    "abbrev. day Wednesday\u0004Wed": "\u00c7r\u015f",
    "abbrev. month April\u0004Apr": "Nis",
    "abbrev. month August\u0004Aug": "A\u011fu",
    "abbrev. month December\u0004Dec": "Ara",
    "abbrev. month February\u0004Feb": "\u015eub",
    "abbrev. month January\u0004Jan": "Oca",
    "abbrev. month July\u0004Jul": "Tem",
    "abbrev. month June\u0004Jun": "Haz",
    "abbrev. month March\u0004Mar": "Mar",
    "abbrev. month May\u0004May": "May",
    "abbrev. month November\u0004Nov": "Kas",
    "abbrev. month October\u0004Oct": "Eki",
    "abbrev. month September\u0004Sep": "Eyl",
    "adjudicators with gender data": "cinsiyet verilerine sahip j\u00fcriler",
    "confirmed": "potvrden\u00e9",
    "decimal marks are allowed": "ondal\u0131k i\u015faretlere izin verilir",
    "feedback scores analysed": "analyzovan\u00fdch sk\u00f3re sp\u00e4tnej v\u00e4zby",
    "feedback scores total": "geri bildirim puanlar\u0131 toplam\u0131",
    "folder": "prie\u010dinok",
    "folders": "prie\u010dinky",
    "inactive": "neakt\u00edvny",
    "no \u00bd marks": "yar\u0131m puan yok",
    "one letter Friday\u0004F": "C",
    "one letter Monday\u0004M": "Pt",
    "one letter Saturday\u0004S": "Ct",
    "one letter Sunday\u0004S": "P",
    "one letter Thursday\u0004T": "Pe",
    "one letter Tuesday\u0004T": "S",
    "one letter Wednesday\u0004W": "\u00c7",
    "optional": "nepovinn\u00e9",
    "saving...": "kaydediliyor...",
    "speaker scores analysed": "analyzovan\u00fdch sk\u00f3re re\u010dn\u00edkov",
    "speaker scores total": "konu\u015fmac\u0131 puanlar\u0131 toplam\u0131",
    "speakers with gender data": "cinsiyet verileri olan konu\u015fmac\u0131lar",
    "tab check": "tab kontrol\u00fc",
    "tab entry": "tab giri\u015fi",
    "tournament": "turnaj",
    "tournaments": "turnaje",
    "unconfirmed": "nepotvrden\u00e9",
    "\u00bd marks are allowed": "yar\u0131m puan var",
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
    "DATETIME_FORMAT": "d F Y H:i",
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "d F Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%y-%m-%d",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "d F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d M Y H:i",
    "SHORT_DATE_FORMAT": "d M Y",
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

