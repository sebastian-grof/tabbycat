
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
      "%(sel)s dari %(cnt)s terpilih"
    ],
    "%1 %2 from %3": "%1 %2 dari %3",
    "%1 %2 from %3 %4": "%1 %2 dari %3 %4",
    "%1 %2 from %3 on %4 (Chair)": "%1 %2 dari %3 di %4 (Kursi)",
    "%1 %2 from %3 on %4 (Panellist)": "%1 %2 dari %3 di %4 (panelis)",
    "%1 %2 from %3 on %4 (Trainee)": "%1 %2 dari %3 di %4 (Peserta Pelatihan)",
    "%1 (%2) with identifier of %3": "%1 (%2) dengan penanda %3",
    "%1 (%2) with no assigned identifier": "%1 (%2) tanpa pengenal yang ditetapkan",
    "%1 (%2, %3)": "%1 (%2, %3)",
    "%1 (Absent; id=%2)": "%1 (Absen; id=%2)",
    "%1 (Present; id=%2)": "%1 (Hadir; id=%2)",
    "%1 (no category) with identifier of %2": "%1 (tidak ada kategori) dengan pengenal dari %2",
    "%1 (no category) with no assigned identifier": "%1 (tanpa kategori) tanpa pengenal yang ditetapkan",
    "%1 checked in %2: %3": "%1 men-cek in %2: %3",
    "%1, %2": "%1, %2",
    "%1, a %2": "%1, sebuah %2",
    "%1, a %2 from %3 with identifier of %4": "%1, sebuah %2 dari %3 dengan pengidentifikasi dari %4",
    "%1, a %2 from %3 with no assigned identifier": "%1, sebuah %2 dari %3 dengan tanpa pengidentifikasi ditentukan",
    "%1, a %2 of no institutional affiliation with identifier of %3": "%1, sebuah %2 dari tanpa afiliasi institusional dengan pengidentifikasi %3",
    "%1, a %2 of no institutional affiliation with no assigned identifier": "%1, sebuah %2 dari tanpa afiliasi institusional dengan tanpa pengidentifikasi yang ditentukan",
    "%1, a team with speakers %2": "%1, sebuah tim dengan pembicara %2",
    "%1:": "%1:",
    "%s selected option not visible": [
      "%s pilihan terpilih tidak muncul"
    ],
    "(click to clear)": "(klik untuk membersihkan)",
    "6 a.m.": "6 pagi",
    "6 p.m.": "18.00",
    "; ": ";",
    "<strong>%1</strong>: %2": "<strong>%1</strong>:%2",
    "<strong>\u2613</strong> All": "<strong>\u2613</strong> Semua",
    "<strong>\u2713</strong> All": "<strong>\u2713</strong> Semua",
    "Add Ballot": "Tambah Balot",
    "Adjudicating with %1.": "Mengadili dengan %1.",
    "Adjudicator Demographics": "Demografi Juri",
    "Adjudicator Results": "Hasil Juri",
    "Aff Veto": "Aff Veto",
    "All": "Semua",
    "Anon": "Anon",
    "Anonymous (due to team codes)": "Anonim (karena kode tim)",
    "April": "April",
    "August": "Agustus",
    "Auto-Allocate": "Alokasi Otomatis",
    "Auto-Prioritise": "Prioritas Otomatis",
    "Available %s": "%s yang tersedia",
    "Ballot Check-Ins": "Balot Check-In",
    "Ballot Statuses": "Status Balot",
    "Ballots Status": "Status balot",
    "Break": "Break",
    "By %1": "Oleh %1",
    "By how many points did they win:": "Dengan berapa nilai mereka menang:",
    "Cancel": "Batal",
    "Category": "Kategori",
    "Chair for Panel of %1": "Kursi untuk panel %1",
    "Checked-In": "Sudah Cek-In",
    "Choose %s by selecting them and then select the \"Choose\" arrow button.": "Pilih %s dengan memilih mereka dan kemudian memilih tombol panah \"Choose\".",
    "Choose a Date": "Pilih Tanggal",
    "Choose a Time": "Pilih Waktu",
    "Choose a time": "Pilih waktu",
    "Choose all %s": "Pilih semua %s",
    "Choose selected %s": "Pilih terpilih %s",
    "Chosen %s": "%s terpilih",
    "Circle %1": "Lingkaran %1",
    "Circle Rank:": "Peringkat Lingkaran:",
    "Circle the last digit of the %1's score:": "Lingkari angka terakhir dari nilai %1:",
    "Circle the last digit of the team's total:": "Lingkarin angka terakhir dari total regu:",
    "Click to check-in manually": "Klik untuk cek-in secara manual",
    "Click to undo a check-in": "Klik untuk membatalkan sebuah cek-in",
    "Confirmed": "Terkonfirmasi",
    "Copy From Check-Ins": "Salin dari Check in",
    "Debated": "Diperdebatkan",
    "December": "Desember",
    "Did %1 deliver the adjudication?": "Apakah %1 menyampaikan putusan tersebut?",
    "February": "Februari",
    "Filter": "Filter",
    "Find in Table": "Temukan di Tabel",
    "Friday": "Jum'at",
    "Gender": "Gender",
    "ID %1,": "ID %1,",
    "IMPORTANT: Check and explicitly note if a speaker gives multiple speeches": "PENTING : Periksa dan catat secara eksplisit jika seorang pembicara memberikan banyak pidato",
    "If you want to view this page without the sidebar (i.e. for displaying to an auditorium) you can use the assistant version.": "Jika Anda ingin melihat laman ini tanpa papantepi (misalkan, untuk menampilkan di auditorium), Anda bisa menggunakan versi asisten.",
    "Independent": "Independen",
    "January": "Januari",
    "July": "Juli",
    "June": "Juni",
    "Latest Actions": "Tindakan Terbaru",
    "Latest Results": "Hasil terbaru",
    "March": "Maret",
    "Mark replies %1 to %2; <strong>%3</strong>.": "Tandai balasan %1 ke %2; <strong>%3</strong>.",
    "Mark speeches %1 to %2; <strong>%3</strong>.": "Tandai pidato %1 to %2; <strong>%3</strong>.",
    "Match": "Cocok",
    "Match Check-Ins": "Check-Ins yang Tepat",
    "May": "Mei",
    "Midnight": "Tengah malam",
    "Monday": "Senin",
    "Neg Veto": "Neg Veto",
    "No": "Tidak",
    "No Actions Yet": "Belum ada tindakan sama sekali",
    "No Adjudicator Ratings Information": "Tidak Ada Informasi Peringkat Juri",
    "No Adjudicator-Adjudicator Feedback Information": "Tidak Ada Informasi Nilai Juri - Juri",
    "No Category": "Tanpa Kategori",
    "No Confirmed Results Yet": "Belum Ada Hasil Yang Dikonfirmasi",
    "No Gender Information": "Tidak Ada Informasi Gender",
    "No Position Information": "Tidak Ada Informasi Posisi",
    "No Region Information": "Tidak Ada Informasi Wilayah",
    "No Speaker Categories Information": "Tidak Ada Informasi Kategori Pembicara",
    "No changes": "Tidak ada perubahan",
    "No code name set": "Tidak ada nama kode yang ditetapkan",
    "No matching people found.": "Orang yang cocok tidak ditemukan.",
    "No matching rooms found.": "Ruangan yang cocok tidak ditemukan.",
    "No, I am submitting feedback on:": "Tidak, saya menyerahkah umpan balik pada:",
    "Noon": "Siang",
    "Not Checked-In": "Tidak Check-In",
    "Note: You are %s hour ahead of server time.": [
      "Catatan: Waktu Anda lebih cepat %s jam dibandingkan waktu server."
    ],
    "Note: You are %s hour behind server time.": [
      "Catatan: Waktu Anda lebih lambat %s jam dibandingkan waktu server."
    ],
    "November": "November",
    "Now": "Sekarang",
    "October": "Oktober",
    "Open the assistant version.": "Buka versi asisten.",
    "Panellist": "Panelis",
    "Priority %1": "Prioritas %1",
    "Rank": "Peringkat",
    "Re-Edit": "Edit kembali",
    "Region": "Wilayah",
    "Remove %s by selecting them and then select the \"Remove\" arrow button.": "Pindahkan%s dengan memilih mereka dan kemudian memilih tombol panah \"Remove\".",
    "Remove all %s": "Pindahkan semua %s",
    "Remove selected %s": "Pindahkan terpilih %s",
    "Return ballots to %1.": "Kembalikan surat suara ke %1.",
    "Return to Draw": "Kembali Ke Pengundian",
    "Review": "Ulasan",
    "Room:": "Ruangan:",
    "Saturday": "Sabtu",
    "Scan Using Camera": "Pindai Menggunakan Kamera",
    "Score:": "Nilai:",
    "September": "September",
    "Set All Breaking as Available": "Tetapkan Semua Kerusakan yang Tersedia",
    "Set all availabilities to exactly match check-ins.": "Tetapkan semua ketersediaan ke check-ins yang tepat.",
    "Set all the availabilities to exactly match what they were in the previous round.": "Tetapkan semua ketersediaan agar sama persis dengan keadaan mereka di babak sebelumnya.",
    "Set people as available only if they have a check-in and are currently unavailable \u2014 i.e. it will not overwrite any existing availabilities.": "Set orang sebagai tersedia hanya jika mereka memiliki check-in dan saat ini tidak tersedia - yaitu tidak akan menimpa ketersediaan yang ada.",
    "Solo Chair": "Kursi Solo",
    "Speaker Demographics": "Demografi Pembicara",
    "Speaker Results": "Hasil Pembicara",
    "Stop Camera Scan": "Hentikan Pindaian Kamera",
    "Sunday": "Ahad",
    "Team": "Tim",
    "The bracket range of the hypothetical debate": "Kisaran braket dari debat hipotetis",
    "The debate's bracket": "Kelompok debat",
    "The estimated total number of live break categories across all teams of the hypothetical debate": "Perkiraan jumlah total kategori istirahat langsung di semua tim debat hipotetis",
    "The motion is <em>%1</em>": "Pergerakannya adalah <em>%1</em>",
    "The total number of live break categories across all teams": "Jumlah total kategori jeda langsung di semua tim",
    "This debate's priority": "Prioritas debat ini",
    "This page will live-update with new check-ins as they occur although the initial list may be up to a minute old.": "Laman ini akan terbarui secara live dengan cek-in baru saat terjadi walaupun daftar inisial akan berumur satu menit.",
    "This person does not have a check-in identifier so they can't be checked in": "Orang ini tidak memiliki pengidentifikasi cek-in sehingga ybs tidak dapat di cek-in",
    "Thursday": "Kamis",
    "Today": "Hari ini",
    "Tomorrow": "Besok",
    "Total:": "Total:",
    "Trainee": "Peserta pelatihan",
    "Tuesday": "Selasa",
    "Turn On Sounds": "Nyalakan Suara",
    "Type into this box to filter down the list of available %s.": "Ketik pada kotak ini untuk menyaring daftar %s yang tersedia.",
    "Type into this box to filter down the list of selected %s.": "Ketik di dalam kotak utnuk menyaring daftar dar %s terpilih.",
    "Unaffiliated": "Tidak terafiliasi",
    "Uncategorised": "Tidak terkategorisasi",
    "Unconfirmed": "Tidak Dikonfirmasi",
    "Unknown": "Tak diketahui",
    "Unsure": "Tidak yakin",
    "Wednesday": "Rabu",
    "Which team won the debate:": "Regu mana yang memenangkan perdebatan:",
    "Yes": "Ya",
    "Yesterday": "Kemarin",
    "You cannot confirm this ballot because you entered it": "Anda tidak bisa mengkonfirmasi balot ini karena Andam telah memasukan nya",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Anda telah memilih tindakan, dan Anda belum membuat perubahan apa pun di setiap bidang. Anda mungkin mencari tombol Buka daripada tombol Simpan.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Anda telah memilih tindakan, tetapi Anda belum menyimpan perubahan ke masing-masing bidang. Silakan klik OK untuk menyimpan. Anda harus menjalankan kembali tindakan tersebut.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Beberapa perubahan bidang yang Anda lakukan belum tersimpan. Perubahan yang telah dilakukan akan hilang.",
    "abbrev. day Friday\u0004Fri": "Jum",
    "abbrev. day Monday\u0004Mon": "Sen",
    "abbrev. day Saturday\u0004Sat": "Sab",
    "abbrev. day Sunday\u0004Sun": "Ahd",
    "abbrev. day Thursday\u0004Thur": "Kam",
    "abbrev. day Tuesday\u0004Tue": "Sel",
    "abbrev. day Wednesday\u0004Wed": "Rab",
    "abbrev. month April\u0004Apr": "Apr",
    "abbrev. month August\u0004Aug": "Agu",
    "abbrev. month December\u0004Dec": "Des",
    "abbrev. month February\u0004Feb": "Feb",
    "abbrev. month January\u0004Jan": "Jan",
    "abbrev. month July\u0004Jul": "Jul",
    "abbrev. month June\u0004Jun": "Jun",
    "abbrev. month March\u0004Mar": "Mar",
    "abbrev. month May\u0004May": "Mei",
    "abbrev. month November\u0004Nov": "Nov",
    "abbrev. month October\u0004Oct": "Okt",
    "abbrev. month September\u0004Sep": "Sep",
    "adjudicators with gender data": "juri dengan data gender",
    "decimal marks are allowed": "Tanda desimal diperbolehkan",
    "feedback scores total": "total skor penilaian",
    "no \u00bd marks": "Tidak ada \u00bd tanda",
    "one letter Friday\u0004F": "J",
    "one letter Monday\u0004M": "S",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "M",
    "one letter Thursday\u0004T": "K",
    "one letter Tuesday\u0004T": "S",
    "one letter Wednesday\u0004W": "R",
    "saving...": "menyimpan...",
    "speaker scores total": "total skor pembicara",
    "speakers with gender data": "pembicara dengan data gender",
    "tab check": "Tab cek",
    "tab entry": "Tab entri",
    "\u00bd marks are allowed": " \u00bd tanda diperbolehkan"
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
    "DATETIME_FORMAT": "j N Y, G.i",
    "DATETIME_INPUT_FORMATS": [
      "%d-%m-%Y %H.%M.%S",
      "%d-%m-%Y %H.%M.%S.%f",
      "%d-%m-%Y %H.%M",
      "%d-%m-%y %H.%M.%S",
      "%d-%m-%y %H.%M.%S.%f",
      "%d-%m-%y %H.%M",
      "%m/%d/%y %H.%M.%S",
      "%m/%d/%y %H.%M.%S.%f",
      "%m/%d/%y %H.%M",
      "%m/%d/%Y %H.%M.%S",
      "%m/%d/%Y %H.%M.%S.%f",
      "%m/%d/%Y %H.%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j N Y",
    "DATE_INPUT_FORMATS": [
      "%d-%m-%Y",
      "%d/%m/%Y",
      "%d-%m-%y",
      "%d/%m/%y",
      "%d %b %Y",
      "%d %B %Y",
      "%m/%d/%y",
      "%m/%d/%Y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d-m-Y G.i",
    "SHORT_DATE_FORMAT": "d-m-Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "G.i",
    "TIME_INPUT_FORMATS": [
      "%H.%M.%S",
      "%H.%M",
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

