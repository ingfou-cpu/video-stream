let selectedIds = new Set();

function toggleRow(id) {
    const cb = document.getElementById('cb-' + id);
    cb.checked = !cb.checked;
    const tr = document.getElementById('row-' + id);
    if (cb.checked) {
        selectedIds.add(id);
        tr.classList.add('selected');
    } else {
        selectedIds.delete(id);
        tr.classList.remove('selected');
    }
    updateDeleteButton();
}

function toggleAll(source) {
    document.querySelectorAll('.record-cb').forEach(cb => {
        cb.checked = source.checked;
        const id = Number(cb.id.replace('cb-', ''));
        const tr = document.getElementById('row-' + id);
        if (source.checked) {
            selectedIds.add(id);
            tr.classList.add('selected');
        } else {
            selectedIds.delete(id);
            tr.classList.remove('selected');
        }
    });
    updateDeleteButton();
}

function updateDeleteButton() {
    const btn = document.getElementById('deleteSelectedBtn');
    const count = selectedIds.size;
    if (count > 0) {
        btn.textContent = 'Supprimer (' + count + ')';
        btn.disabled = false;
    } else {
        btn.textContent = 'Supprimer sélection';
        btn.disabled = true;
    }
}

function deleteSelected() {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    if (!confirm('Supprimer ' + ids.length + ' enregistrement(s) ?')) return;
    document.getElementById('delete-ids').value = ids.join(',');
    document.getElementById('delete-form').submit();
}

function deleteAll() {
    if (!confirm('Supprimer TOUS les enregistrements ? Cette action est irréversible.')) return;
    document.getElementById('delete-all-form').submit();
}

function openModal(id) {
    document.getElementById(id).classList.add('active');
    document.body.style.overflow = 'hidden';
    const firstInput = document.querySelector('#' + id + ' input:not([type="hidden"])');
    if (firstInput) setTimeout(() => firstInput.focus(), 100);
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    document.body.style.overflow = '';
}

function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(m => {
        m.classList.remove('active');
    });
    document.body.style.overflow = '';
}

function openAddModal() {
    document.getElementById('add-form').reset();
    openModal('add-modal');
}

function openEditModal(id) {
    fetch('/detail/' + id + '/')
        .then(r => r.json())
        .then(data => {
            document.getElementById('edit-id').value = data.id;
            document.getElementById('edit-sous_secteur').value = data.sous_secteur;
            document.getElementById('edit-n_operati').value = data.n_operati;
            document.getElementById('edit-chapitre').value = data.chapitre;
            document.getElementById('edit-libelle_op').value = data.libelle_op;
            document.getElementById('edit-ap_initial').value = data.ap_initial;
            document.getElementById('edit-commune').value = data.commune;
            document.getElementById('edit-gest').value = data.gest;
            document.getElementById('edit-form').action = '/edit/' + data.id + '/';
            openModal('edit-modal');
        });
}

function openSearchModal() {
    openModal('search-modal');
}

function openImportModal() {
    openModal('import-modal');
}

function performSearch() {
    const form = document.getElementById('search-form');
    const params = new URLSearchParams(window.location.search);
    form.querySelectorAll('input, select').forEach(el => {
        if (el.value) params.set(el.name, el.value);
        else params.delete(el.name);
    });
    params.set('page', '1');
    window.location.href = '/?' + params.toString();
}

function resetFilters() {
    window.location.href = '/';
}

function exportExcel() {
    window.location.href = '/export/excel/' + window.location.search;
}

function getCount() {
    const btn = document.querySelector('.btn-count');
    btn.disabled = true;
    btn.textContent = 'Comptage...';
    fetch('/count/' + window.location.search)
        .then(r => r.json())
        .then(data => {
            document.getElementById('count-display').textContent =
                'Total : ' + data.total;
            btn.disabled = false;
            btn.textContent = 'Compter';
        })
        .catch(() => {
            btn.disabled = false;
            btn.textContent = 'Compter';
        });
}

function changePerPage(val) {
    const params = new URLSearchParams(window.location.search);
    params.set('per_page', val);
    params.set('page', '1');
    window.location.href = '/?' + params.toString();
}

function sortTable(field) {
    const params = new URLSearchParams(window.location.search);
    const current = params.get('sort');
    const dir = params.get('dir');
    if (current === field) {
        params.set('dir', dir === 'desc' ? 'asc' : 'desc');
    } else {
        params.set('sort', field);
        params.set('dir', 'asc');
    }
    params.set('page', '1');
    window.location.href = '/?' + params.toString();
}

document.addEventListener('click', function(e) {
    const overlay = e.target.closest('.modal-overlay');
    if (overlay && e.target === overlay) closeAllModals();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeAllModals();
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        const activeModal = document.querySelector('.modal-overlay.active');
        if (activeModal) {
            const submitBtn = activeModal.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.click();
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    updateDeleteButton();
    setTimeout(() => {
        document.querySelectorAll('.toast').forEach(t => {
            setTimeout(() => {
                t.style.animation = 'toastOut .3s cubic-bezier(0.2,0,0,1) forwards';
                setTimeout(() => t.remove(), 300);
            }, 4000);
        });
    }, 500);
});
