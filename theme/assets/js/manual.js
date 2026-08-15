/* 2210Docs v0.08.2
   Direct-entry source-of-truth reader with automatic progress, multiple bookmarks,
   update detection, provenance, and Work Ledger evidence. */
(function () {
  'use strict';

  const root = document.documentElement;
  const body = document.body;
  const content = document.getElementById('manualContent');
  const cover = document.getElementById('manual-top');
  const tocList = document.getElementById('tocList');
  const tocSearch = document.getElementById('tocSearch');
  const progressLine = document.getElementById('progressLine');
  const themeButton = document.getElementById('themeButton');
  const backToTop = document.getElementById('backToTop');
  const navToggle = document.getElementById('navToggle');
  const docnav = document.getElementById('docnav');
  const editMenu = document.getElementById('editMenu');
  const readingButton = document.getElementById('readingButton');
  const bookmarkControl = document.getElementById('bookmarkControl');
  const quickBookmarkButton = document.getElementById('quickBookmarkButton');
  const bookmarkPercent = document.getElementById('bookmarkPercent');
  const bookmarkMenu = document.getElementById('bookmarkMenu');
  const bookmarkName = document.getElementById('bookmarkName');
  const bookmarkReference = document.getElementById('bookmarkReference');
  const bookmarkNote = document.getElementById('bookmarkNote');
  const saveNamedBookmarkButton = document.getElementById('saveNamedBookmarkButton');
  const bookmarkList = document.getElementById('bookmarkList');
  const bookmarkCount = document.getElementById('bookmarkCount');
  const bookmarkProgressStatus = document.getElementById('bookmarkProgressStatus');
  const bookmarkProgressDetail = document.getElementById('bookmarkProgressDetail');
  const returnMarker = document.getElementById('returnMarker');
  const returnMarkerPercent = document.getElementById('returnMarkerPercent');
  const resumeSidebarButton = document.getElementById('resumeSidebarButton');
  const startOverButton = document.getElementById('startOverButton');
  const openBookmarksButton = document.getElementById('openBookmarksButton');
  const clearReadingDataButton = document.getElementById('clearReadingDataButton');
  const readingStatus = document.getElementById('readingStatus');
  const readingTimestamp = document.getElementById('readingTimestamp');
  const sidebarBookmarkList = document.getElementById('sidebarBookmarkList');
  const readingNotice = document.getElementById('readingNotice');
  const updateNotice = document.getElementById('updateNotice');
  const updateNoticeTitle = document.getElementById('updateNoticeTitle');
  const updateNoticeText = document.getElementById('updateNoticeText');
  const refreshUpdateButton = document.getElementById('refreshUpdateButton');
  const dismissUpdateButton = document.getElementById('dismissUpdateButton');
  const staticNavLinks = [...document.querySelectorAll('.nav-special-link')];
  const compactHeader = window.matchMedia('(max-width: 700px)');

  const themeKey = 'controlled-manual-theme';
  const documentKey = body?.dataset.documentKey || window.location.pathname || 'manual';
  const readingStateKey = `controlled-manual-reading-v3:${documentKey}`;
  const previousReadingStateKey = `controlled-manual-reading-v2:${documentKey}`;
  const legacyBookmarkKey = `controlled-manual-bookmark:${documentKey}`;
  const dismissedUpdateKey = `controlled-manual-dismissed-update:${documentKey}`;
  const resumeAfterRefreshKey = `controlled-manual-resume-after-refresh:${documentKey}`;
  const updateEndpoint = body?.dataset.updateEndpoint || '';
  const currentBuildId = body?.dataset.buildId || '';
  const MAX_MANUAL_BOOKMARKS = Math.max(1, Math.min(100, Number(body?.dataset.bookmarkLimit || 20)));
  const UPDATE_CHECK_MS = Math.max(15000, Math.min(3600000, Number(body?.dataset.updateCheckSeconds || 60) * 1000));

  let readingState = { schemaVersion: 3, furthest: null, bookmarks: [] };
  let currentPosition = null;
  let headings = [];
  let tocLinks = [];
  let updateTimer = 0;
  let noticeTimer = 0;
  let saveTimer = 0;
  let scrollFrame = 0;
  let pendingBuildId = '';

  function slugify(value) {
    return String(value || '')
      .toLowerCase()
      .trim()
      .replace(/&/g, ' and ')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'section';
  }

  function uniqueId(base, used) {
    let candidate = base;
    let index = 2;
    while (used.has(candidate) || document.getElementById(candidate)) {
      candidate = `${base}-${index}`;
      index += 1;
    }
    used.add(candidate);
    return candidate;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function headerHeight() {
    return document.querySelector('.topbar')?.getBoundingClientRect().height || 64;
  }

  function absoluteTop(element) {
    return window.scrollY + element.getBoundingClientRect().top;
  }

  function setThemeLabel() {
    document.querySelectorAll('[data-theme-label]').forEach((node) => {
      node.textContent = root.dataset.theme === 'dark' ? 'Light' : 'Dark';
    });
  }

  function toggleTheme() {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem(themeKey, root.dataset.theme); } catch (error) { /* View-only fallback. */ }
    setThemeLabel();
  }

  function buildToc() {
    if (!content || !tocList) return [];
    tocList.replaceChildren();
    const found = [...content.querySelectorAll(':scope > h2')];
    const used = new Set();
    const links = [];

    found.forEach((heading, index) => {
      if (!heading.id) heading.id = uniqueId(slugify(heading.textContent), used);
      else used.add(heading.id);
      heading.dataset.manualTitle = heading.textContent.trim() || `Section ${index + 1}`;

      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = `#${heading.id}`;
      link.textContent = heading.dataset.manualTitle;
      const searchable = [link.textContent];
      let sibling = heading.nextElementSibling;
      while (sibling && sibling.tagName !== 'H2') {
        searchable.push(sibling.textContent || '');
        sibling = sibling.nextElementSibling;
      }
      link.dataset.searchText = searchable.join(' ').replace(/\s+/g, ' ').toLowerCase();
      item.appendChild(link);
      tocList.appendChild(item);
      links.push(link);
    });
    return links;
  }

  function observeHeadings(links) {
    if (!('IntersectionObserver' in window) || !content) return;
    const linkById = new Map(links.map((link) => [link.hash.slice(1), link]));
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((link) => link.classList.remove('active'));
        linkById.get(entry.target.id)?.classList.add('active');
      });
    }, { rootMargin: '-18% 0px -72% 0px' });
    headings.forEach((heading) => observer.observe(heading));
  }

  function formatMetricNumbers() {
    const formatter = new Intl.NumberFormat(document.documentElement.lang || 'en-US');
    document.querySelectorAll('.metric-number[data-number]').forEach((node) => {
      const value = Number(node.dataset.number);
      if (Number.isFinite(value)) node.textContent = formatter.format(value);
    });
  }

  function firstSection() {
    return headings[0] || content || cover;
  }

  function readingBounds() {
    const startNode = firstSection();
    if (!startNode || !content) return { start: 0, end: Math.max(1, document.documentElement.scrollHeight - window.innerHeight) };
    const start = Math.max(0, absoluteTop(startNode) - headerHeight() - 14);
    const articleBottom = absoluteTop(content) + content.offsetHeight;
    const end = Math.max(start + 1, articleBottom - window.innerHeight + Math.min(180, window.innerHeight * 0.22));
    return { start, end };
  }

  function progressAt(scrollY) {
    const bounds = readingBounds();
    if (scrollY <= bounds.start) return 0;
    if (scrollY >= bounds.end) return 100;
    return clamp(((scrollY - bounds.start) / (bounds.end - bounds.start)) * 100, 0, 100);
  }

  function currentAnchor() {
    const threshold = headerHeight() + 22;
    let current = cover || firstSection();
    headings.forEach((heading) => {
      if (heading.getBoundingClientRect().top <= threshold) current = heading;
    });
    return current;
  }

  function capturePosition() {
    const anchor = currentAnchor();
    if (!anchor) return null;
    const scrollY = Math.max(0, window.scrollY);
    const progress = Number.parseFloat(progressAt(scrollY).toFixed(1));
    return {
      id: anchor.id || 'manualContent',
      title: anchor === cover ? 'Document cover' : (anchor.dataset.manualTitle || anchor.textContent.trim() || 'Document content'),
      offsetFromAnchor: scrollY - absoluteTop(anchor),
      scrollY,
      progress,
      savedAt: new Date().toISOString(),
      version: body?.dataset.documentVersion || ''
    };
  }

  function normalizePosition(value) {
    if (!value || typeof value !== 'object' || typeof value.id !== 'string') return null;
    const progress = Number(value.progress);
    return {
      id: value.id,
      title: String(value.title || 'Document content'),
      offsetFromAnchor: Number(value.offsetFromAnchor ?? value.offset ?? 0) || 0,
      scrollY: Number(value.scrollY) || 0,
      progress: Number.isFinite(progress) ? clamp(progress, 0, 100) : 0,
      savedAt: String(value.savedAt || new Date().toISOString()),
      version: String(value.version || '')
    };
  }

  function cleanBookmarkText(value, max) {
    return String(value || '').replace(/\s+/g, ' ').trim().slice(0, max);
  }

  function normalizeBookmark(value) {
    const position = normalizePosition(value);
    if (!position) return null;
    return {
      ...position,
      bookmarkId: String(value.bookmarkId || `bookmark-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`),
      name: cleanBookmarkText(value.name || value.title || 'Bookmark', 80) || 'Bookmark',
      reference: cleanBookmarkText(value.reference || value.ticket || value.record || '', 120),
      note: cleanBookmarkText(value.note || value.notes || '', 280),
      createdAt: String(value.createdAt || value.savedAt || new Date().toISOString()),
      updatedAt: String(value.updatedAt || value.savedAt || new Date().toISOString())
    };
  }

  function parseStoredReadingState(raw) {
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    return {
      schemaVersion: 3,
      furthest: normalizePosition(parsed.furthest),
      bookmarks: Array.isArray(parsed.bookmarks)
        ? parsed.bookmarks.map(normalizeBookmark).filter(Boolean).slice(0, MAX_MANUAL_BOOKMARKS)
        : []
    };
  }

  function readReadingState() {
    try {
      const current = parseStoredReadingState(localStorage.getItem(readingStateKey));
      if (current) return current;

      const previous = parseStoredReadingState(localStorage.getItem(previousReadingStateKey));
      if (previous) {
        localStorage.setItem(readingStateKey, JSON.stringify(previous));
        localStorage.removeItem(previousReadingStateKey);
        return previous;
      }

      const legacyRaw = localStorage.getItem(legacyBookmarkKey);
      if (legacyRaw) {
        const legacy = normalizePosition(JSON.parse(legacyRaw));
        if (legacy) {
          const migrated = { schemaVersion: 3, furthest: legacy, bookmarks: [] };
          localStorage.setItem(readingStateKey, JSON.stringify(migrated));
          localStorage.removeItem(legacyBookmarkKey);
          return migrated;
        }
      }
    } catch (error) {
      // Browser-local persistence is optional; reading remains available.
    }
    return { schemaVersion: 3, furthest: null, bookmarks: [] };
  }

  function persistReadingState(options = {}) {
    const write = () => {
      saveTimer = 0;
      try { localStorage.setItem(readingStateKey, JSON.stringify(readingState)); } catch (error) { /* View-only fallback. */ }
    };
    if (options.immediate) {
      if (saveTimer) window.clearTimeout(saveTimer);
      write();
      return;
    }
    if (!saveTimer) saveTimer = window.setTimeout(write, 180);
  }

  function formatSavedTime(value) {
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return 'Saved in this browser';
    try {
      return new Intl.DateTimeFormat(document.documentElement.lang || 'en-US', {
        dateStyle: 'medium', timeStyle: 'short'
      }).format(date);
    } catch (error) {
      return date.toLocaleString();
    }
  }

  function abbreviatedTitle(value, max = 42) {
    const clean = String(value || 'document content').replace(/^\d+[.)]?\s*/, '').trim();
    return clean.length > max ? `${clean.slice(0, max - 1)}…` : clean;
  }

  function showReadingNotice(message) {
    if (!readingNotice) return;
    if (noticeTimer) window.clearTimeout(noticeTimer);
    readingNotice.textContent = message;
    readingNotice.hidden = false;
    noticeTimer = window.setTimeout(() => { readingNotice.hidden = true; }, 2400);
  }

  function jumpToY(targetY) {
    const previous = root.style.scrollBehavior;
    root.style.scrollBehavior = 'auto';
    window.scrollTo(0, Math.max(0, targetY));
    window.requestAnimationFrame(() => { root.style.scrollBehavior = previous; });
  }

  function positionTargetY(position) {
    if (!position) return 0;
    const target = document.getElementById(position.id);
    if (target) {
      const offset = Number(position.offsetFromAnchor) || 0;
      return Math.max(0, absoluteTop(target) + offset);
    }
    return Math.max(0, Number(position.scrollY) || 0);
  }

  function resumePosition(position, options = {}) {
    if (!position) {
      goToSectionOne();
      return;
    }
    if (options.smooth) window.scrollTo({ top: positionTargetY(position), behavior: 'smooth' });
    else jumpToY(positionTargetY(position));
    if (!options.quiet) showReadingNotice(`Returning to ${Math.round(position.progress)}% · ${abbreviatedTitle(position.title)}.`);
  }

  function goToSectionOne() {
    const target = firstSection();
    if (!target) return;
    const top = Math.max(0, absoluteTop(target) - headerHeight() - 14);
    jumpToY(top);
    showReadingNotice('Opening section 1. Your furthest-read point and saved bookmarks remain available.');
  }

  function updateFurthest(position) {
    if (!position) return false;
    const prior = readingState.furthest;
    const hasEnteredManual = position.progress > 0 || window.scrollY >= readingBounds().start - 4;
    if (!hasEnteredManual) return false;
    if (!prior || position.progress > Number(prior.progress || 0) + 0.05) {
      readingState.furthest = position;
      persistReadingState();
      return true;
    }
    return false;
  }

  function bookmarkDefaultName(position) {
    const count = readingState.bookmarks.length + 1;
    return `Bookmark ${count} · ${abbreviatedTitle(position.title, 28)}`;
  }

  function clearBookmarkCreateForm() {
    if (bookmarkName) bookmarkName.value = '';
    if (bookmarkReference) bookmarkReference.value = '';
    if (bookmarkNote) bookmarkNote.value = '';
  }

  function saveManualBookmark(name = '', reference = '', note = '') {
    const position = capturePosition();
    if (!position) return null;
    const now = new Date().toISOString();
    const bookmark = {
      ...position,
      bookmarkId: `bookmark-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
      name: cleanBookmarkText(name, 80) || bookmarkDefaultName(position),
      reference: cleanBookmarkText(reference, 120),
      note: cleanBookmarkText(note, 280),
      createdAt: now,
      updatedAt: now
    };
    readingState.bookmarks.unshift(bookmark);
    readingState.bookmarks = readingState.bookmarks.slice(0, MAX_MANUAL_BOOKMARKS);
    persistReadingState({ immediate: true });
    renderReadingState();
    const refText = bookmark.reference ? ` · ${bookmark.reference}` : '';
    showReadingNotice(`${bookmark.name} saved at ${Math.round(bookmark.progress)}%${refText}.`);
    clearBookmarkCreateForm();
    return bookmark;
  }

  function updateManualBookmark(bookmarkId, values = {}) {
    const index = readingState.bookmarks.findIndex((item) => item.bookmarkId === bookmarkId);
    if (index < 0) return false;
    const prior = readingState.bookmarks[index];
    const position = values.moveToCurrent ? capturePosition() : prior;
    const updated = {
      ...prior,
      ...(position || {}),
      bookmarkId: prior.bookmarkId,
      name: cleanBookmarkText(values.name ?? prior.name, 80) || bookmarkDefaultName(position || prior),
      reference: cleanBookmarkText(values.reference ?? prior.reference, 120),
      note: cleanBookmarkText(values.note ?? prior.note, 280),
      createdAt: prior.createdAt || prior.savedAt || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    readingState.bookmarks[index] = updated;
    persistReadingState({ immediate: true });
    renderReadingState();
    showReadingNotice(`${updated.name} updated at ${Math.round(updated.progress)}%.`);
    return true;
  }

  function deleteManualBookmark(bookmarkId) {
    const before = readingState.bookmarks.length;
    readingState.bookmarks = readingState.bookmarks.filter((item) => item.bookmarkId !== bookmarkId);
    if (readingState.bookmarks.length === before) return;
    persistReadingState({ immediate: true });
    renderReadingState();
    showReadingNotice('Bookmark removed.');
  }

  function clearReadingData() {
    readingState = { schemaVersion: 3, furthest: null, bookmarks: [] };
    currentPosition = capturePosition();
    try {
      localStorage.removeItem(readingStateKey);
      localStorage.removeItem(previousReadingStateKey);
      localStorage.removeItem(legacyBookmarkKey);
    } catch (error) { /* Browser storage is optional. */ }
    renderReadingState();
    showReadingNotice('Reading progress and bookmarks cleared.');
  }

  function fieldLabel(text, input) {
    const label = document.createElement('label');
    label.textContent = text;
    label.appendChild(input);
    return label;
  }

  function bookmarkEditorElement(bookmark) {
    const editor = document.createElement('details');
    editor.className = 'bookmark-editor';
    const summary = document.createElement('summary');
    summary.textContent = 'Edit label, reference, note, or saved position';

    const form = document.createElement('div');
    form.className = 'bookmark-editor-form';

    const name = document.createElement('input');
    name.type = 'text';
    name.maxLength = 80;
    name.value = bookmark.name;
    name.dataset.bookmarkEditName = bookmark.bookmarkId;

    const reference = document.createElement('input');
    reference.type = 'text';
    reference.maxLength = 120;
    reference.value = bookmark.reference || '';
    reference.placeholder = 'CHG, INC, RITM, request, TASK, PR, issue, or other reference';
    reference.dataset.bookmarkEditReference = bookmark.bookmarkId;

    const note = document.createElement('textarea');
    note.rows = 2;
    note.maxLength = 280;
    note.value = bookmark.note || '';
    note.placeholder = 'Reason for the bookmark or action to revisit';
    note.dataset.bookmarkEditNote = bookmark.bookmarkId;

    const actions = document.createElement('div');
    actions.className = 'bookmark-editor-actions';

    const save = document.createElement('button');
    save.type = 'button';
    save.textContent = 'Save edits';
    save.dataset.bookmarkSaveEdit = bookmark.bookmarkId;

    const move = document.createElement('button');
    move.type = 'button';
    move.textContent = 'Move to current position';
    move.dataset.bookmarkMoveCurrent = bookmark.bookmarkId;

    const go = document.createElement('button');
    go.type = 'button';
    go.textContent = `Go to ${Math.round(bookmark.progress)}%`;
    go.dataset.bookmarkOpen = bookmark.bookmarkId;

    actions.append(save, move, go);
    form.append(
      fieldLabel('Bookmark label', name),
      fieldLabel('Ticket / controlled-record reference', reference),
      fieldLabel('Bookmark note', note),
      actions
    );
    editor.append(summary, form);
    return editor;
  }

  function bookmarkItemElement(bookmark, compact = false) {
    const row = document.createElement('div');
    row.className = compact ? 'sidebar-bookmark-item' : 'bookmark-list-item';
    row.dataset.bookmarkId = bookmark.bookmarkId;

    const summaryRow = document.createElement('div');
    summaryRow.className = 'bookmark-item-summary';

    const open = document.createElement('button');
    open.type = 'button';
    open.className = 'bookmark-open';
    open.dataset.bookmarkOpen = bookmark.bookmarkId;
    const title = document.createElement('strong');
    title.textContent = bookmark.name;
    const detail = document.createElement('small');
    const detailParts = [`${Math.round(bookmark.progress)}%`, abbreviatedTitle(bookmark.title, compact ? 26 : 42)];
    if (bookmark.reference) detailParts.push(bookmark.reference);
    detail.textContent = detailParts.join(' · ');
    open.append(title, detail);

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'bookmark-delete';
    remove.dataset.bookmarkDelete = bookmark.bookmarkId;
    remove.setAttribute('aria-label', `Delete ${bookmark.name}`);
    remove.title = `Delete ${bookmark.name}`;
    remove.textContent = '×';

    summaryRow.append(open, remove);
    row.append(summaryRow);
    if (!compact) {
      if (bookmark.note) {
        const note = document.createElement('p');
        note.className = 'bookmark-note-preview';
        note.textContent = bookmark.note;
        row.append(note);
      }
      row.append(bookmarkEditorElement(bookmark));
    }
    return row;
  }

  function renderBookmarkLists() {
    const items = readingState.bookmarks;
    if (bookmarkCount) bookmarkCount.textContent = String(items.length);

    if (bookmarkList) {
      bookmarkList.replaceChildren();
      if (!items.length) {
        const empty = document.createElement('p');
        empty.className = 'bookmark-empty';
        empty.textContent = 'No additional bookmarks saved.';
        bookmarkList.appendChild(empty);
      } else {
        items.forEach((item) => bookmarkList.appendChild(bookmarkItemElement(item, false)));
      }
    }

    if (sidebarBookmarkList) {
      sidebarBookmarkList.replaceChildren();
      items.slice(0, 4).forEach((item) => sidebarBookmarkList.appendChild(bookmarkItemElement(item, true)));
      if (items.length > 4) {
        const more = document.createElement('button');
        more.type = 'button';
        more.className = 'bookmark-more';
        more.textContent = `Manage ${items.length} bookmarks`;
        more.addEventListener('click', openBookmarkManager);
        sidebarBookmarkList.appendChild(more);
      }
    }
  }

  function clearReadingMarks() {
    headings.forEach((heading) => {
      heading.classList.remove('furthest-read-section', 'has-saved-bookmarks');
      heading.removeAttribute('data-bookmark-label');
    });
    tocLinks.forEach((link) => {
      link.classList.remove('furthest-read', 'has-saved-bookmarks');
      link.removeAttribute('data-furthest-progress');
      link.removeAttribute('data-bookmark-count');
    });
  }

  function applyReadingMarks() {
    clearReadingMarks();
    const furthest = readingState.furthest;
    if (furthest) {
      const target = document.getElementById(furthest.id);
      if (headings.includes(target)) target.classList.add('furthest-read-section');
      const link = tocLinks.find((item) => item.hash === `#${furthest.id}`);
      if (link) {
        link.classList.add('furthest-read');
        link.dataset.furthestProgress = `${Math.round(furthest.progress)}%`;
      }
    }

    const counts = new Map();
    readingState.bookmarks.forEach((item) => counts.set(item.id, (counts.get(item.id) || 0) + 1));
    counts.forEach((count, id) => {
      const target = document.getElementById(id);
      if (headings.includes(target)) {
        target.classList.add('has-saved-bookmarks');
        target.dataset.bookmarkLabel = `${count} bookmark${count === 1 ? '' : 's'}`;
      }
      const link = tocLinks.find((item) => item.hash === `#${id}`);
      if (link) {
        link.classList.add('has-saved-bookmarks');
        link.dataset.bookmarkCount = String(count);
      }
    });
  }

  function currentPercent() {
    return Number(currentPosition?.progress || 0);
  }

  function furthestPercent() {
    return Number(readingState.furthest?.progress || 0);
  }

  function setReadingLabels() {
    const furthest = furthestPercent();
    if (bookmarkPercent) bookmarkPercent.textContent = `${Math.round(currentPercent())}%`;
    if (readingButton) {
      const compact = compactHeader.matches;
      if (readingState.furthest) {
        readingButton.textContent = compact ? `Resume ${Math.round(furthest)}%` : `Resume furthest ${Math.round(furthest)}%`;
        readingButton.title = `Resume at the furthest-read point: ${Math.round(furthest)}%`;
      } else {
        readingButton.textContent = compact ? 'Read' : 'Read section 1';
        readingButton.title = 'Open the first procedure section';
      }
    }
    if (resumeSidebarButton) {
      resumeSidebarButton.disabled = !readingState.furthest;
      resumeSidebarButton.textContent = readingState.furthest ? `Resume furthest ${Math.round(furthest)}%` : 'Resume furthest read';
    }
  }

  function renderReturnMarker() {
    if (!returnMarker) return;
    const furthest = furthestPercent();
    const current = currentPercent();
    const behind = Boolean(readingState.furthest) && current < furthest - 0.8;
    returnMarker.hidden = !behind;
    if (returnMarkerPercent) returnMarkerPercent.textContent = `${Math.round(furthest)}%`;
    returnMarker.title = behind ? `Return to the furthest-read point at ${Math.round(furthest)}%` : '';
  }

  function renderReadingState() {
    applyReadingMarks();
    renderBookmarkLists();
    setReadingLabels();

    const furthest = readingState.furthest;
    if (furthest) {
      const savedVersion = furthest.version && furthest.version !== body?.dataset.documentVersion
        ? ` · recorded in ${furthest.version}` : '';
      if (readingStatus) readingStatus.textContent = `Furthest read: ${Math.round(furthest.progress)}%`;
      if (readingTimestamp) readingTimestamp.textContent = `${abbreviatedTitle(furthest.title)} · ${formatSavedTime(furthest.savedAt)}${savedVersion}`;
      if (bookmarkProgressStatus) bookmarkProgressStatus.textContent = `${Math.round(furthest.progress)}% furthest read`;
      if (bookmarkProgressDetail) bookmarkProgressDetail.textContent = `${abbreviatedTitle(furthest.title)} · advances automatically as you read farther.`;
    } else {
      if (readingStatus) readingStatus.textContent = 'Not started';
      if (readingTimestamp) readingTimestamp.textContent = 'Progress begins at section 1 and automatically follows the furthest point reached in this browser.';
      if (bookmarkProgressStatus) bookmarkProgressStatus.textContent = 'Not started';
      if (bookmarkProgressDetail) bookmarkProgressDetail.textContent = 'Automatic progress moves forward with the reader. It does not move backward when you review an earlier section.';
    }
    renderReturnMarker();
  }

  function syncHeaderGeometry() {
    const height = headerHeight();
    root.style.setProperty('--manual-header-height', `${height}px`);
    if (progressLine) progressLine.style.top = `${Math.max(0, height - 4)}px`;
  }

  function updateProgress() {
    syncHeaderGeometry();
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const pagePct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
    if (progressLine) progressLine.style.width = `${clamp(pagePct, 0, 100)}%`;
    backToTop?.classList.toggle('visible', doc.scrollTop > 600);

    currentPosition = capturePosition();
    const advanced = updateFurthest(currentPosition);
    if (advanced) applyReadingMarks();
    setReadingLabels();
    renderReturnMarker();
    if (advanced) {
      const furthest = readingState.furthest;
      if (readingStatus) readingStatus.textContent = `Furthest read: ${Math.round(furthest.progress)}%`;
      if (readingTimestamp) readingTimestamp.textContent = `${abbreviatedTitle(furthest.title)} · saved automatically in this browser`;
      if (bookmarkProgressStatus) bookmarkProgressStatus.textContent = `${Math.round(furthest.progress)}% furthest read`;
      if (bookmarkProgressDetail) bookmarkProgressDetail.textContent = `${abbreviatedTitle(furthest.title)} · advances automatically as you read farther.`;
    }
  }

  function requestProgressUpdate() {
    if (scrollFrame) return;
    scrollFrame = window.requestAnimationFrame(() => {
      scrollFrame = 0;
      updateProgress();
    });
  }

  function openBookmarkManager(options = {}) {
    if (!bookmarkMenu) return;
    bookmarkMenu.open = true;
    window.setTimeout(() => {
      if (options.bookmarkId) {
        const row = bookmarkList?.querySelector(`[data-bookmark-id="${CSS.escape(options.bookmarkId)}"]`);
        const editor = row?.querySelector('.bookmark-editor');
        if (editor) editor.open = true;
        row?.querySelector('[data-bookmark-edit-name]')?.focus();
      } else {
        bookmarkName?.focus();
      }
    }, 0);
  }

  function editValuesFor(bookmarkId) {
    const row = bookmarkList?.querySelector(`[data-bookmark-id="${CSS.escape(bookmarkId)}"]`);
    return {
      name: row?.querySelector(`[data-bookmark-edit-name="${CSS.escape(bookmarkId)}"]`)?.value || '',
      reference: row?.querySelector(`[data-bookmark-edit-reference="${CSS.escape(bookmarkId)}"]`)?.value || '',
      note: row?.querySelector(`[data-bookmark-edit-note="${CSS.escape(bookmarkId)}"]`)?.value || ''
    };
  }

  function handleBookmarkAction(event) {
    const open = event.target.closest('[data-bookmark-open]');
    if (open) {
      const item = readingState.bookmarks.find((bookmark) => bookmark.bookmarkId === open.dataset.bookmarkOpen);
      if (item) {
        bookmarkMenu && (bookmarkMenu.open = false);
        resumePosition(item);
      }
      return;
    }

    const save = event.target.closest('[data-bookmark-save-edit]');
    if (save) {
      updateManualBookmark(save.dataset.bookmarkSaveEdit, editValuesFor(save.dataset.bookmarkSaveEdit));
      return;
    }

    const move = event.target.closest('[data-bookmark-move-current]');
    if (move) {
      updateManualBookmark(move.dataset.bookmarkMoveCurrent, {
        ...editValuesFor(move.dataset.bookmarkMoveCurrent),
        moveToCurrent: true
      });
      return;
    }

    const remove = event.target.closest('[data-bookmark-delete]');
    if (remove) deleteManualBookmark(remove.dataset.bookmarkDelete);
  }

  function dismissedBuild() {
    try { return sessionStorage.getItem(dismissedUpdateKey) || ''; } catch (error) { return ''; }
  }

  function showUpdateNotice(data, options = {}) {
    if (!updateNotice) return;
    const buildId = String(data?.build_id || data?.generated_at || 'new-build');
    if (!options.demo && buildId === dismissedBuild()) return;
    pendingBuildId = buildId;
    const versionBits = [];
    if (data?.document_version && data.document_version !== body?.dataset.documentVersion) versionBits.push(`document ${data.document_version}`);
    if (data?.template_version && data.template_version !== body?.dataset.templateVersion) versionBits.push(`template ${data.template_version}`);
    const versionText = versionBits.length ? ` (${versionBits.join(' · ')})` : '';
    if (updateNoticeTitle) updateNoticeTitle.textContent = 'Update available — refresh your browser';
    if (updateNoticeText) updateNoticeText.textContent = `A newer published build${versionText} is available. Refresh to read the current source; your present location will be restored.`;
    updateNotice.hidden = false;
  }

  function hideUpdateNotice() {
    if (updateNotice) updateNotice.hidden = true;
  }

  async function checkForUpdate() {
    if (!updateEndpoint || !currentBuildId || window.location.protocol === 'file:' || !navigator.onLine) return false;
    try {
      const url = new URL(updateEndpoint, window.location.href);
      url.searchParams.set('_build_check', String(Date.now()));
      const response = await fetch(url.toString(), {
        cache: 'no-store',
        credentials: 'same-origin',
        headers: { Accept: 'application/json' }
      });
      if (!response.ok) return false;
      const data = await response.json();
      const remoteBuildId = String(data?.build_id || data?.generated_at || '');
      if (remoteBuildId && remoteBuildId !== currentBuildId) {
        showUpdateNotice(data);
        return true;
      }
    } catch (error) {
      // Reading continues; the next focus or timed check retries.
    }
    return false;
  }

  function scheduleUpdateChecks() {
    if (updateTimer) window.clearInterval(updateTimer);
    window.setTimeout(checkForUpdate, 4000);
    updateTimer = window.setInterval(checkForUpdate, UPDATE_CHECK_MS);
  }

  function refreshBrowserToLatest() {
    const position = capturePosition();
    try {
      sessionStorage.setItem(resumeAfterRefreshKey, JSON.stringify(position));
    } catch (error) { /* Optional convenience. */ }
    persistReadingState({ immediate: true });
    const url = new URL(window.location.href);
    url.searchParams.set('_refresh', String(Date.now()));
    url.hash = '';
    window.location.replace(url.toString());
  }

  function openHashDetails(hash) {
    if (!hash || !hash.startsWith('#')) return;
    const target = document.getElementById(decodeURIComponent(hash.slice(1)));
    if (target instanceof HTMLDetailsElement) target.open = true;
  }

  function restoreAfterRefresh() {
    let resumePositionData = null;
    try {
      const raw = sessionStorage.getItem(resumeAfterRefreshKey);
      if (raw) resumePositionData = normalizePosition(JSON.parse(raw));
      sessionStorage.removeItem(resumeAfterRefreshKey);
    } catch (error) { /* Optional convenience. */ }
    const url = new URL(window.location.href);
    if (url.searchParams.has('_refresh')) {
      url.searchParams.delete('_refresh');
      window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
    }
    if (resumePositionData) window.setTimeout(() => resumePosition(resumePositionData, { instant: true, quiet: true }), 140);
  }

  tocLinks = buildToc();
  headings = content ? [...content.querySelectorAll(':scope > h2')] : [];
  observeHeadings(tocLinks);
  setThemeLabel();
  formatMetricNumbers();
  readingState = readReadingState();
  currentPosition = capturePosition();
  renderReadingState();
  updateProgress();
  scheduleUpdateChecks();
  restoreAfterRefresh();

  tocSearch?.addEventListener('input', (event) => {
    const query = event.target.value.trim().toLowerCase();
    tocLinks.forEach((link) => link.closest('li')?.classList.toggle('is-filtered', !link.dataset.searchText.includes(query)));
  });

  themeButton?.addEventListener('click', toggleTheme);
  readingButton?.addEventListener('click', () => readingState.furthest ? resumePosition(readingState.furthest) : goToSectionOne());
  quickBookmarkButton?.addEventListener('click', () => {
    const saved = saveManualBookmark();
    quickBookmarkButton.classList.add('just-saved');
    window.setTimeout(() => quickBookmarkButton.classList.remove('just-saved'), 700);
    if (saved) showReadingNotice(`${saved.name} saved. Use the bookmark manager to add or edit a ticket reference and note.`);
  });
  saveNamedBookmarkButton?.addEventListener('click', () => saveManualBookmark(
    bookmarkName?.value || '',
    bookmarkReference?.value || '',
    bookmarkNote?.value || ''
  ));
  [bookmarkName, bookmarkReference].forEach((field) => field?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      saveManualBookmark(bookmarkName?.value || '', bookmarkReference?.value || '', bookmarkNote?.value || '');
    }
  }));
  bookmarkNote?.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      saveManualBookmark(bookmarkName?.value || '', bookmarkReference?.value || '', bookmarkNote.value || '');
    }
  });
  bookmarkList?.addEventListener('click', handleBookmarkAction);
  sidebarBookmarkList?.addEventListener('click', handleBookmarkAction);
  returnMarker?.addEventListener('click', () => resumePosition(readingState.furthest));
  resumeSidebarButton?.addEventListener('click', () => resumePosition(readingState.furthest));
  startOverButton?.addEventListener('click', goToSectionOne);
  openBookmarksButton?.addEventListener('click', openBookmarkManager);
  clearReadingDataButton?.addEventListener('click', clearReadingData);
  refreshUpdateButton?.addEventListener('click', refreshBrowserToLatest);
  dismissUpdateButton?.addEventListener('click', () => {
    if (pendingBuildId) {
      try { sessionStorage.setItem(dismissedUpdateKey, pendingBuildId); } catch (error) { /* Session dismissal is optional. */ }
    }
    hideUpdateNotice();
  });
  backToTop?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  window.addEventListener('scroll', requestProgressUpdate, { passive: true });
  window.addEventListener('resize', () => { currentPosition = capturePosition(); requestProgressUpdate(); });
  window.addEventListener('focus', checkForUpdate);
  window.addEventListener('online', checkForUpdate);
  if (typeof compactHeader.addEventListener === 'function') compactHeader.addEventListener('change', setReadingLabels);
  else if (typeof compactHeader.addListener === 'function') compactHeader.addListener(setReadingLabels);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForUpdate();
  });

  navToggle?.addEventListener('click', () => {
    const isOpen = docnav?.classList.toggle('open') || false;
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });

  document.querySelectorAll('a[href^="#"]').forEach((link) => link.addEventListener('click', () => openHashDetails(link.hash)));
  [...tocLinks, ...staticNavLinks].forEach((link) => link.addEventListener('click', () => {
    if (window.matchMedia('(max-width: 980px)').matches) {
      docnav?.classList.remove('open');
      navToggle?.setAttribute('aria-expanded', 'false');
    }
  }));

  document.addEventListener('click', (event) => {
    if (editMenu?.open && !editMenu.contains(event.target)) editMenu.open = false;
    if (bookmarkMenu?.open && bookmarkControl && !bookmarkControl.contains(event.target)) bookmarkMenu.open = false;
  });

  if (window.location.hash) {
    openHashDetails(window.location.hash);
    const hashTarget = document.getElementById(decodeURIComponent(window.location.hash.slice(1)));
    window.setTimeout(() => hashTarget?.scrollIntoView(), 0);
  }

  if (body?.dataset.previewUpdateDemo === 'true') {
    window.setTimeout(() => showUpdateNotice({
      build_id: 'preview-new-build',
      document_version: body.dataset.documentVersion,
      template_version: body.dataset.templateVersion
    }, { demo: true }), 3500);
  }

  window.controlledManualPage = {
    getReadingState: () => JSON.parse(JSON.stringify(readingState)),
    getCurrentPosition: () => capturePosition(),
    getFurthestRead: () => readingState.furthest,
    getBookmarks: () => [...readingState.bookmarks],
    saveBookmark: (name, reference, note) => saveManualBookmark(name, reference, note),
    updateBookmark: (bookmarkId, values) => updateManualBookmark(bookmarkId, values),
    resumeFurthest: () => resumePosition(readingState.furthest),
    goToSectionOne,
    clearReadingData,
    checkForUpdate,
    refreshBrowserToLatest
  };
}());
