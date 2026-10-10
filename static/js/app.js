// Ön Muhasebe Pro — İstemci Tarafı JavaScript Motoru

let globalState = {
    cariler: [],
    stoklar: [],
    kasalar: [],
    bankalar: [],
    ayarlar: {},
    activeTab: 'dashboard',
    faturaKalemleri: []
};

// --- YARDIMCI FORMAT FONKSİYONLARI ---
function formatMoney(amount, currency = '₺') {
    if (amount === undefined || amount === null || isNaN(amount)) return `0,00 ${currency}`;
    const num = parseFloat(amount);
    const isNeg = num < 0;
    const absNum = Math.abs(num);
    const parts = absNum.toFixed(2).split('.');
    const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    const decPart = parts[1];
    return `${isNeg ? '-' : ''}${intPart},${decPart} ${currency}`;
}

function formatDate(isoStr) {
    if (!isoStr) return '';
    try {
        const parts = isoStr.split('T')[0].split('-');
        if (parts.length === 3) {
            return `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
        return isoStr;
    } catch (e) {
        return isoStr;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-message');
    const iconEl = document.getElementById('toast-icon');

    msgEl.innerText = message;
    if (isError) {
        toast.classList.remove('bg-slate-900');
        toast.classList.add('bg-red-700');
        iconEl.setAttribute('data-lucide', 'alert-circle');
    } else {
        toast.classList.remove('bg-red-700');
        toast.classList.add('bg-slate-900');
        iconEl.setAttribute('data-lucide', 'check-circle');
    }
    lucide.createIcons();

    toast.classList.remove('translate-y-20', 'opacity-0');
    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 3500);
}

// --- SEKME (TAB) YÖNETİMİ ---
function switchTab(tabId, subFilter = null) {
    globalState.activeTab = tabId;

    // Tüm sekmeleri gizle
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    // Hedef sekmeyi aç
    const target = document.getElementById(`tab-${tabId}`);
    if (target) target.classList.add('active');

    // Menü aktiflik durumunu güncelle
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('text-white', 'bg-blue-600', 'shadow-sm', 'shadow-blue-600/30');
        el.classList.add('text-slate-300');
    });
    const activeNav = document.getElementById(`nav-${tabId}`);
    if (activeNav) {
        activeNav.classList.remove('text-slate-300');
        activeNav.classList.add('text-white', 'bg-blue-600', 'shadow-sm', 'shadow-blue-600/30');
    }

    // Başlık güncelle
    const titles = {
        'dashboard': 'Genel Bakış & Özet',
        'cariler': 'Cari Hesap Yönetimi (Müşteri & Tedarikçi)',
        'faturalar': 'Fatura Yönetimi (Satış & Alış Faturaları)',
        'kasa-banka': 'Kasa & Banka (Nakit, Havale, EFT)',
        'cekler': 'Çek & Senet Takibi',
        'stoklar': 'Stok & Hizmet Kartları',
        'raporlar': 'Mali Durum & KDV Raporları',
        'ayarlar': 'Firma Bilgileri & Veritabanı Yedekleme'
    };
    document.getElementById('page-title').innerText = titles[tabId] || 'Ön Muhasebe';

    // Sekmeye özel verileri yükle
    if (tabId === 'dashboard') loadDashboard();
    else if (tabId === 'cariler') loadCariler();
    else if (tabId === 'faturalar') loadFaturalar();
    else if (tabId === 'kasa-banka') loadKasaBanka();
    else if (tabId === 'cekler') loadCekler(subFilter);
    else if (tabId === 'stoklar') loadStoklar();
    else if (tabId === 'raporlar') loadRaporlar();
    else if (tabId === 'ayarlar') loadAyarlar();

    lucide.createIcons();
}

// --- 1. DASHBOARD VERİLERİNİ YÜKLE ---
async function loadDashboard() {
    try {
        const res = await fetch('/api/raporlar/dashboard');
        const d = await res.json();

        // Kartlar
        document.getElementById('stat-alacak').innerText = formatMoney(d.toplam_alacak);
        document.getElementById('stat-borc').innerText = formatMoney(d.toplam_borc);
        document.getElementById('stat-nakit').innerText = formatMoney(d.nakit_varlik_toplami);
        document.getElementById('stat-kasa').innerText = formatMoney(d.toplam_kasa);
        document.getElementById('stat-banka').innerText = formatMoney(d.toplam_banka);
        document.getElementById('stat-cek').innerText = formatMoney(d.alinan_cek_tutar);
        document.getElementById('stat-alinan-cek').innerText = `${d.alinan_cek_sayi} Adet (${formatMoney(d.alinan_cek_tutar)})`;
        document.getElementById('stat-verilen-cek').innerText = `${d.verilen_cek_sayi} Adet (${formatMoney(d.verilen_cek_tutar)})`;

        // Alarmlar
        const alarmsBox = document.getElementById('dashboard-cek-alarmlari');
        const boxGeciken = document.getElementById('box-geciken-cek');
        const boxYaklasan = document.getElementById('box-yaklasan-cek');
        const badgeAlarm = document.getElementById('badge-cek-alarm');

        let totalAlarms = 0;
        if (d.geciken_cek_sayi > 0) {
            boxGeciken.classList.remove('hidden');
            document.getElementById('msg-geciken-cek').innerText = `${d.geciken_cek_sayi} adet (${formatMoney(d.geciken_cek_tutar)}) çekin vadesi geçmiştir!`;
            totalAlarms += d.geciken_cek_sayi;
        } else {
            boxGeciken.classList.add('hidden');
        }

        if (d.yaklasan_cek_sayi > 0) {
            boxYaklasan.classList.remove('hidden');
            document.getElementById('msg-yaklasan-cek').innerText = `${d.yaklasan_cek_sayi} adet (${formatMoney(d.yaklasan_cek_tutar)}) çekin tahsilat günü bu haftadır.`;
            totalAlarms += d.yaklasan_cek_sayi;
        } else {
            boxYaklasan.classList.add('hidden');
        }

        if (totalAlarms > 0) {
            alarmsBox.classList.remove('hidden');
            badgeAlarm.classList.remove('hidden');
            badgeAlarm.innerText = `${totalAlarms} Uyarı`;
        } else {
            alarmsBox.classList.add('hidden');
            badgeAlarm.classList.add('hidden');
        }

        // Son Faturalar Tablosu
        const fatTbody = document.getElementById('dashboard-son-faturalar');
        if (d.son_faturalar && d.son_faturalar.length > 0) {
            fatTbody.innerHTML = d.son_faturalar.map(f => {
                const turBadge = f.fatura_turu === 'SATIS' 
                    ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">Satış</span>' 
                    : '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">Alış</span>';
                const durumBadge = f.odeme_durumu === 'ODENDI'
                    ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">Ödendi</span>'
                    : (f.odeme_durumu === 'KISMI'
                        ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700">Kısmi</span>'
                        : '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">Açık</span>');

                return `
                    <tr class="hover:bg-slate-50 cursor-pointer" onclick="viewFatura(${f.id})">
                        <td class="py-2 px-3 font-mono font-bold text-xs">${f.fatura_no} ${turBadge}</td>
                        <td class="py-2 px-3 font-medium text-slate-800 truncate max-w-[150px]">${f.cari_unvan}</td>
                        <td class="py-2 px-3 font-bold text-right text-slate-900">${formatMoney(f.genel_toplam)}</td>
                        <td class="py-2 px-3 text-center">${durumBadge}</td>
                    </tr>
                `;
            }).join('');
        } else {
            fatTbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-slate-400 text-xs">Henüz fatura düzenlenmemiş.</td></tr>`;
        }

        // Son Kasa / Banka Hareketleri
        const harTbody = document.getElementById('dashboard-son-hareketler');
        if (d.son_hareketler && d.son_hareketler.length > 0) {
            harTbody.innerHTML = d.son_hareketler.map(h => {
                const isGiris = h.islem_turu.includes('TAHSILAT') || h.islem_turu.includes('GELEN');
                const sign = isGiris ? '+' : '-';
                const color = isGiris ? 'text-emerald-600' : 'text-red-600';
                return `
                    <tr>
                        <td class="py-2 px-3 text-slate-500">${formatDate(h.islem_tarihi)}</td>
                        <td class="py-2 px-3 text-slate-700 font-medium">${h.aciklama || h.islem_turu}</td>
                        <td class="py-2 px-3 text-slate-500 truncate max-w-[120px]">${h.cari_unvan || h.hesap_adi || '-'}</td>
                        <td class="py-2 px-3 font-bold text-right ${color}">${sign}${formatMoney(h.tutar)}</td>
                    </tr>
                `;
            }).join('');
        } else {
            harTbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-slate-400 text-xs">Henüz hareket bulunmuyor.</td></tr>`;
        }

        lucide.createIcons();
    } catch (e) {
        console.error("Dashboard yüklenirken hata:", e);
    }
}

// --- 2. CARİLERİ YÜKLE ---
function toggleCariBakiyeSort() {
    const sortEl = document.getElementById('cari-filter-sort');
    if (!sortEl) return;
    if (sortEl.value === 'bakiye_desc') {
        sortEl.value = 'bakiye_asc';
    } else {
        sortEl.value = 'bakiye_desc';
    }
    loadCariler();
}

