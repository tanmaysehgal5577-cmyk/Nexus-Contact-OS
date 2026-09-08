/**
 * NanoBanana Contact OS — Client-Side Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // State
  let currentContacts = [];
  let currentLayout = 'grid'; // 'grid' | 'table'
  let deleteTargetId = null;

  // DOM Elements
  const cardsContainer = document.getElementById('cardsContainer');
  const tableContainer = document.getElementById('tableContainer');
  const tableBody = document.getElementById('tableBody');
  const emptyState = document.getElementById('emptyState');
  const emptyMsg = document.getElementById('emptyMsg');
  const loadingSpinner = document.getElementById('loadingSpinner');
  const totalCountBadge = document.getElementById('totalCountBadge');
  const footerStats = document.getElementById('footerStats');

  const searchInput = document.getElementById('searchInput');
  const btnClearSearch = document.getElementById('btnClearSearch');
  const sortSelect = document.getElementById('sortSelect');
  const btnGridView = document.getElementById('btnGridView');
  const btnTableView = document.getElementById('btnTableView');

  const btnOpenCreateModal = document.getElementById('btnOpenCreateModal');
  const btnSeedData = document.getElementById('btnSeedData');
  const btnExportMenu = document.getElementById('btnExportMenu');
  const exportDropdown = document.getElementById('exportDropdown');

  // Contact Modal
  const contactModal = document.getElementById('contactModal');
  const contactForm = document.getElementById('contactForm');
  const modalTitle = document.getElementById('modalTitle');
  const modalIcon = document.getElementById('modalIcon');
  const contactIdInput = document.getElementById('contactIdInput');
  const nameInput = document.getElementById('nameInput');
  const emailInput = document.getElementById('emailInput');
  const phoneInput = document.getElementById('phoneInput');
  const addressInput = document.getElementById('addressInput');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCancelModal = document.getElementById('btnCancelModal');

  // Delete Modal
  const deleteModal = document.getElementById('deleteModal');
  const deleteConfirmMsg = document.getElementById('deleteConfirmMsg');
  const btnCancelDelete = document.getElementById('btnCancelDelete');
  const btnConfirmDelete = document.getElementById('btnConfirmDelete');

  // Toast
  const toastContainer = document.getElementById('toastContainer');

  // ------------------------------------------------------------- INITIAL LOAD
  loadContacts();
  loadStats();

  // ------------------------------------------------------------- EVENT LISTENERS
  // Search
  let searchDebounce = null;
  searchInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    btnClearSearch.classList.toggle('visible', val.length > 0);
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      loadContacts();
    }, 250);
  });

  btnClearSearch.addEventListener('click', () => {
    searchInput.value = '';
    btnClearSearch.classList.remove('visible');
    loadContacts();
  });

  // Sort
  sortSelect.addEventListener('change', () => {
    loadContacts();
  });

  // View switch
  btnGridView.addEventListener('click', () => {
    currentLayout = 'grid';
    btnGridView.classList.add('active');
    btnTableView.classList.remove('active');
    renderContacts();
  });

  btnTableView.addEventListener('click', () => {
    currentLayout = 'table';
    btnTableView.classList.add('active');
    btnGridView.classList.remove('active');
    renderContacts();
  });

  // Export dropdown
  btnExportMenu.addEventListener('click', (e) => {
    e.stopPropagation();
    exportDropdown.classList.toggle('show');
  });

  document.addEventListener('click', () => {
    exportDropdown.classList.remove('show');
  });

  // Create Modal Open
  btnOpenCreateModal.addEventListener('click', () => {
    openModalForCreate();
  });

  // Seed Data
  btnSeedData.addEventListener('click', async () => {
    try {
      showSpinner(true);
      const res = await fetch('/api/seed', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showToast(`Added ${data.added} realistic sample contacts!`, 'success');
        loadContacts();
        loadStats();
      } else {
        showToast(data.error || 'Failed to seed sample contacts', 'error');
      }
    } catch (err) {
      showToast('Network error while seeding contacts', 'error');
    } finally {
      showSpinner(false);
    }
  });

  // Modal Closers
  btnCloseModal.addEventListener('click', closeModal);
  btnCancelModal.addEventListener('click', closeModal);
  contactModal.addEventListener('click', (e) => {
    if (e.target === contactModal) closeModal();
  });

  btnCancelDelete.addEventListener('click', closeDeleteModal);
  deleteModal.addEventListener('click', (e) => {
    if (e.target === deleteModal) closeDeleteModal();
  });

  // Form Submission (Create or Update)
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFormErrors();

    const id = contactIdInput.value;
    const payload = {
      name: nameInput.value.trim(),
      email: emailInput.value.trim(),
      phone: phoneInput.value.trim(),
      address: addressInput.value.trim(),
    };

    // Client-side quick check
    let hasError = false;
    if (!payload.name) {
      setFieldError('name', 'Full name is required.');
      hasError = true;
    }
    if (!payload.email) {
      setFieldError('email', 'Email address is required.');
      hasError = true;
    }
    if (!payload.phone) {
      setFieldError('phone', 'Phone number is required.');
      hasError = true;
    }

    if (hasError) return;

    try {
      const url = id ? `/api/contacts/${id}` : '/api/contacts';
      const method = id ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        showToast(data.error || 'Failed to save contact', 'error');
        // Map backend errors to fields if recognizable
        const err = data.error || '';
        if (err.toLowerCase().includes('email')) {
          setFieldError('email', err);
        } else if (err.toLowerCase().includes('name')) {
          setFieldError('name', err);
        } else if (err.toLowerCase().includes('phone')) {
          setFieldError('phone', err);
        }
        return;
      }

      showToast(id ? 'Contact updated successfully!' : 'New contact created!', 'success');
      closeModal();
      loadContacts();
      loadStats();
    } catch (err) {
      showToast('Network error while saving contact', 'error');
    }
  });

  // Confirm Delete
  btnConfirmDelete.addEventListener('click', async () => {
    if (!deleteTargetId) return;

    try {
      const res = await fetch(`/api/contacts/${deleteTargetId}`, {
        method: 'DELETE',
      });
      const data = await res.json();

      if (res.ok) {
        showToast('Contact deleted successfully.', 'success');
        closeDeleteModal();
        loadContacts();
        loadStats();
      } else {
        showToast(data.error || 'Failed to delete contact', 'error');
      }
    } catch (err) {
      showToast('Network error while deleting contact', 'error');
    }
  });

  // ------------------------------------------------------------- API CALLS
  async function loadContacts() {
    showSpinner(true);
    const search = searchInput.value.trim();
    const sortVal = sortSelect.value;
    let sort_by = 'name';
    let order = 'asc';

    if (sortVal === 'name_desc') {
      sort_by = 'name';
      order = 'desc';
    } else if (sortVal === 'id_asc') {
      sort_by = 'id';
      order = 'asc';
    } else if (sortVal === 'id_desc') {
      sort_by = 'id';
      order = 'desc';
    }

    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      params.append('sort_by', sort_by);
      params.append('order', order);

      const res = await fetch(`/api/contacts?${params.toString()}`);
      const data = await res.json();
      currentContacts = data.contacts || [];
      renderContacts();
    } catch (err) {
      showToast('Failed to connect to NanoBanana API', 'error');
    } finally {
      showSpinner(false);
    }
  }

  async function loadStats() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      totalCountBadge.textContent = data.total || 0;
      if (data.total > 0 && data.newest) {
        footerStats.textContent = `Latest: ${data.newest.name} • Total Contacts: ${data.total}`;
      } else {
        footerStats.textContent = 'SQLite Database Active • 0 Records';
      }
    } catch (err) {
      // Ignore
    }
  }

  // ------------------------------------------------------------- RENDERING
  function renderContacts() {
    if (currentContacts.length === 0) {
      cardsContainer.innerHTML = '';
      tableBody.innerHTML = '';
      cardsContainer.classList.add('hidden');
      tableContainer.classList.add('hidden');
      emptyState.classList.remove('hidden');

      if (searchInput.value.trim()) {
        emptyMsg.textContent = `No contacts match "${searchInput.value.trim()}". Try clearing search.`;
      } else {
        emptyMsg.textContent = 'Your contact book is empty. Create your first contact or load demo data!';
      }
      return;
    }

    emptyState.classList.add('hidden');

    if (currentLayout === 'grid') {
      tableContainer.classList.add('hidden');
      cardsContainer.classList.remove('hidden');
      renderCards();
    } else {
      cardsContainer.classList.add('hidden');
      tableContainer.classList.remove('hidden');
      renderTable();
    }
  }

  function renderCards() {
    cardsContainer.innerHTML = '';
    currentContacts.forEach((c) => {
      const initials = getInitials(c.name);
      const card = document.createElement('div');
      card.className = 'contact-card';
      card.innerHTML = `
        <div>
          <div class="card-top">
            <div class="user-meta">
              <div class="avatar-badge">${escapeHtml(initials)}</div>
              <div>
                <div class="contact-name">${escapeHtml(c.name)}</div>
                <div class="contact-id-tag">#ID ${c.id}</div>
              </div>
            </div>
          </div>
          
          <div class="card-details">
            <div class="detail-item" title="Click to copy email" data-copy="${escapeHtml(c.email)}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              <span>${escapeHtml(c.email)}</span>
            </div>
            <div class="detail-item" title="Click to copy phone" data-copy="${escapeHtml(c.phone)}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
              <span>${escapeHtml(c.phone)}</span>
            </div>
            ${c.address ? `
            <div class="detail-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              <span>${escapeHtml(c.address)}</span>
            </div>
            ` : ''}
          </div>
        </div>

        <div class="card-actions">
          <button class="btn btn-ghost btn-sm btn-edit" data-id="${c.id}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            <span>Edit</span>
          </button>
          <button class="btn btn-ghost btn-sm btn-delete" data-id="${c.id}" data-name="${escapeHtml(c.name)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            <span>Delete</span>
          </button>
        </div>
      `;

      // Copy click handler
      card.querySelectorAll('[data-copy]').forEach((el) => {
        el.addEventListener('click', () => {
          navigator.clipboard.writeText(el.dataset.copy);
          showToast(`Copied "${el.dataset.copy}" to clipboard!`, 'success');
        });
      });

      // Edit click handler
      card.querySelector('.btn-edit').addEventListener('click', () => {
        openModalForEdit(c);
      });

      // Delete click handler
      card.querySelector('.btn-delete').addEventListener('click', () => {
        openDeleteModal(c.id, c.name);
      });

      cardsContainer.appendChild(card);
    });
  }

  function renderTable() {
    tableBody.innerHTML = '';
    currentContacts.forEach((c) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-family:'JetBrains Mono',monospace; color:var(--accent-gold);">#${c.id}</td>
        <td style="font-weight:600;">${escapeHtml(c.name)}</td>
        <td>${escapeHtml(c.email)}</td>
        <td>${escapeHtml(c.phone)}</td>
        <td style="color:var(--text-muted);">${escapeHtml(c.address || '—')}</td>
        <td style="color:var(--text-dim); font-size:0.8rem;">${escapeHtml(c.updated_at || '—')}</td>
        <td class="text-right">
          <button class="btn btn-ghost btn-sm btn-edit" data-id="${c.id}">Edit</button>
          <button class="btn btn-danger btn-sm btn-delete" data-id="${c.id}" data-name="${escapeHtml(c.name)}">Delete</button>
        </td>
      `;

      tr.querySelector('.btn-edit').addEventListener('click', () => openModalForEdit(c));
      tr.querySelector('.btn-delete').addEventListener('click', () => openDeleteModal(c.id, c.name));
      tableBody.appendChild(tr);
    });
  }

  // ------------------------------------------------------------- MODAL CONTROLLERS
  function openModalForCreate() {
    clearFormErrors();
    contactForm.reset();
    contactIdInput.value = '';
    modalTitle.textContent = 'Create New Contact';
    modalIcon.textContent = '✦';
    contactModal.classList.add('open');
    nameInput.focus();
  }

  function openModalForEdit(contact) {
    clearFormErrors();
    contactIdInput.value = contact.id;
    nameInput.value = contact.name || '';
    emailInput.value = contact.email || '';
    phoneInput.value = contact.phone || '';
    addressInput.value = contact.address || '';
    modalTitle.textContent = `Edit Contact #${contact.id}`;
    modalIcon.textContent = '✎';
    contactModal.classList.add('open');
    nameInput.focus();
  }

  function closeModal() {
    contactModal.classList.remove('open');
    clearFormErrors();
  }

  function openDeleteModal(id, name) {
    deleteTargetId = id;
    deleteConfirmMsg.textContent = `Are you sure you want to permanently delete "${name}" (#${id})?`;
    deleteModal.classList.add('open');
  }

  function closeDeleteModal() {
    deleteModal.classList.remove('open');
    deleteTargetId = null;
  }

  // ------------------------------------------------------------- UTILITIES
  function showSpinner(show) {
    loadingSpinner.style.display = show ? 'flex' : 'none';
  }

  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✔' : '✖';
    toast.innerHTML = `<span style="font-weight:bold;">${icon}</span><span>${escapeHtml(message)}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function clearFormErrors() {
    document.querySelectorAll('.field-error').forEach((el) => (el.textContent = ''));
  }

  function setFieldError(field, message) {
    const el = document.getElementById(`${field}Error`);
    if (el) el.textContent = message;
  }

  function getInitials(name) {
    if (!name) return 'NB';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