async function loadCariler() {
    const tip = document.getElementById('cari-filter-tip')?.value || 'HEPSI';
    const search = document.getElementById('cari-search')?.value || '';
    const bakiyeDurumu = document.getElementById('cari-filter-bakiye')?.value || 'HEPSI';
    const sortBy = document.getElementById('cari-filter-sort')?.value || 'unvan_asc';

    let url = `/api/cariler?tip=${tip}&bakiye_durumu=${bakiyeDurumu}&sort_by=${sortBy}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        globalState.cariler = data;
        document.getElementById('badge-cari-count').innerText = data.length;

        const tbody = document.getElementById('cariler-table-body');
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-400 text-xs">Arama kriterinize uygun cari bulunamadı.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(c => {
            const bakiye = parseFloat(c.bakiye || 0);
            let bakiyeHtml = '';
            if (bakiye > 0.001) {
                bakiyeHtml = `<span class="font-bold text-red-600">${formatMoney(bakiye)} (Borçlu)</span>`;
            } else if (bakiye < -0.001) {
                bakiyeHtml = `<span class="font-bold text-emerald-600">${formatMoney(Math.abs(bakiye))} (Alacaklı)</span>`;
            } else {
                bakiyeHtml = `<span class="text-slate-400 font-medium">0,00 ₺</span>`;
            }

            const tipBadge = c.tip === 'MUSTERI' 
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">Müşteri</span>'
                : (c.tip === 'TEDARIKCI' 
                    ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700">Tedarikçi</span>'
                    : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">Müşteri/Tedarikçi</span>');

            const personelBadge = (c.is_personel == 1 || c.is_personel === true)
                ? '<span class="ml-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 inline-flex items-center gap-0.5"><i data-lucide="user-check" class="w-3 h-3"></i> Personel</span>'
                : '';

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="py-3 px-4 font-mono font-bold text-xs text-slate-600">${c.kod}</td>
                    <td class="py-3 px-4">
                        <div class="font-bold text-slate-900">${c.unvan}</div>
                        <div class="text-[11px] text-slate-400">${c.il ? c.il + ' / ' + (c.ilce || '') : ''} ${c.vergi_no ? ' • V.N: ' + c.vergi_no : ''}</div>
                    </td>
                    <td class="py-3 px-4">${tipBadge}${personelBadge}</td>
                    <td class="py-3 px-4">
                        <div class="text-slate-800 font-medium">${c.yetkili_kisi || '-'}</div>
                        <div class="text-[11px] text-slate-400">${c.telefon || ''}</div>
                    </td>
                    <td class="py-3 px-4 text-right font-medium text-slate-700">${formatMoney(c.borc)}</td>
                    <td class="py-3 px-4 text-right font-medium text-slate-700">${formatMoney(c.alacak)}</td>
                    <td class="py-3 px-4 text-right">${bakiyeHtml}</td>
                    <td class="py-3 px-4 text-center">
                        <div class="flex items-center justify-center gap-1.5">
                            <button onclick="viewCariEkstre(${c.id})" title="Cari Hesap Ekstresi" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-bold transition flex items-center gap-1">
                                <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5 text-blue-600"></i> Ekstre
                            </button>
                            <button onclick="openEditCariModal(${c.id})" title="Cari Kartını Düzelt / Düzenle" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 rounded text-xs font-bold transition flex items-center gap-1">
                                <i data-lucide="edit-3" class="w-3.5 h-3.5 text-amber-600"></i> Düzelt
                            </button>
                            <button onclick="openCariHareketModal(${c.id})" title="Borç / Alacak Dekontu veya Devir Ekle" class="px-2 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded text-xs font-bold transition flex items-center gap-1">
                                <i data-lucide="receipt" class="w-3.5 h-3.5"></i> Dekont
                            </button>
                            <button onclick="openIslemModalForCari(${c.id}, '${c.unvan}', ${bakiye})" title="Ödeme / Tahsilat Gir" class="p-1 hover:bg-emerald-50 text-emerald-600 rounded transition">
                                <i data-lucide="banknote" class="w-4 h-4"></i>
                            </button>
                            <button onclick="deleteCari(${c.id}, '${c.unvan}')" title="Cari Sil" class="p-1 hover:bg-red-50 text-red-500 rounded transition">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
    } catch (e) {
        console.error("Cariler yüklenirken hata:", e);
    }
}

// Alt Sekme Değiştirici (Cari Kart)
function switchCariTab(tab) {
    const btnGenel = document.getElementById('cari-tab-btn-genel');
    const btnPersonel = document.getElementById('cari-tab-btn-personel');
    const contentGenel = document.getElementById('cari-tabcontent-genel');
    const contentPersonel = document.getElementById('cari-tabcontent-personel');

    if (tab === 'genel') {
        if (btnGenel) btnGenel.className = 'px-4 py-2.5 text-xs font-bold border-b-2 border-blue-600 text-blue-600 flex items-center gap-1.5 transition';
        if (btnPersonel) btnPersonel.className = 'px-4 py-2.5 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition';
        if (contentGenel) contentGenel.classList.remove('hidden');
        if (contentPersonel) contentPersonel.classList.add('hidden');
    } else {
        if (btnPersonel) btnPersonel.className = 'px-4 py-2.5 text-xs font-bold border-b-2 border-blue-600 text-blue-600 flex items-center gap-1.5 transition';
        if (btnGenel) btnGenel.className = 'px-4 py-2.5 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition';
        if (contentGenel) contentGenel.classList.add('hidden');
        if (contentPersonel) contentPersonel.classList.remove('hidden');
    }
}

function onPersonelCheckChange() {
    const isChecked = !!document.getElementById('cari-form-is-personel')?.checked;
    const badge = document.getElementById('badge-cari-personel-durum');
    if (badge) {
        if (isChecked) badge.classList.remove('hidden');
        else badge.classList.add('hidden');
    }
}

// Yeni Cari Açma Modalı
function openNewCariModal() {
    const editIdEl = document.getElementById('cari-edit-id');
    if (editIdEl) editIdEl.value = '';
    const titleEl = document.getElementById('modal-cari-baslik');
    if (titleEl) titleEl.innerHTML = '<i data-lucide="user-plus" class="w-4 h-4 text-blue-600"></i> <span>Yeni Cari Kart Tanımla</span>';
    const submitBtn = document.getElementById('cari-submit-btn');
    if (submitBtn) submitBtn.innerText = 'Cariyi Kaydet';

    document.getElementById('cari-form-unvan').value = '';
    document.getElementById('cari-form-tip').value = 'MUSTERI';
    document.getElementById('cari-form-yetkili').value = '';
    document.getElementById('cari-form-telefon').value = '';
    document.getElementById('cari-form-eposta').value = '';
    document.getElementById('cari-form-vd').value = '';
    document.getElementById('cari-form-vno').value = '';
    document.getElementById('cari-form-il').value = '';
    document.getElementById('cari-form-ilce').value = '';
    document.getElementById('cari-form-adres').value = '';

    const devirContainer = document.getElementById('cari-devir-container');
    if (devirContainer) devirContainer.classList.remove('hidden');
    const devirTutarEl = document.getElementById('cari-form-devir-tutar');
    if (devirTutarEl) devirTutarEl.value = '0.00';
    const devirTurEl = document.getElementById('cari-form-devir-tur');
    if (devirTurEl) devirTurEl.value = 'BORC';

    const personelCheck = document.getElementById('cari-form-is-personel');
    if (personelCheck) personelCheck.checked = false;
    const persGorev = document.getElementById('cari-form-personel-gorevi');
    if (persGorev) persGorev.value = '';
    const persDep = document.getElementById('cari-form-personel-departman');
    if (persDep) persDep.value = '';
    onPersonelCheckChange();

    switchCariTab('genel');
    openModal('modal-cari-ekle');
    lucide.createIcons();
}

// Cari Düzeltme Modalı
async function openEditCariModal(cariId) {
    try {
        const res = await fetch(`/api/cariler/${cariId}`);
        if (!res.ok) throw new Error('Cari bilgileri alınamadı.');
        const c = await res.json();

        const editIdEl = document.getElementById('cari-edit-id');
        if (editIdEl) editIdEl.value = c.id;
        const titleEl = document.getElementById('modal-cari-baslik');
        if (titleEl) titleEl.innerHTML = `<i data-lucide="edit-3" class="w-4 h-4 text-amber-600"></i> <span>Cari Kartı Düzelt (${c.kod})</span>`;
        const submitBtn = document.getElementById('cari-submit-btn');
        if (submitBtn) submitBtn.innerText = 'Değişiklikleri Kaydet';

        document.getElementById('cari-form-unvan').value = c.unvan || '';
        document.getElementById('cari-form-tip').value = c.tip || 'MUSTERI';
        document.getElementById('cari-form-yetkili').value = c.yetkili_kisi || '';
        document.getElementById('cari-form-telefon').value = c.telefon || '';
        document.getElementById('cari-form-eposta').value = c.eposta || '';
        document.getElementById('cari-form-vd').value = c.vergi_dairesi || '';
        document.getElementById('cari-form-vno').value = c.vergi_no || c.tckn || '';
        document.getElementById('cari-form-il').value = c.il || '';
        document.getElementById('cari-form-ilce').value = c.ilce || '';
        document.getElementById('cari-form-adres').value = c.adres || '';

        // Düzenleme modunda açılış devir bakiyesi kutusu gizlenir
        const devirContainer = document.getElementById('cari-devir-container');
        if (devirContainer) devirContainer.classList.add('hidden');

        // Personel sekmesi alanları
        const isPersonel = (c.is_personel == 1 || c.is_personel === true);
        const personelCheck = document.getElementById('cari-form-is-personel');
        if (personelCheck) personelCheck.checked = isPersonel;
        const persGorev = document.getElementById('cari-form-personel-gorevi');
        if (persGorev) persGorev.value = c.personel_gorevi || '';
        const persDep = document.getElementById('cari-form-personel-departman');
        if (persDep) persDep.value = c.personel_departman || '';
        onPersonelCheckChange();

        switchCariTab('genel');
        openModal('modal-cari-ekle');
        lucide.createIcons();
    } catch (err) {
        showToast('Cari bilgisi yüklenirken hata: ' + err.message, true);
    }
}

// Cari Ekleme & Düzeltme Formu Submit
async function submitCariForm(e) {
    e.preventDefault();
    const editId = document.getElementById('cari-edit-id')?.value;
    const isEdit = !!editId;

    const data = {
        unvan: document.getElementById('cari-form-unvan').value,
        tip: document.getElementById('cari-form-tip').value,
        yetkili_kisi: document.getElementById('cari-form-yetkili').value,
        telefon: document.getElementById('cari-form-telefon').value,
        eposta: document.getElementById('cari-form-eposta').value,
        vergi_dairesi: document.getElementById('cari-form-vd').value,
        vergi_no: document.getElementById('cari-form-vno').value,
        tckn: document.getElementById('cari-form-vno').value,
        il: document.getElementById('cari-form-il').value,
        ilce: document.getElementById('cari-form-ilce').value,
        adres: document.getElementById('cari-form-adres').value,
        is_personel: !!document.getElementById('cari-form-is-personel')?.checked,
        personel_gorevi: document.getElementById('cari-form-personel-gorevi')?.value || '',
        personel_departman: document.getElementById('cari-form-personel-departman')?.value || ''
    };

    if (!isEdit) {
        const devirTutar = parseFloat(document.getElementById('cari-form-devir-tutar')?.value) || 0.0;
        const devirTur = document.getElementById('cari-form-devir-tur')?.value || 'BORC';
        data.acilis_bakiyesi = devirTutar;
        data.acilis_bakiye_turu = devirTur;
    }

    const url = isEdit ? `/api/cariler/${editId}` : '/api/cariler';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Cari kaydedilemedi.');
        }
        closeModal('modal-cari-ekle');
        showToast(isEdit ? 'Cari kart bilgileri başarıyla güncellendi.' : 'Yeni cari kartı başarıyla eklendi.');
        await loadCariler();
        loadDashboard();

        // Eğer ekstre modalı açıksa yenile
        const ekstreModal = document.getElementById('modal-cari-ekstre');
        if (ekstreModal && !ekstreModal.classList.contains('hidden') && isEdit) {
            viewCariEkstre(parseInt(editId));
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

// --- CARİ DEKONT & DEVİR MODAL İŞLEMLERİ ---
function openCariHareketModal(cariId = null, tip = 'BORC_DEKONTU') {
    const editIdEl = document.getElementById('cari-hareket-edit-id');
    if (editIdEl) editIdEl.value = '';
    const titleEl = document.getElementById('cari-hareket-modal-baslik');
    if (titleEl) titleEl.innerText = 'Borç / Alacak Dekontu & Devir Girişi';
    const submitBtn = document.getElementById('cari-hareket-submit-btn');
    if (submitBtn) submitBtn.innerText = 'Hareketi Kaydet';

    document.getElementById('cari-hareket-tip').value = tip;
    document.getElementById('cari-hareket-tarih').value = new Date().toISOString().split('T')[0];
    document.getElementById('cari-hareket-tutar').value = '';
    document.getElementById('cari-hareket-evrak-no').value = '';
    document.getElementById('cari-hareket-aciklama').value = '';

    // Cari Seçenekleri
    const select = document.getElementById('cari-hareket-cari-select');
    select.innerHTML = '<option value="">-- Cari Seçiniz --</option>' + globalState.cariler.map(c => {
        return `<option value="${c.id}" ${c.id == cariId ? 'selected' : ''}>${c.kod} - ${c.unvan} (${c.tip === 'TEDARIKCI' ? 'Tedarikçi' : 'Müşteri'})</option>`;
    }).join('');

    adjustCariHareketForm();
    openModal('modal-cari-hareket');
}

async function openEditCariHareketModal(hareketId) {
    try {
        const res = await fetch(`/api/cariler/hareket/${hareketId}`);
        if (!res.ok) throw new Error('Hareket bilgisi alınamadı.');
        const h = await res.json();

        const editIdEl = document.getElementById('cari-hareket-edit-id');
        if (editIdEl) editIdEl.value = h.id;
        const titleEl = document.getElementById('cari-hareket-modal-baslik');
        if (titleEl) titleEl.innerText = 'Dekont / Devir Hareketi Düzenle';
        const submitBtn = document.getElementById('cari-hareket-submit-btn');
        if (submitBtn) submitBtn.innerText = 'Değişiklikleri Kaydet';

        document.getElementById('cari-hareket-tip').value = h.islem_turu;
        document.getElementById('cari-hareket-tarih').value = h.tarih ? h.tarih.split('T')[0] : '';
        document.getElementById('cari-hareket-tutar').value = h.tutar;
        document.getElementById('cari-hareket-evrak-no').value = h.evrak_no || '';
        document.getElementById('cari-hareket-aciklama').value = h.aciklama || '';
        if (h.hareket_yonu) {
            document.getElementById('cari-hareket-devir-yon').value = h.hareket_yonu;
        }

        const select = document.getElementById('cari-hareket-cari-select');
        select.innerHTML = '<option value="">-- Cari Seçiniz --</option>' + globalState.cariler.map(c => {
            return `<option value="${c.id}" ${c.id == h.cari_id ? 'selected' : ''}>${c.kod} - ${c.unvan} (${c.tip === 'TEDARIKCI' ? 'Tedarikçi' : 'Müşteri'})</option>`;
        }).join('');

        adjustCariHareketForm();
        openModal('modal-cari-hareket');
    } catch (err) {
        showToast(err.message, true);
    }
}

function adjustCariHareketForm() {
    const tip = document.getElementById('cari-hareket-tip').value;
    const devirDiv = document.getElementById('cari-hareket-devir-yon-div');
    if (tip === 'DEVIR') {
        devirDiv.classList.remove('hidden');
    } else {
        devirDiv.classList.add('hidden');
    }
}

async function submitCariHareketForm(e) {
    e.preventDefault();
    const editId = document.getElementById('cari-hareket-edit-id')?.value;
    const isEdit = !!editId;

    const cariId = document.getElementById('cari-hareket-cari-select').value;
    if (!cariId) {
        showToast('Lütfen bir cari seçiniz.', true);
        return;
    }

    const tip = document.getElementById('cari-hareket-tip').value;
    const tutar = parseFloat(document.getElementById('cari-hareket-tutar').value);
    if (!tutar || tutar <= 0) {
        showToast('Geçerli bir tutar giriniz.', true);
        return;
    }

    const payload = {
        cari_id: parseInt(cariId),
        islem_turu: tip,
        tarih: document.getElementById('cari-hareket-tarih').value,
        tutar: tutar,
        evrak_no: document.getElementById('cari-hareket-evrak-no').value,
        aciklama: document.getElementById('cari-hareket-aciklama').value,
        hareket_yonu: document.getElementById('cari-hareket-devir-yon').value
    };

    const url = isEdit ? `/api/cariler/hareket/${editId}` : '/api/cariler/hareket';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Hareket kaydedilemedi.');
        }

        closeModal('modal-cari-hareket');
        showToast(isEdit ? 'Cari hareket başarıyla güncellendi.' : 'Cari dekont/devir hareketi başarıyla işlendi.');
        loadCariler();
        loadDashboard();

        // Eğer ekstre penceresi açıksa hemen güncelle
        const ekstreModal = document.getElementById('modal-cari-ekstre');
        if (ekstreModal && !ekstreModal.classList.contains('hidden')) {
            viewCariEkstre(parseInt(cariId));
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteCariHareket(hareketId, cariId) {
    if (!confirm('Bu dekont / hareket kaydını silmek istediğinize emin misiniz?')) return;
    try {
        const res = await fetch(`/api/cariler/hareket/${hareketId}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Hareket silinemedi.');
        }
        showToast('Hareket başarıyla silindi.');
        viewCariEkstre(cariId);
        loadCariler();
        loadDashboard();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteCari(id, unvan) {
    if (!confirm(`"${unvan}" unvanlı cariyi silmek istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/cariler/${id}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Cari silinemedi.');
        }
        showToast('Cari başarıyla silindi.');
        loadCariler();
        loadDashboard();
    } catch (err) {
        showToast(err.message, true);
    }
}

// --- CARİ HESAP EKSTRESİ ---
async function viewCariEkstre(cariId) {
    try {
        const res = await fetch(`/api/cariler/${cariId}/ekstre`);
        const d = await res.json();

        document.getElementById('ekstre-cari-unvan').innerText = `${d.cari.kod} - ${d.cari.unvan}`;
        document.getElementById('ekstre-rapor-tarihi').innerText = formatDate(new Date().toISOString());

        // Dekont/Devir Butonunu Bu Cariye Bağla
        const btnYeniHareket = document.getElementById('ekstre-btn-yeni-hareket');
        if (btnYeniHareket) {
            btnYeniHareket.onclick = () => openCariHareketModal(cariId);
        }
        const btnDuzelt = document.getElementById('ekstre-btn-duzelt');
        if (btnDuzelt) {
            btnDuzelt.onclick = () => openEditCariModal(cariId);
        }

        // Antet
        document.getElementById('ekstre-print-firma').innerText = globalState.ayarlar.firma_adi || 'ÖZERLER MERMER';
        document.getElementById('ekstre-print-adres').innerText = globalState.ayarlar.adres || '';
        document.getElementById('ekstre-print-vergi').innerText = `${globalState.ayarlar.vergi_dairesi || ''} / ${globalState.ayarlar.vergi_no || ''}`;

        // Özet
        document.getElementById('ekstre-toplam-borc').innerText = formatMoney(d.toplam_borc);
        document.getElementById('ekstre-toplam-alacak').innerText = formatMoney(d.toplam_alacak);
        document.getElementById('ekstre-net-bakiye').innerText = `${formatMoney(Math.abs(d.son_bakiye))} ${d.son_bakiye_durumu}`;

        const islemRozetleri = {
            'DEVIR': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">Devir Bakiyesi</span>',
            'BORC_DEKONTU': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900">Borç Dekontu</span>',
            'ALACAK_DEKONTU': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-900">Alacak Dekontu</span>',
            'FATURA_SATIS': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">Satış Faturası</span>',
            'FATURA_ALIS': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700">Alış Faturası</span>',
            'NAKIT_TAHSILAT': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">Nakit Tahsilat</span>',
            'KREDI_KARTI_TAHSILAT': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700">Kredi Kartı Tahsilat</span>',
            'POS_TAHSILAT': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700">Kredi Kartı Tahsilat</span>',
            'NAKIT_ODEME': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-red-700">Nakit Ödeme</span>',
            'HAVALE_TAHSILAT': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700">Gelen Havale/EFT</span>',
            'HAVALE_ODEME': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-50 text-orange-700">Giden Havale/EFT</span>',
            'CEK_GIRIS': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700">Alınan Çek</span>',
            'CEK_CIKIS': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">Verilen Çek</span>',
            'CEK_KARSILIKSIZ': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">Karşılıksız Çek</span>'
        };

        const tbody = document.getElementById('ekstre-hareketler-tbody');
        if (!d.hareketler || d.hareketler.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-400">Henüz cari hareket kaydı yok.</td></tr>`;
        } else {
            tbody.innerHTML = d.hareketler.map(h => {
                const rozet = islemRozetleri[h.islem_turu] || `<span class="px-1.5 py-0.5 rounded text-[10px] bg-slate-100">${h.islem_turu}</span>`;
                const isManuel = !h.ref_fatura_id && !h.ref_hareket_id && !h.ref_cek_id;
                const faturaIdArg = h.ref_fatura_id || 'null';
                const islemIdArg = h.ref_hareket_id || 'null';
                const cekIdArg = h.ref_cek_id || 'null';

                return `
                    <tr class="border-b border-slate-100 hover:bg-amber-50/70 cursor-pointer transition group" 
                        onclick="handleEkstreRowClick(${h.id}, ${faturaIdArg}, ${islemIdArg}, ${cekIdArg}, '${h.islem_turu}')"
                        title="Fişi / Faturayı açmak ve düzenlemek için tıklayınız">
                        <td class="py-2 px-3 text-slate-600">${formatDate(h.tarih)}</td>
                        <td class="py-2 px-3">${rozet}</td>
                        <td class="py-2 px-3 font-mono text-slate-600 font-bold">${h.evrak_no || '-'}</td>
                        <td class="py-2 px-3 text-slate-800 font-medium">
                            ${escapeHtml(h.aciklama || '-')}
                        </td>
                        <td class="py-2 px-3 text-right font-medium ${h.borc > 0 ? 'text-slate-900 font-bold' : 'text-slate-400'}">${h.borc > 0 ? formatMoney(h.borc) : '-'}</td>
                        <td class="py-2 px-3 text-right font-medium ${h.alacak > 0 ? 'text-slate-900 font-bold' : 'text-slate-400'}">${h.alacak > 0 ? formatMoney(h.alacak) : '-'}</td>
                        <td class="py-2 px-3 text-right font-bold ${h.yuruyen_bakiye > 0 ? 'text-red-600' : (h.yuruyen_bakiye < 0 ? 'text-emerald-600' : 'text-slate-500')}">
                            ${formatMoney(Math.abs(h.yuruyen_bakiye))} <span class="text-[10px] font-normal">${h.bakiye_durumu}</span>
                        </td>
                        <td class="py-2 px-3 text-center no-print" onclick="event.stopPropagation()">
                            <div class="flex items-center justify-center gap-1">
                                <button onclick="handleEkstreRowClick(${h.id}, ${faturaIdArg}, ${islemIdArg}, ${cekIdArg}, '${h.islem_turu}')" 
                                        title="Fişi / Faturayı Düzenle" 
                                        class="px-2 py-1 bg-amber-100 group-hover:bg-amber-500 group-hover:text-white text-amber-800 rounded text-[11px] font-bold inline-flex items-center gap-1 transition">
                                    <i data-lucide="edit-3" class="w-3 h-3"></i> Düzenle
                                </button>
                                ${isManuel ? `
                                    <button onclick="deleteCariHareket(${h.id}, ${cariId})" title="Bu dekont kaydını sil" class="p-1 text-slate-400 hover:text-red-600 rounded transition">
                                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                                    </button>
                                ` : (islemIdArg !== 'null' ? `
                                    <button onclick="deleteIslemRow(${islemIdArg})" title="Bu kasa/banka hareketini sil" class="p-1 text-slate-400 hover:text-red-600 rounded transition">
                                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                                    </button>
                                ` : '')}
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        openModal('modal-cari-ekstre');
        lucide.createIcons();
    } catch (e) {
        showToast('Ekstre yüklenirken hata oluştu.', true);
    }
}

function handleEkstreRowClick(hareketId, faturaId, islemId, cekId, islemTuru) {
    if (faturaId) {
        openEditFaturaModal(faturaId);
    } else if (islemId) {
        openEditIslemModal(islemId);
    } else if (hareketId && !cekId) {
        openEditCariHareketModal(hareketId);
    } else if (cekId) {
        showToast('Çek ile ilgili işlemler için Çek Takibi modülünü kullanabilirsiniz.');
    }
}

function printEkstre() {
    window.print();
}

// --- 3. FATURALARI YÜKLE ---
async function loadFaturalar() {
    const tur = document.getElementById('fatura-filter-turu').value;
    const durum = document.getElementById('fatura-filter-durum').value;
    const search = document.getElementById('fatura-search').value;

    let url = `/api/faturalar?`;
    if (tur) url += `fatura_turu=${tur}&`;
    if (durum) url += `odeme_durumu=${durum}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        document.getElementById('badge-fatura-count').innerText = data.length;

        const tbody = document.getElementById('faturalar-table-body');
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-slate-400 text-xs">Fatura bulunamadı.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(f => {
            const turBadge = f.fatura_turu === 'SATIS'
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">Satış</span>'
                : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">Alış</span>';

            let durumBadge = '';
            if (f.odeme_durumu === 'ODENDI') {
                durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">Tamamı Ödendi</span>';
            } else if (f.odeme_durumu === 'KISMI') {
                durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700">Kısmi Ödendi</span>';
            } else if (f.odeme_durumu === 'IPTAL') {
                durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-red-700 line-through">İptal Edildi</span>';
            } else {
                durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">Açık / Bekliyor</span>';
            }

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="py-3 px-4 font-mono font-bold text-xs text-slate-800">${f.fatura_no}</td>
                    <td class="py-3 px-4">${turBadge}</td>
                    <td class="py-3 px-4 text-xs">
                        <div class="font-medium text-slate-800">${formatDate(f.fatura_tarihi)}</div>
                        <div class="text-[10px] text-slate-400">Vade: ${formatDate(f.vade_tarihi) || '-'}</div>
                    </td>
                    <td class="py-3 px-4">
                        <div class="font-bold text-slate-900 text-xs truncate max-w-[180px]">${f.cari_unvan}</div>
                    </td>
                    <td class="py-3 px-4 text-right font-medium text-slate-600">${formatMoney(f.ara_toplam)}</td>
                    <td class="py-3 px-4 text-right font-medium text-slate-600">${formatMoney(f.kdv_toplam)}</td>
                    <td class="py-3 px-4 text-right font-black text-slate-900">${formatMoney(f.genel_toplam)}</td>
                    <td class="py-3 px-4 text-right font-bold ${f.kalan_tutar > 0.01 ? 'text-red-600' : 'text-slate-400'}">${formatMoney(f.kalan_tutar)}</td>
                    <td class="py-3 px-4 text-center">${durumBadge}</td>
                    <td class="py-3 px-4 text-center">
                        <div class="flex items-center justify-center gap-1">
                            <button onclick="viewFatura(${f.id})" title="Faturayı Görüntüle ve Yazdır" class="px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded text-xs font-bold transition flex items-center gap-1">
                                <i data-lucide="eye" class="w-3.5 h-3.5"></i> Gör / Yazdır
                            </button>
                            <button onclick="openEditFaturaModal(${f.id})" title="Faturayı Düzenle" class="px-2 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 rounded text-xs font-bold transition flex items-center gap-1">
                                <i data-lucide="edit-3" class="w-3.5 h-3.5"></i> Düzenle
                            </button>
                            ${f.kalan_tutar > 0.01 && f.odeme_durumu !== 'IPTAL' ? `
                                <button onclick="openIslemForFatura(${f.id}, ${f.cari_id}, '${f.cari_unvan}', ${f.kalan_tutar}, '${f.fatura_turu}')" title="Bu Faturaya Ödeme / Tahsilat Gir" class="p-1 hover:bg-emerald-50 text-emerald-600 rounded">
                                    <i data-lucide="credit-card" class="w-4 h-4"></i>
                                </button>
                            ` : ''}
                            ${f.odeme_durumu !== 'IPTAL' && f.odenen_tutar <= 0.01 ? `
                                <button onclick="cancelFatura(${f.id}, '${f.fatura_no}')" title="Faturayı İptal Et" class="p-1 hover:bg-red-50 text-red-500 rounded">
                                    <i data-lucide="ban" class="w-4 h-4"></i>
                                </button>
                            ` : ''}
                            <button onclick="deleteFaturaRow(${f.id}, '${f.fatura_no}')" title="Faturayı Tamamen Sil" class="p-1 hover:bg-rose-50 text-rose-600 rounded transition">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
    } catch (e) {
        console.error("Faturalar yüklenirken hata:", e);
    }
}

// Fatura Düzenleme Modal & Dinamik Kalemler
function openFaturaModal(tur = 'SATIS') {
    globalManualKdvTotal = null;
    const editIdEl = document.getElementById('fatura-edit-id');
    if (editIdEl) editIdEl.value = '';
    const submitBtn = document.getElementById('fatura-submit-btn');
    if (submitBtn) submitBtn.innerText = 'Faturayı Kes ve Kaydet';

    document.getElementById('fatura-turu-input').value = tur;
    document.getElementById('fatura-modal-baslik').innerHTML = tur === 'SATIS'
        ? `<i data-lucide="file-plus" class="w-4 h-4 text-blue-600"></i> Yeni Satış Faturası Düzenle`
        : `<i data-lucide="shopping-bag" class="w-4 h-4 text-purple-600"></i> Yeni Alış Faturası Girişi`;

    document.getElementById('fatura-tarih-input').value = new Date().toISOString().split('T')[0];
    document.getElementById('fatura-no-input').value = '';
    document.getElementById('fatura-aciklama-input').value = '';

    // Cari Seçeneklerini Doldur
    const select = document.getElementById('fatura-cari-select');
    select.innerHTML = '<option value="">-- Cari Seçiniz --</option>' + globalState.cariler.map(c => {
        return `<option value="${c.id}">${c.kod} - ${c.unvan}</option>`;
    }).join('');

    // Kalemleri Sıfırla ve 1 Boş Satır Ekle
    globalState.faturaKalemleri = [];
    document.getElementById('fatura-satirlari-tbody').innerHTML = '';
    addFaturaSatiri();

    openModal('modal-fatura');
    lucide.createIcons();
}

async function openEditFaturaModal(faturaId) {
    try {
        const res = await fetch(`/api/faturalar/${faturaId}`);
        if (!res.ok) throw new Error('Fatura detayları getirilemedi.');
        const f = await res.json();

        const editIdEl = document.getElementById('fatura-edit-id');
        if (editIdEl) editIdEl.value = f.id;
        document.getElementById('fatura-turu-input').value = f.fatura_turu;
        document.getElementById('fatura-modal-baslik').innerHTML = f.fatura_turu === 'SATIS'
            ? `<i data-lucide="edit-3" class="w-4 h-4 text-blue-600"></i> Satış Faturası Düzenle (${f.fatura_no})`
            : `<i data-lucide="edit-3" class="w-4 h-4 text-purple-600"></i> Alış Faturası Düzenle (${f.fatura_no})`;
        const submitBtn = document.getElementById('fatura-submit-btn');
        if (submitBtn) submitBtn.innerText = 'Değişiklikleri Kaydet';

        document.getElementById('fatura-tarih-input').value = f.fatura_tarihi ? f.fatura_tarihi.split('T')[0] : '';
        document.getElementById('fatura-no-input').value = f.fatura_no || '';
        document.getElementById('fatura-aciklama-input').value = f.aciklama || '';

        // Cari Seçeneklerini Doldur ve seç
        const select = document.getElementById('fatura-cari-select');
        select.innerHTML = '<option value="">-- Cari Seçiniz --</option>' + globalState.cariler.map(c => {
            return `<option value="${c.id}" ${c.id == f.cari_id ? 'selected' : ''}>${c.kod} - ${c.unvan}</option>`;
        }).join('');

        // Kalemleri Yükle
        globalState.faturaKalemleri = [];
        document.getElementById('fatura-satirlari-tbody').innerHTML = '';

        if (f.kalemler && f.kalemler.length > 0) {
            f.kalemler.forEach(k => {
                addFaturaSatiriWithData(k);
            });
        } else {
            addFaturaSatiri();
        }

        if (f.kdv_toplam !== undefined && f.kdv_toplam !== null) {
            globalManualKdvTotal = parseFloat(f.kdv_toplam);
        } else {
            globalManualKdvTotal = null;
        }

        recalcFatura(globalManualKdvTotal);
        openModal('modal-fatura');
        lucide.createIcons();
    } catch (e) {
        showToast('Fatura düzenleme formu açılırken hata oluştu: ' + e.message, true);
    }
}

let globalManualKdvTotal = null;

function addFaturaSatiriWithData(item) {
    const tbody = document.getElementById('fatura-satirlari-tbody');
    const rowIndex = globalState.faturaKalemleri.length;

    const miktar = parseFloat(item.miktar) || 1.0;
    const birim_fiyat = parseFloat(item.birim_fiyat) || 0.0;
    const kdv_orani = item.kdv_orani !== undefined && item.kdv_orani !== null ? parseFloat(item.kdv_orani) : 20.0;
    const matrah = miktar * birim_fiyat;
    const kdv_tutari = (item.kdv_tutari !== undefined && item.kdv_tutari !== null)
        ? parseFloat(item.kdv_tutari)
        : Math.round(matrah * (kdv_orani / 100.0) * 100) / 100;
    const satir_toplami = (item.satir_toplami !== undefined && item.satir_toplami !== null)
        ? parseFloat(item.satir_toplami)
        : Math.round((matrah + kdv_tutari) * 100) / 100;

    const rowData = {
        stok_id: item.stok_id || null,
        aciklama: item.aciklama || '',
        miktar: miktar,
        birim: item.birim || 'Adet',
        birim_fiyat: birim_fiyat,
        kdv_orani: kdv_orani,
        kdv_tutari: kdv_tutari,
        satir_toplami: satir_toplami
    };
    globalState.faturaKalemleri.push(rowData);

    const stokOptions = '<option value="">(Serbest Giriş)</option>' + globalState.stoklar.map(s => {
        return `<option value="${s.id}" ${s.id == rowData.stok_id ? 'selected' : ''}>${s.kod} - ${s.ad}</option>`;
    }).join('');

    const tr = document.createElement('tr');
    tr.id = `fatura-row-${rowIndex}`;
    tr.className = "border-b border-slate-200 hover:bg-slate-50";
    tr.innerHTML = `
        <td class="py-2 px-1">
            <select onchange="onStokSecildi(${rowIndex}, this.value)" class="w-full text-xs p-1.5 border border-slate-300 rounded">
                ${stokOptions}
            </select>
        </td>
        <td class="py-2 px-1">
            <input type="text" id="row-aciklama-${rowIndex}" value="${escapeHtml(rowData.aciklama)}" oninput="updateRowField(${rowIndex}, 'aciklama', this.value)" placeholder="Açıklama" class="w-full text-xs p-1.5 border border-slate-300 rounded font-medium">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="any" min="0" id="row-miktar-${rowIndex}" value="${rowData.miktar}" oninput="updateRowField(${rowIndex}, 'miktar', parseFloat(this.value) || 0)" class="w-full text-xs p-1.5 border border-slate-300 rounded text-center">
        </td>
        <td class="py-2 px-1">
            <input type="text" id="row-birim-${rowIndex}" value="${escapeHtml(rowData.birim)}" oninput="updateRowField(${rowIndex}, 'birim', this.value)" class="w-full text-xs p-1.5 border border-slate-300 rounded text-center">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="0.01" min="0" id="row-fiyat-${rowIndex}" value="${rowData.birim_fiyat.toFixed(2)}" oninput="updateRowField(${rowIndex}, 'birim_fiyat', parseFloat(this.value) || 0)" class="w-full text-xs p-1.5 border border-slate-300 rounded text-right font-bold">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="any" min="0" max="100" id="row-kdv-${rowIndex}" value="${rowData.kdv_orani}" oninput="updateRowKdvOrani(${rowIndex}, this.value)" list="kdv-orani-list" class="w-full text-xs p-1.5 border border-slate-300 rounded text-center font-bold" placeholder="%" title="KDV oranını elle yazabilirsiniz (Örn: 20, 10, 8, 1, 0)">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="0.01" min="0" id="row-kdv-tutar-${rowIndex}" value="${rowData.kdv_tutari.toFixed(2)}" oninput="updateRowKdvTutar(${rowIndex}, this.value)" class="w-full text-xs p-1.5 border border-purple-300 bg-purple-50/20 rounded text-right font-semibold text-purple-700" placeholder="0.00" title="KDV tutarını (₺) elle değiştirebilirsiniz">
        </td>
        <td class="py-2 px-2 text-right font-black text-slate-800" id="row-toplam-${rowIndex}">
            ${formatMoney(rowData.satir_toplami)}
        </td>
        <td class="py-2 px-1 text-center">
            <button type="button" onclick="removeFaturaSatiri(${rowIndex})" class="text-red-500 hover:text-red-700 p-1">
                <i data-lucide="trash" class="w-4 h-4"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);
}

function addFaturaSatiri() {
    const tbody = document.getElementById('fatura-satirlari-tbody');
    const rowIndex = globalState.faturaKalemleri.length;

    const defaultItem = {
        stok_id: null,
        aciklama: '',
        miktar: 1.0,
        birim: 'Adet',
        birim_fiyat: 0.0,
        kdv_orani: 20.0,
        kdv_tutari: 0.0,
        satir_toplami: 0.0
    };
    globalState.faturaKalemleri.push(defaultItem);

    const stokOptions = '<option value="">(Serbest Giriş)</option>' + globalState.stoklar.map(s => {
        return `<option value="${s.id}">${s.kod} - ${s.ad}</option>`;
    }).join('');

    const tr = document.createElement('tr');
    tr.id = `fatura-row-${rowIndex}`;
    tr.className = "border-b border-slate-200 hover:bg-slate-50";
    tr.innerHTML = `
        <td class="py-2 px-1">
            <select onchange="onStokSecildi(${rowIndex}, this.value)" class="w-full text-xs p-1.5 border border-slate-300 rounded">
                ${stokOptions}
            </select>
        </td>
        <td class="py-2 px-1">
            <input type="text" id="row-aciklama-${rowIndex}" oninput="updateRowField(${rowIndex}, 'aciklama', this.value)" placeholder="Açıklama" class="w-full text-xs p-1.5 border border-slate-300 rounded font-medium">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="any" min="0" id="row-miktar-${rowIndex}" value="1" oninput="updateRowField(${rowIndex}, 'miktar', parseFloat(this.value) || 0)" class="w-full text-xs p-1.5 border border-slate-300 rounded text-center">
        </td>
        <td class="py-2 px-1">
            <input type="text" id="row-birim-${rowIndex}" value="Adet" oninput="updateRowField(${rowIndex}, 'birim', this.value)" class="w-full text-xs p-1.5 border border-slate-300 rounded text-center">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="0.01" min="0" id="row-fiyat-${rowIndex}" value="0.00" oninput="updateRowField(${rowIndex}, 'birim_fiyat', parseFloat(this.value) || 0)" class="w-full text-xs p-1.5 border border-slate-300 rounded text-right font-bold">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="any" min="0" max="100" id="row-kdv-${rowIndex}" value="20" oninput="updateRowKdvOrani(${rowIndex}, this.value)" list="kdv-orani-list" class="w-full text-xs p-1.5 border border-slate-300 rounded text-center font-bold" placeholder="%" title="KDV oranını elle yazabilirsiniz (Örn: 20, 10, 8, 1, 0)">
        </td>
        <td class="py-2 px-1">
            <input type="number" step="0.01" min="0" id="row-kdv-tutar-${rowIndex}" value="0.00" oninput="updateRowKdvTutar(${rowIndex}, this.value)" class="w-full text-xs p-1.5 border border-purple-300 bg-purple-50/20 rounded text-right font-semibold text-purple-700" placeholder="0.00" title="KDV tutarını (₺) elle değiştirebilirsiniz">
        </td>
        <td class="py-2 px-2 text-right font-black text-slate-800" id="row-toplam-${rowIndex}">
            0,00 ₺
        </td>
        <td class="py-2 px-1 text-center">
            <button type="button" onclick="removeFaturaSatiri(${rowIndex})" class="text-red-500 hover:text-red-700 p-1">
                <i data-lucide="trash" class="w-4 h-4"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);
    lucide.createIcons();
    recalcFatura();
}

function onStokSecildi(rowIndex, stokId) {
    if (!stokId) {
        globalState.faturaKalemleri[rowIndex].stok_id = null;
        return;
    }
    const stok = globalState.stoklar.find(s => s.id == stokId);
    if (!stok) return;

    const isSatis = document.getElementById('fatura-turu-input').value === 'SATIS';
    const fiyat = isSatis ? stok.satis_fiyati : stok.alis_fiyati;
    const kdvOrani = stok.kdv_orani !== undefined ? parseFloat(stok.kdv_orani) : 20.0;
    const miktar = parseFloat(globalState.faturaKalemleri[rowIndex].miktar) || 1.0;
    const matrah = miktar * fiyat;
    const kdvTutari = Math.round(matrah * (kdvOrani / 100.0) * 100) / 100;

    globalState.faturaKalemleri[rowIndex].stok_id = stok.id;
    globalState.faturaKalemleri[rowIndex].aciklama = stok.ad;
    globalState.faturaKalemleri[rowIndex].birim = stok.birim;
    globalState.faturaKalemleri[rowIndex].birim_fiyat = fiyat;
    globalState.faturaKalemleri[rowIndex].kdv_orani = kdvOrani;
    globalState.faturaKalemleri[rowIndex].kdv_tutari = kdvTutari;
    globalState.faturaKalemleri[rowIndex].satir_toplami = matrah + kdvTutari;

    // Form alanlarına yansıt
    document.getElementById(`row-aciklama-${rowIndex}`).value = stok.ad;
    document.getElementById(`row-birim-${rowIndex}`).value = stok.birim;
    document.getElementById(`row-fiyat-${rowIndex}`).value = fiyat;
    document.getElementById(`row-kdv-${rowIndex}`).value = kdvOrani;
    document.getElementById(`row-kdv-tutar-${rowIndex}`).value = kdvTutari.toFixed(2);

    recalcFatura();
}

function updateRowField(rowIndex, field, value) {
    const k = globalState.faturaKalemleri[rowIndex];
    if (!k) return;
    k[field] = value;

    if (field === 'miktar' || field === 'birim_fiyat') {
        const matrah = (k.miktar || 0) * (k.birim_fiyat || 0);
        k.kdv_tutari = Math.round(matrah * ((k.kdv_orani || 0) / 100.0) * 100) / 100;
        k.satir_toplami = matrah + k.kdv_tutari;
        const kdvEl = document.getElementById(`row-kdv-tutar-${rowIndex}`);
        if (kdvEl) kdvEl.value = k.kdv_tutari.toFixed(2);
    }
    recalcFatura();
}

function updateRowKdvOrani(rowIndex, value) {
    const k = globalState.faturaKalemleri[rowIndex];
    if (!k) return;
    const orani = parseFloat(value);
    k.kdv_orani = isNaN(orani) ? 0.0 : orani;
    const matrah = (k.miktar || 0) * (k.birim_fiyat || 0);
    k.kdv_tutari = Math.round(matrah * (k.kdv_orani / 100.0) * 100) / 100;
    k.satir_toplami = matrah + k.kdv_tutari;

    const kdvEl = document.getElementById(`row-kdv-tutar-${rowIndex}`);
    if (kdvEl) kdvEl.value = k.kdv_tutari.toFixed(2);

    recalcFatura();
}

function updateRowKdvTutar(rowIndex, value) {
    const k = globalState.faturaKalemleri[rowIndex];
    if (!k) return;
    const tutar = parseFloat(value);
    k.kdv_tutari = isNaN(tutar) ? 0.0 : tutar;
    const matrah = (k.miktar || 0) * (k.birim_fiyat || 0);
    k.satir_toplami = matrah + k.kdv_tutari;

    if (matrah > 0) {
        const calcRate = Math.round((k.kdv_tutari / matrah) * 1000) / 10;
        k.kdv_orani = calcRate;
        const rateEl = document.getElementById(`row-kdv-${rowIndex}`);
        if (rateEl) rateEl.value = calcRate;
    }

    recalcFatura();
}

function onKdvOzetInput(value) {
    const val = parseFloat(value);
    globalManualKdvTotal = isNaN(val) ? 0.0 : val;
    recalcFatura(globalManualKdvTotal);
}

function removeFaturaSatiri(rowIndex) {
    const tr = document.getElementById(`fatura-row-${rowIndex}`);
    if (tr) tr.remove();
    // Kalem verisini etkisiz hale getir
    if (globalState.faturaKalemleri[rowIndex]) {
        globalState.faturaKalemleri[rowIndex].miktar = 0;
        globalState.faturaKalemleri[rowIndex].birim_fiyat = 0;
        globalState.faturaKalemleri[rowIndex].kdv_tutari = 0;
        globalState.faturaKalemleri[rowIndex].satir_toplami = 0;
    }
    recalcFatura();
}

function recalcFatura(overrideKdvTotal = null) {
    let araToplam = 0.0;
    let calcKdvToplam = 0.0;

    globalState.faturaKalemleri.forEach((k, idx) => {
        if (!k) return;
        const brut = (k.miktar || 0) * (k.birim_fiyat || 0);
        const kdv = k.kdv_tutari !== undefined ? k.kdv_tutari : (brut * ((k.kdv_orani || 0) / 100.0));
        const satirToplam = brut + kdv;
        araToplam += brut;
        calcKdvToplam += kdv;

        const el = document.getElementById(`row-toplam-${idx}`);
        if (el) el.innerText = formatMoney(satirToplam);
    });

    araToplam = Math.round(araToplam * 100) / 100;
    calcKdvToplam = Math.round(calcKdvToplam * 100) / 100;
    let kdvToplam = overrideKdvTotal !== null ? overrideKdvTotal : (globalManualKdvTotal !== null ? globalManualKdvTotal : calcKdvToplam);
    const genelToplam = Math.round((araToplam + kdvToplam) * 100) / 100;

    const araEl = document.getElementById('fatura-ozet-ara-toplam');
    if (araEl) araEl.innerText = formatMoney(araToplam);

    const kdvInput = document.getElementById('fatura-ozet-kdv-input');
    if (kdvInput && overrideKdvTotal === null && globalManualKdvTotal === null) {
        kdvInput.value = kdvToplam.toFixed(2);
    }

    const genelEl = document.getElementById('fatura-ozet-genel-toplam');
    if (genelEl) genelEl.innerText = formatMoney(genelToplam);
}

async function submitFaturaForm(e) {
    e.preventDefault();
    const editId = document.getElementById('fatura-edit-id')?.value;
    const isEdit = !!editId;

    const cariId = document.getElementById('fatura-cari-select').value;
    if (!cariId) {
        showToast('Lütfen bir cari seçiniz.', true);
        return;
    }

    const aktifKalemler = globalState.faturaKalemleri.filter(k => k && k.miktar > 0 && k.aciklama);
    if (aktifKalemler.length === 0) {
        showToast('En az bir geçerli fatura kalemi girilmelidir.', true);
        return;
    }

    const kdvOzetVal = parseFloat(document.getElementById('fatura-ozet-kdv-input')?.value);
    const payload = {
        fatura_no: document.getElementById('fatura-no-input').value || null,
        fatura_turu: document.getElementById('fatura-turu-input').value,
        fatura_tarihi: document.getElementById('fatura-tarih-input').value,
        cari_id: parseInt(cariId),
        aciklama: document.getElementById('fatura-aciklama-input').value,
        iskonto_orani: 0.0,
        kdv_toplam: !isNaN(kdvOzetVal) ? kdvOzetVal : undefined,
        kalemler: aktifKalemler.map(k => ({
            stok_id: k.stok_id || null,
            aciklama: k.aciklama,
            miktar: parseFloat(k.miktar) || 1.0,
            birim: k.birim || 'Adet',
            birim_fiyat: parseFloat(k.birim_fiyat) || 0.0,
            kdv_orani: k.kdv_orani !== undefined ? parseFloat(k.kdv_orani) : 20.0,
            kdv_tutari: k.kdv_tutari !== undefined ? parseFloat(k.kdv_tutari) : undefined,
            iskonto_orani: 0.0
        }))
    };

    const url = isEdit ? `/api/faturalar/${editId}` : '/api/faturalar';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Fatura kaydedilemedi.');
        }
        const faturaRes = await res.json();
        closeModal('modal-fatura');
        showToast(isEdit ? `Fatura ${faturaRes.fatura_no} başarıyla güncellendi!` : `Fatura ${faturaRes.fatura_no} başarıyla düzenlendi!`);
        loadFaturalar();
        loadCariler();
        loadDashboard();

        // Eğer ekstre modalı açıksa ekstreyi yenile
        const ekstreModal = document.getElementById('modal-cari-ekstre');
        if (ekstreModal && !ekstreModal.classList.contains('hidden')) {
            viewCariEkstre(parseInt(cariId));
        }

        if (!isEdit) {
            // Otomatik Fatura Önizlemesini Aç
            viewFatura(faturaRes.id);
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

// Fatura Görüntüleme & Resmi A4 Çıktı
async function viewFatura(faturaId) {
    try {
        const res = await fetch(`/api/faturalar/${faturaId}`);
        const f = await res.json();

        // Antet & Şirket Bilgileri
        document.getElementById('inv-firma-unvan').innerText = f.ayarlar.firma_adi || 'ÖZERLER MERMER';
        document.getElementById('inv-firma-adres').innerText = f.ayarlar.adres || '';
        document.getElementById('inv-firma-vergi').innerText = `${f.ayarlar.vergi_dairesi || ''} / ${f.ayarlar.vergi_no || ''}`;
        document.getElementById('inv-firma-iletisim').innerText = `Tel: ${f.ayarlar.telefon || ''} | E-posta: ${f.ayarlar.eposta || ''}`;

        // Fatura Detayları
        document.getElementById('inv-tur-etiket').innerText = f.fatura_turu === 'SATIS' ? 'SATIŞ FATURASI' : 'ALIŞ FATURASI';
        document.getElementById('inv-fatura-no').innerText = f.fatura_no;
        document.getElementById('inv-fatura-tarih').innerText = formatDate(f.fatura_tarihi);
        document.getElementById('inv-vade-tarih').innerText = formatDate(f.vade_tarihi) || '-';

        // Müşteri / Cari Bilgileri
        document.getElementById('inv-cari-unvan').innerText = f.cari_unvan;
        document.getElementById('inv-cari-adres').innerText = f.cari_adres ? `${f.cari_adres} ${f.cari_ilce || ''}/${f.cari_il || ''}` : '-';
        document.getElementById('inv-cari-vergi').innerText = `V.D.: ${f.cari_vergi_dairesi || '-'} | V.No: ${f.cari_vergi_no || f.cari_tckn || '-'}`;
        document.getElementById('inv-cari-tel').innerText = f.cari_telefon ? `Tel: ${f.cari_telefon}` : '';

        // Kalemler Tablosu
        const tbody = document.getElementById('inv-kalemler-tbody');
        tbody.innerHTML = (f.kalemler || []).map((k, idx) => {
            return `
                <tr>
                    <td class="py-2 px-3 text-slate-500">${idx + 1}</td>
                    <td class="py-2 px-3 font-semibold text-slate-800">${k.aciklama}</td>
                    <td class="py-2 px-3 text-right font-medium">${k.miktar}</td>
                    <td class="py-2 px-3 text-slate-500">${k.birim}</td>
                    <td class="py-2 px-3 text-right font-mono">${formatMoney(k.birim_fiyat)}</td>
                    <td class="py-2 px-3 text-right">%${k.kdv_orani}</td>
                    <td class="py-2 px-3 text-right font-mono">${formatMoney(k.kdv_tutari)}</td>
                    <td class="py-2 px-3 text-right font-bold text-slate-900 font-mono">${formatMoney(k.satir_toplami)}</td>
                </tr>
            `;
        }).join('');

        // Toplamlar & Yazı ile
        document.getElementById('inv-ara-toplam').innerText = formatMoney(f.ara_toplam);
        document.getElementById('inv-kdv-toplam').innerText = formatMoney(f.kdv_toplam);
        document.getElementById('inv-genel-toplam').innerText = formatMoney(f.genel_toplam);
        document.getElementById('inv-yaziyla-tutar').innerText = f.yaziyla_genel_toplam;

        document.getElementById('inv-banka-bilgi').innerText = `${f.ayarlar.varsayilan_banka || ''} - ${f.ayarlar.varsayilan_iban || ''}`;
        document.getElementById('inv-fatura-notu').innerText = f.aciklama || f.ayarlar.fatura_notu || '';

        openModal('modal-fatura-goruntule');
    } catch (e) {
        showToast('Fatura detayları yüklenemedi.', true);
    }
}

function printFatura() {
    window.print();
}

async function cancelFatura(faturaId, faturaNo) {
    if (!confirm(`${faturaNo} numaralı faturayı iptal etmek istediğinize emin misiniz? Stoklar ve cari bakiyesi geri alınacaktır.`)) return;
    try {
        const res = await fetch(`/api/faturalar/${faturaId}/iptal`, { method: 'POST' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Fatura iptal edilemedi.');
        }
        showToast('Fatura başarıyla iptal edildi.');
        loadFaturalar();
        loadCariler();
        loadDashboard();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteFaturaRow(faturaId, faturaNo) {
    if (!confirm(`${faturaNo} numaralı faturayı tamamen silmek istediğinize emin misiniz?\n\nBu işlem faturayı, kalemlerini ve cari hareketini kalıcı olarak silecektir.`)) return;
    try {
        const res = await fetch(`/api/faturalar/${faturaId}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Fatura silinemedi.');
        }
        showToast('Fatura başarıyla silindi.');
        loadFaturalar();
        loadCariler();
        loadDashboard();
    } catch (err) {
        showToast(err.message, true);
    }
}

// --- 4. KASA & BANKA YÖNETİMİ ---
async function loadKasaBanka() {
    try {
        const [kasaRes, bankaRes, harRes] = await Promise.all([
            fetch('/api/kasa-banka/kasalar'),
            fetch('/api/kasa-banka/bankalar'),
            fetch('/api/kasa-banka/hareketler')
        ]);
        globalState.kasalar = await kasaRes.json();
        globalState.bankalar = await bankaRes.json();
        const hareketler = await harRes.json();

        // Kartları Render Et
        const grid = document.getElementById('hesap-kartlari-grid');
        let html = '';

        // Kasalar
        globalState.kasalar.forEach(k => {
            html += `
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                            <i data-lucide="wallet" class="w-4 h-4 text-emerald-600"></i> ${escapeHtml(k.ad)}
                        </span>
                        <div class="flex items-center gap-1">
                            <span class="text-[10px] font-mono px-1.5 py-0.5 bg-slate-100 rounded text-slate-600 mr-1">${escapeHtml(k.kod)}</span>
                            <button onclick="openEditKasaModal(${k.id})" title="Kasayı Düzenle" class="p-1 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded transition">
                                <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            </button>
                            <button onclick="deleteKasa(${k.id}, '${escapeHtml(k.ad)}')" title="Kasayı Sil" class="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition">
                                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                    </div>
                    <div class="mt-3">
                        <div class="text-xl font-black text-slate-900">${formatMoney(k.bakiye)}</div>
                        <div class="text-[11px] text-slate-400 mt-0.5">${k.islem_sayisi} işlem kaydedildi</div>
                    </div>
                    <div class="absolute bottom-0 left-0 right-0 h-1 bg-emerald-500"></div>
                </div>
            `;
        });

        // Bankalar
        globalState.bankalar.forEach(b => {
            html += `
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                            <i data-lucide="landmark" class="w-4 h-4 text-blue-600"></i> ${escapeHtml(b.banka_adi)}
                        </span>
                        <div class="flex items-center gap-1">
                            <span class="text-[10px] text-slate-400 mr-1">${escapeHtml(b.sube_adi || '')}</span>
                            <button onclick="openEditBankaModal(${b.id})" title="Banka Hesabını Düzenle" class="p-1 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded transition">
                                <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            </button>
                            <button onclick="deleteBanka(${b.id}, '${escapeHtml(b.banka_adi)}')" title="Banka Hesabını Sil" class="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition">
                                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                    </div>
                    <div class="mt-3">
                        <div class="text-xl font-black text-slate-900">${formatMoney(b.bakiye)}</div>
                        <div class="text-[10px] text-slate-500 font-mono truncate mt-0.5" title="${escapeHtml(b.iban)}">${escapeHtml(b.iban)}</div>
                    </div>
                    <div class="absolute bottom-0 left-0 right-0 h-1 bg-blue-500"></div>
                </div>
            `;
        });

        grid.innerHTML = html;

        // Hareketler Tablosu
        const tbody = document.getElementById('kasa-hareketleri-table-body');
        if (!hareketler || hareketler.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400 text-xs">Henüz kasa veya banka hareketi bulunmuyor.</td></tr>`;
        } else {
            tbody.innerHTML = hareketler.map(h => {
                const isGiris = h.islem_turu.includes('TAHSILAT') || h.islem_turu.includes('GELEN');
                const sign = isGiris ? '+' : '-';
                const color = isGiris ? 'text-emerald-600 font-black' : 'text-red-600 font-black';

                const turAdlari = {
                    'KASA_TAHSILAT': 'Nakit Tahsilat',
                    'KASA_ODEME': 'Nakit Ödeme',
                    'BANKA_GELEN_HAVALE': 'Gelen Havale/EFT',
                    'BANKA_GIDEN_HAVALE': 'Giden Havale/EFT',
                    'KREDI_KARTI_TAHSILAT': 'Kredi Kartı ile Tahsilat',
                    'POS_TAHSILAT': 'Kredi Kartı ile Tahsilat',
                    'KASA_BANKA_VIRMAN': 'Kasadan Bankaya Virman',
                    'BANKA_KASA_VIRMAN': 'Bankadan Nakit Çekim',
                    'CEK_TAHSILATI_KASA': 'Çek Tahsilatı (Kasa)',
                    'CEK_TAHSILATI_BANKA': 'Çek Tahsilatı (Banka)',
                    'MASRAF_ODEME': 'Masraf / Gider Ödemesi'
                };

                const isCek = h.islem_turu && h.islem_turu.startsWith('CEK_');

                return `
                    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                        <td class="py-3 px-4 text-xs text-slate-600">${formatDate(h.islem_tarihi)}</td>
                        <td class="py-3 px-4 font-semibold text-xs text-slate-800">${turAdlari[h.islem_turu] || h.islem_turu}</td>
                        <td class="py-3 px-4 text-xs font-medium text-slate-700">${h.kasa_adi || h.banka_adi || '-'}</td>
                        <td class="py-3 px-4 text-xs text-slate-800">${h.cari_unvan || '-'} ${h.fatura_no ? `(Fat: ${h.fatura_no})` : ''}</td>
                        <td class="py-3 px-4 text-xs text-slate-500">${h.evrak_no ? `[${h.evrak_no}] ` : ''}${h.aciklama || '-'}</td>
                        <td class="py-3 px-4 text-right text-xs ${color}">${sign}${formatMoney(h.tutar)}</td>
                        <td class="py-3 px-4 text-center">
                            <div class="inline-flex items-center justify-center gap-1">
                                ${!isCek ? `
                                <button onclick="openEditIslemModal(${h.id})" title="İşlemi Düzenle" class="p-1.5 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded transition">
                                    <i data-lucide="edit-3" class="w-4 h-4"></i>
                                </button>
                                ` : ''}
                                <button onclick="deleteIslemRow(${h.id})" title="İşlemi Sil" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition">
                                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        lucide.createIcons();
    } catch (e) {
        console.error("Kasa/Banka yüklenirken hata:", e);
    }
}

// Tahsilat & Ödeme Modal İşlemleri
async function openIslemModal(tur = 'KASA_TAHSILAT', cariId = null, faturaId = null) {
    const editIdEl = document.getElementById('islem-edit-id');
    if (editIdEl) editIdEl.value = '';
    const titleEl = document.getElementById('islem-modal-baslik');
    if (titleEl) {
        if (tur === 'KREDI_KARTI_TAHSILAT' || tur === 'POS_TAHSILAT') {
            titleEl.innerHTML = '<i data-lucide="credit-card" class="w-4 h-4 text-indigo-600"></i> Kredi Kartı ile Tahsilat (POS)';
        } else {
            titleEl.innerHTML = '<i data-lucide="arrow-down-left" class="w-4 h-4 text-emerald-600"></i> Tahsilat & Ödeme Girişi';
        }
    }
    const submitBtn = document.getElementById('islem-submit-btn');
    if (submitBtn) {
        submitBtn.innerText = (tur === 'KREDI_KARTI_TAHSILAT' || tur === 'POS_TAHSILAT') ? 'Tahsilatı Tamamla' : 'İşlemi Tamamla';
    }

    if (!globalState.cariler || globalState.cariler.length === 0) {
        try {
            const cRes = await fetch('/api/cariler');
            if (cRes.ok) globalState.cariler = await cRes.json();
        } catch (_) {}
    }
    if (!globalState.kasalar || globalState.kasalar.length === 0) {
        try {
            const kRes = await fetch('/api/kasa-banka/kasalar');
            if (kRes.ok) globalState.kasalar = await kRes.json();
        } catch (_) {}
    }
    if (!globalState.bankalar || globalState.bankalar.length === 0) {
        try {
            const bRes = await fetch('/api/kasa-banka/bankalar');
            if (bRes.ok) globalState.bankalar = await bRes.json();
        } catch (_) {}
    }

    document.getElementById('islem-form-turu').value = tur;
    document.getElementById('islem-form-tarih').value = new Date().toISOString().split('T')[0];
    document.getElementById('islem-form-tutar').value = '';
    document.getElementById('islem-form-aciklama').value = '';
    document.getElementById('islem-form-evrak').value = '';

    // Cari Seçenekleri
    const cariSelect = document.getElementById('islem-form-cari');
    cariSelect.innerHTML = '<option value="">-- İlgili Cari Yok / Seçilmedi --</option>' + (globalState.cariler || []).map(c => {
        return `<option value="${c.id}" ${c.id == cariId ? 'selected' : ''}>${c.kod} - ${c.unvan}</option>`;
    }).join('');

    // Kasa Seçenekleri
    const kasaSelect = document.getElementById('islem-form-kasa');
    kasaSelect.innerHTML = (globalState.kasalar || []).map(k => `<option value="${k.id}">${k.ad}</option>`).join('');

    // Banka Seçenekleri
    const bankaSelect = document.getElementById('islem-form-banka');
    bankaSelect.innerHTML = (globalState.bankalar || []).map(b => `<option value="${b.id}">${b.banka_adi} - ${b.iban}</option>`).join('');

    adjustIslemForm();
    openModal('modal-islem');
    lucide.createIcons();
}

async function openEditIslemModal(hareketId) {
    try {
        if (!globalState.cariler || globalState.cariler.length === 0) {
            try {
                const cRes = await fetch('/api/cariler');
                if (cRes.ok) globalState.cariler = await cRes.json();
            } catch (_) {}
        }
        if (!globalState.kasalar || globalState.kasalar.length === 0) {
            try {
                const kRes = await fetch('/api/kasa-banka/kasalar');
                if (kRes.ok) globalState.kasalar = await kRes.json();
            } catch (_) {}
        }
        if (!globalState.bankalar || globalState.bankalar.length === 0) {
            try {
                const bRes = await fetch('/api/kasa-banka/bankalar');
                if (bRes.ok) globalState.bankalar = await bRes.json();
            } catch (_) {}
        }

        const res = await fetch(`/api/kasa-banka/hareketler/${hareketId}`);
        if (!res.ok) throw new Error('İşlem detayları alınamadı.');
        const h = await res.json();

        const editIdEl = document.getElementById('islem-edit-id');
        if (editIdEl) editIdEl.value = h.id;
        const titleEl = document.getElementById('islem-modal-baslik');
        if (titleEl) titleEl.innerHTML = '<i data-lucide="edit-3" class="w-4 h-4 text-emerald-600"></i> Tahsilat / Ödeme Düzenle';
        const submitBtn = document.getElementById('islem-submit-btn');
        if (submitBtn) submitBtn.innerText = 'Değişiklikleri Kaydet';

        document.getElementById('islem-form-turu').value = h.islem_turu;
        document.getElementById('islem-form-tarih').value = h.islem_tarihi ? h.islem_tarihi.split('T')[0] : '';
        document.getElementById('islem-form-tutar').value = h.tutar;
        document.getElementById('islem-form-aciklama').value = h.aciklama || '';
        document.getElementById('islem-form-evrak').value = h.evrak_no || '';

        // Cari Seçenekleri
        const cariSelect = document.getElementById('islem-form-cari');
        cariSelect.innerHTML = '<option value="">-- İlgili Cari Yok / Seçilmedi --</option>' + (globalState.cariler || []).map(c => {
            return `<option value="${c.id}" ${c.id == h.cari_id ? 'selected' : ''}>${c.kod} - ${c.unvan}</option>`;
        }).join('');

        // Kasa Seçenekleri
        const kasaSelect = document.getElementById('islem-form-kasa');
        kasaSelect.innerHTML = (globalState.kasalar || []).map(k => `<option value="${k.id}" ${k.id == h.kasa_id ? 'selected' : ''}>${k.ad}</option>`).join('');

        // Banka Seçenekleri
        const bankaSelect = document.getElementById('islem-form-banka');
        bankaSelect.innerHTML = (globalState.bankalar || []).map(b => `<option value="${b.id}" ${b.id == h.banka_id ? 'selected' : ''}>${b.banka_adi} - ${b.iban}</option>`).join('');

        if (h.fatura_id) {
            document.getElementById('modal-islem').setAttribute('data-fatura-id', h.fatura_id);
        } else {
            document.getElementById('modal-islem').removeAttribute('data-fatura-id');
        }

        adjustIslemForm();
        openModal('modal-islem');
        lucide.createIcons();
    } catch (e) {
        showToast('İşlem düzenleme formu açılırken hata: ' + e.message, true);
    }
}

async function deleteIslemRow(islemId) {
    if (!confirm('Bu kasa/banka hareketini silmek istediğinize emin misiniz?\n\nİşlem silindiğinde ilgili hesap bakiyesi, cari hesabı ve fatura durumu otomatik olarak düzeltilecektir.')) {
        return;
    }

    try {
        const res = await fetch(`/api/kasa-banka/hareketler/${islemId}`, {
            method: 'DELETE'
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Hareket silinemedi.');
        }

        showToast('Kasa/Banka hareketi başarıyla silindi ve bakiyeler güncellendi.');
        loadKasaBanka();
        loadCariler();
        loadFaturalar();
        loadDashboard();

        // Eğer ekstre modalı açıksa yenile
        const ekstreModal = document.getElementById('modal-cari-ekstre');
        if (ekstreModal && !ekstreModal.classList.contains('hidden')) {
            const currentCariId = ekstreModal.getAttribute('data-cari-id');
            if (currentCariId) viewCariEkstre(parseInt(currentCariId));
        }
    } catch (e) {
        showToast('Silme işlemi başarısız: ' + e.message, true);
    }
}

function openIslemForFatura(faturaId, cariId, cariUnvan, kalanTutar, faturaTuru) {
    const islemTuru = faturaTuru === 'SATIS' ? 'BANKA_GELEN_HAVALE' : 'BANKA_GIDEN_HAVALE';
    openIslemModal(islemTuru, cariId, faturaId);
    document.getElementById('islem-form-tutar').value = kalanTutar;
    document.getElementById('islem-form-aciklama').value = `Fatura Tahsilatı / Ödemesi`;
    // Fatura ID'sini gizli tutmak için modalda attribute verelim
    document.getElementById('modal-islem').setAttribute('data-fatura-id', faturaId);
}

function openIslemModalForCari(cariId, cariUnvan, bakiye) {
    const islemTuru = bakiye > 0 ? 'KASA_TAHSILAT' : 'KASA_ODEME';
    openIslemModal(islemTuru, cariId);
    if (bakiye !== 0) {
        document.getElementById('islem-form-tutar').value = Math.abs(bakiye);
    }
}

function adjustIslemForm() {
    const tur = document.getElementById('islem-form-turu').value;
    const kasaDiv = document.getElementById('islem-field-kasa');
    const bankaDiv = document.getElementById('islem-field-banka');
    const cariDiv = document.getElementById('islem-field-cari');
    const bankaLabel = bankaDiv ? bankaDiv.querySelector('label') : null;

    if (tur.startsWith('KASA_')) {
        kasaDiv.classList.remove('hidden');
        bankaDiv.classList.add('hidden');
        cariDiv.classList.remove('hidden');
        if (bankaLabel) bankaLabel.innerText = 'Banka Hesabı Seçiniz';
    } else if (tur.startsWith('BANKA_GELEN') || tur.startsWith('BANKA_GIDEN')) {
        kasaDiv.classList.add('hidden');
        bankaDiv.classList.remove('hidden');
        cariDiv.classList.remove('hidden');
        if (bankaLabel) bankaLabel.innerText = 'Banka Hesabı Seçiniz';
    } else if (tur === 'KREDI_KARTI_TAHSILAT' || tur === 'POS_TAHSILAT') {
        kasaDiv.classList.add('hidden');
        bankaDiv.classList.remove('hidden');
        cariDiv.classList.remove('hidden');
        if (bankaLabel) bankaLabel.innerText = 'Banka / POS Hesabı Seçiniz';
    } else if (tur === 'KASA_BANKA_VIRMAN' || tur === 'BANKA_KASA_VIRMAN') {
        kasaDiv.classList.remove('hidden');
        bankaDiv.classList.remove('hidden');
        cariDiv.classList.add('hidden');
        if (bankaLabel) bankaLabel.innerText = 'Banka Hesabı Seçiniz';
    } else {
        kasaDiv.classList.remove('hidden');
        bankaDiv.classList.remove('hidden');
        cariDiv.classList.add('hidden');
        if (bankaLabel) bankaLabel.innerText = 'Banka Hesabı Seçiniz';
    }
}

async function submitIslemForm(e) {
    e.preventDefault();
    const editId = document.getElementById('islem-edit-id')?.value;
    const isEdit = !!editId;

    const tur = document.getElementById('islem-form-turu').value;
    const tutar = parseFloat(document.getElementById('islem-form-tutar').value);
    const faturaIdAttr = document.getElementById('modal-islem').getAttribute('data-fatura-id');

    const data = {
        islem_turu: tur,
        tarih: document.getElementById('islem-form-tarih').value,
        tutar: tutar,
        kasa_id: document.getElementById('islem-form-kasa').value ? parseInt(document.getElementById('islem-form-kasa').value) : null,
        banka_id: document.getElementById('islem-form-banka').value ? parseInt(document.getElementById('islem-form-banka').value) : null,
        cari_id: document.getElementById('islem-form-cari').value ? parseInt(document.getElementById('islem-form-cari').value) : null,
        fatura_id: faturaIdAttr ? parseInt(faturaIdAttr) : null,
        aciklama: document.getElementById('islem-form-aciklama').value,
        evrak_no: document.getElementById('islem-form-evrak').value
    };

    const url = isEdit ? `/api/kasa-banka/hareketler/${editId}` : '/api/kasa-banka/islem';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'İşlem gerçekleştirilemedi.');
        }
        document.getElementById('modal-islem').removeAttribute('data-fatura-id');
        closeModal('modal-islem');
        showToast(isEdit ? 'İşlem başarıyla güncellendi.' : 'Tahsilat/Ödeme işlemi başarıyla kaydedildi.');
        loadKasaBanka();
        loadCariler();
        loadFaturalar();
        loadDashboard();

        // Eğer ekstre modalı açıksa yenile
        const ekstreModal = document.getElementById('modal-cari-ekstre');
        if (ekstreModal && !ekstreModal.classList.contains('hidden') && data.cari_id) {
            viewCariEkstre(parseInt(data.cari_id));
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

function openNewKasaModal() {
    const editIdEl = document.getElementById('kasa-edit-id');
    if (editIdEl) editIdEl.value = '';
    const titleEl = document.getElementById('modal-kasa-baslik');
    if (titleEl) titleEl.innerText = 'Yeni Nakit Kasa Tanımla';
    const submitBtn = document.getElementById('kasa-submit-btn');
    if (submitBtn) submitBtn.innerText = 'Kaydet';

    document.getElementById('kasa-yeni-ad').value = '';
    document.getElementById('kasa-yeni-pb').value = 'TRY';
    openModal('modal-kasa-ekle');
}

async function openEditKasaModal(kasaId) {
    try {
        const res = await fetch(`/api/kasa-banka/kasalar/${kasaId}`);
        if (!res.ok) throw new Error('Kasa bilgileri alınamadı.');
        const k = await res.json();

        const editIdEl = document.getElementById('kasa-edit-id');
        if (editIdEl) editIdEl.value = k.id;
        const titleEl = document.getElementById('modal-kasa-baslik');
        if (titleEl) titleEl.innerText = 'Kasa Bilgilerini Düzenle';
        const submitBtn = document.getElementById('kasa-submit-btn');
        if (submitBtn) submitBtn.innerText = 'Değişiklikleri Kaydet';

        document.getElementById('kasa-yeni-ad').value = k.ad || '';
        document.getElementById('kasa-yeni-pb').value = k.para_birimi || 'TRY';
        openModal('modal-kasa-ekle');
    } catch (e) {
        showToast(e.message, true);
    }
}

async function deleteKasa(kasaId, kasaAdi) {
    if (!confirm(`"${kasaAdi}" kasasını silmek istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/kasa-banka/kasalar/${kasaId}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Kasa silinemedi.');
        }
        showToast('Kasa başarıyla silindi.');
        loadKasaBanka();
    } catch (e) {
        showToast(e.message, true);
    }
}

function openNewBankaModal() {
    const editIdEl = document.getElementById('banka-edit-id');
    if (editIdEl) editIdEl.value = '';
    const titleEl = document.getElementById('modal-banka-baslik');
    if (titleEl) titleEl.innerText = 'Yeni Banka Hesabı Ekle';
    const submitBtn = document.getElementById('banka-submit-btn');
    if (submitBtn) submitBtn.innerText = 'Kaydet';

    document.getElementById('banka-yeni-ad').value = '';
    document.getElementById('banka-yeni-sube').value = '';
    document.getElementById('banka-yeni-iban').value = '';
    openModal('modal-banka-ekle');
}

async function openEditBankaModal(bankaId) {
    try {
        const res = await fetch(`/api/kasa-banka/bankalar/${bankaId}`);
        if (!res.ok) throw new Error('Banka bilgileri alınamadı.');
        const b = await res.json();

        const editIdEl = document.getElementById('banka-edit-id');
        if (editIdEl) editIdEl.value = b.id;
        const titleEl = document.getElementById('modal-banka-baslik');
        if (titleEl) titleEl.innerText = 'Banka Hesabını Düzenle';
        const submitBtn = document.getElementById('banka-submit-btn');
        if (submitBtn) submitBtn.innerText = 'Değişiklikleri Kaydet';

        document.getElementById('banka-yeni-ad').value = b.banka_adi || '';
        document.getElementById('banka-yeni-sube').value = b.sube_adi || '';
        document.getElementById('banka-yeni-iban').value = b.iban || '';
        openModal('modal-banka-ekle');
    } catch (e) {
        showToast(e.message, true);
    }
}

async function deleteBanka(bankaId, bankaAdi) {
    if (!confirm(`"${bankaAdi}" banka hesabını silmek istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/kasa-banka/bankalar/${bankaId}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Banka hesabı silinemedi.');
        }
        showToast('Banka hesabı başarıyla silindi.');
        loadKasaBanka();
    } catch (e) {
        showToast(e.message, true);
    }
}

async function submitKasaForm(e) {
    e.preventDefault();
    const editId = document.getElementById('kasa-edit-id')?.value;
    const isEdit = !!editId;

    const data = {
        ad: document.getElementById('kasa-yeni-ad').value,
        para_birimi: document.getElementById('kasa-yeni-pb').value
    };

    const url = isEdit ? `/api/kasa-banka/kasalar/${editId}` : '/api/kasa-banka/kasalar';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Kasa işlemi gerçekleştirilemedi.');
        }
        closeModal('modal-kasa-ekle');
        showToast(isEdit ? 'Kasa bilgileri güncellendi.' : 'Yeni kasa oluşturuldu.');
        loadKasaBanka();
    } catch (e) {
        showToast(e.message, true);
    }
}

async function submitBankaForm(e) {
    e.preventDefault();
    const editId = document.getElementById('banka-edit-id')?.value;
    const isEdit = !!editId;

    const data = {
        banka_adi: document.getElementById('banka-yeni-ad').value,
        sube_adi: document.getElementById('banka-yeni-sube').value,
        iban: document.getElementById('banka-yeni-iban').value
    };

    const url = isEdit ? `/api/kasa-banka/bankalar/${editId}` : '/api/kasa-banka/bankalar';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Banka işlemi gerçekleştirilemedi.');
        }
        closeModal('modal-banka-ekle');
        showToast(isEdit ? 'Banka hesabı güncellendi.' : 'Yeni banka hesabı eklendi.');
        loadKasaBanka();
    } catch (e) {
        showToast(e.message, true);
    }
}

// --- 5. ÇEK TAKİBİ YÖNETİMİ ---
async function loadCekler(subFilter = null) {
    const tur = document.getElementById('cek-filter-turu').value;
    const durum = document.getElementById('cek-filter-durum').value;
    const search = document.getElementById('cek-search').value;

    let url = `/api/cekler?`;
    if (tur) url += `cek_turu=${tur}&`;
    if (durum) url += `durum=${durum}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;

    try {
        const res = await fetch(url);
        let data = await res.json();

        if (subFilter === 'GECIKTI') {
            data = data.filter(c => c.vade_uyari === 'GECIKTI');
        } else if (subFilter === 'YAKLASTI') {
            data = data.filter(c => c.vade_uyari === 'YAKLASTI' || c.vade_uyari === 'BUGUN');
        }

        const tbody = document.getElementById('cekler-table-body');
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center py-8 text-slate-400 text-xs">Kayıtlı çek bulunamadı.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(c => {
            const turBadge = c.cek_turu === 'ALINAN'
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">Müşteri Çeki</span>'
                : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">Firma Çekimiz</span>';

            let vadeBadge = '';
            if (c.vade_uyari === 'GECIKTI') {
                vadeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-black bg-red-100 text-red-700 flex items-center gap-1 w-max"><i data-lucide="alert-circle" class="w-3 h-3"></i> ${Math.abs(c.kalan_gun)} Gün Geçti</span>`;
            } else if (c.vade_uyari === 'BUGUN') {
                vadeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-black bg-amber-100 text-amber-800 w-max">BUGÜN!</span>`;
            } else if (c.vade_uyari === 'YAKLASTI') {
                vadeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 w-max">${c.kalan_gun} Gün Kaldı</span>`;
            } else if (c.vade_uyari === 'KAPANDI') {
                vadeBadge = `<span class="px-2 py-0.5 rounded text-[10px] text-slate-400 w-max">Kapandı</span>`;
            } else {
                vadeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-medium text-emerald-700 bg-emerald-50 w-max">${c.kalan_gun} Gün Var</span>`;
            }

            const durumEtiketleri = {
                'PORTFOYDE': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">Portföyde</span>',
                'BANKAYA_VERILDI': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">Bankada</span>',
                'TAHSIL_EDILDI': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">Tahsil Edildi</span>',
                'CIROLANMIS': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">Cirolandı</span>',
                'KARSILIKSIZ': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800">Karşılıksız</span>',
                'IADE_EDILDI': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-600">İade Edildi</span>'
            };

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="py-3 px-4 font-mono font-bold text-xs text-slate-900">${c.cek_no}</td>
                    <td class="py-3 px-4">${turBadge}</td>
                    <td class="py-3 px-4 font-bold text-xs text-slate-800">${formatDate(c.vade_tarihi)}</td>
                    <td class="py-3 px-4">${vadeBadge}</td>
                    <td class="py-3 px-4 text-xs">
                        <div class="font-bold text-slate-800">${c.banka_adi}</div>
                        <div class="text-[10px] text-slate-400">${c.sube_adi || ''}</div>
                    </td>
                    <td class="py-3 px-4 text-xs">
                        <div class="font-bold text-slate-900 truncate max-w-[150px]">${c.cari_unvan}</div>
                        <div class="text-[10px] text-slate-400">${c.kesideci ? 'Keşideci: ' + c.kesideci : ''}</div>
                    </td>
                    <td class="py-3 px-4 text-right font-black text-slate-900">${formatMoney(c.tutar)}</td>
                    <td class="py-3 px-4 text-center">${durumEtiketleri[c.durum] || c.durum}</td>
                    <td class="py-3 px-4 text-center">
                        <div class="flex items-center justify-center gap-1">
                            ${c.durum === 'PORTFOYDE' || c.durum === 'BANKAYA_VERILDI' ? `
                                <button onclick="openCekDurumModal(${c.id}, '${c.cek_no}', ${c.tutar})" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 rounded text-xs font-bold transition">
                                    İşlem Yap
                                </button>
                            ` : '<span class="text-xs text-slate-400 mr-2">-</span>'}
                            <button onclick="deleteCekRow(${c.id}, '${c.cek_no}')" title="Çeki Tamamen Sil" class="p-1 hover:bg-rose-50 text-rose-600 rounded transition">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
    } catch (e) {
        console.error("Çekler yüklenirken hata:", e);
    }
}

function openCekModal(tur = 'ALINAN') {
    document.getElementById('cek-form-turu').value = tur;
    document.getElementById('cek-modal-baslik').innerHTML = tur === 'ALINAN'
        ? `<i data-lucide="credit-card" class="w-4 h-4 text-blue-600"></i> Yeni Alınan Müşteri Çeki`
        : `<i data-lucide="credit-card" class="w-4 h-4 text-slate-700"></i> Verilen Firma Çekimiz`;

    document.getElementById('cek-form-no').value = '';
    document.getElementById('cek-form-vade').value = '';
    document.getElementById('cek-form-tutar').value = '';
    document.getElementById('cek-form-banka').value = '';
    document.getElementById('cek-form-sube').value = '';
    document.getElementById('cek-form-kesideci').value = '';
    document.getElementById('cek-form-aciklama').value = '';

    const cariSelect = document.getElementById('cek-form-cari');
    cariSelect.innerHTML = '<option value="">-- Çekin Alındığı / Verildiği Cari --</option>' + globalState.cariler.map(c => {
        return `<option value="${c.id}">${c.kod} - ${c.unvan}</option>`;
    }).join('');

    openModal('modal-cek');
}

async function submitCekForm(e) {
    e.preventDefault();
    const data = {
        cek_turu: document.getElementById('cek-form-turu').value,
        cek_no: document.getElementById('cek-form-no').value,
        vade_tarihi: document.getElementById('cek-form-vade').value,
        tutar: parseFloat(document.getElementById('cek-form-tutar').value),
        banka_adi: document.getElementById('cek-form-banka').value,
        sube_adi: document.getElementById('cek-form-sube').value,
        kesideci: document.getElementById('cek-form-kesideci').value,
        cari_id: parseInt(document.getElementById('cek-form-cari').value),
        aciklama: document.getElementById('cek-form-aciklama').value
    };

    try {
        const res = await fetch('/api/cekler', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Çek kaydedilemedi.');
        }
        closeModal('modal-cek');
        showToast('Çek portföye başarıyla kaydedildi.');
        loadCekler();
        loadCariler();
        loadDashboard();
    } catch (err) {
        showToast(err.message, true);
    }
}

// Çek Durum Değişikliği (Tahsil Etme / Ciro / Karşılıksız)
function openCekDurumModal(id, cekNo, tutar) {
    document.getElementById('cek-durum-id').value = id;
    document.getElementById('cek-durum-no').innerText = cekNo;
    document.getElementById('cek-durum-tutar').innerText = formatMoney(tutar);
    document.getElementById('cek-durum-tarih').value = new Date().toISOString().split('T')[0];

    // Banka listesini doldur
    const bankaSelect = document.getElementById('cek-durum-banka');
    bankaSelect.innerHTML = globalState.bankalar.map(b => `<option value="${b.id}">${b.banka_adi} - ${b.iban}</option>`).join('');

    // Kasa listesini doldur
    const kasaSelect = document.getElementById('cek-durum-kasa');
    kasaSelect.innerHTML = globalState.kasalar.map(k => `<option value="${k.id}">${k.ad}</option>`).join('');

    // Ciro edilecek cari listesi
    const ciroSelect = document.getElementById('cek-durum-ciro-select');
    ciroSelect.innerHTML = '<option value="">-- Cirolanacak Tedarikçi / Cari --</option>' + globalState.cariler.map(c => {
        return `<option value="${c.id}">${c.kod} - ${c.unvan}</option>`;
    }).join('');

    adjustCekDurumForm();
    openModal('modal-cek-durum');
}

function adjustCekDurumForm() {
    const yeni = document.getElementById('cek-durum-yeni').value;
    const tahsilDiv = document.getElementById('cek-durum-tahsil-hesap');
    const ciroDiv = document.getElementById('cek-durum-ciro-cari');

    if (yeni === 'TAHSIL_EDILDI') {
        tahsilDiv.classList.remove('hidden');
        ciroDiv.classList.add('hidden');
    } else if (yeni === 'CIROLANMIS') {
        tahsilDiv.classList.add('hidden');
        ciroDiv.classList.remove('hidden');
    } else {
        tahsilDiv.classList.add('hidden');
        ciroDiv.classList.add('hidden');
    }
}

function adjustTahsilHedef() {
    const tur = document.getElementById('cek-durum-aktarim-turu').value;
    const bDiv = document.getElementById('cek-durum-banka-div');
    const kDiv = document.getElementById('cek-durum-kasa-div');
    if (tur === 'BANKA') {
        bDiv.classList.remove('hidden');
        kDiv.classList.add('hidden');
    } else {
        bDiv.classList.add('hidden');
        kDiv.classList.remove('hidden');
    }
}

async function submitCekDurumForm(e) {
    e.preventDefault();
    const cekId = document.getElementById('cek-durum-id').value;
    const yeniDurum = document.getElementById('cek-durum-yeni').value;
    const aktarimTuru = document.getElementById('cek-durum-aktarim-turu').value;

    const data = {
        yeni_durum: yeniDurum,
        islem_tarihi: document.getElementById('cek-durum-tarih').value,
        banka_id: (yeniDurum === 'TAHSIL_EDILDI' && aktarimTuru === 'BANKA') ? parseInt(document.getElementById('cek-durum-banka').value) : null,
        kasa_id: (yeniDurum === 'TAHSIL_EDILDI' && aktarimTuru === 'KASA') ? parseInt(document.getElementById('cek-durum-kasa').value) : null,
        cirolanan_cari_id: yeniDurum === 'CIROLANMIS' ? parseInt(document.getElementById('cek-durum-ciro-select').value) : null
    };

    try {
        const res = await fetch(`/api/cekler/${cekId}/durum`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Çek durumu güncellenemedi.');
        }
        closeModal('modal-cek-durum');
        showToast('Çek işlemi başarıyla tamamlandı.');
        loadCekler();
        loadKasaBanka();
        loadCariler();
        loadDashboard();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteCekRow(cekId, cekNo) {
    if (!confirm(`${cekNo} numaralı çek kaydını tamamen silmek istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/cekler/${cekId}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Çek silinemedi.');
        }
        showToast('Çek başarıyla silindi.');
        loadCekler();
        loadCariler();
        loadKasaBanka();
        loadDashboard();
    } catch (err) {
        showToast(err.message, true);
    }
}


// --- 6. STOKLAR & HİZMETLER ---
async function loadStoklar() {
    const tip = document.getElementById('stok-filter-tip').value;
    const search = document.getElementById('stok-search').value;

    let url = `/api/stoklar?`;
    if (tip) url += `tip=${tip}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        globalState.stoklar = data;

        const tbody = document.getElementById('stoklar-table-body');
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-400 text-xs">Stok kartı bulunamadı.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(s => {
            const isKritik = s.tip === 'URUN' && s.stok_miktari <= s.kritik_stok;
            const stokBadge = isKritik 
                ? `<span class="px-2 py-0.5 rounded text-[10px] font-black bg-red-100 text-red-700">${s.stok_miktari} (Kritik)</span>`
                : `<span class="font-bold text-slate-800">${s.stok_miktari}</span>`;

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="py-3 px-4 font-mono font-bold text-xs text-slate-700">${s.kod}</td>
                    <td class="py-3 px-4 font-bold text-xs text-slate-900">${s.ad}</td>
                    <td class="py-3 px-4 text-xs text-slate-500">${s.tip === 'URUN' ? 'Ürün' : 'Hizmet'} / ${s.birim}</td>
                    <td class="py-3 px-4 text-right font-medium text-slate-600">${formatMoney(s.alis_fiyati)}</td>
                    <td class="py-3 px-4 text-right font-bold text-slate-900">${formatMoney(s.satis_fiyati)}</td>
                    <td class="py-3 px-4 text-center font-medium text-slate-600">%${s.kdv_orani}</td>
                    <td class="py-3 px-4 text-right text-xs">${s.tip === 'URUN' ? stokBadge : '-'}</td>
                    <td class="py-3 px-4 text-center">
                        <button onclick="editStok(${s.id})" class="text-blue-600 hover:text-blue-800 text-xs font-bold mr-2">Düzenle</button>
                        <button onclick="deleteStokRow(${s.id}, '${s.ad}')" class="text-rose-600 hover:text-rose-800 text-xs font-bold">Sil</button>
                    </td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
    } catch (e) {
        console.error("Stoklar yüklenirken hata:", e);
    }
}

async function submitStokForm(e) {
    e.preventDefault();
    const data = {
        ad: document.getElementById('stok-form-ad').value,
        tip: document.getElementById('stok-form-tip').value,
        birim: document.getElementById('stok-form-birim').value,
        alis_fiyati: parseFloat(document.getElementById('stok-form-alis').value) || 0,
        satis_fiyati: parseFloat(document.getElementById('stok-form-satis').value) || 0,
        kdv_orani: parseFloat(document.getElementById('stok-form-kdv').value) || 0.0,
        stok_miktari: parseFloat(document.getElementById('stok-form-miktar').value) || 0,
        kritik_stok: 5.0
    };

    try {
        const res = await fetch('/api/stoklar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Stok kartı kaydedilemedi.');
        closeModal('modal-stok-ekle');
        showToast('Yeni ürün/hizmet kartı başarıyla eklendi.');
        loadStoklar();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteStokRow(stokId, ad) {
    if (!confirm(`"${ad}" isimli stok kartını silmek istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/stoklar/${stokId}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Stok kartı silinemedi.');
        }
        showToast('Stok kartı başarıyla silindi.');
        loadStoklar();
    } catch (err) {
        showToast(err.message, true);
    }
}


// --- 7. MALİ RAPORLAR & ANALİZ MODÜLÜ ---
let currentRaporSubTab = 'faturalar';
let lastRaporData = { faturalar: null, tahsilat: null, hesap: null, kdv: null };
let raporDebounceTimer = null;

function formatDateInput(d) {
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function setRaporDateRange(range) {
    const now = new Date();
    let start = '';
    let end = '';

    if (range === 'today') {
        start = formatDateInput(now);
        end = formatDateInput(now);
    } else if (range === 'this_week') {
        const day = now.getDay();
        const diffToMonday = now.getDate() - (day === 0 ? 6 : day - 1);
        const monday = new Date(now.getFullYear(), now.getMonth(), diffToMonday);
        start = formatDateInput(monday);
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        end = formatDateInput(sunday);
    } else if (range === 'this_month') {
        const y = now.getFullYear();
        const m = now.getMonth();
        start = formatDateInput(new Date(y, m, 1));
        end = formatDateInput(new Date(y, m + 1, 0));
    } else if (range === 'this_year') {
        const y = now.getFullYear();
        start = `${y}-01-01`;
        end = `${y}-12-31`;
    } else if (range === 'all') {
        start = '';
        end = '';
    }

    document.getElementById('rapor-baslangic').value = start;
    document.getElementById('rapor-bitis').value = end;

    // Chip butonlarının stillerini güncelle
    document.querySelectorAll('.rapor-chip').forEach(btn => {
        if (btn.dataset.range === range) {
            btn.className = 'rapor-chip px-3 py-1.5 text-xs font-bold rounded-lg border border-blue-600 bg-blue-50 text-blue-700 transition';
        } else {
            btn.className = 'rapor-chip px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 transition';
        }
    });

    fetchActiveRapor();
}

function onRaporCustomDateChange() {
    // Özel tarih girildiğinde buton seçimini kaldır
    document.querySelectorAll('.rapor-chip').forEach(btn => {
        btn.className = 'rapor-chip px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 transition';
    });
    fetchActiveRapor();
}

function switchRaporSubTab(subTab) {
    currentRaporSubTab = subTab;

    // Buton aktifliklerini ayarla
    document.querySelectorAll('.rapor-subtab-btn').forEach(btn => {
        btn.className = 'rapor-subtab-btn px-4 py-2.5 text-xs font-semibold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2 transition';
    });
    const activeBtn = document.getElementById(`btn-subtab-${subTab}`);
    if (activeBtn) {
        activeBtn.className = 'rapor-subtab-btn px-4 py-2.5 text-xs font-bold border-b-2 border-blue-600 text-blue-600 flex items-center gap-2 transition';
    }

    // İçerikleri göster/gizle
    document.querySelectorAll('.rapor-subcontent').forEach(el => el.classList.add('hidden'));
    const activeContent = document.getElementById(`rapor-subcontent-${subTab}`);
    if (activeContent) {
        activeContent.classList.remove('hidden');
    }

    lucide.createIcons();
    fetchActiveRapor();
}

function debounceRaporFilter() {
    clearTimeout(raporDebounceTimer);
    raporDebounceTimer = setTimeout(() => {
        fetchActiveRapor();
    }, 300);
}

async function populateRaporHesapSelect() {
    const select = document.getElementById('rh-filter-hesap');
    if (!select) return;
    const currentVal = select.value;

    try {
        const [kasaRes, bankaRes] = await Promise.all([
            fetch('/api/kasa-banka/kasalar'),
            fetch('/api/kasa-banka/bankalar')
        ]);
        const kasalar = await kasaRes.json();
        const bankalar = await bankaRes.json();

        let html = '<option value="TUMU">Tüm Kasa ve Bankalar (Konsolide)</option>';
        if (kasalar.length > 0) {
            html += '<optgroup label="Nakit Kasalar">';
            kasalar.forEach(k => {
                html += `<option value="KASA_${k.id}">[Kasa] ${k.ad} (${formatMoney(k.bakiye)})</option>`;
            });
            html += '</optgroup>';
        }
        if (bankalar.length > 0) {
            html += '<optgroup label="Banka Hesapları">';
            bankalar.forEach(b => {
                html += `<option value="BANKA_${b.id}">[Banka] ${b.banka_adi} - ${b.iban} (${formatMoney(b.bakiye)})</option>`;
            });
            html += '</optgroup>';
        }
        select.innerHTML = html;
        if (currentVal) select.value = currentVal;
    } catch (e) {
        console.error("Hesap listesi doldurulamadı:", e);
    }
}

async function loadRaporlar() {
    const baslangicInput = document.getElementById('rapor-baslangic');
    const bitisInput = document.getElementById('rapor-bitis');

    if (!baslangicInput.value && !bitisInput.value) {
        const now = new Date();
        const y = now.getFullYear();
        const m = now.getMonth();
        baslangicInput.value = formatDateInput(new Date(y, m, 1));
        bitisInput.value = formatDateInput(new Date(y, m + 1, 0));
    }

    await populateRaporHesapSelect();
    await fetchActiveRapor();
}

async function fetchActiveRapor() {
    if (currentRaporSubTab === 'faturalar') {
        await loadRaporFaturalar();
    } else if (currentRaporSubTab === 'tahsilat') {
        await loadRaporTahsilat();
    } else if (currentRaporSubTab === 'hesap') {
        await loadRaporHesap();
    } else if (currentRaporSubTab === 'kdv') {
        await loadRaporKdv();
    }
    lucide.createIcons();
}

// 1. FATURALAR RAPORU YÜKLE
async function loadRaporFaturalar() {
    const baslangic = document.getElementById('rapor-baslangic').value;
    const bitis = document.getElementById('rapor-bitis').value;
    const tur = document.getElementById('rf-filter-tur').value;
    const durum = document.getElementById('rf-filter-durum').value;
    const search = document.getElementById('rf-search').value;

    let url = `/api/raporlar/faturalar?tur=${tur}&durum=${durum}`;
    if (baslangic) url += `&baslangic=${baslangic}`;
    if (bitis) url += `&bitis=${bitis}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        lastRaporData.faturalar = data;

        // KPI Kartlarını Doldur
        document.getElementById('badge-rapor-fatura-count').innerText = data.ozet.toplam_adet;
        document.getElementById('rf-satis-toplam').innerText = formatMoney(data.ozet.satis_toplam);
        document.getElementById('rf-satis-adet').innerText = `${data.ozet.satis_adet} Fatura Kesildi`;
        document.getElementById('rf-satis-kdv').innerText = `${formatMoney(data.ozet.satis_kdv)} KDV`;

        document.getElementById('rf-alis-toplam').innerText = formatMoney(data.ozet.alis_toplam);
        document.getElementById('rf-alis-adet').innerText = `${data.ozet.alis_adet} Fatura Alındı`;
        document.getElementById('rf-alis-kdv').innerText = `${formatMoney(data.ozet.alis_kdv)} KDV`;

        document.getElementById('rf-odenen-toplam').innerText = formatMoney(data.ozet.satis_odenen + data.ozet.alis_odenen);
        document.getElementById('rf-kalan-toplam').innerText = formatMoney(data.ozet.satis_kalan + data.ozet.alis_kalan);

        // Tabloyu Doldur
        const tbody = document.getElementById('rf-table-body');
        if (!data.faturalar || data.faturalar.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-slate-400">Seçilen tarih aralığında ve kriterlerde fatura bulunamadı.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.faturalar.map(f => {
            const turBadge = f.fatura_turu === 'SATIS'
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">Satış</span>'
                : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">Alış</span>';

            let durumBadge = '';
            if (f.odeme_durumu === 'ODENDI') durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">Ödendi</span>';
            else if (f.odeme_durumu === 'KISMI') durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700">Kısmi</span>';
            else if (f.odeme_durumu === 'IPTAL') durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-500 line-through">İptal</span>';
            else durumBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-red-700">Bekliyor</span>';

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="py-2.5 px-4 text-slate-600 font-medium">${formatDate(f.fatura_tarihi)}</td>
                    <td class="py-2.5 px-4 font-mono font-bold text-slate-900">${f.fatura_no}</td>
                    <td class="py-2.5 px-4">${turBadge}</td>
                    <td class="py-2.5 px-4">
                        <div class="font-bold text-slate-800">${f.cari_unvan}</div>
                        <div class="text-[10px] text-slate-400 font-mono">${f.cari_kod || ''}</div>
                    </td>
                    <td class="py-2.5 px-4 text-right text-slate-600">${formatMoney(f.ara_toplam)}</td>
                    <td class="py-2.5 px-4 text-right text-slate-600">${formatMoney(f.kdv_toplam)}</td>
                    <td class="py-2.5 px-4 text-right font-bold text-slate-900">${formatMoney(f.genel_toplam)}</td>
                    <td class="py-2.5 px-4 text-right font-medium ${f.kalan_tutar > 0.01 ? 'text-amber-600 font-bold' : 'text-slate-400'}">${formatMoney(f.kalan_tutar)}</td>
                    <td class="py-2.5 px-4 text-center">${durumBadge}</td>
                    <td class="py-2.5 px-4 text-center">
                        <button onclick="viewFaturaDetay(${f.id})" title="Fatura Görüntüle" class="p-1 hover:bg-blue-50 text-blue-600 rounded transition">
                            <i data-lucide="eye" class="w-4 h-4"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error("Fatura raporu yüklenemedi:", e);
    }
}

// 2. TAHSİLAT & ÖDEME RAPORU YÜKLE
async function loadRaporTahsilat() {
    const baslangic = document.getElementById('rapor-baslangic').value;
    const bitis = document.getElementById('rapor-bitis').value;
    const islemGrubu = document.getElementById('rt-filter-grup').value;
    const search = document.getElementById('rt-search').value;

    let url = `/api/raporlar/tahsilat-odeme?islem_grubu=${islemGrubu}`;
    if (baslangic) url += `&baslangic=${baslangic}`;
    if (bitis) url += `&bitis=${bitis}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        lastRaporData.tahsilat = data;

        // KPI Kartlarını Doldur
        document.getElementById('badge-rapor-tahsilat-count').innerText = data.ozet.toplam_adet;
        document.getElementById('rt-tahsilat-toplam').innerText = formatMoney(data.ozet.toplam_tahsilat);
        document.getElementById('rt-tahsilat-alt').innerText = `${data.ozet.tahsilat_adet} işlem (Kasa: ${formatMoney(data.ozet.kasa_tahsilat)}, Banka: ${formatMoney(data.ozet.banka_tahsilat)})`;

        document.getElementById('rt-odeme-toplam').innerText = formatMoney(data.ozet.toplam_odeme);
        document.getElementById('rt-odeme-alt').innerText = `${data.ozet.odeme_adet} işlem (Kasa: ${formatMoney(data.ozet.kasa_odeme)}, Banka: ${formatMoney(data.ozet.banka_odeme)})`;

        const netAkisEl = document.getElementById('rt-net-akis');
        netAkisEl.innerText = formatMoney(data.ozet.net_nakit_akisi);
        if (data.ozet.net_nakit_akisi > 0) {
            netAkisEl.className = 'text-2xl font-black text-emerald-600 mt-2';
            document.getElementById('rt-net-alt').innerText = 'Nakit Fazlası (Tahsilat Ağırlıklı)';
        } else if (data.ozet.net_nakit_akisi < 0) {
            netAkisEl.className = 'text-2xl font-black text-red-600 mt-2';
            document.getElementById('rt-net-alt').innerText = 'Nakit Açığı (Ödeme Ağırlıklı)';
        } else {
            netAkisEl.className = 'text-2xl font-black text-slate-800 mt-2';
            document.getElementById('rt-net-alt').innerText = 'Nakit Giriş & Çıkış Dengede';
        }

        // Tabloyu Doldur
        const tbody = document.getElementById('rt-table-body');
        if (!data.hareketler || data.hareketler.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-400">Seçilen tarih aralığında ve kriterlerde tahsilat veya ödeme hareketi bulunamadı.</td></tr>`;
            return;
        }

        const islemRozetleri = {
            'KASA_TAHSILAT': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">Nakit Tahsilat</span>',
            'KASA_ODEME': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-red-700">Nakit Ödeme</span>',
            'BANKA_GELEN_HAVALE': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700">Gelen Havale/EFT</span>',
            'BANKA_GIDEN_HAVALE': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-50 text-orange-700">Giden Havale/EFT</span>',
            'KREDI_KARTI_TAHSILAT': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700">Kredi Kartı / POS</span>',
            'POS_TAHSILAT': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700">Kredi Kartı / POS</span>',
            'CEK_TAHSILATI_KASA': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700">Çek Tahsilatı (Kasa)</span>',
            'CEK_TAHSILATI_BANKA': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700">Çek Tahsilatı (Banka)</span>',
            'KASA_BANKA_VIRMAN': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">Kasa ➔ Banka</span>',
            'BANKA_KASA_VIRMAN': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">Banka ➔ Kasa</span>',
            'MASRAF_ODEME': '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700">Masraf Ödemesi</span>'
        };

        tbody.innerHTML = data.hareketler.map(h => {
            const rozet = islemRozetleri[h.islem_turu] || `<span class="px-1.5 py-0.5 rounded text-[10px] bg-slate-100">${h.islem_turu}</span>`;
            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="py-2.5 px-4 text-slate-600 font-medium">${formatDate(h.islem_tarihi)}</td>
                    <td class="py-2.5 px-4">${rozet}</td>
                    <td class="py-2.5 px-4 font-bold text-slate-800">${h.hesap_tanimi}</td>
                    <td class="py-2.5 px-4">
                        <div class="font-medium text-slate-900">${h.cari_unvan || '-'}</div>
                    </td>
                    <td class="py-2.5 px-4 font-mono text-slate-600">${h.evrak_no || '-'}</td>
                    <td class="py-2.5 px-4 text-slate-600">${h.aciklama || '-'}</td>
                    <td class="py-2.5 px-4 text-right font-bold ${h.giris > 0 ? 'text-emerald-600' : 'text-slate-300'}">
                        ${h.giris > 0 ? '+' + formatMoney(h.giris) : '-'}
                    </td>
                    <td class="py-2.5 px-4 text-right font-bold ${h.cikis > 0 ? 'text-red-600' : 'text-slate-300'}">
                        ${h.cikis > 0 ? '-' + formatMoney(h.cikis) : '-'}
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error("Tahsilat raporu yüklenemedi:", e);
    }
}

// 3. HESAP HAREKETLERİ (MUAVİN) RAPORU YÜKLE
async function loadRaporHesap() {
    const baslangic = document.getElementById('rapor-baslangic').value;
    const bitis = document.getElementById('rapor-bitis').value;
    const hesapSecimi = document.getElementById('rh-filter-hesap').value;
    const search = document.getElementById('rh-search').value;

    let url = `/api/raporlar/hesap-hareketleri?hesap_secimi=${hesapSecimi}`;
    if (baslangic) url += `&baslangic=${baslangic}`;
    if (bitis) url += `&bitis=${bitis}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        lastRaporData.hesap = data;

        // KPI Kartlarını Doldur
        document.getElementById('rh-devir-bakiye').innerText = formatMoney(data.ozet.devir_bakiye);
        document.getElementById('rh-toplam-giris').innerText = '+' + formatMoney(data.ozet.toplam_giris);
        document.getElementById('rh-toplam-cikis').innerText = '-' + formatMoney(data.ozet.toplam_cikis);
        document.getElementById('rh-kapanis-bakiye').innerText = formatMoney(data.ozet.kapanis_bakiye);

        // Tabloyu Doldur
        const tbody = document.getElementById('rh-table-body');
        if (!data.hareketler || data.hareketler.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center py-8 text-slate-400">Seçilen hesap ve tarih aralığında hareket kaydı bulunamadı.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.hareketler.map(h => {
            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="py-2.5 px-4 text-slate-600 font-medium">${formatDate(h.islem_tarihi)}</td>
                    <td class="py-2.5 px-4 font-bold text-slate-800">${h.hesap_tanimi}</td>
                    <td class="py-2.5 px-4">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">${h.islem_turu}</span>
                    </td>
                    <td class="py-2.5 px-4 text-slate-800 font-medium">${h.cari_unvan || (h.fatura_no ? 'Fatura: ' + h.fatura_no : '-')}</td>
                    <td class="py-2.5 px-4 font-mono text-slate-600">${h.evrak_no || '-'}</td>
                    <td class="py-2.5 px-4 text-slate-600">${h.aciklama || '-'}</td>
                    <td class="py-2.5 px-4 text-right font-medium ${h.giris > 0 ? 'text-emerald-600 font-bold' : 'text-slate-300'}">
                        ${h.giris > 0 ? '+' + formatMoney(h.giris) : '-'}
                    </td>
                    <td class="py-2.5 px-4 text-right font-medium ${h.cikis > 0 ? 'text-red-600 font-bold' : 'text-slate-300'}">
                        ${h.cikis > 0 ? '-' + formatMoney(h.cikis) : '-'}
                    </td>
                    <td class="py-2.5 px-4 text-right font-black text-slate-900">${formatMoney(h.yuruyen_bakiye)}</td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error("Hesap hareketleri yüklenemedi:", e);
    }
}

// 4. KDV RAPORU YÜKLE
async function loadRaporKdv() {
    const baslangic = document.getElementById('rapor-baslangic').value;
    const bitis = document.getElementById('rapor-bitis').value;

    let url = '/api/raporlar/kdv?';
    if (baslangic) url += `baslangic=${baslangic}&`;
    if (bitis) url += `bitis=${bitis}&`;

    try {
        const res = await fetch(url);
        const kdv = await res.json();
        lastRaporData.kdv = kdv;

        document.getElementById('kdv-hesaplanan').innerText = formatMoney(kdv.hesaplanan_kdv);
        document.getElementById('kdv-satis-matrah').innerText = `Matrah: ${formatMoney(kdv.satis_matrah)}`;
        document.getElementById('kdv-indirilecek').innerText = formatMoney(kdv.indirilecek_kdv);
        document.getElementById('kdv-alis-matrah').innerText = `Matrah: ${formatMoney(kdv.alis_matrah)}`;
        document.getElementById('kdv-fark').innerText = formatMoney(Math.abs(kdv.fark));
        document.getElementById('kdv-sonuc-baslik').innerText = kdv.durum;
        document.getElementById('kdv-sonuc-aciklama').innerText = kdv.fark > 0 
            ? 'Bu dönem vergi dairesine ödenecek tahmini KDV tutarıdır.'
            : (kdv.fark < 0 ? 'Gelecek döneme devreden KDV alacağıdır.' : 'Hesaplanan ve indirilecek KDV denktir.');

        document.getElementById('kdv-tarih-etiket').innerText = (baslangic && bitis)
            ? `${formatDate(baslangic)} — ${formatDate(bitis)}`
            : 'Tüm Dönemler';

        const kutu = document.getElementById('kdv-sonuc-kutu');
        if (kdv.fark > 0) {
            kutu.className = 'p-4 rounded-xl bg-amber-50 border border-amber-200';
        } else {
            kutu.className = 'p-4 rounded-xl bg-emerald-50 border border-emerald-200';
        }
    } catch (e) {
        console.error("KDV raporu yüklenemedi:", e);
    }
}

// 5. RAPOR YAZDIRMA & ÖNİZLEME PENCERESİ
function openRaporPrintModal() {
    const baslangic = document.getElementById('rapor-baslangic').value;
    const bitis = document.getElementById('rapor-bitis').value;
    const donemStr = (baslangic && bitis)
        ? `${formatDate(baslangic)} — ${formatDate(bitis)}`
        : (baslangic ? `${formatDate(baslangic)}'den İtibaren` : 'Tüm Dönemler');

    document.getElementById('rapor-print-firma').innerText = globalState.ayarlar.firma_adi || 'ÖZERLER MERMER';
    document.getElementById('rapor-print-adres').innerText = globalState.ayarlar.adres || '';
    document.getElementById('rapor-print-vergi').innerText = `${globalState.ayarlar.vergi_dairesi || ''} / ${globalState.ayarlar.vergi_no || ''}`;
    document.getElementById('rapor-print-donem').innerText = donemStr;
    document.getElementById('rapor-print-cikti-tarihi').innerText = formatDate(new Date().toISOString());

    const ozetDiv = document.getElementById('rapor-print-ozet-kutulari');
    const thead = document.getElementById('rapor-print-thead');
    const tbody = document.getElementById('rapor-print-tbody');
    const turEtiket = document.getElementById('rapor-print-tur-etiket');

    if (currentRaporSubTab === 'faturalar' && lastRaporData.faturalar) {
        const d = lastRaporData.faturalar;
        turEtiket.innerText = 'DÖNEMSEL FATURALAR RAPORU';
        ozetDiv.innerHTML = `
            <div class="grid grid-cols-4 gap-3">
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Toplam Satış</span>
                    <div class="text-sm font-black text-slate-900 mt-1">${formatMoney(d.ozet.satis_toplam)}</div>
                    <span class="text-[10px] text-slate-500">${d.ozet.satis_adet} Fatura</span>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Toplam Alış</span>
                    <div class="text-sm font-black text-slate-900 mt-1">${formatMoney(d.ozet.alis_toplam)}</div>
                    <span class="text-[10px] text-slate-500">${d.ozet.alis_adet} Fatura</span>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Hesaplanan KDV</span>
                    <div class="text-sm font-black text-slate-900 mt-1">${formatMoney(d.ozet.satis_kdv)}</div>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Bekleyen Bakiye</span>
                    <div class="text-sm font-black text-amber-700 mt-1">${formatMoney(d.ozet.satis_kalan + d.ozet.alis_kalan)}</div>
                </div>
            </div>
        `;
        thead.innerHTML = `
            <tr class="bg-slate-100 text-slate-700 font-bold border-b border-slate-300">
                <th class="py-2 px-3">Tarih</th>
                <th class="py-2 px-3">Fatura No</th>
                <th class="py-2 px-3">Tür</th>
                <th class="py-2 px-3">Cari Unvanı</th>
                <th class="py-2 px-3 text-right">Ara Toplam</th>
                <th class="py-2 px-3 text-right">KDV</th>
                <th class="py-2 px-3 text-right">Genel Toplam</th>
                <th class="py-2 px-3 text-right">Kalan</th>
                <th class="py-2 px-3 text-center">Durum</th>
            </tr>
        `;
        tbody.innerHTML = d.faturalar.map(f => `
            <tr class="border-b border-slate-200">
                <td class="py-2 px-3">${formatDate(f.fatura_tarihi)}</td>
                <td class="py-2 px-3 font-mono font-bold">${f.fatura_no}</td>
                <td class="py-2 px-3 font-semibold">${f.fatura_turu === 'SATIS' ? 'Satış' : 'Alış'}</td>
                <td class="py-2 px-3 font-medium">${f.cari_unvan}</td>
                <td class="py-2 px-3 text-right">${formatMoney(f.ara_toplam)}</td>
                <td class="py-2 px-3 text-right">${formatMoney(f.kdv_toplam)}</td>
                <td class="py-2 px-3 text-right font-bold">${formatMoney(f.genel_toplam)}</td>
                <td class="py-2 px-3 text-right font-medium">${formatMoney(f.kalan_tutar)}</td>
                <td class="py-2 px-3 text-center">${f.odeme_durumu}</td>
            </tr>
        `).join('');

    } else if (currentRaporSubTab === 'tahsilat' && lastRaporData.tahsilat) {
        const d = lastRaporData.tahsilat;
        turEtiket.innerText = 'TAHSİLAT VE ÖDEMELER RAPORU';
        ozetDiv.innerHTML = `
            <div class="grid grid-cols-3 gap-3">
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Toplam Tahsilatlar (+)</span>
                    <div class="text-sm font-black text-emerald-700 mt-1">${formatMoney(d.ozet.toplam_tahsilat)}</div>
                    <span class="text-[10px] text-slate-500">${d.ozet.tahsilat_adet} işlem</span>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Toplam Ödemeler (-)</span>
                    <div class="text-sm font-black text-red-700 mt-1">${formatMoney(d.ozet.toplam_odeme)}</div>
                    <span class="text-[10px] text-slate-500">${d.ozet.odeme_adet} işlem</span>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Net Nakit Akışı</span>
                    <div class="text-sm font-black text-slate-900 mt-1">${formatMoney(d.ozet.net_nakit_akisi)}</div>
                </div>
            </div>
        `;
        thead.innerHTML = `
            <tr class="bg-slate-100 text-slate-700 font-bold border-b border-slate-300">
                <th class="py-2 px-3">Tarih</th>
                <th class="py-2 px-3">İşlem Türü</th>
                <th class="py-2 px-3">Hesap</th>
                <th class="py-2 px-3">Cari / Muhatap</th>
                <th class="py-2 px-3">Evrak No</th>
                <th class="py-2 px-3">Açıklama</th>
                <th class="py-2 px-3 text-right">Tahsilat (+)</th>
                <th class="py-2 px-3 text-right">Ödeme (-)</th>
            </tr>
        `;
        tbody.innerHTML = d.hareketler.map(h => `
            <tr class="border-b border-slate-200">
                <td class="py-2 px-3">${formatDate(h.islem_tarihi)}</td>
                <td class="py-2 px-3 font-semibold">${h.islem_turu}</td>
                <td class="py-2 px-3">${h.hesap_tanimi}</td>
                <td class="py-2 px-3 font-medium">${h.cari_unvan || '-'}</td>
                <td class="py-2 px-3 font-mono">${h.evrak_no || '-'}</td>
                <td class="py-2 px-3">${h.aciklama || '-'}</td>
                <td class="py-2 px-3 text-right font-bold">${h.giris > 0 ? '+' + formatMoney(h.giris) : '-'}</td>
                <td class="py-2 px-3 text-right font-bold">${h.cikis > 0 ? '-' + formatMoney(h.cikis) : '-'}</td>
            </tr>
        `).join('');

    } else if (currentRaporSubTab === 'hesap' && lastRaporData.hesap) {
        const d = lastRaporData.hesap;
        turEtiket.innerText = 'HESAP HAREKETLERİ MUAVİN DÖKÜMÜ';
        ozetDiv.innerHTML = `
            <div class="grid grid-cols-4 gap-3">
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Devir Bakiyesi</span>
                    <div class="text-sm font-black text-slate-800 mt-1">${formatMoney(d.ozet.devir_bakiye)}</div>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Toplam Giriş (+)</span>
                    <div class="text-sm font-black text-emerald-700 mt-1">${formatMoney(d.ozet.toplam_giris)}</div>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Toplam Çıkış (-)</span>
                    <div class="text-sm font-black text-red-700 mt-1">${formatMoney(d.ozet.toplam_cikis)}</div>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Kapanış Bakiyesi</span>
                    <div class="text-sm font-black text-blue-900 mt-1">${formatMoney(d.ozet.kapanis_bakiye)}</div>
                </div>
            </div>
        `;
        thead.innerHTML = `
            <tr class="bg-slate-100 text-slate-700 font-bold border-b border-slate-300">
                <th class="py-2 px-3">Tarih</th>
                <th class="py-2 px-3">Hesap</th>
                <th class="py-2 px-3">İşlem Türü</th>
                <th class="py-2 px-3">Cari / Açıklama</th>
                <th class="py-2 px-3">Evrak No</th>
                <th class="py-2 px-3 text-right">Giriş (+)</th>
                <th class="py-2 px-3 text-right">Çıkış (-)</th>
                <th class="py-2 px-3 text-right font-black">Bakiye</th>
            </tr>
        `;
        tbody.innerHTML = d.hareketler.map(h => `
            <tr class="border-b border-slate-200">
                <td class="py-2 px-3">${formatDate(h.islem_tarihi)}</td>
                <td class="py-2 px-3 font-semibold">${h.hesap_tanimi}</td>
                <td class="py-2 px-3">${h.islem_turu}</td>
                <td class="py-2 px-3">${h.cari_unvan || h.aciklama || '-'}</td>
                <td class="py-2 px-3 font-mono">${h.evrak_no || '-'}</td>
                <td class="py-2 px-3 text-right font-medium">${h.giris > 0 ? '+' + formatMoney(h.giris) : '-'}</td>
                <td class="py-2 px-3 text-right font-medium">${h.cikis > 0 ? '-' + formatMoney(h.cikis) : '-'}</td>
                <td class="py-2 px-3 text-right font-bold">${formatMoney(h.yuruyen_bakiye)}</td>
            </tr>
        `).join('');

    } else if (lastRaporData.kdv) {
        const kdv = lastRaporData.kdv;
        turEtiket.innerText = 'DÖNEMSEL KDV DURUMU RAPORU';
        ozetDiv.innerHTML = `
            <div class="grid grid-cols-3 gap-3">
                <div class="p-4 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-xs font-bold text-slate-600 uppercase">Hesaplanan KDV (391)</span>
                    <div class="text-lg font-black text-blue-900 mt-1">${formatMoney(kdv.hesaplanan_kdv)}</div>
                    <span class="text-xs text-slate-500">Matrah: ${formatMoney(kdv.satis_matrah)}</span>
                </div>
                <div class="p-4 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-xs font-bold text-slate-600 uppercase">İndirilecek KDV (191)</span>
                    <div class="text-lg font-black text-purple-900 mt-1">${formatMoney(kdv.indirilecek_kdv)}</div>
                    <span class="text-xs text-slate-500">Matrah: ${formatMoney(kdv.alis_matrah)}</span>
                </div>
                <div class="p-4 bg-slate-50 border border-slate-200 rounded text-center">
                    <span class="text-xs font-bold text-slate-600 uppercase">Net Vergi Durumu</span>
                    <div class="text-lg font-black text-slate-900 mt-1">${formatMoney(Math.abs(kdv.fark))}</div>
                    <span class="text-xs font-bold text-blue-700">${kdv.durum}</span>
                </div>
            </div>
        `;
        thead.innerHTML = '';
        tbody.innerHTML = '';
    }

    openModal('modal-rapor-yazdir');
}

// --- 8. AYARLAR & YEDEKLEME ---
async function loadAyarlar() {
    try {
        const res = await fetch('/api/ayarlar');
        const a = await res.json();
        globalState.ayarlar = a;

        document.getElementById('sidebar-firma-adi').innerText = a.firma_adi || 'Ön Muhasebe';
        document.getElementById('ayarlar-firma-adi').value = a.firma_adi || '';
        document.getElementById('ayarlar-yetkili').value = a.yetkili || '';
        document.getElementById('ayarlar-vergi-dairesi').value = a.vergi_dairesi || '';
        document.getElementById('ayarlar-vergi-no').value = a.vergi_no || '';
        document.getElementById('ayarlar-telefon').value = a.telefon || '';
        document.getElementById('ayarlar-eposta').value = a.eposta || '';
        document.getElementById('ayarlar-web').value = a.web || '';
        document.getElementById('ayarlar-adres').value = a.adres || '';
        document.getElementById('ayarlar-varsayilan-banka').value = a.varsayilan_banka || '';
        document.getElementById('ayarlar-varsayilan-iban').value = a.varsayilan_iban || '';
        document.getElementById('ayarlar-fatura-notu').value = a.fatura_notu || '';
    } catch (e) {
        console.error("Ayarlar yüklenirken hata:", e);
    }
}

async function saveAyarlar(e) {
    e.preventDefault();
    const data = {
        firma_adi: document.getElementById('ayarlar-firma-adi').value,
        yetkili: document.getElementById('ayarlar-yetkili').value,
        vergi_dairesi: document.getElementById('ayarlar-vergi-dairesi').value,
        vergi_no: document.getElementById('ayarlar-vergi-no').value,
        telefon: document.getElementById('ayarlar-telefon').value,
        eposta: document.getElementById('ayarlar-eposta').value,
        web: document.getElementById('ayarlar-web').value,
        adres: document.getElementById('ayarlar-adres').value,
        varsayilan_banka: document.getElementById('ayarlar-varsayilan-banka').value,
        varsayilan_iban: document.getElementById('ayarlar-varsayilan-iban').value,
        fatura_notu: document.getElementById('ayarlar-fatura-notu').value
    };

    try {
        const res = await fetch('/api/ayarlar', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Ayarlar kaydedilemedi.');
        showToast('Firma bilgileri başarıyla güncellendi.');
        loadAyarlar();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function loadSampleData() {
    if (!confirm("Örnek demo verileri yüklemek istiyor musunuz?")) return;
    try {
        const res = await fetch('/api/ayarlar/ornek-veri-yukle', { method: 'POST' });
        if (!res.ok) throw new Error('Veriler yüklenemedi.');
        showToast('Örnek veriler başarıyla yüklendi.');
        loadDashboard();
        loadCariler();
        loadFaturalar();
        loadKasaBanka();
        loadCekler();
        loadStoklar();
    } catch (e) {
        showToast(e.message, true);
    }
}

async function uploadYedekDosyasi(event) {
    const file = event.target.files[0];
    if (!file) return;
    if (!confirm(`"${file.name}" isimli yedek dosyasını geri yüklemek istiyor musunuz?\n\nDikkat: Mevcut veritabanının güvenlik yedeği otomatik olarak data klasörüne kaydedilecektir.`)) {
        event.target.value = '';
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch('/api/ayarlar/yedek-yukle', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Yedek yüklenemedi.');
        alert(data.message || 'Yedek başarıyla yüklendi!');
        location.reload();
    } catch (e) {
        alert('Yükleme Hatası: ' + e.message);
    } finally {
        event.target.value = '';
    }
}

async function resetAllData(tumunuTemizle = true) {
    const mesaj = tumunuTemizle
        ? "⚠️ DİKKAT: Veritabanındaki TÜM örnek faturalar, cariler, stoklar, çekler ve kasa/banka hareketleri silinecektir.\n\nKendi şirket kayıtlarınızla sıfırdan tertemiz bir başlangıç yapmak için bu işlem önerilir.\n\nİşlemden önce mevcut veritabanının otomatik güvenlik yedeği 'data/yedekler' klasörüne kaydedilecektir.\n\nDevam etmek istiyor musunuz?"
        : "⚠️ DİKKAT: Tüm faturalar, çekler ve kasa/banka hareketleri sıfırlanacaktır. Cari ve Stok kartlarınız korunacak ancak bakiyeleri 0 olacaktır.\n\nDevam etmek istiyor musunuz?";

    if (!confirm(mesaj)) return;

    try {
        const res = await fetch(`/api/ayarlar/verileri-sifirla?tumunu_temizle=${tumunuTemizle}`, {
            method: 'POST'
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Sıfırlama işlemi başarısız.');
        alert(data.message || 'Veriler başarıyla temizlendi!');
        location.reload();
    } catch (e) {
        alert('Hata: ' + e.message);
    }
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('hidden');
    lucide.createIcons();
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
}

// ESC Tuşu ile Modal Kapatma
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('[id^="modal-"]').forEach(m => m.classList.add('hidden'));
    }
});

async function uygulamayiKapat() {
    if (!confirm('Ön Muhasebe Pro programını kapatmak istediğinize emin misiniz?')) {
        return;
    }
    try {
        await fetch('/api/ayarlar/kapat', { method: 'POST' });
    } catch (e) {
        // Backend kapanırken fetch iptal olabilir, normaldir
    }
    document.body.innerHTML = `
        <div style="height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0f172a;color:#f8fafc;font-family:system-ui,-apple-system,sans-serif;">
            <div style="text-align:center;padding:2rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;box-shadow:0 20px 25px -5px rgba(0,0,0,0.5);max-width:400px;">
                <div style="font-size:3rem;margin-bottom:1rem;">👋</div>
                <h2 style="font-size:1.25rem;font-weight:700;margin-bottom:0.5rem;">Program Güvenle Kapatıldı</h2>
                <p style="font-size:0.875rem;color:#94a3b8;margin-bottom:1.5rem;">Tüm verileriniz kaydedildi. Bu pencereyi kapatabilirsiniz.</p>
                <button onclick="window.close()" style="background:#2563eb;color:#fff;border:none;padding:0.6rem 1.5rem;border-radius:0.5rem;font-weight:600;cursor:pointer;">Pencereyi Kapat</button>
            </div>
        </div>
    `;
    setTimeout(() => {
        try { window.close(); } catch (e) {}
    }, 400);
}


// Sayfa Başlangıcı
window.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('header-date').innerText = new Date().toLocaleDateString('tr-TR', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });

    await loadAyarlar();
    await loadCariler();
    await loadStoklar();
    await loadKasaBanka();
    await loadDashboard();

    lucide.createIcons();
});
